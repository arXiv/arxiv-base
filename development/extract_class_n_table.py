import json
import ast
from ruamel.yaml import YAML
import sys

def extract_class_table_mapping(filename: str):
    with open(filename, 'r') as src:
        source = src.read()

    parse_tree = ast.parse(source)

    class_table_mapping = {}

    for node in ast.walk(parse_tree):
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            table_name = None

            # Walk through the class body to find __tablename__ assignments
            for body_item in node.body:
                if isinstance(body_item, ast.Assign):
                    for target in body_item.targets:
                        if isinstance(target, ast.Name) and target.id == "__tablename__":
                            if isinstance(body_item.value, ast.Str):
                                table_name = body_item.value.s

            if table_name:
                class_table_mapping[table_name] = class_name

    return class_table_mapping

if __name__ == '__main__':
    output = sys.stdout
    filename = 'arxiv/db/models.py'  # Replace this with the path to your Python file
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    class_table_mapping = extract_class_table_mapping(filename)
    yaml = YAML()
    yaml.dump(class_table_mapping, output)

