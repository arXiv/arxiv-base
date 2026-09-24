# Build, push and deploy consistency-checks.
#
#   make build                      # local image consistency-checks:$(TAG)
#   make push   ENV=dev             # tag + push to the env's Artifact Registry
#   make plan   ENV=dev             # terraform plan, pinned to the pushed digest -> tfplan-dev
#   make apply  ENV=dev             # apply exactly that saved plan
#   make deploy ENV=dev             # push + plan (review), then run `make apply`
#
# ENV is dev (arxiv-development) or prod (arxiv-production). One-time docker
# login to the registry: make docker-auth

ENV ?= dev
TAG ?= $(shell git describe --always --dirty)
REGION := us-central1

ifeq ($(ENV),prod)
PROJECT  := arxiv-production
REPO     := arxiv-docker
TF_STATE := prod-arxiv-terraform-state
else ifeq ($(ENV),dev)
PROJECT  := arxiv-development
REPO     := arxiv-dev-docker
TF_STATE := dev-arxiv-terraform-state
else
$(error ENV must be dev or prod, got '$(ENV)')
endif

LOCAL_IMAGE  := consistency-checks:$(TAG)
REMOTE_IMAGE := $(REGION)-docker.pkg.dev/$(PROJECT)/$(REPO)/consistency-checks:$(TAG)
# Digest reference of the pushed image, resolved when used (after push).
# Override with IMAGE=... to deploy some other image.
IMAGE ?= $(shell docker inspect --format '{{range .RepoDigests}}{{println .}}{{end}}' $(REMOTE_IMAGE) 2>/dev/null \
                 | grep '^$(REGION)-docker.pkg.dev/$(PROJECT)/$(REPO)/' | head -1)

TF := terraform -chdir=terraform
PLAN := tfplan-$(ENV)

.PHONY: build push docker-auth init plan apply deploy

build:
	docker build -f Dockerfile -t $(LOCAL_IMAGE) ..

push: build
	docker tag $(LOCAL_IMAGE) $(REMOTE_IMAGE)
	docker push $(REMOTE_IMAGE)

docker-auth:
	gcloud auth configure-docker $(REGION)-docker.pkg.dev

init:
	$(TF) init -reconfigure -input=false -backend-config="bucket=$(TF_STATE)"

plan: init
	@test -n "$(IMAGE)" || { echo "No pushed image for $(REMOTE_IMAGE): run 'make push ENV=$(ENV)' or pass IMAGE=..."; exit 1; }
	$(TF) plan -input=false -var-file=envs/$(ENV).tfvars -var="image=$(IMAGE)" -out=$(PLAN)

apply: init
	@test -f terraform/$(PLAN) || { echo "No terraform/$(PLAN): run 'make plan ENV=$(ENV)' first"; exit 1; }
	$(TF) apply -input=false $(PLAN)
	rm -f terraform/$(PLAN)

deploy: push plan
	@echo "Review the plan above, then: make apply ENV=$(ENV)"
