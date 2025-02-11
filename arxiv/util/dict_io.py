"""
Dictionary object <--> file I/O
"""

import os.path
import typing
from collections import OrderedDict
from typing import TextIO

import json
from ruamel.yaml import YAML, MappingNode, ScalarNode
from ruamel.yaml.representer import RoundTripRepresenter

#
# ruamel.yaml to represent the OrderedDict correctly
#
def _repr_str(dumper: RoundTripRepresenter, data: str) -> ScalarNode:
    """
    "Print" string object for yaml dumping

    Args:
        dumper: ruamel.yaml round trip I/O
        data: any string data

    Returns:
        ScalarNode
    """
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


def _repr_ordered_dict(dumper: RoundTripRepresenter, data: OrderedDict) -> MappingNode:
    """
    "print" ordered dict for yaml dumping
    Args:
        dumper: ruamel.yaml round trip I/O
        data: OrderedDict instance

    Returns:
        MappingNode: mapped representation
    """
    return dumper.represent_mapping('tag:yaml.org,2002:map', dict(data))


def from_yaml_to_dict(filename: str) -> dict:
    """
    YAML to dict object
    Args:
        filename:

    Returns: dict object

    """
    with open(filename, encoding='utf-8') as yamlfile:
        yaml = YAML()
        return yaml.load(yamlfile)


def from_json_to_dict(filename: str) -> dict:
    """
    JSON to dict object

    Args:
        filename:

    Returns: dict object

    """
    with open(filename, encoding='utf-8') as jsonfile:
        return json.load(jsonfile)


def from_dict_to_yaml(data: typing.Union[dict, list], output: TextIO) -> None:
    """
    dict object to text
    Args:
        data: dict or list
        output: text

    Returns: None

    """
    yaml = YAML()
    yaml.representer.add_representer(str, _repr_str)
    yaml.representer.add_representer(OrderedDict, _repr_ordered_dict)
    yaml.dump(data, output)


def from_dict_to_json(data: dict, output: TextIO) -> None:
    """
    dict object to JSON text
    Args:
        data:
        output:

    Returns:

    """
    json.dump(data, output, indent=4)


def from_file_to_dict(filename: str) -> dict:
    """
    Derive file format from filename and read/return dict object
    Args:
        filename:

    Returns: doct object

    """
    (name, ext) = os.path.splitext(filename)
    match ext.lower():
        case ".yaml":
            return from_yaml_to_dict(filename)
        case ".yml":
            return from_yaml_to_dict(filename)
        case ".json":
            return from_json_to_dict(filename)
        case _:
            raise ValueError(f"Unsupported file format: {filename}")
