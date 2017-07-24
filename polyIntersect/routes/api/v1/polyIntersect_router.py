import json
import dask

from flask import jsonify, request

from polyIntersect.routes.api.v1 import endpoints
from polyIntersect.validators import validate_greeting

import polyIntersect.micro_functions.poly_intersect as analysis_funcs


def create_dag_from_json(graphJson):
    graph_obj = json.loads(graphJson)

    graph = dict()

    for k, v in graph_obj.items():

        if not isinstance(k, str):
            raise ValueError('graph keys must be strings')

        if not isinstance(v, list) or not len(v):
            raise ValueError(('graph values must be lists'
                              '[<func_name>, <func_arg1>, <func_arg2>]'))

        special_funcs = ['geojson', 'gfw:pro']

        func_name = v[0]
        is_valid = analysis_funcs.is_valid(func_name)
        is_special = func_name in special_funcs
        if not is_valid and not is_special:
            raise ValueError('invalid function: {}'.format(func_name))

        func_args = v[1:] if len(v) else []

        if func_name == 'geojson':
            graph[k] = tuple([analysis_funcs.json2ogr] + func_args)
        else:
            graph[k] = tuple([getattr(analysis_funcs, func_name)] + func_args)

    return graph


def compute(graph, outputs):
    final_output = {}
    results = dask.get(graph, outputs)
    for result, name in zip(results, outputs):
        if isinstance(result, dict) and 'features' in result.keys():
            final_output[name] = analysis_funcs.ogr2json(result)
        else:
            final_output[name] = result
    return final_output


@endpoints.route('/executeGraph', strict_slashes=False, methods=['POST'])
@validate_greeting
def execute_graph_view():
    dag = str(request.form['dag'])
    graph = create_dag_from_json(dag)
    outputs = json.loads(str(request.form['result_keys']))
    data = compute(graph, outputs)
    response = jsonify(data)
    response.status_code = 200
    return response
