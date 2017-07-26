import json
from os import path

PROJECT_DIR = path.dirname(path.dirname(path.abspath(__file__)))
BASE_DIR = path.dirname(PROJECT_DIR)


def load_config_json(name):
    json_path = path.abspath(path.join(BASE_DIR,
                                       'microservice',
                                       '{}.json'.format(name)))
    with open(json_path) as data_file:
        info = json.load(data_file)
    return info
