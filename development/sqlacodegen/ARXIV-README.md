# Changes from sqlacodegen

When you run the original codegen, it it obvious the existing code has a quite a lot of changes made to it.
This creates a challenge to re-run the codegen and update the db/models.py. 

The overall codegen is driven by development/db_codegen.py, and the modification of sqlacoden allows the 
merging of existing and re-generated Python code.

For example, when sqlacodeden runs, the model's class names are derived from the table name. This is not true
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

#### table_args

When the `table_args` is given `drop` , it is dropped and does not appear in the output.
When `replace` is used, python's string replace is applied to it. There is no semantic consideration. 

#### columns

You can override the RHS of column. For example:

    status: "mapped_column(Enum('new', 'frozen', 'published', 'rejected'), nullable=False, index=True, server_default=FetchedValue())"

If the table schema has no concept of string literal enum but you want to define it, you may want to override 
the generated definition. 

There are two types of column's RHS. One with type and without type. When the first character of RHS is ":", it is
a typed RHS. 


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
