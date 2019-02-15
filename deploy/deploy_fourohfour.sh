#!/bin/bash

set -o pipefail
set -o errexit
set -o nounset

# Deploy builds to Kubernetes!
#
# This script can be used to deploy builds to Kubernetes using Helm.
#
# Params:
# - chart name (not including repository name)
# - namespace (used to select other env vars, see below)
#
# Pre-requisites:
# - Must have already provisioned an SA for Tiller, and initialized the Tiller
#   service in the target namespace.
# - Must have already provisioned an SA for Travis in the target namespace.
#   The following env vars should be set, e.g. in the Travis-CI interface:
#   - USER_SA_{namespace} = the service account name
#   - USER_TOKEN_{namespace} = base64-encoded bearer token for the Travis SA.
# - In addition, the following env vars must be set to configure access to
#   the Kubernetes API server:
#   - CLUSTER_ENDPOINT = URI of the K8s API server
#   - CA_CERT = base64 encoded root CA of the K8s cluster
#   - CLUSTER_NAME = the name of the cluster
# - The following env vars must be set for Helm to work:
#   - HELM_REPOSITORY = the location of the arXiv helm repository,
#     e.g. s3://...
#   - HELM_RELEASE_{namespace} = the name of the release that this script will
#     install or upgrade.

CHART_NAME=$1
ENVIRONMENT=$2
TOKEN_NAME=USER_TOKEN_$(echo $ENVIRONMENT | awk '{print toupper($0)}')
SA_NAME=USER_SA_$(echo $ENVIRONMENT | awk '{print toupper($0)}')
RELEASE_NAME=HELM_RELEASE_$(echo $ENVIRONMENT | awk '{print toupper($0)}')
USER_TOKEN=${!TOKEN_NAME}
USER_SA=${!SA_NAME}
HELM_RELEASE=${!RELEASE_NAME}

if [ -z "${TRAVIS_TAG}" ]; then
    IMAGE_TAG=${TRAVIS_COMMIT}
else
    IMAGE_TAG=${TRAVIS_TAG}
fi

echo "Deploying ${CHART_NAME} in ${ENVIRONMENT}"

# Install kubectl & Helm
curl -LO https://storage.googleapis.com/kubernetes-release/release/v1.9.2/bin/linux/amd64/kubectl
chmod +x ./kubectl
sudo mv ./kubectl /usr/local/bin/kubectl
echo "Intalled kubectl"

curl https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get > get_helm.sh
chmod 700 get_helm.sh
sudo ./get_helm.sh -v v2.8.0
echo "Intalled Helm"

# Configure Kubernetes & Helm
echo $CA_CERT | base64 --decode > ${HOME}/ca.crt

kubectl config set-cluster $CLUSTER_NAME --embed-certs=true --server=$CLUSTER_ENDPOINT --certificate-authority=${HOME}/ca.crt
kubectl config set-credentials $USER_SA --token=$(echo $USER_TOKEN | base64 --decode)
kubectl config set-context travis --cluster=$CLUSTER_NAME --user=$USER_SA --namespace=$ENVIRONMENT
kubectl config use-context travis
kubectl config current-context
echo "Configured kubectl"

helm init --client-only --tiller-namespace $ENVIRONMENT
echo "Set up helm client"

# Add S3 repo. Requires AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to be set
# in the environment.
helm plugin install https://github.com/hypnoglow/helm-s3.git
helm repo add arxiv $HELM_REPOSITORY
helm repo update
echo "Updated Helm repo"

# Deploy to Kubernetes.
helm get $HELM_RELEASE --tiller-namespace $ENVIRONMENT
status=$?
if [ status -eq 0 ]; then
    echo "Release exists; upgrading"
    helm upgrade $HELM_RELEASE arxiv/$CHART_NAME --set=imageTag=$TRAVIS_COMMIT --set=namespace=$ENVIRONMENT --tiller-namespace $ENVIRONMENT --namespace $ENVIRONMENT
else
    echo "Release does not exist; creating"
    helm install arxiv/$CHART_NAME --name=$HELM_RELEASE --set=imageTag=$TRAVIS_COMMIT --set=namespace=$ENVIRONMENT --tiller-namespace $ENVIRONMENT --namespace $ENVIRONMENT
fi
echo "Deployed!"

function cleanup {
    printf "Cleaning up...\n"
    rm -vf "${HOME}/ca.crt"
    printf "Cleaning done."
}

trap cleanup EXIT
