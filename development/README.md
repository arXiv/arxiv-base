# Generating arxiv/db/models.py

**DO NOT EDIT db/models.py.**

## Ingredients

* MySQL database access in order to get the database schema from
* The original arxiv-base's arxiv/db/orig_models.py.
* arxiv/db/arxiv-db-metadata.yaml
* Modified version of sqlacodegen in arxiv-base/development/sqlacodegen
* The steps are driven by development/db_codegen.py which does the merge.

This will generate arxiv/db/models.py

    arXiv database (mysql) -----------\
                                       > sqlacodegen --> arxiv/db/autogen_models.py  
    arxiv/db/arxiv-db-metadata.yaml --/

    arxiv/db/orig_models.py -----\
                                  + merge --> arxiv/db//models.py
    arxiv/db/autogen_models.py --/

TL;DR - If you need to add to db/models.py, you either add it to db/orig_models.py or to db/arxiv-db-metadata.yaml.

**DO NOT EDIT db/models.py.**

## Steps

First, you need a venv with poetry. Set it up with arxiv-base's pyproject.toml as usual.

Second, you need one of two:

* docker to run the mysql
* local mysql

If you do not have local mysql, docker mysql is used. development/db_codegen pulls and 
starts the docker, if you just run it, the docker mysql is used.

so once

    . venv/bin/activate
    python development/db_codegen.py

generates `arxiv/db/models.py`

**DO NOT EDIT db/models.py.**

## Anatomy of db_codegen.py

does following steps. 

1. start mysql docker if no MySQL running
2. load arxiv/db/arxiv_db_schema.sql to the local mysql
3. runs the modified development/sqlacodegen with the codegen metadata. This generates arxvi/db/autogen_models.py
4. merges arxiv/db/autogen_models.py and arxiv/db/orig_models.py and creates arxiv/db/models.py

### Modified sqlacodegen

In order to accomate the existing changes made to arxiv/db/models.py in the past, unmodified sqlacodegen cannot
generate the code we need from the database schema. 
The details of sqlacodegn modification is in development/sqlacodegen/ARXIV-README.md. 

Here is the TL;DR of changes made to it:

1. Overriding the class name of model class
2. Overriding the TableModel / Table selection
3. Manipulate the __table_args__
4. Set the index/primary key attribute to the column definition from the table args.
5. Override the column definition
6. Override the relationship definition
7. Append the extra relationship

With these changes, auto-generated models (autogen_models.py) becomes somewhat close to what we need but 
it cannot be used as is. db_codegen.py post-processes the autogen .py.

For more details of sqlacodegen changes from the original, see
[development/sqlacodegen/ARXIV-README.md](development/sqlacodegen/ARXIV-README.md).


### Merge autogen_models.py and orig_models.py

In order to maintain the hand-edited portion of arxiv/db/models.py, it is renamed as `orig_models.py`, and used
as an input of merge source. 

This is how merge works:

1. Parse orig_models.py. This is usually named `existing_` in the code
2. Parse autogen_models.py. This is usually prefixed with `latest_` in the code
3. Catalogs the classes in "latest". 
4. Traverse the parse tree of "existing"
5. While traversing existing parsed tree, if if finds the matching class in latest, replace the assignments in the class.
6. Also update the simple assignments if it is "FOO = Table()" 
7. Print the updated tree

Parsing, traversing and updating the Python code uses [CST](https://github.com/Instagram/LibCST). 
[AST](https://docs.python.org/3/library/ast.html) cannot be used as it removes the comments. 

**IMPORTANT**

Because of this, if you add a new table, **it does not show up in the db/models.py. You need to manually add the 
class to arxiv/db/orig_models.py**.

When you run the db_models.py, it leaves the db/autogen_models.py. You copy&paste to db/orig_models.py and run
the db_codegen.py again. It will show up.

### Merging rules of SchemaTransformer

CST provides a tree traversing method that takes an object of Transformer (cst.CSTTransformer).

The tree travering invokes the member functions prefixed by "enter" and "leave". Using this, the transformer 
visits the classes and assignments in the `orig_models.py` and replaces the class members with the latest
members.

#### leave_ClassDef

This is where the latest model object is merged to existing model. 

#### leave_Assign

This is where the latest table def is replaced. 

### Running db_codegen.py under debugger

Generally, you don't need any special set-up other than running MySQL/arxiv database.


## Helpers

`extract_class_n_table.py` parses a model python file and prints out the table and class name map. 
This is the first thing you have to do to start the `arxiv-db-metadata.yaml` file.

`dump-schema.sh` unloads the schema from database and writes to arxiv_db_schemas.sql.
You need to provide the database access credential to run the mysqldump command.
For this to run, you'd need to run a db access proxy on port 2021.


I repeat **DO NOT EDIT db/models.py.**
