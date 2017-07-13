from osgeo import ogr, osr
import geojson as gj
from geomet import wkt as WKT
import urllib3
import polyIntersect.micro_functions.urls as urls

def verify_polygons(in_json):
    if not in_json:
        raise AssertionError('JSON input is empty.')

    try:
        loaded_json = gj.loads(in_json)
    except Exception as e:
        raise AssertionError('Invalid JSON input.\n  ERROR MESSAGE: {}.'.format(e))

    validation = gj.is_valid(loaded_json)
    if validation['valid'].lower() != 'yes':
        raise AssertionError('ERROR MESSAGE: {}'.format(validation['message']))

    for feature in loaded_json['features']:
        geom_type = feature['geometry']['type']
        if geom_type.lower() != 'polygon' and geom_type.lower() != 'multipolygon':
            raise AssertionError('Input JSON contains a feature not of type POLYGON or MULTIPOLYGON.')
    
    return

def json_polys_to_ogr(in_json):
    polys = ogr.Geometry(ogr.wkbMultiPolygon)
    for feature in gj.loads(in_json)['features']:
        poly = ogr.CreateGeometryFromJson(gj.dumps(feature['geometry']))
        polys.AddGeometry(poly)
    
    return polys

def dissolve_ogr_to_single_feature(ogr_geom):
    dissolved = ogr_geom.UnionCascaded()
    
    return dissolved

def buffer_ogr_polygons(ogr_geom, distance, dissolve=True, original_epsg=4326): # EPSG 4326 = WGS84
    buffers = ogr.Geometry(ogr.wkbMultiPolygon)
    
    if ogr_geom.GetGeometryType() == 6: # Geometry type 6 is MultiPolygon    
        parts = ogr_geom.GetGeometryCount()
        for i in range(0, parts):
            geom = ogr_geom.GetGeometryRef(i)
            buffers.AddGeometry(build_buffer(geom, distance, original_epsg))

    else: # Geometry type must be Polygon (type 3) here
        buff = build_buffer(ogr_geom, distance, original_epsg)
        buffers.AddGeometry(buff)

    if dissolve:
        buffers_dissolved = dissolve_ogr_to_single_feature(buffers)

    return buffers_dissolved

def project(ogr_geom, centroid, direction, original_epsg):
    wkt_proj = 'PROJCS["World_Azimuthal_Equidistant_custom_center", \
                    GEOGCS["GCS_WGS_1984", \
                        DATUM["WGS_1984", \
                            SPHEROID["WGS_1984",6378137,298.257223563]], \
                        PRIMEM["Greenwich",0], \
                        UNIT["Degree",0.017453292519943295]], \
                    PROJECTION["Azimuthal_Equidistant"], \
                    PARAMETER["False_Easting",0], \
                    PARAMETER["False_Northing",0], \
                    PARAMETER["Central_Meridian",{}], \
                    PARAMETER["Latitude_Of_Origin",{}], \
                    UNIT["Meter",1], \
                    AUTHORITY["EPSG","54032"]]' \
                    .format(centroid.GetX(), centroid.GetY())

    original_sr = osr.SpatialReference()
    original_sr.ImportFromEPSG(original_epsg)
    
    target_sr = osr.SpatialReference()
    target_sr.ImportFromWkt(wkt_proj)

    if direction.lower() == 'to-custom':
        transform = osr.CoordinateTransformation(original_sr, target_sr)
    elif direction.lower() == 'to-original':
        transform = osr.CoordinateTransformation(target_sr, original_sr) 
    else:
        raise Exception('utils.project \'direction\' parameter invalid. Must be either \'to-original\' or \'to-custom\'')

    ogr_geom.Transform(transform)

    return ogr_geom

def build_buffer(ogr_geom, distance, original_epsg, export_as='OGR', return_to_original_sr=True):
    centroid = ogr_geom.Centroid()
    
    poly_prj = project(ogr_geom, centroid, 'to-custom', original_epsg)

    buff = poly_prj.Buffer(distance)

    if return_to_original_sr:
        buff_prj = project(buff, centroid, 'to-original', original_epsg)

        if export_as == 'JSON':
            return buff_prj.ExportToJson()
        elif export_as == 'WKT':
            return buff_prj.ExportToWkt()
        elif export_as == 'OGR':
            return buff_prj
    else:
        if export_as == 'JSON':
            return buff.ExportToJson()
        elif export_as == 'WKT':
            return buff.ExportToWkt()
        elif export_as == 'OGR':
            return buf

def calculate_dissolved_area(ogr_geom, original_epsg=4326):
    area_m2 = 0

    if ogr_geom.GetGeometryType() == 6: # Geometry type 6 is MultiPolygon
        parts = ogr_geom.GetGeometryCount()
        for i in range(0, parts):
            geom = ogr_geom.GetGeometryRef(i) # Reads geom as LinearRing
            area_part = project(geom, geom.Centroid(), 'to-custom', original_epsg).GetArea()
            area_m2+=area_part

    else: # Geometry type must be Polygon (type 3) here
        area_m2 = project(ogr_geom, ogr_geom.Centroid(), 'to-custom', original_epsg).GetArea()
    
    area_ha = area_m2 * 0.0001
    
    return area_ha


# get_min_max_xy assumes ogr_geom is passed in with decimal degrees as the linear unit,
# so that decimal degrees are returned as min/max x/y
def get_min_max_xy(ogr_geom):
    envelope = ogr_geom.GetEnvelope()
    return envelope

def get_intersect_geom_from_endpoint(ogr_geom, layer, fields, original_epsg=4326):
    #####=====  GET ENVELOPE OF MIN/MAX X/Y OF USER  =====##### 
    #####===== POLYGONS TO EXTRACT GEOM FROM SERVICE =====#####
    minX, maxX, minY, maxY = get_min_max_xy(ogr_geom)
    
    #####===== TRY TO GET SPATIAL REFERENCE OF USER POLYGONS  =====##### 
    sr = ogr_geom.GetSpatialReference()
    if not sr:
        sr = original_epsg

    geom = {'xmin' : minX,\
            'ymin' : minY, \
            'xmax' : maxX, \
            'ymax' : maxY, \
            'spatialReference' : {'wkid' : sr}}

    query = {'where'          : '1=1',
             'geometry'       : geom,
             'geometryType'   : 'esriGeometryEnvelope', 
             'spatialRel'     : 'esriSpatialRelIntersects',
             'outFields'      : '*',
             'returnGeometry' : 'true',
             'outSR'          : '',
             'f'              : 'geojson'}

    http = urllib3.PoolManager()
    
    if layer=='gadmAdm2':
        intersect_polys = http.request('GET', urls.gadmAdm2, fields=query)

    elif layer=='gadmAdm1':
        intersect_polys = http.request('GET', urls.gadmAdm1, fields=query)

    elif layer=='gadmAdm0':
        intersect_polys = http.request('GET', urls.gadmAdm0, fields=query)

    else:
        raise AssertionError('Specified intersect_layer ({}) does not exist.'.format(layer))

    return gj.dumps(gj.loads(intersect_polys.data.decode('utf-8')))
