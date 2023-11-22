import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from db.db import get_db_session, User, Activity
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from stravalib.client import Client
from pint import Quantity
from concurrent.futures import ThreadPoolExecutor
from fastapi import BackgroundTasks
import logging
import requests

router = APIRouter()

logger = logging.getLogger("myLogger")

# Load the environment variables from config/.env
load_dotenv("config/.env")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Strava route to link user Strava account
@router.get("/strava/strava-callback")
async def strava_callback(state: str, code: str, background_tasks: BackgroundTasks):
    token_url = "https://www.strava.com/oauth/token"
    payload = {
        "client_id": os.getenv("STRAVA_CLIENT_ID"),
        "client_secret": os.getenv("STRAVA_CLIENT_SECRET"),
        "code": code,
        "grant_type": "authorization_code",
    }
    try:
        response = requests.post(token_url, data=payload)
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Error retrieving tokens from Strava.",
            )

        tokens = response.json()

        with get_db_session() as db_session:
            # Query the activities records using SQLAlchemy
            db_user = db_session.query(User).filter(User.strava_state == state).first()

            if db_user:
                db_user.strava_token = tokens["access_token"]
                db_user.strava_refresh_token = tokens["refresh_token"]
                db_user.strava_token_expires_at = datetime.fromtimestamp(
                    tokens["expires_at"]
                )
                db_session.commit()  # Commit the changes to the database

                # get_strava_activities((datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%SZ"))
                background_tasks.add_task(
                    get_user_strava_activities,
                    (datetime.utcnow() - timedelta(days=90)).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                    db_user.id,
                )

                # Redirect to the main page or any other desired page after processing
                redirect_url = "https://gearguardian.jvslab.pt/settings/settings.php?profileSettings=1&stravaLinked=1"  # Change this URL to your main page
                return RedirectResponse(url=redirect_url)
            else:
                raise HTTPException(status_code=404, detail="User not found.")

    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    except NameError as err:
        print(err)


# Strava logic to refresh user Strava account refresh account
def refresh_strava_token():
    # Strava token refresh endpoint
    token_url = "https://www.strava.com/oauth/token"

    try:
        with get_db_session() as db_session:
            # Query all users from the database
            users = db_session.query(User).all()

            for user in users:
                # expires_at = user.strava_token_expires_at
                if user.strava_token_expires_at is not None:
                    refresh_time = user.strava_token_expires_at - timedelta(minutes=60)

                    if datetime.utcnow() > refresh_time:
                        # Parameters for the token refresh request
                        payload = {
                            "client_id": os.getenv("STRAVA_CLIENT_ID"),
                            "client_secret": os.getenv("STRAVA_CLIENT_SECRET"),
                            "refresh_token": user.strava_refresh_token,
                            "grant_type": "refresh_token",
                        }

                        try:
                            # Make a POST request to refresh the Strava token
                            response = requests.post(token_url, data=payload)
                            response.raise_for_status()  # Raise an error for bad responses

                            tokens = response.json()

                            # Update the user in the database
                            db_user = (
                                db_session.query(User)
                                .filter(User.id == user.id)
                                .first()
                            )

                            if db_user:
                                db_user.strava_token = tokens["access_token"]
                                db_user.strava_refresh_token = tokens["refresh_token"]
                                db_user.strava_token_expires_at = (
                                    datetime.fromtimestamp(tokens["expires_at"])
                                )
                                db_session.commit()  # Commit the changes to the database
                                logger.info(
                                    f"Token refreshed successfully for user {user.id}."
                                )
                            else:
                                logger.error("User not found in the database.")
                        except requests.exceptions.RequestException as req_err:
                            logger.error(
                                f"Error refreshing token for user {user.id}: {req_err}"
                            )
                    else:
                        logger.info(
                            f"Token not refreshed for user {user.id}. Will not expire in less than 60min"
                        )
                else:
                    logger.info(f"User {user.id} does not have strava linked")
    except NameError as db_err:
        logger.error(f"Database error: {db_err}")


# Define an HTTP PUT route set strava unique state for link logic
@router.put("/strava/set-user-unique-state/{state}")
async def strava_set_user_unique_state(state: str, token: str = Depends(oauth2_scheme)):
    from . import sessionController

    try:
        # Validate the user's access token using the oauth2_scheme
        sessionController.validate_token(token)

        with get_db_session() as db_session:
            payload = jwt.decode(
                token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")]
            )
            user_id = payload.get("id")

            # Query the database to find the user by their ID
            user = db_session.query(User).filter(User.id == user_id).first()

            # Check if the user with the given ID exists
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # Set the user's photo paths to None to delete the photo
            user.strava_state = state

            # Commit the changes to the database
            db_session.commit()
    except JWTError:
        # Handle JWT (JSON Web Token) authentication error
        raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception as err:
        # Handle any other unexpected exceptions
        print(err)
        raise HTTPException(
            status_code=500, detail="Failed to update user strava state"
        )

    # Return a success message
    return {"message": f"Strava state for user {user_id} has been updated"}


# Define an HTTP PUT route set strava unique state for link logic
@router.put("/strava/unset-user-unique-state")
async def strava_unset_user_unique_state(token: str = Depends(oauth2_scheme)):
    from . import sessionController

    try:
        # Validate the user's access token using the oauth2_scheme
        sessionController.validate_token(token)

        with get_db_session() as db_session:
            payload = jwt.decode(
                token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")]
            )
            user_id = payload.get("id")

            # Query the database to find the user by their ID
            user = db_session.query(User).filter(User.id == user_id).first()

            # Check if the user with the given ID exists
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # Set the user's photo paths to None to delete the photo
            user.strava_state = None

            # Commit the changes to the database
            db_session.commit()
    except JWTError:
        # Handle JWT (JSON Web Token) authentication error
        raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception as err:
        # Handle any other unexpected exceptions
        print(err)
        raise HTTPException(
            status_code=500, detail="Failed to update user strava state"
        )

    # Return a success message
    return {"message": f"Strava state for user {user_id} has been updated"}


# Strava logic to refresh user Strava account refresh account
def get_strava_activities(start_date: datetime):
    try:
        with get_db_session() as db_session:
            # Query all users from the database
            users = db_session.query(User).all()

            for user in users:
                if user.strava_token_expires_at is not None:
                    stravaClient = Client(access_token=user.strava_token)

                    strava_activities = list(
                        stravaClient.get_activities(after=start_date)
                    )
                    chunk_size = (
                        len(strava_activities) // 4
                    )  # Adjust the number of threads as needed

                    # activity_chunks = [
                    #     strava_activities[i : i + chunk_size]
                    #     for i in range(0, len(strava_activities), chunk_size)
                    # ]

                    # with ThreadPoolExecutor() as executor:
                    #     # Process each chunk of activities using threads
                    #     results = list(
                    #         executor.map(
                    #             lambda chunk: process_activities(
                    #                 chunk, user.id, stravaClient
                    #             ),
                    #             activity_chunks,
                    #         )
                    #     )

                    # Check if chunk_size is zero
                    for i in (
                        range(0, len(strava_activities), chunk_size)
                        if chunk_size > 0
                        else [0]
                    ):
                        activity_chunk = strava_activities[i : i + chunk_size]

                        with ThreadPoolExecutor() as executor:
                            results = list(
                                executor.map(
                                    lambda chunk: process_activities(
                                        chunk, user.id, stravaClient
                                    ),
                                    [activity_chunk],  # Wrap in a list for map
                                )
                            )

                    # Flatten the list of results
                    activities_to_insert = [
                        activity for sublist in results for activity in sublist
                    ]

                    # Bulk insert all activities
                    with get_db_session() as db_session:
                        db_session.bulk_save_objects(activities_to_insert)
                        db_session.commit()

                else:
                    logger.info(f"User {user.id} does not have strava linked")
    except NameError as db_err:
        logger.error(f"Database error: {db_err}")


# Strava logic to refresh user Strava account refresh account
def get_user_strava_activities(start_date: datetime, user_id: int):
    with get_db_session() as db_session:
        db_user = db_session.query(User).get(user_id)

        if db_user:
            if db_user.strava_token_expires_at is not None:
                stravaClient = Client(access_token=db_user.strava_token)

                strava_activities = list(stravaClient.get_activities(after=start_date))
                chunk_size = (
                    len(strava_activities) // 4
                )  # Adjust the number of threads as needed

                # activity_chunks = [
                #     strava_activities[i : i + chunk_size]
                #     for i in range(0, len(strava_activities), chunk_size)
                # ]

                # with ThreadPoolExecutor() as executor:
                #     # Process each chunk of activities using threads
                #     results = list(
                #         executor.map(
                #             lambda chunk: process_activities(
                #                 chunk, db_user.id, stravaClient
                #             ),
                #             activity_chunks,
                #         )
                #     )

                # Check if chunk_size is zero
                for i in (
                    range(0, len(strava_activities), chunk_size)
                    if chunk_size > 0
                    else [0]
                ):
                    activity_chunk = strava_activities[i : i + chunk_size]

                    with ThreadPoolExecutor() as executor:
                        results = list(
                            executor.map(
                                lambda chunk: process_activities(
                                    chunk, db_user.id, stravaClient
                                ),
                                [activity_chunk],  # Wrap in a list for map
                            )
                        )

                # Flatten the list of results
                activities_to_insert = [
                    activity for sublist in results for activity in sublist
                ]

                # Bulk insert all activities
                with get_db_session() as db_session:
                    db_session.bulk_save_objects(activities_to_insert)
                    db_session.commit()

            else:
                logger.info(f"User {db_user.id} does not have strava linked")
        else:
            logger.info(f"User with ID {user_id} not found.")


def process_activities(strava_activities, user_id, stravaClient):
    activities_to_insert = []

    for activity in strava_activities:
        with get_db_session() as db_session:
            activity_record = (
                db_session.query(Activity)
                .filter(Activity.strava_activity_id == activity.id)
                .first()
            )

            if activity_record:
                continue  # Skip existing activities

            # Process the activity and append to the list
            processed_activity = process_activity(activity, user_id, stravaClient)
            activities_to_insert.append(processed_activity)

    return activities_to_insert


def process_activity(activity, user_id, stravaClient):
    start_date_parsed = activity.start_date
    # Ensure activity.elapsed_time is a numerical value
    elapsed_time_seconds = (
        activity.elapsed_time.total_seconds()
        if isinstance(activity.elapsed_time, timedelta)
        else activity.elapsed_time
    )
    end_date_parsed = start_date_parsed + timedelta(seconds=elapsed_time_seconds)

    latitude = 0
    longitude = 0

    if hasattr(activity, "start_latlng") and activity.start_latlng is not None:
        latitude = activity.start_latlng.lat
        longitude = activity.start_latlng.lon

    city = None
    town = None
    country = None
    if latitude != 0 and longitude != 0:
        url = f"https://geocode.maps.co/reverse?lat={latitude}&lon={longitude}"
        try:
            # Make a GET request
            response = requests.get(url)

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                # Parse the JSON response
                data = response.json()

                # Extract the town and country from the address components
                city = data.get("address", {}).get("city", None)
                town = data.get("address", {}).get("town", None)
                country = data.get("address", {}).get("country", None)
            else:
                print(f"Error location: {response.status_code}")
                print(f"Error location: {url}")
        except Exception as e:
            print(f"An error occurred: {e}")

    # List to store constructed waypoints
    waypoints = []

    # Initialize variables for elevation gain and loss
    elevation_gain = 0
    elevation_loss = 0
    previous_elevation = None

    # Get streams for the activity
    streams = stravaClient.get_activity_streams(
        activity.id,
        types=[
            "latlng",
            "altitude",
            "time",
            "heartrate",
            "cadence",
            "watts",
            "velocity_smooth",
        ],
    )

    # Extract data from streams
    latitudes = streams["latlng"].data if "latlng" in streams else []
    longitudes = streams["latlng"].data if "latlng" in streams else []
    elevations = streams["altitude"].data if "altitude" in streams else []
    times = streams["time"].data if "time" in streams else []
    heart_rates = streams["heartrate"].data if "heartrate" in streams else []
    cadences = streams["cadence"].data if "cadence" in streams else []
    powers = streams["watts"].data if "watts" in streams else []
    velocities = streams["velocity_smooth"].data if "velocity_smooth" in streams else []

    for i in range(len(heart_rates)):
        waypoint = {
            "lat": latitudes[i] if i < len(latitudes) else None,
            "lon": longitudes[i] if i < len(longitudes) else None,
            "ele": elevations[i] if i < len(elevations) else None,
            "time": times[i] if i < len(times) else None,
            "hr": heart_rates[i] if i < len(heart_rates) else None,
            "cad": cadences[i] if i < len(cadences) else None,
            "power": powers[i] if i < len(powers) else None,
            "vel": velocities[i] if i < len(velocities) else None,
            "pace": 1 / velocities[i]
            if i < len(velocities) and velocities[i] != 0
            else None,
            # Add other relevant fields based on your requirements
        }

        # Calculate elevation gain and loss on-the-fly
        current_elevation = elevations[i] if i < len(elevations) else None

        if current_elevation is not None:
            if previous_elevation is not None:
                elevation_change = current_elevation - previous_elevation

                if elevation_change > 0:
                    elevation_gain += elevation_change
                else:
                    elevation_loss += abs(elevation_change)

            previous_elevation = current_elevation

        # Append the constructed waypoint to the waypoints list
        waypoints.append(waypoint)

    average_speed = 0
    if activity.average_speed is not None:
        average_speed = (
            float(activity.average_speed.magnitude)
            if isinstance(activity.average_speed, Quantity)
            else activity.average_speed
        )

    average_pace = 1 / average_speed if average_speed != 0 else 0

    average_watts = 0
    if activity.average_watts is not None:
        average_watts = activity.average_watts

    auxType = 10  # Default value
    type_mapping = {
        "running": 1,
        "Run": 1,
        "trail running": 2,
        "TrailRun": 2,
        "VirtualRun": 3,
        "cycling": 4,
        "Ride": 4,
        "GravelRide": 5,
        "EBikeRide": 6,
        "EMountainBikeRide": 6,
        "VirtualRide": 7,
        "virtual_ride": 7,
        "MountainBikeRide": 8,
        "swimming": 9,
        "Swim": 9,
        "open_water_swimming": 9,
        "Workout": 10,
    }
    auxType = type_mapping.get(activity.sport_type, 10)

    # Create a new Activity record
    newActivity = Activity(
        user_id=user_id,
        name=activity.name,
        distance=round(float(activity.distance))
        if isinstance(activity.distance, Quantity)
        else round(activity.distance),
        activity_type=auxType,
        start_time=start_date_parsed,
        end_time=end_date_parsed,
        city=city,
        town=town,
        country=country,
        # created_at=func.now(),  # Use func.now() to set 'created_at' to the current timestamp
        created_at=datetime.utcnow(),
        waypoints=waypoints,
        elevation_gain=elevation_gain,
        elevation_loss=elevation_loss,
        pace=average_pace,
        average_speed=average_speed,
        average_power=average_watts,
        strava_activity_id=activity.id,
    )

    return newActivity
