# Dockerfile
#FROM python:3.9-slim-buster
FROM python:3

WORKDIR /app

# Copy requirements.txt first to leverage Docker cache
#COPY requirements.txt requirements.txt
#RUN pip install -r requirements.txt

RUN pip install Flask
RUN pip install flask_mysqldb
RUN pip install pika

COPY . /app

# Set environment variables for MySQL connection
#ENV MYSQL_HOST=mysql  
ENV MYSQL_HOST=localhost 

# IMPORTANT  Use the service name
ENV MYSQL_USER=root

#ENV MYSQL_PASSWORD=password 
ENV MYSQL_PASSWORD=root123 

#  Change this  Use a Kubernetes secret.
ENV MYSQL_DB=suppliers_db

CMD ["python", "supplier_service.py"]