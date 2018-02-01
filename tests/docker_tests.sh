#!/bin/sh

# The status endpoint will differ based on whether this is a PR or commit.
if [ "$TRAVIS_PULL_REQUEST_SHA" = "" ];  then SHA=$TRAVIS_COMMIT; else SHA=$TRAVIS_PULL_REQUEST_SHA; fi

# Check that base builds
docker build -t arxiv-base:latest -f ./Dockerfile .
DOCKER_BUILD_BASE_STATUS=$?
if [ $DOCKER_BUILD_BASE_STATUS -ne 0 ]; then
    DOCKER_BUILD_BASE_STATE="failure" && echo "docker build base failed";
else DOCKER_BUILD_BASE_STATE="success" &&  echo "docker build base passed";
fi

curl -u $USERNAME:$GITHUB_TOKEN \
    -d '{"state": "'$DOCKER_BUILD_BASE_STATE'", "target_url": "https://travis-ci.org/'$TRAVIS_REPO_SLUG'/builds/'$TRAVIS_BUILD_ID'", "description": "", "context": "docker/buildbase"}' \
    -XPOST https://api.github.com/repos/$TRAVIS_REPO_SLUG/statuses/$SHA \
    > /dev/null 2>&1
