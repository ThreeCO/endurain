# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Create a virtual environment and install dependencies
RUN python -m venv /venv
ENV PATH=/venv/bin:$PATH
# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
#ENV NAME World
ENV DB_HOST=""
ENV DB_PORT=3306
ENV DB_USER=""
ENV DB_PASSWORD=""
ENV DB_DATABASE=""
ENV SECRET_KEY=""
ENV ALGORITHM="HS256"
ENV ACCESS_TOKEN_EXPIRE_MINUTES=30
ENV STRAVA_CLIENT_ID=""
ENV STRAVA_CLIENT_SECRET=""
ENV STRAVA_AUTH_CODE=""
ENV JAEGER_HOST=""
ENV STRAVA_DAYS_ACTIVITIES_ONLINK=30

# Run app.py when the container launches
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]