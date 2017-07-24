from os import path

from polyIntersect.micro_functions.poly_intersect import json2ogr
from polyIntersect.micro_functions.poly_intersect import dissolve
from polyIntersect.micro_functions.poly_intersect import intersect

from .sample_data import DISSOLVE_GEOJSON

fixtures = path.abspath(path.join(path.dirname(__file__), 'fixtures'))


def test_dissolve_successful():
    geom = json2ogr(DISSOLVE_GEOJSON)
    geom_diss = dissolve(geom)
    assert geom_diss.GetGeometryCount() == 1


def test_intersect_successful():
    import pdb;pdb.set_trace()
    assert False
