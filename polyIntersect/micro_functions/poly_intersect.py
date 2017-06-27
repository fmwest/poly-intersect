import geojson as gj
from shapely.geometry import mapping, shape
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.polygon import Polygon
from shapely.ops import transform
import pyproj
from functools import partial
from polyIntersect.micro_functions.dissolve_buffer import dissolve_and_buffer, convert_to_geojson
from polyIntersect.micro_functions.dissolve import verify_polygons, proj_to_wgs84
import logging


def get_intersection(u_polys, intersect_polys_json):
    # Get geometry of intersect polys and calculate intersection polygons
    intersections = []

    loaded_json = gj.loads(intersect_polys_json)

    for feature in loaded_json['features']:
        poly = shape(feature['geometry'])

        # Projects to Albers Equal Area (i.e. 'aea') for area calculation
        poly_proj = transform(partial(pyproj.transform,
                      pyproj.Proj(init='EPSG:4326'),
                      pyproj.Proj(
                      proj='eqc',
                      lat1=poly.bounds[1],
                      lat2=poly.bounds[3])),
                      poly)
        intersection = u_polys.intersection(poly_proj)
        if intersection:
            intersections.append(intersection)

    # Convert list of multiple polygons to a single multipolygon and calculate area of multipolygon
    all_intersections = MultiPolygon(intersections)

    return all_intersections

def intersect_area_geom(user_json, intersect_polys_json, return_intersect_geom=False):
    verified = verify_polygons(user_json)
    if verified != True:
        raise AssertionError('{} Error found in user polygon(s) input'.format(verified))
    
    verified = verify_polygons(intersect_polys_json)
    if verified != True:
        raise AssertionError('{} Error found in user polygon(s) input'.format(verified))

    # Get user polygon geometry
    user_polys, buffer_10km, buffer_50km = dissolve_and_buffer(user_json, return_shapely_buffers=True)

    # Convert from sq. meters to hectares
    user_poly_area = user_polys.area*0.0001
    area_10km = buffer_10km.area*0.0001
    area_50km = buffer_50km.area*0.0001

    intersection_user = get_intersection(user_polys, intersect_polys_json)
    intersection_10km = get_intersection(buffer_10km, intersect_polys_json)
    intersection_50km = get_intersection(buffer_50km, intersect_polys_json)

    # Convert from sq. meters to hectares
    intersection_area_user = intersection_user.area*0.0001
    intersection_area_10km = intersection_10km.area*0.0001
    intersection_area_50km = intersection_50km.area*0.0001

    # 
    pct_overlap_user = intersection_area_user / user_poly_area * 100
    pct_overlap_10km = intersection_area_10km / area_10km * 100
    pct_overlap_50km = intersection_area_50km / area_50km * 100

    result = {}
    result['areaHa_user'] = user_poly_area
    result['areaHa_10km'] = area_10km
    result['areaHa_50km'] = area_50km
    result['pct_overlap_user'] = pct_overlap_user
    result['pct_overlap_10km'] = pct_overlap_10km
    result['pct_overlap_50km'] = pct_overlap_50km

    if return_intersect_geom:
        wgs84_user = proj_to_wgs84(intersection_user)
        wgs84_10km = proj_to_wgs84(intersection_10km)
        wgs84_50km = proj_to_wgs84(intersection_50km)

        fc_user = convert_to_geojson(wgs84_user, 'user_poly')
        fc_10km = convert_to_geojson(wgs84_10km, 'buffer_10km')
        fc_50km = convert_to_geojson(wgs84_50km, 'buffer_50km')

        result['intersect_geom_user'] = fc_user
        result['intersect_geom_10km'] = fc_10km
        result['intersect_geom_50km'] = fc_50km

    return gj.dumps(result)