import geojson as gj
import logging
import polyIntersect.micro_functions.utils as u

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
        pct_overlap_user = user_area_intersection_ha / user_area_ha * 100
        pct_overlap_10km = buff_10km_intersection_ha / buff_10km_ha * 100
        pct_overlap_50km = buff_50km_intersection_ha / buff_50km_ha * 100

        #####===== POPULATE RESULTS WITH AREAS =====#####
        result['areaHa_user'] = user_area_ha
        result['areaHa_10km'] = buff_10km_ha
        result['areaHa_50km'] = buff_50km_ha
        result['pct_overlap_user'] = pct_overlap_user
        result['pct_overlap_10km'] = pct_overlap_10km
        result['pct_overlap_50km'] = pct_overlap_50km

        return result
    except:
        raise
