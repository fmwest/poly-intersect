import geojson as gj
from shapely.geometry import mapping, shape
from shapely.geometry.multipolygon import MultiPolygon
from shapely.ops import transform, unary_union
import pyproj
from functools import partial

def verify_polygons(in_json):
    if not in_json:
        return 'JSON input is empty.'
    try:
        loaded_json = gj.loads(in_json)
    except Exception as e:
        return 'Invalid JSON input.  ERROR MESSAGE: {}.'.format(e)

    for feature in loaded_json['features']:
        geom_type = shape(feature['geometry']).geom_type
        if geom_type.lower() != 'polygon' and geom_type.lower() != 'multipolygon':
            return 'Input JSON contains a feature not of type POLYGON or MULTIPOLYGON.'
    return True

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

def proj_to_wgs84(polys):
    project = partial(pyproj.transform,
                      pyproj.Proj(proj="eqc"),
                      pyproj.Proj(init="epsg:4326"))

    polys_wgs84 = transform(project, polys)

    return polys_wgs84

def dissolve_polys(aoi, return_shapely_dissolve=False):
    #####===== verify() function commented out for land_rights microservice because verification is done in land_rights.py =====#####
    #verified = verify_polygons(aoi)
    #if verified != True:
    #    raise AssertionError(verified)

    user_polys = user_json_to_shapely_polys(aoi)
    user_polys_dissolve = dissolve(user_polys)

    if return_shapely_dissolve:
        return user_polys_dissolve
    
    user_polys_dissolve_wgs84 = proj_to_wgs84(user_polys_dissolve)
    user_polys_dissolve_json = gj.dumps(mapping(user_polys_dissolve_wgs84))

    return user_polys_dissolve_json
