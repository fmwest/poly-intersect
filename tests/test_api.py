import json

from polyIntersect import app

# data
from .sample_data import MAINE_GEOJSON
from .sample_data import SELF_INTERSECTING_GEOJSON
from .sample_data import INTERSECT_BASE_GEOJSON
from .sample_data import INTERSECT_FULLY_WITHIN_GEOJSON
from .sample_data import INTERSECT_PARTIALLY_WITHIN_GEOJSON


# test flask client
app = app.test_client()


def test_hello():
    url = '/api/v1/polyIntersect/hello?'
    result = app.get(url)
    assert result.status_code == 200
    assert result.content_type == 'application/json'


def test_execute_graph():
    url = '/api/v1/polyIntersect/executeGraph?'

    graph = {'convert_aoi':       ['geojson', json.loads(INTERSECT_BASE_GEOJSON)],
             'convert_intersect': ['geojson', json.loads(INTERSECT_FULLY_WITHIN_GEOJSON)],
             'dissolve_aoi':      ['dissolve', 'convert_aoi'],
             'buffer_aoi':        ['buffer_to_dist', 'dissolve_aoi', 10],
             'intersect_aoi':     ['intersect', 'buffer_aoi', 'convert_intersect'],
             'area_overlap':      ['get_area_overlap', 'convert_aoi', 'intersect_aoi']} 

    payload = {}
    payload['dag'] = json.dumps(graph)
    payload['result_keys'] = json.dumps(['intersect_aoi', 'area_overlap'])

    result = app.post(url, data=payload)
    result_obj = json.loads(result.data)

    assert result.status_code == 200
    assert result.content_type == 'application/json'
    assert 'intersect_aoi' in list(result_obj.keys())
    assert 'area_overlap' in list(result_obj.keys())


def _test_execute_graph_with_invalid_method():
    url = '/api/v1/polyIntersect/executeGraph?'

    graph = {'convert_aoi':       ['geojson', json.loads(INTERSECT_BASE_GEOJSON)],
             'convert_intersect': ['geojson', json.loads(INTERSECT_FULLY_WITHIN_GEOJSON)],
             'dissolve_aoi':      ['dissolve', 'convert_aoi'],
             'buffer_aoi':        ['buffer_to_dist', 'dissolve_aoi', 10],
             'intersect_aoi':     ['intersect', 'buffer_aoi', 'convert_intersect'],
             'area_overlap':      ['get_area_overlap', 'convert_aoi', 'intersect_aoi'],
             'result_keys':       ['intersect_aoi', 'area_overlap']}

    payload = {}
    payload['dag'] = json.dumps(graph)

    result = app.post(url, data=payload)

    # make sure this returns a malformed request error

    assert result.status_code == 200
    assert result.content_type == 'application/json'


def _test_poly_intersect_successful():
    url = '/api/v1/polyIntersect'

    payload = {}
    payload['user_poly'] = MAINE_GEOJSON
    payload['intersect_polys'] = MAINE_GEOJSON

    result = app.post(url, data=payload)

    assert result.status_code == 200
    assert result.content_type == 'application/json'
    assert result.data

    result_obj = json.loads(result.data)
    assert isinstance(result_obj, dict)
    assert 'areaHa_10km' in result_obj.keys()
    assert 'areaHa_50km' in result_obj.keys()
    assert 'pct_overlap_10km' in result_obj.keys()
    assert 'pct_overlap_50km' in result_obj.keys()
    assert 'pct_overlap_user' in result_obj.keys()
    assert result_obj['pct_overlap_user'] == 100


def _test_poly_intersect_successful_with_self_intersecting_polygon():
    url = '/api/v1/polyIntersect'

    payload = {}
    payload['user_poly'] = SELF_INTERSECTING_GEOJSON
    payload['intersect_polys'] = SELF_INTERSECTING_GEOJSON

    result = app.post(url, data=payload)
    assert result.status_code == 200
    assert result.content_type == 'application/json'

    result_obj = json.loads(result.data)
    assert isinstance(result_obj, dict)


def _test_geom_area():
    url = '/api/v1/polyIntersect/geom'
    payload = {}
    payload['user_poly'] = MAINE_GEOJSON
    payload['intersect_polys'] = MAINE_GEOJSON

    result = app.post(url, data=payload)
    assert result.status_code == 200
    assert result.content_type == 'application/json'
