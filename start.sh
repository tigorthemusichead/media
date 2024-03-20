sudo docker build --tag transcriber .
sudo docker run -d -p 80:5000 transcriber
