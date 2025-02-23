# Changes from sqlacodegen

When you run the original codegen, it it obvious the existing code has a quite a lot of changes made to it.
This creates a challenge to re-run the codegen and update the db/models.py. 

The overall codegen is driven by development/db_codegen.py, and the modification of sqlacodegen allows the 
merging of existing and re-generated Python code.

For example, when sqlacodegen runs, the model's class names are derived from the table name. This is not true
in our source code anymore. This was a starting point of modifying sqlacodegen.

The key difference is that, the original codegen generates the faithful models of original tables. This is not 
necessary for our use, as the python model is NOT the source of truth. 
We need the db/models.py to be able to access data. 
The database schema is instead managed externally and unfortunately somewhat ad-hoc. 

db/models.py is used to create new tables for testing so the Python model closely matching to the database has 
some importance.

There are 7 features added to sqlacodegen. 

1. Overriding the class name
2. Overriding the TableModel / Table selection
3. Manipulate the __table_args__
4. Set the index/primary key attribute to the column definition from the table args.
5. Override the column definition
6. Override the relationship definition
7. Append the extra relationship

NOTE: After all of these changes made, the original sqlacodegen allows to inject the "generator" class in a 
CLI arg. So, I did not have to clone all of it. I however added CLI arg so the full-clone is not entirely 
wasteful.

## Use of codegen metadata

arxiv/db/arxiv-db-metadata.yaml provides the input to the codegen.
The top-level key corresponds to the table name.

This is an example of metadata for a table.

    arXiv_ownership_requests:
      class_name: OwnershipRequest
      table_args: drop
      columns:
        user_id: mapped_column(ForeignKey('tapir_users.user_id'), nullable=False, index=True, server_default=FetchedValue())
        endorsement_request_id: mapped_column(ForeignKey('arXiv_endorsement_requests.request_id'), index=True)
    
      relationships:
        endorsement_request: "relationship('EndorsementRequest', primaryjoin='OwnershipRequest.endorsement_request_id == EndorsementRequest.request_id', back_populates='arXiv_ownership_requests')"
        user: "relationship('TapirUser', primaryjoin='OwnershipRequest.user_id == TapirUser.user_id', back_populates='arXiv_ownership_requests')"
      additional_relationships:
        - "request_audit = relationship('OwnershipRequestsAudit', back_populates='ownership_request', uselist=False)"
        - "documents = relationship('Document', secondary=t_arXiv_ownership_requests_papers)"

### Definition of metadata

For table model class:

    TABLE_NAME:
      class_name: <class_name>

      table_args: <drop>
        - replace: [<from_str>, <to_str>]

      columns:
        <column_name>: <rhs> | <typed_rhs>

      relationships:
        <relationship_name>: <rhs>
          <replacement_relationship_name>: <rhs>

      additional_relationships:
        - <str>

For table instance:

    TABLE_NAME:
      indecies:
        - replace: [<from_str>, <to_str>]

#### table_args

When the `table_args` is given `drop` , it is dropped and does not appear in the output.
When `replace` is used, python's string replace is applied to it. There is no semantic consideration. 

    arXiv_admin_metadata:
      class_name: AdminMetadata
      table_args:
        - replace: ["Index('pidv', 'paper_id', 'version', unique=True)", "Index('arxiv_admin_pidv', 'paper_id', 'version', unique=True)"]

In this case, `pidv` is renamed to `arxiv_admin_pidv`. This is done because `pidv` is used as a column name and
the model object cannot have both. This kind of hand-editing is in the original db/models.py but the metadata splits
it out so we can preserve the changes.

#### columns

You can override the RHS of column. For example:

    status: "mapped_column(Enum('new', 'frozen', 'published', 'rejected'), nullable=False, index=True, server_default=FetchedValue())"

If the table schema has no concept of string literal enum but you want to define it, you may want to override 
the generated definition. 

There are two types of column's RHS. One with type and without type. When the first character of RHS is ":", it is
a typed RHS. 

#### relationships

    relationships:
      user: ""

When there is no value, it is dropped.

    relationships:
      user: "relationship('TapirUser', primaryjoin='CrossControl.user_id == TapirUser.user_id', back_populates='arXiv_cross_controls')"

The value is used for the relationship. This is often used when the back_populates property name is changed from 
the default value. (eg. dropping "arXiv_" or "controls" vs "control")

    relationships:
      arXiv_categories:
        arXiv_category: "relationship('Category', primaryjoin='and_(CrossControl.archive == Category.archive, CrossControl.subject_class == Category.subject_class)', back_populates='arXiv_cross_controls')"

Here, from the DDL, the default name is `arXiv_categories` but it is renamed in the model to be `arXiv_category`. 
This syntax allows to rename and give it the value. 

Note that, the field type is given from the DDL. Do not include the type in the value. Doing so causes the Python
syntax error.

#### additional_relationships

The string literals are appended to the relationship.

#### indicies

The table definition's Index uses same mechanism as table_args to patch up the index definition.

## Class name designation

`class_name` designates the class name used in the generated code. If the table is simple, you'd not get 
the model class. Instead, the sqlacodegen generates a table definition. 

This is an example of Table object. 

    t_arXiv_bad_pw = Table(
        "arXiv_bad_pw",
        metadata,
        Column("user_id", Integer, nullable=False, server_default=FetchedValue()),
    )

If you provide the table name with a class name, the codegen then generates the model class instead. 
You must ues this very carefully since this is not a natural representation. This feature exists for maintaining
the existing table classes and if possible, avoid using this feature as you'd need to manipulate the class definition
in significant way. 


## Development and debugging

To run sqlacodegen under the debugger, it is highly recommended to run mysql on local machine, and load the schema
to replicate the tables without data. 

Once you have a local mysql, 

    python -m sqlacodegen "mysql://testuser:testpassword@127.0.0.1/testdb" --outfile "arxiv/db/near_models.py" --model-metadata "arxiv/db/arxiv-db-metadata.yaml"

to run it under debugger. `development/db_codegen.py` populates the docker mysql tables. Keep the docker mysql
running so you'd be able to repeatedly run the command without any impact to the production.
