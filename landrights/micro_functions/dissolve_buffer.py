import geojson as gj
from shapely.geometry import mapping, shape
from shapely.geometry.multipolygon import MultiPolygon
from shapely.ops import transform, unary_union
import pyproj
from functools import partial
from landrights.micro_functions.dissolve import dissolve_polys

def buffer_polys(polys, dist_10km = 10000, dist_50km = 50000):
    buffer_10km = polys.buffer(dist_10km)
    buffer_50km = polys.buffer(dist_50km)
    return buffer_10km, buffer_50km

def convert_to_geojson(polys, name):
    geom_type = polys.geom_type
    polys_mapping = mapping(polys)

    if geom_type == 'Polygon':
        geojson = gj.Feature(properties={"name": name}, geometry=gj.Polygon(polys_mapping['coordinates']))
    elif geom_type == 'MultiPolygon':
        geojson = gj.Feature(properties={"name": name}, geometry=gj.MultiPolygon(polys_mapping['coordinates']))
    else:
        return AssertionError('{} is not of type Polygon or MultiPolygon'.format(name))
    return geojson

def dissolve_and_buffer(aoi, return_shapely_buffers=False):
    user_polys = dissolve_polys(aoi, return_shapely_dissolve=True)
    user_polys_buffer10km, user_polys_buffer50km = buffer_polys(user_polys)

    if return_shapely_buffers:
        return user_polys, user_polys_buffer10km, user_polys_buffer50km

    from landrights.micro_functions.dissolve import proj_to_wgs84
    wgs84_user = proj_to_wgs84(user_polys)
    wgs84_10km = proj_to_wgs84(user_polys_buffer10km)
    wgs84_50km = proj_to_wgs84(user_polys_buffer50km)

    feat_user = convert_to_geojson(wgs84_user, 'user_poly')
    feat_10km = convert_to_geojson(wgs84_10km, 'buffer_10km')
    feat_50km = convert_to_geojson(wgs84_50km, 'buffer_50km')

    collection = gj.FeatureCollection([feat_user, feat_10km, feat_50km])
    user_polys_and_buffers_json = gj.dumps(collection)

    return user_polys_and_buffers_json