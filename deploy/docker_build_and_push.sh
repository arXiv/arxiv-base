#!/bin/bash
set -o errexit

if [ -z $1 ]; then
    echo 'docker build context required, ex ./ or ./somedir'; exit 1
fi
if [ -z $2 ]; then
    echo 'docker image name required, ex arxiv/base'; exit 1
fi
if [ -z $3 ]; then
    echo 'docker tag required, ex 0.1.3'; exit1
fi

BUILD_DIR=$1
IMAGE_NAME=$2
TAG=$3

echo "$DOCKERHUB_PASSWORD" | docker login --username "$DOCKERHUB_USERNAME" --password-stdin

docker login -u "$DOCKERHUB_USERNAME" -p "$DOCKERHUB_PASSWORD"
docker build -t ${IMAGE_NAME}:${TAG} --build-arg BUILD_TIME="$(date)"
docker push ${IMAGE_NAME}:${TAG}

# echo "docker build $1 -t $2"
# docker build "$1" -t "$2"
# echo "docker push $2"
# docker push "$2"
docker logout

