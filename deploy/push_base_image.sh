#!/bin/bash
set -o errexit

docker login -u "$DOCKERHUB_USERNAME" -p "$DOCKERHUB_PASSWORD"
docker build . -t arxiv/base:${TRAVIS_COMMIT};
docker push arxiv/base:${TRAVIS_COMMIT}
