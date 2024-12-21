docker build -t flask-crud-api .

docker run -d -p 5000:5000 flask-crud-api:latest

#volume mount
C:/Users/saket/Desktop/Work_1/Python Flask/flask_crud

docker run -d -p 5001:5001 -v C:/Users/saket/Desktop/Work_1/Python Flask/flask_crud:/app flask-crud-api:latest

