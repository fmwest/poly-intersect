import logging
import json
import dask

from flask import jsonify, request

from polyIntersect.routes.api.v1 import endpoints, error
from polyIntersect.validators import validate_greeting

import polyIntersect.micro_functions.poly_intersect as analysis_funcs


@endpoints.route('/hello', strict_slashes=False, methods=['GET', 'POST'])
@validate_greeting
def hello():
    data = 'hello adnan'
    response = jsonify(data)
    response.status_code = 200
    return response


@endpoints.route('/', strict_slashes=False, methods=['POST'])
@validate_greeting
def polyIntersect_area():
    x = []
    try:
        user_poly = str(request.form['user_poly'])
        intersect_polys = str(request.form['intersect_polys'])
        data = analysis_funcs.intersect_area_geom(user_poly, intersect_polys)
    except Exception as e:
        logging.info('FAILED: {}'.format(e))
        return 'FAILED: {}\n  ERROR: {}'.format(x, e)

    if False:
        return error(status=400, detail='Not valid')

    response = jsonify(data)
    response.status_code = 200
    return response


@endpoints.route('/geom', strict_slashes=False, methods=['POST'])
@validate_greeting
def polyIntersect_area_geom():
    try:
        user_poly = str(request.form['user_poly'])
        intersect_polys = str(request.form['intersect_polys'])
        data = intersect_area_geom(user_poly, intersect_polys,
                                   return_intersect_geom=True)
    except Exception as e:
        logging.info('FAILED: {}'.format(e))
        return 'FAILED: {}'.format(e)

    if False:
        return error(status=400, detail='Not valid')

    response = jsonify(data)
    response.status_code = 200
    return response


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
            graph[k] = [analysis_funcs.json2ogr] + func_args
        else:
            graph[k] = [getattr(analysis_funcs, func_name)] + func_args

    return graph


def serialize_output(outputs):

    if not isinstance(outputs, list):
        raise ValueError('outputs must be list')

    for item in outputs:
        import pdb; pdb.set_trace()
        # test if it is an ogr object and convert it to geojson
        pass



@endpoints.route('/executeGraph', strict_slashes=False, methods=['POST'])
@validate_greeting
def execute_graph_view():

    dag = str(request.form['dag'])
    graph = create_dag_from_json(dag)

    outputs = json.loads(str(request.form['result_keys']))
    result_obj = dask.get(dag, outputs)
    results = get(dsk, outputs)
    data = serialize_output(results)

    response = jsonify(data)
    response.status_code = 200
    return response
