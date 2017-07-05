import sys
import geojson as gj
import logging
import utils as u

def intersect_area_geom(user_json, intersect_polys_json, return_intersect_geom=False):
    try:
        #####===== VERIFY THAT INPUT JSON FILES ARE VALID, AND CONTAIN ONLY POLYGONS OR MULTIPOLYGONS =====#####
        u.verify_polygons(user_json)
        u.verify_polygons(intersect_polys_json)

        #####===== DEFINE THE RESULT OBJECT =====#####
        result = {}

        #####===== DISSOLVE USER POLYS AND CREATE 10KM AND 50KM BUFFERS =====#####
        user_polys = u.dissolve_to_single_feature(user_json)
        buffs_10km = u.buffer_and_dissolve_to_single_feature(user_json, 10000)
        buffs_50km = u.buffer_and_dissolve_to_single_feature(user_json, 50000)

        #####===== DISSOLVE INTERSECTION POLYGONS TO A SINGLE FEATURE =====#####
        intersect_polys = u.dissolve_to_single_feature(intersect_polys_json)

        #####===== CALCULATE INTERSECTIONS OF USER POLYGONS AND BUFFERS WITH INTERSECT POLYGONS =====#####
        intersection_user = user_polys.Intersection(intersect_polys)
        intersection_10km = buffs_10km.Intersection(intersect_polys)
        intersection_50km = buffs_50km.Intersection(intersect_polys)

        #####===== IF RETURN INTERSECT GEOMETRY IS TRUE, POPULATE RESULTS WITH INTERSECT GEOMETRY =====#####
        #####===== THIS IS DONE HERE BECAUSE THE u.calculate_area FUNCTION MODIFIES THE GEOMETRY OBJECTS =====#####
        if return_intersect_geom:
            result['intersect_geom_user'] = intersection_user.ExportToJson()
            result['intersect_geom_10km'] = intersection_10km.ExportToJson()
            result['intersect_geom_50km'] = intersection_50km.ExportToJson()

        #####===== CALCULATE AREA OF USER POLYS AND BUFFERS =====#####    
        user_area_ha = u.calculate_area(user_polys)
        buff_10km_ha = u.calculate_area(buffs_10km)
        buff_50km_ha = u.calculate_area(buffs_50km)

        #####===== CALCULATE AREA OF INTERSECTIONS =====#####
        user_area_intersection_ha = u.calculate_area(intersection_user)
        buff_10km_intersection_ha = u.calculate_area(intersection_10km)
        buff_50km_intersection_ha = u.calculate_area(intersection_50km)

        #####===== CALCULATE % OVERLAP =====#####
        pct_overlap_user = user_area_intersection_ha / user_area_ha
        pct_overlap_10km = buff_10km_intersection_ha / buff_10km_ha
        pct_overlap_50km = buff_50km_intersection_ha / buff_50km_ha

        #####===== POPULATE RESULTS WITH AREAS =====#####
        result['areaHa_user'] = user_area_ha
        result['areaHa_10km'] = buff_10km_ha
        result['areaHa_50km'] = buff_50km_ha
        result['pct_overlap_user'] = pct_overlap_user
        result['pct_overlap_10km'] = pct_overlap_10km
        result['pct_overlap_50km'] = pct_overlap_50km

        return gj.dumps(result)

    except Exception as e:
        raise 'Error in intersect_area_geom function.\n  ERROR MESSAGE{}'.format(e)


json = gj.dumps({"type":"FeatureCollection","features":[{"type":"Feature","properties":{},"geometry":{"type":"Polygon","coordinates":[[[-67.1044921875,-13.154376055418515],[-66.62109375,-13.154376055418515],[-66.62109375,-12.726084296948184],[-67.1044921875,-12.726084296948184],[-67.1044921875,-13.154376055418515]]]}},{"type":"Feature","properties":{},"geometry":{"type":"Polygon","coordinates":[[[-66.79962158203125,-13.215882123462867],[-66.44805908203125,-13.215882123462867],[-66.44805908203125,-13.001881592751694],[-66.79962158203125,-13.001881592751694],[-66.79962158203125,-13.215882123462867]]]}},{"type":"Feature","properties":{},"geometry":{"type":"Polygon","coordinates":[[[-66.99188232421874,-13.552551566455168],[-66.72821044921874,-13.552551566455168],[-66.72821044921874,-13.08215359040091],[-66.99188232421874,-13.08215359040091],[-66.99188232421874,-13.552551566455168]]]}},{"type":"Feature","properties":{},"geometry":{"type":"Polygon","coordinates":[[[-67.7197265625,-13.595269396120543],[-67.19238281249999,-13.595269396120543],[-67.19238281249999,-13.296084123052045],[-67.7197265625,-13.296084123052045],[-67.7197265625,-13.595269396120543]]]}}]})
#poly_equator = gj.dumps({"type":"FeatureCollection","features":[{"type":"Feature","properties":{},"geometry":{"type":"Polygon","coordinates":[[[-76.77383422851562,-2.1926103907087064],[-76.62002563476562,-2.1926103907087064],[-76.62002563476562,-2.0443963749034846],[-76.77383422851562,-2.0443963749034846],[-76.77383422851562,-2.1926103907087064]]]}}]})
#poly_north = gj.dumps({"type":"FeatureCollection","features":[{"type":"Feature","properties":{},"geometry":{"type":"Polygon","coordinates":[[[-40.27587890625,81.85342744432137],[-39.74853515625,81.85342744432137],[-39.74853515625,81.95399949951451],[-40.27587890625,81.95399949951451],[-40.27587890625,81.85342744432137]]]}}]})
#u2 = gj.dumps({"type":"FeatureCollection","features":[{"type":"Feature","properties":{},"geometry":{"type":"Polygon","coordinates":[[[-45,79.87429692631282],[-36.5625,79.87429692631282],[-36.5625,80.87282721505686],[-45,80.87282721505686],[-45,79.87429692631282]]]}},{"type":"Feature","properties":{},"geometry":{"type":"Polygon","coordinates":[[[-47.98828124999999,76.18499546094715],[-39.7265625,76.18499546094715],[-39.7265625,77.80477074199557],[-47.98828124999999,77.80477074199557],[-47.98828124999999,76.18499546094715]]]}}]})
p = gj.dumps({"type":"FeatureCollection","features":[{"type":"Feature","properties":{},"geometry":{"type":"Polygon","coordinates":[[[-68.18115234375,-12.511665400971019],[-68.15917968749999,-12.77162508236537],[-68.12896728515625,-13.036669323115234],[-67.5714111328125,-13.17577122442339],[-66.92047119140625,-13.205186527631493],[-66.8902587890625,-13.108905124689748],[-66.9232177734375,-13.015262066957174],[-66.9451904296875,-12.951029216018357],[-68.18115234375,-12.511665400971019]]]}},{"type":"Feature","properties":{},"geometry":{"type":"Polygon","coordinates":[[[-66.9781494140625,-12.755552799313902],[-67.027587890625,-13.114255082724755],[-66.26953125,-12.267547413218194],[-66.67053222656249,-12.149430892248033],[-66.86004638671875,-12.47680542229143],[-66.9781494140625,-12.755552799313902]]]}},{"type":"Feature","properties":{},"geometry":{"type":"Polygon","coordinates":[[[-66.610107421875,-14.046001880594341],[-66.15692138671875,-14.046001880594341],[-66.15692138671875,-13.255986429192873],[-66.610107421875,-13.255986429192873],[-66.610107421875,-14.046001880594341]]]}}]})

res = intersect_area_geom(json, p, True)
'''
print('\n')
print(gj.loads(res)['intersect_geom_user'])
print('\n')
print(gj.loads(res)['intersect_geom_10km'])
print('\n')
print(gj.loads(res)['intersect_geom_50km'])
'''
print('\ndone')