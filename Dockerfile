
# Specify the base image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBUG 0
ENV PORT 80

# Expose a port for the API
EXPOSE 80

# Specify the command to run the application
CMD ["python", "api/app.py"]