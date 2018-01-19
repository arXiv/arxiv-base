#!/bin/sh

# The status endpoint will differ based on whether this is a PR or commit.
if [ "$TRAVIS_PULL_REQUEST_SHA" = "" ];  then SHA=$TRAVIS_COMMIT; else SHA=$TRAVIS_PULL_REQUEST_SHA; fi

# Check that base builds
docker build -t arxiv-base:latest ./arxiv-base
DOCKER_BUILD_BASE_STATUS=$?
if [ $DOCKER_BUILD_BASE_STATUS -ne 0 ]; then
    DOCKER_BUILD_BASE_STATE="failure" && echo "docker build base failed";
else DOCKER_BUILD_BASE_STATE="success" &&  echo "docker build base passed";
fi

curl -u $USERNAME:$GITHUB_TOKEN \
    -d '{"state": "'$DOCKER_BUILD_BASE_STATE'", "target_url": "https://travis-ci.org/'$TRAVIS_REPO_SLUG'/builds/'$TRAVIS_BUILD_ID'", "description": "", "context": "docker/buildbase"}' \
    -XPOST https://api.github.com/repos/$TRAVIS_REPO_SLUG/statuses/$SHA \
    > /dev/null 2>&1


# Check that zero builds
docker build -t arxiv-zero:latest .
DOCKER_BUILD_ZERO_STATUS=$?
if [ $DOCKER_BUILD_ZERO_STATUS -ne 0 ]; then
    DOCKER_BUILD_ZERO_STATE="failure" && echo "docker build zero failed";
else DOCKER_BUILD_ZERO_STATE="success" &&  echo "docker build zero passed";
fi

curl -u $USERNAME:$GITHUB_TOKEN \
    -d '{"state": "'$DOCKER_BUILD_ZERO_STATE'", "target_url": "https://travis-ci.org/'$TRAVIS_REPO_SLUG'/builds/'$TRAVIS_BUILD_ID'", "description": "", "context": "docker/build"}' \
    -XPOST https://api.github.com/repos/$TRAVIS_REPO_SLUG/statuses/$SHA \
    > /dev/null 2>&1


# Check that zero runs
docker run -d -p 8000:8000 --name arxiv-zero-test arxiv-zero
DOCKER_RUN_ZERO_STATUS=$?
if [ $DOCKER_RUN_ZERO_STATUS -ne 0 ]; then
    DOCKER_RUN_ZERO_STATE="failure" && echo "docker run zero failed";
else DOCKER_RUN_ZERO_STATE="success" &&  echo "docker run zero passed";
fi

curl -u $USERNAME:$GITHUB_TOKEN \
    -d '{"state": "'$DOCKER_RUN_ZERO_STATE'", "target_url": "https://travis-ci.org/'$TRAVIS_REPO_SLUG'/builds/'$TRAVIS_BUILD_ID'", "description": "", "context": "docker/run"}' \
    -XPOST https://api.github.com/repos/$TRAVIS_REPO_SLUG/statuses/$SHA \
    > /dev/null 2>&1

# Check service is running as expected
curl http://localhost:8000/zero/api/status | grep "nobody but us"
CURL_TEST_ZERO_STATUS=$?
if [ $CURL_TEST_ZERO_STATUS -ne 0 ]; then
    CURL_TEST_ZERO_STATE="failure" && echo "curl failed";
else CURL_TEST_ZERO_STATE="success" &&  echo "curl passed";
fi

curl -u $USERNAME:$GITHUB_TOKEN \
    -d '{"state": "'$CURL_TEST_ZERO_STATE'", "target_url": "https://travis-ci.org/'$TRAVIS_REPO_SLUG'/builds/'$TRAVIS_BUILD_ID'", "description": "", "context": "curl/basic"}' \
    -XPOST https://api.github.com/repos/$TRAVIS_REPO_SLUG/statuses/$SHA \
    > /dev/null 2>&1


docker rm -f arxiv-zero-test
