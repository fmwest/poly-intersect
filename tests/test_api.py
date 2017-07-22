import json

from os import path

from polyIntersect import app


fixtures = path.abspath(path.join(path.dirname(__file__), 'fixtures'))


with open(path.join(fixtures, 'maine.geojson')) as f:
    maine_geojson = "".join(f.read().split())


with open(path.join(fixtures, 'self-intersecting.geojson')) as f:
    self_intersecting_geojson = "".join(f.read().split())


def test_hello():
    test_app = app.test_client()
    url = '/api/v1/polyIntersect/hello?'
    result = test_app.get(url)
    assert result.status_code == 200
    assert result.content_type == 'application/json'


def test_poly_intersect_successful():
    test_app = app.test_client()
    url = '/api/v1/polyIntersect'

    payload = {}
    payload['user_poly'] = maine_geojson
    payload['intersect_polys'] = maine_geojson

    result = test_app.post(url, data=payload)

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
    payload['user_poly'] = self_intersecting_geojson
    payload['intersect_polys'] = self_intersecting_geojson

    result = app.post(url, data=payload)
    assert result.status_code == 200
    assert result.content_type == 'application/json'
    result_obj = json.loads(result.data)
    assert isinstance(result_obj, dict)


def test_geom_area():
    url = '/api/v1/polyIntersect/geom'
    payload = {}
    payload['user_poly'] = maine_geojson
    payload['intersect_polys'] = maine_geojson

    result = app.post(url, data=payload)
    assert result.status_code == 200
    assert result.content_type == 'application/json'
