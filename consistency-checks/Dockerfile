# consistency-checks: one image, one Cloud Run Job per check (see README.md).
#
# Build from the arxiv-base repo root, it needs ../ (arxiv-base) and ../arxiv-functions:
#   docker build -f consistency-checks/Dockerfile -t consistency-checks .
# Run:
#   docker run --rm -e DB_URL=... consistency-checks db_stats --no-mail

FROM python:3.13-slim-bookworm AS build

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /bin/uv
# build deps for mysqlclient
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential pkg-config default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /src
COPY pyproject.toml poetry.lock ./
COPY arxiv ./arxiv
COPY gcp ./gcp
COPY arxiv-functions ./arxiv-functions
COPY consistency-checks ./consistency-checks
RUN cd consistency-checks && uv sync --frozen --no-dev --no-editable


FROM python:3.13-slim-bookworm

# libmariadb3 for mysqlclient; poppler-utils for pdfinfo (recent_articles)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libmariadb3 poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /opt/venv /opt/venv
ENV PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

RUN useradd --create-home checks
USER checks
WORKDIR /home/checks

ENTRYPOINT ["python", "-m", "consistency_checks"]
