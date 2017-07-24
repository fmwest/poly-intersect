from os import path
import rtree

from polyIntersect.micro_functions.poly_intersect import json2ogr
from polyIntersect.micro_functions.poly_intersect import ogr2json
from polyIntersect.micro_functions.poly_intersect import dissolve
from polyIntersect.micro_functions.poly_intersect import intersect
from polyIntersect.micro_functions.poly_intersect import index_featureset

from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon

from .sample_data import DISSOLVE_GEOJSON
from .sample_data import INTERSECT_BASE_GEOJSON
from .sample_data import INTERSECT_PARTIALLY_WITHIN_GEOJSON

fixtures = path.abspath(path.join(path.dirname(__file__), 'fixtures'))


def test_successfully_index_featureset():
    featureset = json2ogr(DISSOLVE_GEOJSON)
    index = index_featureset(featureset)
    assert isinstance(index, rtree.index.Index)


def test_successfully_dissolve_string_field():
    featureset = json2ogr(DISSOLVE_GEOJSON)
    assert len(featureset['features']) == 4

    geom_diss = dissolve(featureset, field='str_value')
    assert len(geom_diss['features']) == 2


def test_successfully_dissolve_int_field():
    featureset = json2ogr(DISSOLVE_GEOJSON)
    assert len(featureset['features']) == 4

    geom_diss = dissolve(featureset, field='int_value')
    assert len(geom_diss['features']) == 2


def test_successfully_dissolve_decimal_field():
    featureset = json2ogr(DISSOLVE_GEOJSON)
    assert len(featureset['features']) == 4

    geom_diss = dissolve(featureset, field='dec_value')
    assert len(geom_diss['features']) == 2


def test_successfully_dissolve_no_field_arg():
    featureset = json2ogr(DISSOLVE_GEOJSON)
    assert len(featureset['features']) == 4

    geom_diss = dissolve(featureset)
    assert len(geom_diss['features']) == 1


def test_successful_intersection():

    featureset1 = json2ogr(INTERSECT_PARTIALLY_WITHIN_GEOJSON)
    featureset2 = json2ogr(INTERSECT_BASE_GEOJSON)

    result_featureset = intersect(featureset1, featureset2)
    assert len(result_featureset['features']) == 1
    assert isinstance(result_featureset['features'][0]['geometry'],
                      MultiPolygon)


def test_json2ogr():
    geom_converted_version = json2ogr(DISSOLVE_GEOJSON)

    assert isinstance(geom_converted_version, dict)
    assert 'features' in geom_converted_version.keys()

    for f in geom_converted_version['features']:
        assert isinstance(f['geometry'], Polygon)


def test_ogr2json():

    geom_converted_version = json2ogr(DISSOLVE_GEOJSON)
    geom_converted_back = ogr2json(geom_converted_version)

    for i, f in enumerate(geom_converted_back['features']):
        assert isinstance(f['geometry'], dict)
