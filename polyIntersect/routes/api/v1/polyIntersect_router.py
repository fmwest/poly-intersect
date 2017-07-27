from os import path
import dask
import json
from flask import request, jsonify
from polyIntersect.routes.api.v1 import endpoints
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


@endpoints.route('/hello', strict_slashes=False, methods=['GET', 'POST'])
def hello():
    data = 'hello adnan'
    return data


@endpoints.route('/brazil-biomes', strict_slashes=False, methods=['POST'])
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
