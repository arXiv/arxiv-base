#!/bin/bash
set -o errexit

if [ -z $1 ]; then
    echo 'docker build context required, ex ./ or ./somedir'; exit 1
fi
if [ -z $2 ]; then
    echo 'docker name:tag required'; exit 1
fi

echo "$DOCKER_PASSWORD" | docker login --username "$DOCKER_USERNAME" --password-stdin
echo "docker build $1 -t $2"
echo "docker push $2"
