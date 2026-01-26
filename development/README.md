# Generating arxiv/db/models.py

**DO NOT EDIT db/models.py.**

## How to generate db/models.py from prod

You should unload the latest schema from the production database.
There is a shell script for this as development/dump-schema.sh

Assuming you have access to the replica with the cloud sql proxy,

    /usr/local/bin/cloud-sql-proxy --address 0.0.0.0 --port 2021 arxiv-production:us-central1:arxiv-production-rep9 > /dev/null 2>&1 &
    
Have a read only database password in `~/.arxiv/arxvi-db-read-only-password` so that
the shell script to unload schema works.Then you run

    ./dump-schema.sh

This creates a SQL schema dump "arxiv_db_schema.sql". Compare this with `arxiv-base/arxiv/db/arxiv_db_schema.sql`.
It is strongly recmmended to comment out `SET @@GLOBAL.GTID_PURGED=` line in it before checking in.
It would look like:

    -- SET @@GLOBAL.GTID_PURGED='2d19f914-b050-11e7-95e6-005056a34791:1-572482257';

Once it's done, move the .sql to `arxiv-base/arxiv/db` if the schema is changed.
If they are the same, you may not need to update the db/models.py.
Run this in arxiv-base directory.


    cd arxiv-base
    python -v
    # 3.11
    python -m venv .venv
    . .venv/bin/activate
    pip install poetry
    poetry install
    python development/db_codegen.


## Overiew

See page 7 of presentation.
https://docs.google.com/presentation/d/14uWeVSOTUUm186KIyhMi-TiXvDS-KzLza93LJbyv0gc/edit?slide=id.gc6f9e470d_0_24#slide=id.gc6f9e470d_0_24

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

Second, you need to download the database schema. Prepare the database password at `~/.arxiv/arxvi-db-read-only-password`

Third, you need one of two:

* docker to run the mysql (recommended)
* local mysql 

If you do not have local mysql, docker mysql is used. development/db_codegen pulls and 
starts the docker, if you just run it, the docker mysql is used.

so once

    cd <YOUR-ARXIV-BASE like ~/arxiv/arxiv-base> 
    . venv/bin/activate
    development/dump-schema.sh
    python development/db_codegen.py

generates `arxiv/db/models.py`

**DO NOT EDIT db/models.py.**

Third, you need to unload the production database schema and populate `arxiv/db/arxiv_db_schema.sql`.

    cd ~/arxiv/arxiv-base/development
    make proxy

starts the proxy db connection to the rep9 in arXiv production on port 2021.

    sh ./dump-schema.sh

It is reasonable to notice that this does not access the database for the sqlcodegen, and
rather use a locally replicated database. The primary reason is that while working on the
codegen, it repeatedly needed to unload the schema and it is sloweer. The secondary reason
is keeping track of schema change is a good idea anyway as we seem to not have it in arxiv-base.


## Anatomy of db_codegen.py

does following steps. 

1. start mysql docker if no MySQL running
2. load arxiv/db/arxiv_db_schema.sql to the local mysql
3. runs the modified development/sqlacodegen with the codegen metadata. This generates arxiv/db/autogen_models.py
4. merges arxiv/db/autogen_models.py and arxiv/db/orig_models.py and creates arxiv/db/models.py

### Modified sqlacodegen

In order to accomate the existing changes made to arxiv/db/models.py in the past, unmodified sqlacodegen cannot
generate the code we need from the database schema. 
The details of sqlacodegen modification is in development/sqlacodegen/ARXIV-README.md. 

Here is the TL;DR of changes made to it:

1. Overriding the class name of model class
2. Overriding the TableModel / Table selection
3. Manipulate the __table_args__
4. Set the index/primary key attribute to the column definition from the table args.
5. Override the column definition
6. Override the relationship definition
7. Append the extra relationship

With these changes, auto-generated models (autogen_models.py) becomes somewhat close to what we need, but 
it cannot be used as is. db_codegen.py post-processes the autogen .py.

For more details of sqlacodegen changes from the original, see
[development/sqlacodegen/ARXIV-README.md](sqlacodegen/ARXIV-README.md).


### Merge autogen_models.py and orig_models.py

In order to maintain the hand-edited portion of arxiv/db/models.py, it is renamed as `orig_models.py`, and used
as an input of merge source. 

This is how merge works:

1. Parse orig_models.py. This is usually named `existing_` in the code
2. Parse autogen_models.py. This is usually prefixed with `latest_` in the code
3. Catalogs the classes in "latest". 
4. Traverse the parse tree of "existing"
5. While traversing existing parsed tree, if it finds the matching class in latest, replace the assignments in the class.
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

The tree traversing invokes the member functions prefixed by "enter" and "leave". Using this, the transformer 
visits the classes and assignments in the `orig_models.py` and replaces the class members with the latest
members.

#### leave_ClassDef

This is where the latest model object is merged to existing model. 

#### leave_Assign

This is where the latest table def is replaced. 

### Running db_codegen.py under debugger

Generally, you don't need any special set-up other than running MySQL/arxiv database.


## FAQ

Q:
After update, sqlite3 based test failed. And error looks like this.

    self = <sqlalchemy.dialects.sqlite.pysqlite.SQLiteDialect_pysqlite object at 0x7f1708d218d0>, cursor = <sqlite3.Cursor object at 0x7f1708d3e640>
    statement = '\nCREATE TABLE "arXiv_admin_log" (\n\tid INTEGER NOT NULL, \n\tlogtime VARCHAR(24), \n\tcreated DATETIME DEFAULT CURR...NULL, \n\tupdated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL, \n\tPRIMARY KEY (id)\n)\n\n'
    parameters = (), context = <sqlalchemy.dialects.sqlite.base.SQLiteExecutionContext object at 0x7f1708ee8710>
    
        def do_execute(self, cursor, statement, parameters, context=None):
    >       cursor.execute(statement, parameters)
    E       sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) near "ON": syntax error
    E       [SQL: 
    E       CREATE TABLE "arXiv_admin_log" (
    E               id INTEGER NOT NULL, 
    E               logtime VARCHAR(24), 
    E               created DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    E               paper_id VARCHAR(20), 
    E               username VARCHAR(20), 
    E               host VARCHAR(64), 
    E               program VARCHAR(20), 
    E               command VARCHAR(20), 
    E               logtext TEXT, 
    E               document_id INTEGER, 
    E               submission_id INTEGER, 
    E               notify INTEGER, 
    E               old_created DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    E               updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL, 
    E               PRIMARY KEY (id)
    E       )
    E       
    E       ]
    E       (Background on this error at: https://sqlalche.me/e/20/e3q8)
    
    ../../.pyenv/versions/3.11.4/envs/base/lib/python3.11/site-packages/sqlalchemy/engine/default.py:942: OperationalError


A: The error indicates (sqlite3.OperationalError) near "ON": syntax error so

    E               updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL, 

Failed. Looking at the generated models.py, the offending column definition is

        updated: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

which came from the prod db schema. The column definition is specific to MySQL and does not work with sqlite3.
In other word, you need to override the RHS of updated. in `arxiv/db/arxiv-db-metadata-yaml`, add the RHS of updated. In this case,
you want to have the default and on-update, set to the current timestamp.

    arXiv_admin_log:
      class_name: AdminLog
      columns:
        updated: "mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))"
    
In short, the sqlacodegen is NOT capable of understanding how to generalize the MySQL construct of setting timestamp to the `updated` column.
This works fine for MySQL but we never create db schema from Python model, this part is meaningless. It only matters to sqlite3 tests.
(and therefore, with missing charset of table, sqlite3 tests do not detect charset inconsitent joins, etc.)


## Helpers

`extract_class_n_table.py` parses a model python file and prints out the table and class name map. 
This is the first thing you have to do to start the `arxiv-db-metadata.yaml` file.

`dump-schema.sh` unloads the schema from database and writes to arxiv_db_schemas.sql.
You need to provide the database access credential to run the mysqldump command.
For this to run, you'd need to run a db access proxy on port 2021.


I repeat **DO NOT EDIT db/models.py.**
