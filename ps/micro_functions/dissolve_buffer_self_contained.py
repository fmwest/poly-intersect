import geojson as gj
from shapely.geometry import mapping, shape
from shapely.geometry.multipolygon import MultiPolygon
from shapely.ops import transform, unary_union
import pyproj
from functools import partial

def verify_polygons(in_json):
    loaded_json = gj.loads(in_json)

    for feature in loaded_json['features']:
        geom_type = shape(feature['geometry']).geom_type
        if geom_type.lower() != 'polygon' and geom_type.lower() != 'multipolygon':
            print('  NOT POLY')
            raise AssertionError('Input JSON contains a feature not of type POLYGON or MULTIPOLYGON')
    return

def user_json_to_shapely_polys(in_json):
    polys = []

    loaded_json = gj.loads(in_json)

    for feature in loaded_json['features']:
        poly = shape(feature['geometry'])
        polys.append(poly)
    multi_polys = MultiPolygon(polys)

    polys_proj = transform(partial(pyproj.transform,
                  pyproj.Proj(init='EPSG:4326'),
                  pyproj.Proj(proj='eqc', lat1=multi_polys.bounds[1], lat2=multi_polys.bounds[3])), multi_polys)
    return polys_proj   

def dissolve(polys):
    dissolved = unary_union(polys)
    return dissolved

def buffer_polys(polys, dist_10km = 10000, dist_50km = 50000):
    buffer_10km = polys.buffer(dist_10km)
    buffer_50km = polys.buffer(dist_50km)
    return buffer_10km, buffer_50km

def proj_to_wgs84(polys):
    project = partial(pyproj.transform,
                      pyproj.Proj(proj="eqc"),
                      pyproj.Proj(init="epsg:4326"))

    polys_wgs84 = transform(project, polys)

    return polys_wgs84

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

def dissolve_and_buffer(aoi, return_shapely_polys=False):
    verify_polygons(aoi)
    
    user_polys = user_json_to_shapely_polys(aoi)
    user_polys_dissolve = dissolve(user_polys)
    user_polys_buffer10km, user_polys_buffer50km = buffer_polys(user_polys_dissolve)

    if return_shapely_polys:
        return user_polys_dissolve, user_polys_buffer10km, user_polys_buffer50km

    wgs84_user = proj_to_wgs84(user_polys_dissolve)
    wgs84_10km = proj_to_wgs84(user_polys_buffer10km)
    wgs84_50km = proj_to_wgs84(user_polys_buffer50km)

    feat_user = convert_to_geojson(wgs84_user, 'user_poly')
    feat_10km = convert_to_geojson(wgs84_10km, 'buffer_10km')
    feat_50km = convert_to_geojson(wgs84_50km, 'buffer_50km')

    collection = gj.FeatureCollection([feat_user, feat_10km, feat_50km])
    user_polys_and_buffers_json = gj.dumps(collection)

    return user_polys_and_buffers_json