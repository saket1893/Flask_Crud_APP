docker build -t flask-crud-api .

docker run -d -p 5000:5000 flask-crud-api:latest

docker run -d -p 5001:5001 -v {LocalDirectorryPath}:/app flask-crud-api:latest

