from os import path

from polyIntersect.micro_functions.poly_intersect import json2ogr
from polyIntersect.micro_functions.poly_intersect import dissolve
from polyIntersect.micro_functions.poly_intersect import intersect

from .sample_data import DISSOLVE_ME

fixtures = path.abspath(path.join(path.dirname(__file__), 'fixtures'))


def test_dissolve_successful():
    import pdb;pdb.set_trace()
    geom = json2ogr(DISSOLVE_ME)
    geom_diss = dissolve(geom, 'str_value')
    assert geom_diss.GetGeometryCount() == 2


def test_intersect_successful():
    import pdb;pdb.set_trace()
    geom_intersect = intersect(self_intersect, self_intersect)
    assert geom_intersect
