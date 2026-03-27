docker build -t api-orders:v1 .

docker tag api-orders:v1 xxxxxxxx.dkr.ecr.eu-central-1.amazonaws.com/formation/tp-orders:v1

aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin xxxxxx.dkr.ecr.eu-central-1.amazonaws.com