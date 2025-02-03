# Use the official Python image as a base image
FROM python:3-slim

# Set the working directory in the container
WORKDIR /app

# Install pip-chill
RUN pip install --no-cache-dir pip-chill

# Copy the application code into the container
COPY . /app

# Generate requirements.txt with pip-chill
#RUN pip-chill > requirements.txt

# Install the required packages based on the newly created requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create a directory for the configuration files
RUN mkdir /config

# Expose the port that Streamlit will run on
EXPOSE 8501

# Declare a volume (this creates a mount point inside the container)
VOLUME ["/app"]

# Command to run the Streamlit app
CMD ["python","-m","streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
