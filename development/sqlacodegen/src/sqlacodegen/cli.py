from __future__ import annotations

import argparse
import json
import os
import sys
from contextlib import ExitStack
from typing import TextIO

from sqlalchemy.engine import create_engine
from sqlalchemy.schema import MetaData
from ruamel.yaml import YAML

try:
    import citext
except ImportError:
    citext = None

try:
    import geoalchemy2
except ImportError:
    geoalchemy2 = None

try:
    import pgvector.sqlalchemy
except ImportError:
    pgvector = None

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points, version
else:
    from importlib.metadata import entry_points, version


def main() -> None:
    generators = {ep.name: ep for ep in entry_points(group="sqlacodegen.generators")}
    parser = argparse.ArgumentParser(
        description="Generates SQLAlchemy model code from an existing database."
    )
    parser.add_argument("url", nargs="?", help="SQLAlchemy url to the database")
    parser.add_argument(
        "--options", help="options (comma-delimited) passed to the generator class"
    )
    parser.add_argument(
        "--version", action="store_true", help="print the version number and exit"
    )
    parser.add_argument(
        "--schemas", help="load tables from the given schemas (comma-delimited)"
    )
    parser.add_argument(
        "--generator",
        choices=generators,
        default="declarative",
        help="generator class to use",
    )
    parser.add_argument(
        "--tables", help="tables to process (comma-delimited, default: all)"
    )
    parser.add_argument(
        "--model-metadata", help="the model's codegen metadata"
    )
    parser.add_argument("--noviews", action="store_true", help="ignore views")
    parser.add_argument("--outfile", help="file to write output to (default: stdout)")
    args = parser.parse_args()

    if args.version:
        print(version("sqlacodegen"))
        return

    if not args.url:
        print("You must supply a url\n", file=sys.stderr)
        parser.print_help()
        return

    if citext:
        print(f"Using sqlalchemy-citext {version('citext')}")

    if geoalchemy2:
        print(f"Using geoalchemy2 {version('geoalchemy2')}")

    if pgvector:
        print(f"Using pgvector {version('pgvector')}")

    # Use reflection to fill in the metadata
    naming_convention = {
        "ix": "ix_%(table_name)s_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }

    engine = create_engine(args.url)
    metadata = MetaData(naming_convention=naming_convention)
    tables = args.tables.split(",") if args.tables else None
    schemas = args.schemas.split(",") if args.schemas else [None]

    options = set(args.options.split(",")) if args.options else set()
    for schema in schemas:
        metadata.reflect(engine, schema, not args.noviews, tables)

    kwargs = {}
    if args.model_metadata:
        with open(args.model_metadata, "r", encoding="utf-8") as metadata_fd:
            if os.path.splitext(args.model_metadata)[1] == ".json":
                kwargs["model_metadata"] = json.load(metadata_fd)
            elif os.path.splitext(args.model_metadata)[1] == ".yaml":
                yaml = YAML(typ="safe")
                kwargs["model_metadata"] = yaml.load(metadata_fd)
            else:
                raise Exception("not supported")

    # Instantiate the generator
    generator_class = generators[args.generator].load()

    generator = generator_class(metadata, engine, options, **kwargs)

    # Open the target file (if given)
    with ExitStack() as stack:
        outfile: TextIO
        if args.outfile:
            outfile = open(args.outfile, "w", encoding="utf-8")
            stack.enter_context(outfile)
        else:
            outfile = sys.stdout

        # Write the generated model code to the specified file or standard output
        outfile.write(generator.generate())
