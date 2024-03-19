docker build --tag transcriber .
docker run -d -p 80:5000 transcriber
