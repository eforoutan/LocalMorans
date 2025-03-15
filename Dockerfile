FROM python:3.9-slim

# Install necessary Python packages
RUN pip install geopandas libpysal esda matplotlib

# Set the working directory in the container
WORKDIR /app

# Copy the Python script into the container
COPY calc_local_morans.py /app/calc_local_morans.py

# Set the ENTRYPOINT to the Python script
# This allows passing arguments directly to the script at runtime
ENTRYPOINT ["python", "/app/calc_local_morans.py"]
