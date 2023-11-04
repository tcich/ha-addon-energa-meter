docker build -t energa-meter:latest .
docker build -t energa-meter:v0.1.6-dev .




docker run -p 8000:8000 -e ENERGA_USERNAME=plkp.roz.z2@gmail.com -e ENERGA_PASSWORD=1WUnSnbdnbGempSzEahh energa-meter:v0.1.6-dev