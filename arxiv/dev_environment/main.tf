terraform {
    required_providers {
        google = {
            source = "hashicorp/google"
            version = "4.51.0"
        }
    }
}

provider "google" {
    project = "arxiv-development"
}

provider "docker" {
  
}

data "google_secret_manager_secret_version" "CLASSIC_DB_URI" {
    secret = "browse-sqlalchemy-db-uri"
    version = "latest"
}

resource "docker_container" "classic_db" {
    image = "classic_db_img"
    name = "classic_db"
    env = [
        "CLASSIC_DB_URI=${data.google_secret_manager_secret_version.CLASSIC_DB_URI.secret_data}"
    ]
}