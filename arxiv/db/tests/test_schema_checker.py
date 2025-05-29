import logging
import os.path
from typing import Tuple

import libcst as cst

class CannotBeListError(Exception):
    pass

def is_assign_expr(elem: cst.CSTNode):
    """Check the element type for assignment"""
    if isinstance(elem, cst.SimpleStatementLine):
        return isinstance(elem.body[0], (cst.Assign, cst.AnnAssign))
    return False

def first_target(node: cst.CSTNode):
    """Find the LHS name. If it is targets, use the first one"""
    if is_assign_expr(node):
        if hasattr(node.body[0], 'target'):
            return node.body[0].target.value
        if hasattr(node.body[0], 'targets'):
            return node.body[0].targets[0].target.value
    return None

def find_keyword_arg(elem: cst.Call, key_name: str) -> Tuple[int, cst.Arg] | None:
    """
    Find a keyword ard in the function call.
    """
    assert(isinstance(elem, cst.Call))
    for idx, arg in enumerate(elem.args):
        if hasattr(arg, 'keyword') and arg.keyword and arg.keyword.value == key_name:
            return idx, arg
    return None

def list_type_found(subscript: cst.Subscript) -> bool:
    # If this is really List, found!
    if isinstance(subscript.value, cst.Name) and subscript.value.value == "List":
        return True

    for child in subscript.children:
        if isinstance(child, cst.SubscriptElement):
            for elem in child.children:
                if isinstance(elem, cst.Index):
                    for index_elem in elem.children:
                        if isinstance(index_elem, cst.Subscript) and isinstance(index_elem.value, cst.Name) and index_elem.value.value == "List":
                            return True
                if isinstance(elem, cst.Subscript) and list_type_found(elem):
                    return True
    return False


def is_a_list_type(anno: cst.Annotation) -> bool:
    for elem in anno.children:
        if isinstance(elem, cst.Subscript):
            return list_type_found(elem)


class SchemaChecker(cst.CSTTransformer):
    """
    Visits the CST's node and checks the db.models.

    * This checks to see the use of lselist=False in relationship and if the LH type contains List, the test fails.
    """

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.CSTNode:
        """
        Update the existing assignments with latest assignments.

        The intention is to replace all of assignments with the latest.

        """

        class_name = original_node.name.value

        # Accumulate the assignments aka columns and relationships
        for elem in original_node.body.body:
            if not is_assign_expr(elem):
                continue
            if isinstance(elem.body[0].value, cst.Call) and isinstance(elem.body[0].value, cst.Call):
                if elem.body[0].value.func.value == "relationship":
                    # uselist needs to be preserved
                    use_list = find_keyword_arg(elem.body[0].value, "uselist")
                    if use_list and use_list[1].value.value == "False":
                        for child in elem.body[0].children:
                            # Interested in the type so once the assignment shows up, no need to continue
                            if isinstance(child, cst.AssignEqual):
                                break
                            if isinstance(child, cst.Annotation) and is_a_list_type(child):
                                logging.info(f"{class_name}.{elem.body[0].target!r} uselist with List type.")
                                raise CannotBeListError(f"Class {class_name} You need to fix the db.models.py. uselist=False relationship should not have List type in the LH.")

        return original_node


def test_the_checker():
    """
    Test the checker to see it actually detects the bad relationship.
    """
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    models_py = os.path.join(tests_dir, 'poisoned.py')
    with open(models_py) as models_file:
        source = models_file.read()
        try:
            models_tree = cst.parse_module(source)
        except Exception as exc:
            logging.error("%s: failed to parse", models_py, exc_info=exc)
            exit(1)

    checker = SchemaChecker()
    try:
        models_tree.visit(checker)
    except CannotBeListError:
        return None
    raise Exception("checker is not working")


def test_check_db_models():
    arxiv_db_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    models_py = os.path.join(arxiv_db_dir, 'models.py')
    with open(models_py) as models_file:
        source = models_file.read()
        try:
            models_tree = cst.parse_module(source)
        except CannotBeListError as exc:
            logging.error("%s: failed to parse", models_py, exc_info=exc)
            exit(1)

    checker = SchemaChecker()
    models_tree.visit(checker)
    return None
