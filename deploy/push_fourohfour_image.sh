#!/bin/bash
set -o errexit

docker login -u "$DOCKERHUB_USERNAME" -p "$DOCKERHUB_PASSWORD"
docker build ./fourohfour -t arxiv/fourohfour:${TRAVIS_COMMIT};
docker push arxiv/fourohfour:${TRAVIS_COMMIT}
