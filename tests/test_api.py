import json

import pytest

from polyIntersect import app

# data
from .sample_data import DISSOLVE_GEOJSON
from .sample_data import INTERSECT_BASE_GEOJSON
from .sample_data import INTERSECT_PARTIALLY_WITHIN_GEOJSON
from .sample_data import BRAZIL_USER_POLY
from .sample_data import get_indonesia


# test flask client
app = app.test_client()

slow = pytest.mark.skipif(
    not pytest.config.getoption("--runslow"),
    reason="need --runslow option to run"
)


def test_execute_graph():
    url = '/api/v1/polyIntersect/executeGraph?'

    feats1 = json.loads(INTERSECT_PARTIALLY_WITHIN_GEOJSON)
    feats2 = json.loads(INTERSECT_BASE_GEOJSON)

    graph = {'convert_aoi': ['geojson', json.loads(DISSOLVE_GEOJSON)],
             'convert_intersect_partial': ['geojson', feats1],
             'convert_intersect_base': ['geojson', feats2],
             'dissolve_aoi': ['dissolve', 'convert_aoi', 'str_value'],
             'intersect_aoi': ['intersect',
                               'convert_intersect_partial',
                               'convert_intersect_base']}

    payload = {}
    payload['dag'] = json.dumps(graph)
    payload['result_keys'] = json.dumps(['intersect_aoi', 'dissolve_aoi'])

    result = app.post(url, data=payload)
    result_obj = json.loads(result.data)

    assert result.status_code == 200
    assert result.content_type == 'application/json'
    assert 'intersect_aoi' in list(result_obj.keys())
    assert 'dissolve_aoi' in list(result_obj.keys())


def test_example_graph():
    url = '/api/v1/polyIntersect/brazil-biomes?'

    feats1 = json.loads(BRAZIL_USER_POLY)

    payload = {}
    payload['user_json'] = json.dumps(feats1)
    payload['category'] = 'name'

    result = app.post(url, data=payload)
    result_obj = json.loads(result.data)

    assert result.status_code == 200
    assert result.content_type == 'application/json'
    assert 'intersect-area' in list(result_obj.keys())
    assert 'intersect-area-percent' in list(result_obj.keys())


@slow
def test_dissolve_indonesia():
    url = '/api/v1/polyIntersect/executeGraph?'
    INDONESIA_GEOJSON = get_indonesia()

    feats1 = json.loads(INDONESIA_GEOJSON)
    graph = {
        'convert_aoi': ['geojson', feats1],
        'dissolve_aoi': ['dissolve', 'convert_aoi'],
    }

    payload = {}
    payload['dag'] = json.dumps(graph)
    payload['result_keys'] = json.dumps(['dissolve_aoi'])

    result = app.post(url, data=payload)
    result_obj = json.loads(result.data)

    assert result.status_code == 200
    assert result.content_type == 'application/json'
    assert 'dissolve_aoi' in list(result_obj.keys())
