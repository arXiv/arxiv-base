""" arxiv-base/development/db_codegen.py

Generated arxiv-base/arxiv/db/models.py

The script

"""

from __future__ import annotations
import re
import sys
import os
import time
from typing import Tuple
import logging
import libcst as cst

import socket
import subprocess

logging.basicConfig(level=logging.INFO)


tables_i_cannot_update = {
    'DBLPAuthor': True,
    'TapirNicknamesAudit': True,
    'MemberInstitutionIP': True,

    "t_arXiv_ownership_requests_papers": True,
    "t_arXiv_updates_tmp": True,
    "t_arXiv_admin_state": True,
    # "t_arXiv_in_category": True,
}

def first_target(body: cst.CSTNode):
    """Get the first LHS name"""
    if hasattr(body, 'targets'):
        return body.targets[0].id
    if hasattr(body, 'target'):
        return body.target.id
    return None


def is_intpk(elem: cst.CSTNode):
    """Figure out this is intpk"""
    return hasattr(elem, 'annotation') and hasattr(elem.annotation, 'slice') and hasattr(elem.annotation.slice, 'id') and elem.annotation.slice.id == "intpk"


def patch_mysql_types(contents: str):
    """Mass regex replace the python code for mostly MySQL dependant types."""
    # Define a mapping of MySQL dialect types to generic SQLAlchemy types
    type_mapping = [
        (re.compile(r'= mapped_column\(BIGINT\s*\(\d+\)'), r'= mapped_column(BigInteger'),  # Replace BIGINT(size) with BIGINT
        (re.compile(r'= mapped_column\(DECIMAL\s*\((\d+),\s*(\d+)\)'), r'= mapped_column(Numeric(\1, \2)'),  # Replace DECIMAL(m,n) with Numeric(m,n)
        (re.compile(r'= mapped_column\(MEDIUMINT\s*\(\d+\)'), r'= mapped_column(Integer'),  # Replace MEDIUMINT(size) with int
        (re.compile(r'= mapped_column\(INTEGER\s*\(\d+\)'), r'= mapped_column(Integer'),  # Replace INTEGER(size) with int
        (re.compile(r'= mapped_column\(SMALLINT\s*\(\d+\)'), r'= mapped_column(Integer'),  # Replace SMALLINT(size) with int
        (re.compile(r'= mapped_column\(TINYINT\s*\(\d+\)'), r'= mapped_column(Integer'),  # Replace TINYINT(size) with int
        (re.compile(r'= mapped_column\(VARCHAR\s*\((\d+)\)'), r'= mapped_column(String(\1)'),  # Replace VARCHAR(size) with String
        (re.compile(r'= mapped_column\(MEDIUMTEXT\s*\((\d+)\)'), r'= mapped_column(Text(\1)'),  # Replace MEDIUMTEXT with Text
        (re.compile(r'= mapped_column\(TIMESTAMP'), r'= mapped_column(DateTime'),  # Replace MEDIUMTEXT with Text
        (re.compile(r'= mapped_column\(CHAR\s*\((\d+)\)'), r'= mapped_column(String(\1)'),  # Replace CHAR(size) with str
        (re.compile(r' CHAR\s*\((\d+)\),'), r' String(\1),'),  # Replace CHAR(size) with str
        (re.compile(r'Mapped\[decimal.Decimal\]'), r'Mapped[float]'),  #
        (re.compile(r'Mapped\[datetime.datetime\]'), r'Mapped[datetime]'),  #
        (re.compile(r'Optional\[datetime.datetime\]'), r'Optional[datetime]'),  #
        (re.compile(r'INTEGER(\(\d+\)){0,1}'), r'Integer'),
        (re.compile(r'TINYINT(\(\d+\)){0,1}'), r'Integer'),
        (re.compile(r'MEDIUMINT(\(\d+\)){0,1}'), r'Integer'),
        (re.compile(r'SMALLINT(\(\d+\)){0,1}'), r'Integer'),
        (re.compile(r'MEDIUMTEXT(\(\d+\)){0,1}'), r'Text'),
        (re.compile(r'Base\.metadata'), r'metadata'),
        (re.compile(r'text\("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"\)'), r'FetchdValue()'),
        (re.compile(r'datetime\.date'), r'dt.date'),

        # Replace INTEGER(size) with int
    ]

    # Perform the replacement using regex for all types
    def mapper(line: str) -> str:
        mysql_type: re.Pattern
        for mysql_type, generic_type in type_mapping:
            if mysql_type.search(line):
                line = mysql_type.sub(generic_type, line)
        return line
    contents = "\n".join([mapper(line) for line in contents.splitlines()])
    return contents

# ================================================================================================================
#
# Model code merging

def is_assign_expr(elem: cst.CSTNode):
    """Check the element type for assignment"""
    if isinstance(elem, cst.SimpleStatementLine):
        return isinstance(elem.body[0], (cst.Assign, cst.AnnAssign))
    return False

def is_table_def(node: cst.CSTNode):
    """If this is a simple statement and RHS is table, this is a table definition."""
    return isinstance(node, cst.SimpleStatementLine) and is_table_assign(node.body[0])

def is_table_assign(node: cst.CSTNode):
    """Assignment that the RHS starts with Table() is a table assign."""
    return isinstance(node, cst.Assign) and isinstance(node.value, cst.Call) and node.value.func.value == "Table"


def find_keyword_arg(elem: cst.Call, key_name: str) -> Tuple[int, cst.Arg] | None:
    """
    Find a keyword ard in the function call.
    """
    assert(isinstance(elem, cst.Call))
    for idx, arg in enumerate(elem.args):
        if hasattr(arg, 'keyword') and arg.keyword and arg.keyword.value == key_name:
            return idx, arg
    return None


def copy_server_default(to_elem: cst.Call, from_elem: cst.Call) -> cst.Call:
    """Copy the keyword 'server_default' from/to
    If the original's server_default is working, even if the schema says otherwise, keep it.

    This might have a wrong impact in the instance but that's how it was working so preserve the behavior
    """
    assert(isinstance(from_elem, cst.Call))
    assert(isinstance(to_elem, cst.Call))

    existing_server_default = find_keyword_arg(from_elem, 'server_default')
    if existing_server_default:
        _, existing_arg = existing_server_default
        server_default = find_keyword_arg(to_elem, 'server_default')

        if server_default:
            idx, _ = server_default
            arg: cst.Arg = to_elem.args[idx]
            new_arg = arg.with_changes(value=existing_arg.value)

            # Replace the old argument with the new one in the args list
            updated_call = to_elem.with_changes(args=[
                *to_elem.args[:idx],
                new_arg,
                *to_elem.args[idx + 1:]
            ])
            return updated_call
    return to_elem


class SchemaTransformer(cst.CSTTransformer):
    """
    Visits the CST's node and applies the transformation.

    Since the nodes are immutable object, all of changes are to create new object and pass it back.

    In db/models.py, there are the class-based models and table objects. Merge of model is done with `leave_ClassDef`
    and merge of table is done with `leave_Assign`.

    """
    def __init__(self, latest_def, latest_tables):
        # Merging data
        self.latest_def = latest_def
        self.latest_tables = latest_tables

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.CSTNode:
        """
        Update the existing assignments with latest assignments.

        The intention is to replace all of assignments with the latest.

        """

        class_name = original_node.name.value

        # Skip the things I don't want to touch
        if class_name in tables_i_cannot_update:
            return updated_node

        if class_name in self.latest_def:
            # Only updates if there is a latest.
            latest_node = self.latest_def[class_name]

            # Collect the existing assignments from the original class body. These are the column and relationship
            # definitions.
            # If the assignments is NOT found in the latest, it could be a problematic so remember this.
            existing_assignments = {
                self.first_target(elem): elem for elem in original_node.body.body if
                is_assign_expr(elem)
            }

            updated_body = []

            # Remember the original slot order. __tablename__ and __table_args__ are special. it is always the
            # first and 2nd.

            # This is necessary to maintain the order of columns. Some of our tests do not use the column names
            # in the sql statement so if you change the order, those test data fail to load.
            # Also, if we ever stop using orig_models.py and use models.py as the old input (we may do so in future)
            # maintaining the column order is good for easier code review.
            original_slot_order = {
                "__tablename__": 0,
                "__table_args__": 1,
            }

            # Save the order of assign statement.
            for elem in original_node.body.body:
                if is_assign_expr(elem):
                    target = self.first_target(elem)
                    if target not in original_slot_order:
                        original_slot_order[target] = len(original_slot_order.keys())

            # If there is a non-assignment for first part, it's likely doc string so keep it
            preamble = []
            for elem in original_node.body.body:
                if is_assign_expr(elem):
                    break
                preamble.append(elem)

            # Accumulate the assignments aka columns and relationships
            for elem in latest_node.body.body:
                if not is_assign_expr(elem):
                    continue
                target = self.first_target(elem)
                if target in existing_assignments:
                    existing_elem = existing_assignments[target]
                    # Use the original element if it's marked as int primary key or similar
                    # Also, it the line is commented, keep.
                    if self.is_intpk(existing_elem) or self.has_comment(existing_elem):
                        updated_body.append(existing_elem)
                    else:
                        if isinstance(elem.body[0].value, cst.Call) and isinstance(existing_elem.body[0].value, cst.Call):
                            if existing_elem.body[0].value.func.value == "relationship":
                                existing_primary_join = find_keyword_arg(existing_elem.body[0].value, "primaryjoin")
                                if existing_primary_join:
                                    latest_primary_join = find_keyword_arg(existing_elem.body[0].value, "primaryjoin")
                                    latest_pj = str(latest_primary_join[1].value.value) if latest_primary_join else "none"
                                    if str(existing_primary_join[1].value.value) != latest_pj:
                                        logging.warning(
                                            f"{class_name}.{elem.body[0].targep!r} primary join -> {existing_primary_join[1].value.value} != {latest_pj}")

                            elem = elem.with_changes(
                                body=[
                                    elem.body[0].with_changes(
                                        value=copy_server_default(elem.body[0].value, existing_elem.body[0].value)
                                    )
                                ])
                            pass

                        updated_body.append(elem)
                    # Remove this from the existing assignments so it's visited.
                    del existing_assignments[target]
                else:
                    # the slot not appearing shows up after the existing ones
                    if target not in original_slot_order:
                        original_slot_order[target] = len(original_slot_order.keys())
                    updated_body.append(elem)

            # Adjust the slot order based on the existing slot while appending the new ones at the bottom
            updated_body.sort(key=lambda slot: original_slot_order[self.first_target(slot)])

            # Append the non-assigns. Non-assign before the assign is "preamble"
            after_assign = False
            for elem in original_node.body.body:
                if is_assign_expr(elem):
                    after_assign = True
                    continue
                if after_assign:
                    updated_body.append(elem)

            a_key: str
            intended = {}
            for a_key, a_value in existing_assignments.items():
                if not isinstance(a_value, cst.SimpleStatementLine):
                    continue
                # If the lhs is all upper, it is def. added by hand. So, leave it in the class
                if a_key == a_key.upper():
                    updated_body.append(a_value)
                    intended[a_key] = a_value
                    continue

                # If the line has any comment, hand-added, so leave it
                for line in a_value.leading_lines:
                    if line.comment:
                        updated_body.append(a_value)
                        intended[a_key] = a_value
                        continue

            # Warn the left over assigns.
            if existing_assignments:
                # ignore all uppers
                props = [prop for prop in existing_assignments.keys() if prop not in intended]
                if props:
                    extras = [class_name] + [f"    {prop}" for prop in props]
                    logging.warning(f"Class with extra existing assignmet(s):\n" +  "\n".join(extras))

            # Rebuild the class body with updated assignments
            body = preamble + updated_body
            return updated_node.with_changes(body=updated_node.body.with_changes(body=body))
        return updated_node

    def first_target(self, node: cst.CSTNode):
        """Find the LHS name. If it is targets, use the first one"""
        if is_assign_expr(node):
            if hasattr(node.body[0], 'target'):
                return node.body[0].target.value
            if hasattr(node.body[0], 'targets'):
                return node.body[0].targets[0].target.value
        return None

    def is_intpk(self, elem: cst.CSTNode):
        """Find the intpk and print it as so.
        In the orid_models.py, we use this syntax sugar so keep using it.

        It this is a simple assign:
          and it's annotated
            and the annotation uses intpk,
              -> True

        """
        if isinstance(elem, cst.SimpleStatementLine):
            if hasattr(elem.body[0], 'annotation'):
                for anno in elem.body[0].annotation.children:
                    if isinstance(anno, cst.Subscript):
                        for sub_elem in anno.children:
                            if isinstance(sub_elem, cst.SubscriptElement):
                                for frag in sub_elem.children:
                                    if hasattr(frag, 'value') and frag.value.value == 'intpk':
                                        return True
        return False

    def has_comment(self, elem: cst.CSTNode):
        """commented? The commented line means that the statement's very last comment is not blank comment"""
        if isinstance(elem, cst.SimpleStatementLine):
            return elem.leading_lines and elem.leading_lines[-1] \
                and elem.leading_lines \
                and elem.leading_lines[-1] \
                and elem.leading_lines[-1].comment \
                and elem.leading_lines[-1].comment.value \
                and elem.leading_lines[-1].comment.value[1:].strip()
        return False

    def leave_Assign(self, original_node: cst.Assign, updated_node: cst.Assign) -> cst.CSTNode:
        """
        Handle the Table assignment
        """

        # Check if the value of the assignment is a Table call
        lhs_name = original_node.targets[0].target.value
        if lhs_name in tables_i_cannot_update:
            return updated_node

        if not is_table_assign(original_node):
            # If this is not FOO = Table(BAR), leave as is
            return original_node

        latest_table_def: cst.Assign = self.latest_tables.get(lhs_name)
        if not latest_table_def:
            return original_node

        # If the original node is commented, consider it as hand-updated so leave as is
        if isinstance(original_node, cst.SimpleStatementLine):
            if original_node.leading_lines and original_node.leading_lines[-1].comment:
                return original_node

        # Going to replace the table with the new one
        updated_node = latest_table_def

        # updated_node = updated_node.with_changes(value=)
        rh_new = updated_node.value
        rh_old = original_node.value

        # Assignments do have ards
        if hasattr(rh_new, 'args') and hasattr(rh_old, 'args'):
            #
            # This seems not needed
            #
            # foreign_key_constaints = {}
            # simple_indecies = {}
            # for new_col in rh_new.args:
            #     if isinstance(new_col.value, cst.Call):
            #         if new_col.value.func.value == "ForeignKeyConstraint":
            #             # see the args
            #             # args[0] is the list of columns on this table, and args[1] is the far table
            #             # if it's simple, remember
            #             cols = new_col.value.args[0]
            #             far = new_col.value.args[1]
            #             if len(cols.value.elements) == 1 and len(far.value.elements) == 1:
            #                 # this is a simple foreign key ref
            #                 foreign_key_constaints[cols.value.elements[0]] = far.value.elements[0]
            #
            #         elif new_col.value.func.value == "Index":
            #             index_name = new_col.value.args[0]
            #             columns = new_col.value.args[1:]
            #             if len(columns) == 1:
            #                 simple_indecies[index_name.value.value] = columns[0].value.value

            # Collect the old columns to look at
            columns = {}
            for old_col in rh_old.args:
                # I only care the Column("foo")
                if isinstance(old_col.value, cst.Call) and old_col.value.func.value == "Column":
                    # column def
                    column_name = old_col.value.args[0].value.value
                    columns[column_name] = old_col

            for i_col, new_column in enumerate(rh_new.args):
                # I only care the Column("<a column>")
                if isinstance(new_column.value, cst.Call) and new_column.value.func.value == "Column":
                    # new column def and matching one
                    column_name = new_column.value.args[0].value.value
                    old_column = columns.get(column_name)

                    # If the old one exists...
                    if old_column:
                        # Copy the server_default= value
                        patched_call = copy_server_default(new_column.value, old_column.value)
                        if not patched_call.deep_equals(new_column.value):
                            column = new_column.with_changes(value = patched_call)
                            updated_node = updated_node.with_changes(
                                value = updated_node.value.with_changes(
                                    args=[
                                        *updated_node.value.args[:i_col],
                                        column,
                                        *updated_node.value.args[i_col + 1:]
                                    ]
                                )
                            )


        return updated_node


def find_classes_and_tables(tree: cst.CSTNode):
    classes = {}
    tables = {}

    for node in tree.body:
        if isinstance(node, cst.ClassDef):
            classes[node.name.value] = node
        if is_table_def(node):
            tables[node.body[0].targets[0].target.value] = node.body[0]
    return classes, tables

# ================================================================================================================

#

def is_port_open(host: str, port: int):
    """See the TCP port is open or not"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        return result == 0


def run_mysql_container(port: int):
    """Start a mysql docker"""
    mysql_image = "mysql:5.7.20"
    try:
        subprocess.run(["docker", "pull", mysql_image], check=True)

        subprocess.run(
            [
                "docker", "run", "-d", "--name", "mysql-test",
                "-e", "MYSQL_ROOT_PASSWORD=testpassword",
                "-e", "MYSQL_USER=testuser",
                "-e", "MYSQL_PASSWORD=testpassword",
                "-e", "MYSQL_DATABASE=testdb",
                "-p", f"{port}:3306",
                mysql_image
            ],
            check=True
        )
        logging.info("MySQL Docker container started successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")


def load_sql_file(sql_file):
    """Load a sql file to mysql

    If you see

ERROR 1840 (HY000) at line 24: @@GLOBAL.GTID_PURGED can only be set when @@GLOBAL.GTID_EXECUTED is empty.
ERROR:root:Error loading SQL file: Command '['mysql', '--host=127.0.0.1', '-uroot', '-ptestpassword', 'testdb']' returned non-zero exit status 1.

    it means that the sql is already loaded so ignore the error.

    """
    with open(sql_file, encoding="utf-8") as sql:
        try:
            subprocess.run(["mysql", "--host=127.0.0.1", "-uroot", "-ptestpassword", "testdb"],
                           stdin=sql, check=True)
            logging.info(f"SQL file '{sql_file}' loaded successfully into 'testdb'.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error loading SQL file: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")


def main() -> None:

    # This is the default mysql port. If you are using a native MySQL, that's fine. If you don't want to install
    # mysql, it uses the MySQL docker.
    mysql_port = 3306

    arxiv_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    arxiv_dir = os.path.join(arxiv_base_dir, "arxiv")

    p_outfile = os.path.join(arxiv_dir, "db/autogen_models.py")
    db_metadata = os.path.join(arxiv_dir, "db/arxiv-db-metadata.yaml")

    codegen_dir = os.path.join(arxiv_base_dir, "development/sqlacodegen")

    # If there is no MySQL up and running, start a container
    if not is_port_open("127.0.0.1", mysql_port):
        run_mysql_container(mysql_port)
        for _ in range(20):
            if is_port_open("127.0.0.1", mysql_port):
                break
            time.sleep(1)

    # Load the arxiv_db_schema.sql to the database.
    load_sql_file(os.path.join(arxiv_dir, "db/arxiv_db_schema.sql"))

    p_url = "mysql://testuser:testpassword@127.0.0.1/testdb"
    sys.path.append(os.path.join(codegen_dir, "src"))
    subprocess.run(['venv/bin/python', '-m', 'sqlacodegen', p_url, '--outfile', p_outfile,
                    '--model-metadata', db_metadata], check=True, cwd=arxiv_base_dir)

    # autogen_models.py
    with open(p_outfile, 'r') as src:
        source = src.read()

    # Parse the autogen
    try:
        latest_tree = cst.parse_module(source)
    except Exception as exc:
        logging.error("%s: failed to parse", p_outfile, exc_info=exc)
        exit(1)

    # Traverse the autogen and build the dicts
    latest_classes, latest_tables = find_classes_and_tables(latest_tree)

    # Parse the exiting models
    with open(os.path.join(arxiv_dir, 'db/orig_models.py'), encoding='utf-8') as model_fd:
        existing_models = model_fd.read()
    existing_tree = cst.parse_module(existing_models)

    # Also build the dicts for the existing models and tables
    existing_classes, existing_tables = find_classes_and_tables(existing_tree)

    # Warn of tables not mentioned in the existing model. This means the new table added and the
    # exiting model does not know about it.
    new_classes: [str] = list(set(latest_classes.keys()) - set(existing_classes.keys()))
    new_classes.remove('Base') # base shows up here but Base is imported in existing models.py
    if new_classes:
        logging.warning("NEW CLASSES! Add this to the original")
        for new_class in new_classes:
            logging.warning(f"class {new_class}")

    new_tables = list(set(latest_tables.keys()) - set(existing_tables.keys()))
    if new_tables:
        logging.warning("NEW TABLES! Add this to the original")
        for new_table in new_tables:
            logging.warning(f"class {new_table}")

    # Merge the exiting and latest models
    transformer = SchemaTransformer(latest_classes, latest_tables)
    updated_tree = existing_tree.visit(transformer)

    # Write out the models after the merge
    updated_model = os.path.join(arxiv_dir, 'db/models.py')
    with open(updated_model, "w", encoding='utf-8') as updated_fd:
        updated_fd.write(updated_tree.code)

    # Patch the models with regex
    # 1. MySQL types are replaced with the generic types.
    # 2. sqlacodegen and db/models.py import things differently (eg from datatime import datatime)
    # These can be done with hacking sqlacodegen but decided on the quick-and-dirty.
    with open(updated_model, encoding='utf-8') as updated_fd:
        contents = updated_fd.read()
    contents = patch_mysql_types(contents)
    with open(updated_model, 'w', encoding='utf-8') as updated_fd:
        updated_fd.write(contents)

    # Then, make the code look neat.
    subprocess.run(['black', "-l", "200", updated_model])


if __name__ == "__main__":
    """
	patch arxiv/db/autogen_models.py arxiv/db/autogen_models_patch.diff
    """
    main()
