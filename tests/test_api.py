import json

from polyIntersect import app

# data
from .sample_data import MAINE_GEOJSON
from .sample_data import SELF_INTERSECTING_GEOJSON


# test flask client
app = app.test_client()


def test_hello():
    url = '/api/v1/polyIntersect/hello?'
    result = app.get(url)
    assert result.status_code == 200
    assert result.content_type == 'application/json'


def test_execute_graph():
    url = '/api/v1/polyIntersect/executeGraph?'


def test_poly_intersect_successful():
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


def test_poly_intersect_successful_with_self_intersecting_polygon():
    url = '/api/v1/polyIntersect'

    payload = {}
    payload['user_poly'] = SELF_INTERSECTING_GEOJSON
    payload['intersect_polys'] = SELF_INTERSECTING_GEOJSON

    result = app.post(url, data=payload)
    assert result.status_code == 200
    assert result.content_type == 'application/json'

    result_obj = json.loads(result.data)
    assert isinstance(result_obj, dict)


def test_geom_area():
    url = '/api/v1/polyIntersect/geom'
    payload = {}
    payload['user_poly'] = MAINE_GEOJSON
    payload['intersect_polys'] = MAINE_GEOJSON

    result = app.post(url, data=payload)
    assert result.status_code == 200
    assert result.content_type == 'application/json'
