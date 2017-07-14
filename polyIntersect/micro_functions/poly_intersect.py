import geojson as gj
import polyIntersect.micro_functions.utils as u

def intersect_area_geom(user_json, intersect_json, return_intersect_geom, fields='*'):
    try:
        #####===== VERIFY THAT INPUT JSON FILES ARE VALID, AND CONTAIN ONLY POLYGONS OR MULTIPOLYGONS =====#####
        u.verify_polygons(user_json)
        u.verify_polygons(intersect_json)
        
        #####===== DEFINE THE RESULT OBJECT =====#####
        result = {}

        #####===== CONVERT INPUT JSON TO OGR POLYGONS =====#####
        user_ogr      = u.json_polys_to_ogr(user_json) 
        intersect_ogr = u.json_polys_to_ogr(intersect_json)

        #####===== DISSOLVE USER POLYS AND CREATE 10KM AND 50KM BUFFERS =====#####
        user_dissolve  = u.dissolve_ogr_to_single_feature(user_ogr)
        buff_10km = u.buffer_ogr_polygons(user_dissolve.Clone(), 10000)
        buff_50km = u.buffer_ogr_polygons(user_dissolve.Clone(), 50000)

        #####===== DISSOLVE INTERSECTION POLYGONS TO A SINGLE FEATURE =====#####
        intersect_polygons = u.dissolve_ogr_to_single_feature(intersect_ogr)

        #####===== CALCULATE INTERSECTIONS OF USER POLYGONS AND BUFFERS WITH INTERSECT POLYGONS =====#####
        intersection_user = user_dissolve.Intersection(intersect_polygons)
        intersection_10km = buff_10km.Intersection(intersect_polygons)
        intersection_50km = buff_50km.Intersection(intersect_polygons)

        #####===== IF RETURN INTERSECT GEOMETRY IS TRUE, POPULATE RESULTS WITH INTERSECT GEOMETRY =====#####
        #####===== THIS IS DONE HERE BECAUSE THE u.calculate_dissolved_area FUNCTION MODIFIES THE GEOMETRY OBJECTS =====#####
        if return_intersect_geom:
            result['intersect_geom_user'] = intersection_user.ExportToJson()
            result['intersect_geom_10km'] = intersection_10km.ExportToJson()
            result['intersect_geom_50km'] = intersection_50km.ExportToJson()

        #####===== CALCULATE AREA OF USER POLYS AND BUFFERS =====#####    
        user_area_ha = u.calculate_dissolved_area(user_dissolve)
        buff_10km_ha = u.calculate_dissolved_area(buff_10km)
        buff_50km_ha = u.calculate_dissolved_area(buff_50km)

        #####===== CALCULATE AREA OF INTERSECTIONS =====#####
        user_area_intersection_ha = u.calculate_dissolved_area(intersection_user)
        buff_10km_intersection_ha = u.calculate_dissolved_area(intersection_10km)
        buff_50km_intersection_ha = u.calculate_dissolved_area(intersection_50km)

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

        return str(result)
    except:
        raise
'''
def intersect_area_geom_from_endpoint(user_json, arcgis_server_layer, return_intersect_geom, fields='*'):
    try:
        #####===== VERIFY THAT INPUT JSON FILES ARE VALID, AND CONTAIN ONLY POLYGONS OR MULTIPOLYGONS =====#####
        u.verify_polygons(user_json)
        
        #####===== DEFINE THE RESULT OBJECT =====#####
        result = {}

        #####===== CONVERT INPUT JSON TO OGR POLYGONS =====#####
        user_ogr = u.json_polys_to_ogr(user_json) 

        #####===== DISSOLVE USER POLYS AND CREATE 10KM AND 50KM BUFFERS =====#####
        user_dissolve  = u.dissolve_ogr_to_single_feature(user_ogr)
        buff_10km = u.buffer_ogr_polygons(user_dissolve.Clone(), 10000)
        buff_50km = u.buffer_ogr_polygons(user_dissolve.Clone(), 50000)

        #####===== GET INTERSECT GEOMETRY FROM ARC ENDPOINT =====#####
        intersect_polys_json = u.get_intersect_geom_from_endpoint(buff_50km, arcgis_server_layer, fields)
        u.verify_polygons(intersect_polys_json)

        #####===== CONVERT INTERSECT GEOMETRY TO OGR POLYGONS =====#####
        intersect_ogr = u.json_polys_to_ogr(intersect_polys_json)

        #####===== DISSOLVE INTERSECTION POLYGONS TO A SINGLE FEATURE =====#####
        intersect_polygons = u.dissolve_ogr_to_single_feature(intersect_ogr)

        #####===== CALCULATE INTERSECTIONS OF USER POLYGONS AND BUFFERS WITH INTERSECT POLYGONS =====#####
        intersection_user = user_dissolve.Intersection(intersect_polygons)
        intersection_10km = buff_10km.Intersection(intersect_polygons)
        intersection_50km = buff_50km.Intersection(intersect_polygons)

        #####===== IF RETURN INTERSECT GEOMETRY IS TRUE, POPULATE RESULTS WITH INTERSECT GEOMETRY =====#####
        #####===== THIS IS DONE HERE BECAUSE THE u.calculate_dissolved_area FUNCTION MODIFIES THE GEOMETRY OBJECTS =====#####
        if return_intersect_geom:
            result['intersect_geom_user'] = intersection_user.ExportToJson()
            result['intersect_geom_10km'] = intersection_10km.ExportToJson()
            result['intersect_geom_50km'] = intersection_50km.ExportToJson()

        #####===== CALCULATE AREA OF USER POLYS AND BUFFERS =====#####    
        user_area_ha = u.calculate_dissolved_area(user_dissolve)
        buff_10km_ha = u.calculate_dissolved_area(buff_10km)
        buff_50km_ha = u.calculate_dissolved_area(buff_50km)

        #####===== CALCULATE AREA OF INTERSECTIONS =====#####
        user_area_intersection_ha = u.calculate_dissolved_area(intersection_user)
        buff_10km_intersection_ha = u.calculate_dissolved_area(intersection_10km)
        buff_50km_intersection_ha = u.calculate_dissolved_area(intersection_50km)

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

        return str(result)
    except:
        raise
'''
def intersect_area_geom_from_endpoint(user_json, arcgis_server_layer, return_intersect_geom, buff, fields='*'):
    try:
        #####===== VERIFY THAT INPUT JSON FILES ARE VALID, AND CONTAIN ONLY POLYGONS OR MULTIPOLYGONS =====#####
        u.verify_polygons(user_json)
        
        #####===== DEFINE THE RESULT OBJECT =====#####
        result = {}

        #####===== CONVERT INPUT JSON TO OGR POLYGONS =====#####
        user_ogr = u.json_polys_to_ogr(user_json) 

        #####===== DISSOLVE USER POLYS AND CREATE 10KM AND 50KM BUFFERS =====#####
        user_dissolve  = u.dissolve_ogr_to_single_feature(user_ogr)
        if buff:
            buff_10km = u.buffer_ogr_polygons(user_dissolve.Clone(), 10000)
            buff_50km = u.buffer_ogr_polygons(user_dissolve.Clone(), 50000)


        #####===== GET INTERSECT GEOMETRY FROM ARC ENDPOINT =====#####
        if buff:
            intersect_polys_json = u.get_intersect_geom_from_endpoint(buff_50km, arcgis_server_layer, fields)
        else:
            intersect_polys_json = u.get_intersect_geom_from_endpoint(user_dissolve, arcgis_server_layer, fields)
        u.verify_polygons(intersect_polys_json)
        #####===== CONVERT INTERSECT GEOMETRY TO OGR POLYGONS =====#####
        intersect_ogr = u.json_polys_to_ogr(intersect_polys_json)

        #####===== DISSOLVE INTERSECTION POLYGONS TO A SINGLE FEATURE =====#####
        intersect_polygons = u.dissolve_ogr_to_single_feature(intersect_ogr)

        #####===== CALCULATE INTERSECTIONS OF USER POLYGONS AND BUFFERS WITH INTERSECT POLYGONS =====#####
        intersection_user = user_dissolve.Intersection(intersect_polygons)
        if buff:
            intersection_10km = buff_10km.Intersection(intersect_polygons)
            intersection_50km = buff_50km.Intersection(intersect_polygons)

        #####===== IF RETURN INTERSECT GEOMETRY IS TRUE, POPULATE RESULTS WITH INTERSECT GEOMETRY =====#####
        #####===== THIS IS DONE HERE BECAUSE THE u.calculate_dissolved_area FUNCTION MODIFIES THE GEOMETRY OBJECTS =====#####
        if return_intersect_geom:
            result['intersect_geom_user'] = intersection_user.ExportToJson()
            if buff:
                result['intersect_geom_10km'] = intersection_10km.ExportToJson()
                result['intersect_geom_50km'] = intersection_50km.ExportToJson()

        #####===== CALCULATE AREA OF USER POLYS AND BUFFERS =====#####    
        user_area_ha = u.calculate_dissolved_area(user_dissolve)
        if buff:
            buff_10km_ha = u.calculate_dissolved_area(buff_10km)
            buff_50km_ha = u.calculate_dissolved_area(buff_50km)

        #####===== CALCULATE AREA OF INTERSECTIONS =====#####
        user_area_intersection_ha = u.calculate_dissolved_area(intersection_user)
        if buff:
            buff_10km_intersection_ha = u.calculate_dissolved_area(intersection_10km)
            buff_50km_intersection_ha = u.calculate_dissolved_area(intersection_50km)

        #####===== CALCULATE % OVERLAP =====#####
        pct_overlap_user = user_area_intersection_ha / user_area_ha * 100
        if buff:
            pct_overlap_10km = buff_10km_intersection_ha / buff_10km_ha * 100
            pct_overlap_50km = buff_50km_intersection_ha / buff_50km_ha * 100

        #####===== POPULATE RESULTS WITH AREAS =====#####
        result['areaHa_user'] = user_area_ha
        result['pct_overlap_user'] = pct_overlap_user
        if buff:
            result['areaHa_10km'] = buff_10km_ha
            result['areaHa_50km'] = buff_50km_ha        
            result['pct_overlap_10km'] = pct_overlap_10km
            result['pct_overlap_50km'] = pct_overlap_50km

        return str(result)
    except:
        raise