from os import path
import rtree
import json

from polyIntersect.micro_functions.poly_intersect import esri_server2ogr
from polyIntersect.micro_functions.poly_intersect import json2ogr
from polyIntersect.micro_functions.poly_intersect import ogr2json
from polyIntersect.micro_functions.poly_intersect import dissolve
from polyIntersect.micro_functions.poly_intersect import intersect
from polyIntersect.micro_functions.poly_intersect import index_featureset
from polyIntersect.micro_functions.poly_intersect import buffer_to_dist
from polyIntersect.micro_functions.poly_intersect import project_local
from polyIntersect.micro_functions.poly_intersect import get_intersect_area
from polyIntersect.micro_functions.poly_intersect import get_intersect_area_percent
from polyIntersect.micro_functions.poly_intersect import get_intersect_count
from polyIntersect.micro_functions.poly_intersect import get_intersect_z_scores


from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon

from .sample_data import DISSOLVE_GEOJSON
from .sample_data import INTERSECT_BASE_GEOJSON
from .sample_data import INTERSECT_PARTIALLY_WITHIN_GEOJSON
from .sample_data import INTERSECT_MULTIPLE_FEATURES
from .sample_data import INDONESIA_USER_POLY
from .sample_data import BRAZIL_USER_POLY

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


def test_maintain_crs():
    featureset = json2ogr(DISSOLVE_GEOJSON)
    assert len(featureset['features']) == 4

    geom_diss = dissolve(featureset, field='str_value')
    assert len(geom_diss['features']) == 2
    assert 'crs' in geom_diss.keys()


def test_successful_intersection():

    featureset1 = json2ogr(INTERSECT_PARTIALLY_WITHIN_GEOJSON)
    featureset2 = json2ogr(INTERSECT_BASE_GEOJSON)

    result_featureset = intersect(featureset1, featureset2)
    assert len(result_featureset['features']) == 1
    assert isinstance(result_featureset['features'][0]['geometry'],
                      MultiPolygon)


def test_project():
    featureset = json2ogr(DISSOLVE_GEOJSON)
    assert len(featureset['features']) == 4

    geom_projected = project_local(featureset)
    assert isinstance(geom_projected, dict)
    assert 'features' in geom_projected.keys()
    assert (geom_projected['crs']['properties']['name']
            == 'urn:ogc:def:uom:EPSG::9102')
    assert (featureset['crs']['properties']['name']
           != 'urn:ogc:def:uom:EPSG::9102')


def test_project_already_projected():
    featureset = json2ogr(DISSOLVE_GEOJSON)
    assert len(featureset['features']) == 4

    geom_projected1 = project_local(featureset)
    try:
        geom_projected2 = project_local(geom_projected1)
    except ValueError as e:
        assert str(e) == 'geometries have already been projected with the \
                          World Azimuthal Equidistant coordinate system'


def test_projected_buffer():
    featureset = json2ogr(DISSOLVE_GEOJSON)
    assert len(featureset['features']) == 4

    geom_projected = project_local(featureset)
    geom_buffered = buffer_to_dist(geom_projected, 10)
    assert isinstance(geom_buffered, dict)
    assert 'features' in geom_buffered.keys()
    assert len(geom_buffered['features']) == 4

    for f_in, f_out in zip(featureset['features'], geom_buffered['features']):
        assert f_out['geometry'].area > f_in['geometry'].area


def test_not_projected_buffer():
    featureset = json2ogr(DISSOLVE_GEOJSON)
    assert len(featureset['features']) == 4

    try:
        geom_buffered = buffer_to_dist(featureset, 10)
    except ValueError as e:
        assert str(e) == 'geometries must be projected with the World \
                          Azimuthal Equidistant coordinate system'


def test_area_percent_no_categories():
    featureset1 = json2ogr(INTERSECT_PARTIALLY_WITHIN_GEOJSON)
    featureset2 = json2ogr(INTERSECT_BASE_GEOJSON)

    result_featureset = intersect(featureset1, featureset2)
    assert len(result_featureset['features']) == 1

    pct_overlap = get_intersect_area_percent(featureset1, result_featureset)
    assert isinstance(pct_overlap, float)
    assert pct_overlap > 0 and pct_overlap <= 100


def test_area_percent_with_categories():
    featureset1 = json2ogr(INTERSECT_BASE_GEOJSON)
    featureset2 = json2ogr(INTERSECT_MULTIPLE_FEATURES)

    intersection = intersect(featureset1, featureset2)
    assert len(intersection['features']) == 2
    field_vals = [f['properties']['id'] for f in intersection['features']]
    assert len(field_vals) == len(set(field_vals))

    pct_overlap = get_intersect_area_percent(featureset1, intersection,
                                             category='id')
    assert isinstance(pct_overlap, dict)
    assert len(pct_overlap.keys()) == 2
    for val in pct_overlap.keys():
        assert pct_overlap[val] > 0 and pct_overlap[val] <= 100


def test_area_stats_with_categories():
    featureset1 = json2ogr(INTERSECT_BASE_GEOJSON)
    featureset2 = json2ogr(INTERSECT_MULTIPLE_FEATURES)

    intersection = intersect(featureset1, featureset2)
    assert len(intersection['features']) == 2
    field_vals = [f['properties']['id'] for f in intersection['features']]
    assert len(field_vals) == len(set(field_vals))

    pct_overlap = get_intersect_area_percent(featureset1, intersection,
                                             category='id')
    assert isinstance(pct_overlap, dict)
    assert len(pct_overlap.keys()) == 2
    for val in pct_overlap.keys():
        assert pct_overlap[val] > 0 and pct_overlap[val] <= 100


def test_area_percent_no_categories_fail():
    featureset1 = json2ogr(INTERSECT_BASE_GEOJSON)
    featureset2 = json2ogr(INTERSECT_MULTIPLE_FEATURES)

    intersection = intersect(featureset1, featureset2)
    assert len(intersection['features']) == 2
    field_vals = [f['properties']['id'] for f in intersection['features']]
    assert len(field_vals) == len(set(field_vals))

    try:
        pct_overlap = get_intersect_area_percent(featureset1, intersection,
                                                 category='id')
    except ValueError as e:
        assert str(e) == 'Intersected area must be dissolved to a single \
                              feature if no category field is specified'


def test_count():
    featureset1 = json2ogr(INTERSECT_BASE_GEOJSON)
    featureset2 = json2ogr(INTERSECT_MULTIPLE_FEATURES)

    intersection = intersect(featureset1, featureset2)
    assert len(intersection['features']) == 2

    count = get_intersect_count(intersection, 'id')
    assert count == 3


def test_z_scores():
    featureset1 = json2ogr(INTERSECT_BASE_GEOJSON)
    featureset2 = json2ogr(INTERSECT_MULTIPLE_FEATURES)

    intersection = intersect(featureset1, featureset2)
    assert len(intersection['features']) == 2

    scores = get_intersect_z_scores(intersection, 'id', 'value')
    assert len(scores) == 2
    assert 1 in scores.keys() and 2 in scores.keys()
    assert isinstance(scores[1], float)


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


def test_esri_server2json():
    host = 'http://gis-gfw.wri.org'
    layer = 'country_data/south_america/MapServer/4'
    layer_url = path.join(host, 'arcgis/rest/services', layer)

    featureset = esri_server2ogr(layer_url, BRAZIL_USER_POLY)
    assert 'features' in featureset.keys()
    assert isinstance(featureset['features'][0]['geometry'], (Polygon, MultiPolygon))
    assert len(featureset['features']) > 0
