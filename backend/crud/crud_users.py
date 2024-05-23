import os
import glob
import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from urllib.parse import unquote

from schemas import schema_users
import models

# Define a loggger created on main.py
logger = logging.getLogger("myLogger")

def delete_user_photo_filesystem(user_id: int):
    # Define the pattern to match files with the specified name regardless of the extension
    folder = "user_images"
    file = f"{user_id}.*"

    print(os.path.join(folder, file))

    # Find all files matching the pattern
    files_to_delete = glob.glob(os.path.join(folder, file))

    print(f"Files to delete: {files_to_delete}")

    # Remove each file found
    for file_path in files_to_delete:
        print(f"Deleting: {file_path}")
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted: {file_path}")


def format_user_birthdate(user):
    user.birthdate = user.birthdate.strftime("%Y-%m-%d") if user.birthdate else None
    return user


def authenticate_user(username: str, password: str, db: Session):
    try:
        # Get the user from the database
        user = (
            db.query(models.User)
            .filter(
                models.User.username == username, models.User.password == password
            )
            .first()
        )

        # Check if the user exists and if the password is correct and if not return None
        if not user:
            return None

        # Return the user if the password is correct
        return user
    except Exception as err:
        # Log the exception
        logger.error(f"Error in authenticate_user: {err}", exc_info=True)
        # Raise an HTTPException with a 500 Internal Server Error status code
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from err


def get_all_users(db: Session):
    try:
        # Get the number of users from the database
        return db.query(models.User).all()
    except Exception as err:
        # Log the exception
        logger.error(f"Error in get_all_number: {err}", exc_info=True)
        # Raise an HTTPException with a 500 Internal Server Error status code
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from err


def get_users_number(db: Session):
    try:
        # Get the number of users from the database
        return db.query(models.User).count()
    except Exception as err:
        # Log the exception
        logger.error(f"Error in get_users_number: {err}", exc_info=True)
        # Raise an HTTPException with a 500 Internal Server Error status code
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from err


def get_users_with_pagination(db: Session, page_number: int = 1, num_records: int = 5):
    try:
        # Get the users from the database
        users = (
            db.query(models.User)
            .offset((page_number - 1) * num_records)
            .limit(num_records)
            .all()
        )

        # If the users were not found, return None
        if not users:
            return None

        # Format the birthdate
        for user in users:
            user = format_user_birthdate(user)

        # Return the users
        return users
    except Exception as err:
        # Log the exception
        logger.error(f"Error in get_users_with_pagination: {err}", exc_info=True)
        # Raise an HTTPException with a 500 Internal Server Error status code
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from err


def get_user_if_contains_username(username: str, db: Session):
    try:
        # Define a search term
        partial_username = unquote(username).replace("+", " ")

        # Get the user from the database
        users = (
            db.query(models.User)
            .filter(models.User.username.like(f"%{partial_username}%"))
            .all()
        )

        # If the user was not found, return None
        if users is None:
            return None

        # Format the birthdate
        for user in users:
            user = format_user_birthdate(user)

        # Return the user
        return users
    except Exception as err:
        # Log the exception
        logger.error(f"Error in get_user_if_contains_username: {err}", exc_info=True)
        # Raise an HTTPException with a 500 Internal Server Error status code
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from err


def get_user_by_username(username: str, db: Session):
    try:
        # Get the user from the database
        user = db.query(models.User).filter(models.User.username == username).first()

        # If the user was not found, return None
        if user is None:
            return None

        # Format the birthdate
        user = format_user_birthdate(user)

        # Return the user
        return user
    except Exception as err:
        # Log the exception
        logger.error(f"Error in get_user_by_username: {err}", exc_info=True)
        # Raise an HTTPException with a 500 Internal Server Error status code
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from err


def get_user_by_id(user_id: int, db: Session):
    try:
        # Get the user from the database
        user = db.query(models.User).filter(models.User.id == user_id).first()

        # If the user was not found, return None
        if user is None:
            return None

        # Format the birthdate
        user = format_user_birthdate(user)

        # Return the user
        return user
    except Exception as err:
        # Log the exception
        logger.error(f"Error in get_user_by_id: {err}", exc_info=True)
        # Raise an HTTPException with a 500 Internal Server Error status code
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from err


def get_user_id_by_username(username: str, db: Session):
    try:
        # Get the user from the database
        user_id = (
            db.query(models.User.id)
            .filter(models.User.username == unquote(username).replace("+", " "))
            .first()
        )

        # If the user was not found, return None
        if user_id is None:
            return None

        # Return the user id
        return user_id
    except Exception as err:
        # Log the exception
        logger.error(f"Error in get_user_id_by_username: {err}", exc_info=True)
        # Raise an HTTPException with a 500 Internal Server Error status code
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from err


def get_user_photo_path_by_id(user_id: int, db: Session):
    try:
        # Get the user from the database
        user_db = (
            db.query(models.User.photo_path).filter(models.User.id == user_id).first()
        )

        # If the user was not found, return None
        if user_db is None:
            return None

        # Return the user
        return user_db.photo_path
    except Exception as err:
        # Log the exception
        logger.error(f"Error in get_user_photo_path_by_id: {err}", exc_info=True)
        # Raise an HTTPException with a 500 Internal Server Error status code
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from err


def get_user_photo_path_aux_by_id(user_id: int, db: Session):
    try:
        # Get the user from the database
        user_db = (
            db.query(models.User.photo_path_aux)
            .filter(models.User.id == user_id)
            .first()
        )

        # If the user was not found, return None
        if user_db is None:
            return None

        # Return the photo_path_aux value directly
        return user_db.photo_path_aux
    except Exception as err:
        # Log the exception
        logger.error(f"Error in get_user_photo_path_aux_by_id: {err}", exc_info=True)
        # Raise an HTTPException with a 500 Internal Server Error status code
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from err


def create_user(user: schema_users.UserCreate, db: Session):
    try:
        # Create a new user
        db_user = models.User(
            name=user.name,
            username=user.username,
            password=user.password,
            email=user.email,
            city=user.city,
            birthdate=user.birthdate,
            preferred_language=user.preferred_language,
            gender=user.gender,
            access_type=user.access_type,
            photo_path=user.photo_path,
            photo_path_aux=user.photo_path_aux,
            is_active=user.is_active,
        )

        # Add the user to the database
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # Return the user
        return db_user
    except IntegrityError as integrity_error:
        # Rollback the transaction
        db.rollback()

        # Raise an HTTPException with a 500 Internal Server Error status code
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate entry error. Check if email and username are unique",
        ) from integrity_error
    except Exception as err:
        # Rollback the transaction
        db.rollback()

        # Log the exception
        logger.error(f"Error in create_user: {err}", exc_info=True)

        # Raise an HTTPException with a 500 Internal Server Error status code
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from err


def edit_user(user: schema_users.User, db: Session):
    try:
        # Get the user from the database
        db_user = db.query(models.User).filter(models.User.id == user.id).first()

        # Update the user
        if user.name is not None:
            db_user.name = user.name
        if user.username is not None:
            db_user.username = user.username
        if user.email is not None:
            db_user.email = user.email
        if user.city is not None:
            db_user.city = user.city
        if user.birthdate is not None:
            db_user.birthdate = user.birthdate
        if user.preferred_language is not None:
            db_user.preferred_language = user.preferred_language
        if user.gender is not None:
            db_user.gender = user.gender
        if user.access_type is not None:
            db_user.access_type = user.access_type
        if user.photo_path is not None:
            db_user.photo_path = user.photo_path
        if user.photo_path_aux is not None:
            db_user.photo_path_aux = user.photo_path_aux
        if user.is_active is not None:
            db_user.is_active = user.is_active

        # Commit the transaction
        db.commit()

        if db_user.photo_path is None:
            # Delete the user photo in the filesystem
            delete_user_photo_filesystem(db_user.id)
    except IntegrityError as integrity_error:
        # Rollback the transaction
        db.rollback()

        # Raise an HTTPException with a 500 Internal Server Error status code
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate entry error. Check if email and username are unique",
        ) from integrity_error
    except Exception as err:
        # Rollback the transaction
        db.rollback()

        # Log the exception
        logger.error(f"Error in edit_user: {err}", exc_info=True)

        # Raise an HTTPException with a 500 Internal Server Error status code
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from err


def edit_user_password(user_id: int, password: str, db: Session):
    try:
        # Get the user from the database
        db_user = db.query(models.User).filter(models.User.id == user_id).first()

        # Update the user
        db_user.password = password

        # Commit the transaction
        db.commit()
    except Exception as err:
        # Rollback the transaction
        db.rollback()

        # Log the exception
        logger.error(f"Error in edit_user_password: {err}", exc_info=True)

        # Raise an HTTPException with a 500 Internal Server Error status code
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from err
    

def edit_user_photo_path(user_id: int, photo_path: str, db: Session):
    try:
        # Get the user from the database
        db_user = db.query(models.User).filter(models.User.id == user_id).first()

        # Update the user
        db_user.photo_path = photo_path

        # Commit the transaction
        db.commit()

        # Return the photo path
        return photo_path
    except Exception as err:
        # Rollback the transaction
        db.rollback()

        # Log the exception
        logger.error(f"Error in edit_user_photo_path: {err}", exc_info=True)

        # Raise an HTTPException with a 500 Internal Server Error status code
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from err


def delete_user_photo(user_id: int, db: Session):
    try:
        # Get the user from the database
        db_user = db.query(models.User).filter(models.User.id == user_id).first()

        # Update the user
        db_user.photo_path = None
        db_user.photo_path_aux = None

        # Commit the transaction
        db.commit()

        # Delete the user photo in the filesystem
        delete_user_photo_filesystem(user_id)
    except Exception as err:
        # Rollback the transaction
        db.rollback()

        # Log the exception
        logger.error(f"Error in delete_user_photo: {err}", exc_info=True)

        # Raise an HTTPException with a 500 Internal Server Error status code
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from err


def delete_user(user_id: int, db: Session):
    try:
        # Delete the user
        num_deleted = db.query(models.User).filter(models.User.id == user_id).delete()

        # Check if the user was found and deleted
        if num_deleted == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found",
            )

        # Commit the transaction
        db.commit()

        # Delete the user photo in the filesystem
        delete_user_photo_filesystem(user_id)
    except Exception as err:
        # Rollback the transaction
        db.rollback()

        # Log the exception
        logger.error(f"Error in delete_user: {err}", exc_info=True)

        # Raise an HTTPException with a 500 Internal Server Error status code
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from err
