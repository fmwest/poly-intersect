from os import path
import logging
import dask
import json
from flask import request, jsonify
from polyIntersect.routes.api.v1 import endpoints, error
from polyIntersect.validators import validate_greeting
from polyIntersect.micro_functions.poly_intersect import \
    intersect_area_geom, intersect_area_geom_from_endpoint

import polyIntersect.micro_functions.poly_intersect as analysis_funcs


@endpoints.route('/hello', strict_slashes=False, methods=['GET', 'POST'])
@validate_greeting
def hello():
    data = 'hello adnan'
    return data


def create_dag_from_json(graphJson):
    graph_obj = json.loads(graphJson)

    graph = dict()

    for k, v in graph_obj.items():

        if not isinstance(k, str):
            raise ValueError('graph keys must be strings')

        if not isinstance(v, list) or not len(v):
            raise ValueError(('graph values must be lists'
                              '[<func_name>, <func_arg1>, <func_arg2>]'))

        special_funcs = ['geojson', 'esri:server', 'gfw:pro']

        func_name = v[0]
        is_valid = analysis_funcs.is_valid(func_name)
        is_special = func_name in special_funcs
        if not is_valid and not is_special:
            raise ValueError('invalid function: {}'.format(func_name))

        func_args = v[1:] if len(v) else []

        if func_name == 'geojson':
            graph[k] = tuple([analysis_funcs.json2ogr] + func_args)
        elif func_name == 'esri:server':
            graph[k] = tuple([analysis_funcs.esri_server2ogr] + func_args)
        elif func_name == 'cartodb':
            graph[k] = tuple([analysis_funcs.cartodb2ogr] + func_args)
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


@endpoints.route('/brazil-biomes', strict_slashes=False,
                 methods=['POST'])
@validate_greeting
def execute_model():

    host = 'http://gis-gfw.wri.org'
    layer = 'country_data/south_america/MapServer/4'
    layer_url = path.join(host, 'arcgis/rest/services', layer)

    # form params
    user_json = str(request.form['user_json'])
    user_category = str(request.form['category'])

    # TODO: the extra json parse can probably go away...

    graph = {
        'aoi': ['geojson', json.loads(user_json)],

        'reference_data': ['esri:server', layer_url],

        'dissolve-aoi': ['dissolve', 'aoi'],

        'intersect-aoi-dataset': ['intersect', 'dissolve-aoi',
                                  'reference_data'],

        'intersect-area': ['get_intersect_area', 'dissolve-aoi',
                           'intersect-aoi-dataset', user_category],

        'intersect-area-percent': ['get_intersect_area_percent',
                                   'dissolve-aoi', 'intersect-aoi-dataset',
                                   user_category]
    }

    dag = create_dag_from_json(json.dumps(graph))
    outputs = ['intersect-area-percent', 'intersect-area']
    data = compute(dag, outputs)
    response = jsonify(data)
    response.status_code = 200
    return response


@endpoints.route('/', strict_slashes=False, methods=['POST'])
@validate_greeting
def polyIntersect_area():
    x = []
    try:
        # Get parameters from POST
        user_poly = str(request.form['user_poly'])
        intersect_polys = str(request.form['intersect_polys'])

        # Verify that return geom_geom is True or False, if not defined,
        # make it False
        try:
            return_geom = str(request.form['return_geom'])
        except:
            return_geom = 'False'
        assert return_geom == 'False' or return_geom == 'True', \
            'return_geom is {}, must be "True" or "False"'.format(return_geom)
        if return_geom == 'False':
            return_intersect_geom = False
        elif return_geom == 'True':
            return_intersect_geom = True

        data = intersect_area_geom(user_poly, intersect_polys,
                                   return_intersect_geom, fields='*')
    except Exception as e:
        logging.info('FAILED: {}'.format(e))
        return 'FAILED: {}\n  ERROR: {}'.format(x, e)

    if False:
        return error(status=400, detail='Not valid')
    return data


@endpoints.route('/endpoint', strict_slashes=False, methods=['POST'])
@validate_greeting
def polyIntersect_area_from_endpoint():
    x = []
    try:
        # Get parameters from POST
        user_poly = str(request.form['user_poly'])
        arcgis_server_layer = str(request.form['arcgis_server_layer'])

        # Verify that return geom_geom is True or False, if not defined,
        # make it False
        try:
            return_geom = str(request.form['return_geom'])
        except:
            return_geom = 'False'
        assert return_geom == 'False' or return_geom == 'True', \
            'return_geom is {}, must be "True" or "False"'.format(return_geom)
        if return_geom == 'False':
            return_intersect_geom = False
        elif return_geom == 'True':
            return_intersect_geom = True

        # Verify that return geom_geom is True or False, if not defined,
        # make it False
        try:
            buff = str(request.form['buffer'])
        except:
            buff = 'False'
        assert buff == 'False' or buff == 'True', \
            'buffer is {}, must be "True" or "False"'.format(buff)
        if buff == 'False':
            buffer_poly = False
        elif buff == 'True':
            buffer_poly = True

        data = intersect_area_geom_from_endpoint(user_poly,
                                                 arcgis_server_layer,
                                                 return_intersect_geom,
                                                 buffer_poly,
                                                 fields='*')
    except Exception as e:
        logging.info('FAILED: {}'.format(e))
        return 'FAILED: {}\n  ERROR: {}'.format(x, e)

    if False:
        return error(status=400, detail='Not valid')
    return data
