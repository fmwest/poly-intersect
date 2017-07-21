
from os import path

from polyIntersect import app

app = app.test_client()

fixtures = path.abspath(path.join(path.dirname(__file__), 'fixtures'))

with open(path.join(fixtures, 'maine.geojson')) as f:
    maine = "".join(f.read().split())

with open(path.join(fixtures, 'maine-geometry.geojson')) as f:
    maine_geom = "".join(f.read().split())

with open(path.join(fixtures, 'maine-featureset.geojson')) as f:
    maine_featureset = "".join(f.read().split())


def test_hello():
    url = '/api/v1/polyIntersect/hello?'
    result = app.get(url)
    assert result.status_code == 200


def test_poly_intersect_successful():
    url = '/api/v1/polyIntersect'

    payload = {}
    payload['user_poly'] = maine_featureset
    payload['intersect_polys'] = maine_featureset

    result = app.post(url, data=payload)
    assert result.status_code == 200


def test_geom_area():
    url = '/api/v1/polyIntersect/geom'
    payload = {}
    payload['user_poly'] = maine_featureset
    payload['intersect_polys'] = maine_featureset

    result = app.post(url, data=payload)
    assert result.status_code == 200
