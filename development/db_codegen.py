from __future__ import annotations
import re
import sys
import os
import subprocess
from typing import Tuple
import logging

from libcst.matchers import SimpleStatementLine
from ruamel.yaml import YAML

# import ast
import libcst as cst

logging.basicConfig(level=logging.INFO)


tables_i_cannot_update = {
    'DBLPAuthor': True,
    'TapirNicknamesAudit': True,
    'MemberInstitutionIP': True,

    "t_arXiv_ownership_requests_papers": True,
    "t_arXiv_updates_tmp": True,
    "t_arXiv_admin_state": True,
}

def first_target(body):
    if hasattr(body, 'targets'):
        return body.targets[0].id
    if hasattr(body, 'target'):
        return body.target.id
    return None


def is_intpk(elem):
    return hasattr(elem, 'annotation') and hasattr(elem.annotation, 'slice') and hasattr(elem.annotation.slice, 'id') and elem.annotation.slice.id == "intpk"

def patch_mysql_types(contents: str):
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
        (re.compile(r' class_:'), r' _class:'),  #
        (re.compile(r'Mapped\[decimal.Decimal\]'), r'Mapped[float]'),  #
        (re.compile(r'Mapped\[datetime.datetime\]'), r'Mapped[datetime]'),  #
        (re.compile(r'Optional\[datetime.datetime\]'), r'Optional[datetime]'),  #
        (re.compile(r'INTEGER(\(\d+\)){0,1}'), r'Integer'),
        (re.compile(r'TINYINT(\(\d+\)){0,1}'), r'Integer'),
        (re.compile(r'MEDIUMINT(\(\d+\)){0,1}'), r'Integer'),
        (re.compile(r'SMALLINT(\(\d+\)){0,1}'), r'Integer'),
        (re.compile(r'MEDIUMTEXT(\(\d+\)){0,1}'), r'Text'),
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


def is_assign_expr(elem):
    if isinstance(elem, cst.SimpleStatementLine):
        return isinstance(elem.body[0], (cst.Assign, cst.AnnAssign))
    return False

def is_table_def(node):
    return isinstance(node, cst.SimpleStatementLine) and is_table_assign(node.body[0])

def is_table_assign(node):
    return isinstance(node, cst.Assign) and isinstance(node.value, cst.Call) and node.value.func.value == "Table"


def find_keyword_arg(elem: cst.Call, key_name: str) -> Tuple[int, cst.Arg] | None:
    assert(isinstance(elem, cst.Call))
    for idx, arg in enumerate(elem.args):
        if hasattr(arg, 'keyword') and arg.keyword and arg.keyword.value == key_name:
            return idx, arg
    return None

def copy_server_default(to_elem: cst.Call, from_elem: cst.Call) -> cst.Call:
    """Copy the keyword 'server_default' from/to"""
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
    def __init__(self, latest_def, latest_tables):
        self.latest_def = latest_def
        self.latest_tables = latest_tables

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.CSTNode:
        #
        class_name = original_node.name.value
        if class_name in tables_i_cannot_update:
            return updated_node

        if class_name in self.latest_def:
            latest_node = self.latest_def[class_name]

            # Collect the existing assignments from the original class body
            existing_assignments = {
                self.first_target(elem): elem for elem in original_node.body.body if
                is_assign_expr(elem)
            }

            updated_body = []

            for elem in latest_node.body.body:
                if is_assign_expr(elem):
                    target = self.first_target(elem)
                    if target in existing_assignments:
                        existing_elem = existing_assignments[target]
                        # Use the original element if it's marked as int primary key or similar
                        # Also, it the line is commented, keep.
                        if self.is_intpk(existing_elem) or self.has_comment(existing_elem):
                            updated_body.append(existing_elem)
                        else:
                            if isinstance(elem.body[0].value, cst.Call) and isinstance(existing_elem.body[0].value, cst.Call):
                                elem = elem.with_changes(
                                    body=[
                                        elem.body[0].with_changes(
                                            value=copy_server_default(elem.body[0].value, existing_elem.body[0].value)
                                        )
                                    ])
                                pass
                            updated_body.append(elem)
                        # Remove this from the existing assignments so it's not processed again
                        del existing_assignments[target]
                    else:
                        updated_body.append(elem)
                else:
                    updated_body.append(elem)

            for elem in original_node.body.body:
                if not is_assign_expr(elem):
                    updated_body.append(elem)

            if existing_assignments:
                logging.info("#========================================================================")
                logging.info(f"# {class_name}")
                for remain_key, remain_value in existing_assignments.items():
                    logging.info(f"    {remain_key}")
                logging.info("#========================================================================")

            a_key: str
            for a_key, a_value in existing_assignments.items():
                if not isinstance(a_value, cst.SimpleStatementLine):
                    continue
                # If the lhs is all upper, it is def. added by hand. So, leave it in the class
                if a_key == a_key.upper():
                    updated_body.append(a_value)
                    continue

                # If the line has any comment, hand-added, so leave it
                for line in a_value.leading_lines:
                    if line.comment:
                        updated_body.append(a_value)
                        continue

            # Rebuild the class body with updated assignments
            return updated_node.with_changes(body=updated_node.body.with_changes(body=updated_body))
        return updated_node

    def first_target(self, node):
        if is_assign_expr(node):
            if hasattr(node.body[0], 'target'):
                return node.body[0].target.value
            if hasattr(node.body[0], 'targets'):
                return node.body[0].targets[0].target.value
        return None

    def is_intpk(self, elem):
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

    def has_comment(self, elem):
        if isinstance(elem, cst.SimpleStatementLine):
            return elem.leading_lines and elem.leading_lines[-1].comment
        return False

    def leave_Assign(self, original_node: cst.Assign, updated_node: cst.Assign) -> cst.CSTNode:
        # Check if the value of the assignment is a Table call
        lhs_name = original_node.targets[0].target.value
        if lhs_name in tables_i_cannot_update:
            return updated_node

        if not is_table_assign(original_node):
            return original_node
        latest_table_def: cst.Assign = self.latest_tables.get(lhs_name)
        if not latest_table_def:
            return original_node

        # If the original node is commented, consider it as hand-updated so leave as is
        if isinstance(original_node, cst.SimpleStatementLine):
            if original_node.leading_lines and original_node.leading_lines[-1].comment:
                return original_node

        # updated_node = updated_node.with_changes(value=)
        rh_new = latest_table_def.value
        rh_old = updated_node.value
        # Update the table def's RH with new's RH
        if hasattr(rh_new, 'args') and hasattr(rh_old, 'args'):
            columns = {}
            for old_col in rh_old.args:
                # I only care the Column("foo")
                if isinstance(old_col.value, cst.Call) and old_col.value.func.value == "Column":
                    # column def
                    column_name = old_col.value.args[0].value.value
                    columns[column_name] = old_col

            for i_col, new_column in enumerate(rh_new.args):
                # I only care the Column("foo")
                if isinstance(new_column.value, cst.Call) and new_column.value.func.value == "Column":
                    # column def
                    column_name = new_column.value.args[0].value.value
                    old_column = columns.get(column_name)
                    if old_column:
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


def main() -> None:
    p_outfile = "arxiv/db/autogen_models.py"

    #with open(os.path.expanduser('~/.arxiv/arxiv-db-prod-readonly'), encoding='utf-8') as uri_fd:
    #    p_url: str = uri_fd.read().strip()
    #with open(os.path.expanduser('~/.arxiv/arxiv-db-dev-proxy'), encoding='utf-8') as uri_fd:
    #    p_url: str = uri_fd.read().strip()
    p_url = "mysql://testuser:testpassword@127.0.0.1/testdb"
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sqlacodegen", "src"))
    subprocess.run(['development/sqlacodegen/venv/bin/python', '-m', 'sqlacodegen', p_url, '--outfile', p_outfile, '--model-metadata', "arxiv/db/arxiv-db-metadata.yaml"], check=True)

    subprocess.run(['development/sqlacodegen/venv/bin/python', '-m', 'sqlacodegen', p_url, '--outfile', "arxiv/db/raw-autogen_models.py"], check=True)

    with open(p_outfile, 'r') as src:
        source = src.read()

    try:
        latest_tree = cst.parse_module(source)
    except Exception as exc:
        logging.error("%s: failed to parse", p_outfile, exc_info=exc)
        exit(1)

    latest_def = {}
    latest_tables = {}

    for node in latest_tree.body:
        if isinstance(node, cst.ClassDef):
            latest_def[node.name.value] = node
        if is_table_def(node):
            latest_tables[node.body[0].targets[0].target.value] = node.body[0]

    with open(os.path.expanduser('arxiv/db/orig_models.py'), encoding='utf-8') as model_fd:
        existing_models = model_fd.read()
    existing_tree = cst.parse_module(existing_models)

    transformer = SchemaTransformer(latest_def, latest_tables)
    updated_tree = existing_tree.visit(transformer)

    updated_model = 'arxiv/db/models.py'
    with open(os.path.expanduser(updated_model), "w", encoding='utf-8') as updated_fd:
        updated_fd.write(updated_tree.code)

    with open(updated_model, encoding='utf-8') as updated_fd:
        contents = updated_fd.read()
    contents = patch_mysql_types(contents)
    with open(updated_model, 'w', encoding='utf-8') as updated_fd:
        updated_fd.write(contents)
    subprocess.run(['black', "-l", "200", updated_model])


if __name__ == "__main__":
    """
	patch arxiv/db/autogen_models.py arxiv/db/autogen_models_patch.diff
    """
    main()
