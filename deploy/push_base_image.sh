#!/bin/bash
set -o errexit

if [ -z "${TRAVIS_TAG}" ]; then
    IMAGE_TAG=${TRAVIS_COMMIT}
else
    IMAGE_TAG=${TRAVIS_TAG}
fi

docker login -u "$DOCKERHUB_USERNAME" -p "$DOCKERHUB_PASSWORD"
docker build . -t arxiv/base:${TRAVIS_COMMIT};
docker push arxiv/base:${IMAGE_TAG}
