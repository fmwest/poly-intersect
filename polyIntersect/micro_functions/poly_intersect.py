import json
import itertools
import rtree
import requests
from parse import search
from geomet import wkt
from datetime import datetime, timedelta

from functools import partial, lru_cache
import pyproj
import numpy as np
from time import time

from shapely.geometry import shape, mapping
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.collection import GeometryCollection
from shapely.ops import unary_union, transform


__all__ = ['json2ogr', 'ogr2json', 'dissolve', 'intersect', 'project_local',
           'project_global', 'buffer_to_dist', 'get_area', 'get_area_percent',
           'esri_server2ogr', 'get_species_count', 'esri_server2histo',
           'esri_count_groupby', 'cartodb2ogr', 'esri_count_30days',
           'esri_last_instance', 'erase']

HA_CONVERSION = 10000
t0 = 0


def json2ogr(in_json):
    '''
    Convert geojson object to GDAL geometry
    '''

    if isinstance(in_json, str):
        in_json = json.loads(in_json)

    if not isinstance(in_json, dict):
        raise ValueError('input json must be dictionary')

    if 'features' not in in_json.keys():
        raise ValueError('input json must contain features property')

    for f in in_json['features']:
        f['geometry'] = shape(f['geometry'])

    for i in range(len(in_json['features'])):
        in_json['features'][i]['properties']['id'] = i

    return in_json


def ogr2json(featureset):
    '''
    Convert GDAL geometry to geojson object
    '''

    new_features = []
    for f in featureset['features']:
        new_features.append(dict(geometry=mapping(f['geometry']),
                                 properties=f['properties'],
                                 type=f['type']))
        # f['geometry'] = mapping(f['geometry'])

    new_featureset = dict(type=featureset['type'],
                          features=new_features)
    if 'crs' in featureset.keys():
        new_featureset['crs'] = featureset['crs']
    return json.dumps(new_featureset)


def explode(coords):
    """Explode a GeoJSON geometry's coordinates object and yield coordinate
    tuples. As long as the input is conforming, the type of the geometry
    doesn't matter.
    https://gis.stackexchange.com/questions/90553/fiona-get-each-feature-
    extent-bounds"""
    for e in coords:
        if isinstance(e, (float, int)):
            yield coords
            break
        else:
            for f in explode(e):
                yield f


def bbox(f):
    x, y = zip(*list(explode(f['geometry']['coordinates'])))
    x1, x2, y1, y2 = min(x), max(x), min(y), max(y)
    return [[[x1, y1],
             [x2, y1],
             [x2, y2],
             [x1, y2],
             [x1, y1]]]


@lru_cache(5)
def esri_server2ogr(layer_endpoint, aoi, out_fields, where='1=1'):

    url = layer_endpoint.replace('?f=pjson', '') + '/query'

    params = {}
    params['where'] = where
    if 'objectid' not in out_fields:
        out_fields = 'objectid,' + out_fields if out_fields else 'objectid'
    params['outFields'] = out_fields
    params['returnGeometry'] = True
    params['returnM'] = False
    params['returnZ'] = False
    params['f'] = 'geojson'
    params['geometryType'] = 'esriGeometryPolygon'
    params['spatialRel'] = 'esriSpatialRelIntersects'
    # params['geometry'] = str({'rings': bbox(json.loads(aoi)['features'][0]),
    #                           'spatialReference': {'wkid': 4326}})

    # iterate through aoi features (Esri does not accept multipart polygons
    # as a spatial filter, and the aoi features may be too far apart to combine
    # into one bounding box)
    featureset = {}
    objectids = []
    for f in json.loads(aoi)['features']:
        params['geometry'] = str({'rings': bbox(f),
                                  'spatialReference': {'wkid': 4326}})
        req = requests.post(url, data=params)
        req.raise_for_status()
        response = json2ogr(req.text)

        # append response to full dataset, except features already included
        if featureset:
            for h in response['features']:
                if h['properties']['objectid'] not in objectids:
                    featureset['features'].append(h)
                    objectids.append(h['properties']['objectid'])
        else:
            featureset = response

    return featureset

    # req = requests.post(url, data=params)
    # req.raise_for_status()

    # return json2ogr(req.text)


def esri_server2histo(layer_endpoint, aoi):
    url = layer_endpoint.replace('?f=pjson', '') + '/computeHistograms'

    params = {}
    params['f'] = 'json'
    params['geometryType'] = 'esriGeometryPolygon'
    params['spatialRel'] = 'esriSpatialRelIntersects'
    params['returnGeometry'] = True
    params['where'] = '1=1'

    featureset = json.loads(aoi) if isinstance(aoi, str) else aoi
    if featureset['features']:
        f = featureset['features'][0]
        params['geometry'] = str({'rings': f['geometry']['coordinates'],
                                  'spatialReference': {'wkid': 4326}})
        req = requests.post(url, data=params)
        req.raise_for_status()
        histograms = req.json()['histograms'][0]['counts']

    return histograms


def esri_count_groupby(layer_endpoint, aoi, count_fields):
    url = layer_endpoint.replace('?f=pjson', '') + '/query'

    params = {}
    params['f'] = 'json'
    params['geometryType'] = 'esriGeometryPolygon'
    params['where'] = '1=1'
    params['spatialRel'] = 'esriSpatialRelIntersects'
    params['returnGeometry'] = False
    params['groupByFieldsForStatistics'] = count_fields
    count_fields = count_fields.split(',')
    params['outStatistics'] = json.dumps([{
        'statisticType': 'count',
        'onStatisticField': count_fields[0],
        'outStatisticFieldName': 'count'
    }])

    featureset = json.loads(aoi) if isinstance(aoi, str) else aoi
    if featureset['features']:
        f = featureset['features'][0]
        params['geometry'] = str({'rings': f['geometry']['coordinates'],
                                  'spatialReference': {'wkid': 4326}})
        req = requests.post(url, data=params)
        req.raise_for_status()
        try:
            counts = {'-'.join([str(item['attributes'][field]) for field in
                                count_fields]): item['attributes']['count']
                      for item in req.json()['features']}

            return counts
        except Exception as e:
            raise ValueError((str(e), url, params, req.text))
    return None


def esri_count_30days(layer_endpoint, aoi, date_field):
    url = layer_endpoint.replace('?f=pjson', '') + '/query'

    date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')

    params = {}
    params['f'] = 'json'
    params['geometryType'] = 'esriGeometryPolygon'
    params['where'] = "{} >= date '{}'".format(date_field, date)
    params['spatialRel'] = 'esriSpatialRelIntersects'
    params['returnGeometry'] = False
    params['returnCountOnly'] = True

    featureset = json.loads(aoi) if isinstance(aoi, str) else aoi
    if featureset['features']:
        f = featureset['features'][0]
        params['geometry'] = str({'rings': f['geometry']['coordinates'],
                                  'spatialReference': {'wkid': 4326}})
        req = requests.post(url, data=params)
        req.raise_for_status()
        counts = req.json()['count']

        return counts
    return None


def esri_last_instance(layer_endpoint, aoi, field):
    url = layer_endpoint.replace('?f=pjson', '') + '/query'

    params = {}
    params['f'] = 'json'
    params['geometryType'] = 'esriGeometryPolygon'
    params['where'] = '1=1'
    params['spatialRel'] = 'esriSpatialRelIntersects'
    params['returnGeometry'] = False
    params['outFields'] = field
    params['orderByFields'] = field
    params['returnDistinctValues'] = True

    featureset = json.loads(aoi) if isinstance(aoi, str) else aoi
    if featureset['features']:
        f = featureset['features'][0]
        params['geometry'] = str({'rings': f['geometry']['coordinates'],
                                  'spatialReference': {'wkid': 4326}})
        req = requests.post(url, data=params)
        req.raise_for_status()
        try:
            instances = [item['attributes'][field] for item in
                         req.json()['features']]
            last_instance = instances[-1] if instances else None

            return last_instance
        except Exception as e:
            raise ValueError((str(e), url, params, req.text))
    return None


@lru_cache(5)
def cartodb2ogr(service_endpoint, aoi, out_fields, where=''):
    endpoint_template = 'https://{}.carto.com/tables/{}/'
    username, table = search(endpoint_template, service_endpoint + '/')
    url = 'https://{username}.carto.com/api/v2/sql'.format(username=username)

    featureset = json.loads(aoi) if isinstance(aoi, str) else aoi

    params = {}
    fields = ['ST_AsGeoJSON(the_geom) as geometry']
    out_fields = out_fields.split(',')
    for field in out_fields:
        if field:
            fields.append('{field} as {field}'.format(field=field))

    where_clause = "ST_Intersects(ST_Buffer({},0),the_geom)"
    where_clause = where_clause.format("ST_GeomFromText('{}',4326)".format(
        wkt.dumps({'type': 'MultiPolygon',
                   'coordinates': [bbox(f) for f in featureset['features']]}
                  )))
    if where and not where == '1=1':
        where_clause += 'AND {}'.format(where)

    q = 'SELECT {fields} FROM {table} WHERE {where}'
    params = {'q': q.format(fields=','.join(fields), table=table,
              where=where_clause)}

    try:
        req = requests.get(url, params=params)
        req.raise_for_status()
    except Exception as e:
        raise ValueError((e, [bbox(f) for f in featureset['features']]))

    response = json.loads(req.text)['rows']
    features = {
        'type': 'FeatureCollection',
        'features': [{
            'type': 'Feature',
            'geometry': json.loads(feat['geometry']),
            'properties': {field: feat[field] for field in out_fields if field}
        } for feat in response]
    }
    global t0
    t0 = time()
    featureset = json2ogr(features)
    # raise ValueError(time()-t0)
    return featureset


def dissolve(featureset, field=None):
    '''
    Dissolve a set of geometries on a field, or dissolve fully to a single
    feature if no field is provided
    '''

    if field:
        def sort_func(k):
            return k['properties'][field]
    else:
        sort_func = None

    new_features = []

    if len(featureset['features']) > 0:
        if sort_func:
            features = sorted(featureset['features'], key=sort_func)
            for key, group in itertools.groupby(features, key=sort_func):
                properties, geoms = zip(*[(f['properties'],
                                          f['geometry']) for f in group])
                new_features.append(dict(type='Feature',
                                         geometry=unary_union(geoms),
                                         properties=properties[0]))

        else:
            geoms = [f['geometry'] for f in featureset['features']]
            properties = {}  # TODO: decide which attributes should go in here
            new_features.append(dict(type='Feature',
                                     geometry=unary_union(geoms),
                                     properties=properties))

    new_featureset = dict(type=featureset['type'],
                          features=new_features)
    if 'crs' in featureset.keys():
        new_featureset['crs'] = featureset['crs']
    return new_featureset


def index_featureset(featureset):
    '''
    '''
    index = rtree.index.Index()
    for i, f in enumerate(featureset['features']):
        geom = f['geometry']
        if isinstance(geom, GeometryCollection):
            minx = np.min([item.bounds[0] for item in geom])
            miny = np.min([item.bounds[1] for item in geom])
            maxx = np.max([item.bounds[2] for item in geom])
            maxy = np.max([item.bounds[3] for item in geom])
            index.insert(i, (minx, miny, maxx, maxy))
        else:
            index.insert(i, geom.bounds)
    return index


def intersect(featureset1, featureset2):
    '''
    '''

    index = index_featureset(featureset2)

    new_features = []

    for f in featureset1['features']:
        feat1 = f
        geom1 = f['geometry']
        for fid in list(index.intersection(geom1.bounds)):
            feat2 = featureset2['features'][fid]
            geom2 = feat2['geometry']
            if not geom1.is_valid:
                # raise ValueError('Geometry from featureset1 is not valid')
                geom1 = geom1.buffer(0)
            if not geom2.is_valid:
                # raise ValueError('Geometry from featureset2 is not valid')
                geom2 = geom2.buffer(0)

            if geom1.intersects(geom2):  # TODO: optimize to on intersect call?
                new_geom = geom1.intersection(geom2)
                new_feat = dict(properties={**feat2['properties'],
                                            **feat1['properties']},
                                geometry=new_geom,
                                type='Feature')
                new_features.append(new_feat)

    new_featureset = dict(type=featureset2['type'],
                          features=new_features)
    if 'crs' in featureset2.keys():
        new_featureset['crs'] = featureset2['crs']

    return new_featureset


def erase(featureset, erase_featureset):
    '''
    '''

    index = index_featureset(erase_featureset)

    new_features = []

    for f in featureset['features']:
        feat = f
        geom = f['geometry']
        for fid in list(index.intersection(geom.bounds)):
            erase_feat = erase_featureset['features'][fid]
            erase_geom = erase_feat['geometry']
            if geom.intersects(erase_geom):
                new_geom = geom.difference(erase_geom)
                new_feat = dict(properties={**feat['properties']},
                                geometry=new_geom,
                                type='Feature')
                new_features.append(new_feat)

    new_featureset = dict(type=featureset['type'],
                          features=new_features)
    if 'crs' in featureset.keys():
        new_featureset['crs'] = featureset['crs']

    return new_featureset


def project_features(featureset, project):
    new_features = []
    for f in featureset['features']:
        if isinstance(f['geometry'], Polygon):
            geom = Polygon(f['geometry'])
        elif isinstance(f['geometry'], MultiPolygon):
            geom = MultiPolygon(f['geometry'])
        elif isinstance(f['geometry'], GeometryCollection):
            geom = GeometryCollection(f['geometry'])

        projected_geom = transform(project, geom)
        new_feat = dict(properties=f['properties'],
                        geometry=projected_geom,
                        type='Feature')
        new_features.append(new_feat)

    return dict(type=featureset['type'],
                features=new_features)


def project_local(featureset):
    if ('crs' in featureset.keys() and
            featureset['crs']['properties']['name'] ==
            'urn:ogc:def:uom:EPSG::9102'):
        return featureset

    name = 'urn:ogc:def:uom:EPSG::9102'

    # get cumulative centroid of all features
    x, y = 0, 0
    for f in featureset['features']:
        if isinstance(f['geometry'], GeometryCollection):
            x += np.mean([geom_item.centroid.x for geom_item in f['geometry']])
            y += np.mean([geom_item.centroid.y for geom_item in f['geometry']])
        else:
            x += f['geometry'].centroid.x
            y += f['geometry'].centroid.y
    x = x / len(featureset['features']) if featureset['features'] else 0
    y = y / len(featureset['features']) if featureset['features'] else 0

    # define local projection
    proj4 = '+proj=aeqd +lat_0={} +lon_0={} +x_0=0 +y_0=0 +datum=WGS84 \
             +units=m +no_defs +R=6371000 '.format(y, x)

    # define projection transformation
    project = partial(pyproj.transform,
                      pyproj.Proj(init='epsg:4326'),
                      pyproj.Proj(proj4))

    # peoject features and add projection info
    new_featureset = project_features(featureset, project)
    new_featureset['crs'] = dict(type="name",
                                 properties=dict(name=name,
                                                 centroid=[x, y]))
    return new_featureset


def project_global(featureset):
    if ('crs' in featureset.keys() and
            featureset['crs']['properties']['name'] == 'EPSG:4326'):
        return featureset
    elif 'crs' not in featureset.keys():
        raise ValueError('Local projection must have crs info to reproject')

    name = 'EPSG:4326'
    [x, y] = featureset['crs']['properties']['centroid']

    proj4 = '+proj=aeqd +lat_0={} +lon_0={} +x_0=0 +y_0=0 +datum=WGS84 \
             +units=m +no_defs +R=6371000 '.format(y, x)

    project = partial(pyproj.transform,
                      pyproj.Proj(proj4),
                      pyproj.Proj(init='epsg:4326'))

    new_featureset = project_features(featureset, project)
    new_featureset['crs'] = dict(type="name",
                                 properties=dict(name=name))
    return new_featureset


def buffer_to_dist(featureset, distance):
    '''
    Buffer a geometry with a given distance (assumed to be kilometers)
    '''
    if not (featureset['crs']['properties']['name'] ==
            'urn:ogc:def:uom:EPSG::9102'):
        raise ValueError('geometries must be projected with the World ' +
                         'Azimuthal Equidistant coordinate system')

    new_features = []

    for f in featureset['features']:
        geom = f['geometry']
        buffered_geom = geom.buffer(int(distance) * 1000.0)
        new_feat = dict(properties=f['properties'],
                        geometry=buffered_geom,
                        type='Feature')
        new_features.append(new_feat)

    new_featureset = dict(type=featureset['type'],
                          features=new_features)
    if 'crs' in featureset.keys():
        new_featureset['crs'] = featureset['crs']
    return new_featureset


# ------------------------- Calculation Functions --------------------------

def validate_featureset(featureset, fields=[None]):
    '''
    '''
    valid_fields = [f for f in fields if f]
    for field in valid_fields:
        for f in featureset['features']:
            if field not in f['properties'].keys():
                raise ValueError('Featureset with category field must ' +
                                 'have category field as a property of ' +
                                 'every feature')
    if len(valid_fields) == 0:
        if len(featureset['features']) > 1:
            raise ValueError('Featureset with multiple features must ' +
                             'be dissolved or have a category field in ' +
                             'order to calculate statistics')


def get_area(featureset, field=None):
    validate_featureset(featureset, [field])

    if field:
        area = {}
        for f in featureset['features']:
            area[f['properties'][field]] = f['geometry'].area / HA_CONVERSION
    else:
        if featureset['features']:
            area = featureset['features'][0]['geometry'].area / HA_CONVERSION
        else:
            area = 0
    return area


def get_area_percent(featureset, aoi_area, aoi_field=None, int_field=None):
    validate_featureset(featureset, [int_field, aoi_field])

    if aoi_field and int_field:
        area_pct = {}
        for aoi, area in aoi_area.items():
            area_pct[aoi] = {}
            for f in [f for f in featureset['features'] if
                      f['properties'][aoi_field] == aoi]:
                int_category = f['properties'][int_field]
                area_pct[aoi][int_category] = (f['geometry'].area /
                                               HA_CONVERSION / area * 100)
    elif aoi_field:
        area_pct = {}
        for f in featureset['features']:
            aoi = f['properties'][aoi_field]
            area = aoi_area[aoi]
            area_pct[aoi] = (f['geometry'].area / HA_CONVERSION / area *
                             100)
        for aoi in aoi_area.keys():
            if aoi not in area_pct.keys():
                area_pct[aoi] = 0
    elif int_field:
        area_pct = {}
        for f in featureset['features']:
            int_category = f['properties'][int_field]
            area_pct[int_category] = (f['geometry'].area / HA_CONVERSION /
                                      aoi_area * 100)
    else:
        if featureset['features']:
            area_pct = (featureset['features'][0]['geometry'].area /
                        HA_CONVERSION / aoi_area * 100)
        else:
            area_pct = 0

    return area_pct


def get_histo_loss_area(histograms, forest_density=30):
    '''
    Returns the sum of tree cover loss for years 2001 through 2014
    '''
    density_map = {0: 10, 10: 25, 15: 40, 20: 55,
                   25: 70, 30: 85, 50: 100, 75: 115}
    if forest_density not in density_map.keys():
        raise ValueError('Forest density must be one of the following:\n' +
                         '  10, 15, 20, 25, 30, 50, 75')
    year_indices = [range(density_map[forest_density] + i + 1, 130, 15)
                    for i in range(14)]
    histo_area_loss = [sum([histograms[i] for i in indices])
                       for indices in year_indices]

    return histo_area_loss


def get_histo_pre2001_area(histograms):
    '''
    Returns the sum of histo on tree cover loss, aggregated on years prior to
    2001
    '''
    year_indices = range(10, 130, 15)
    histo_area_loss = sum([histograms[i] for i in year_indices])

    return histo_area_loss


def get_histo_total_area(histograms):
    '''
    Returns total area of histo within the aoi
    '''
    year_indices = [range(i, 130, 15) for i in range(14)]
    histo_area_total = [sum([histograms[i] for i in indices])
                        for indices in year_indices]

    return histo_area_total


def get_date_from_timestamp(timestamp):
    '''
    '''
    if timestamp > 100000000000:
        timestamp = timestamp/1000
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')


# def get_intersect_area(intersection, intersection_proj, unit='hectare'):
#     '''
#     Calculate the area overlap of an intersection with the user AOI. Can
#     calculate areas by category using a groupby field.

#     If calculating areas by category, there must be one feature per unique
#     value in the category field. If not, there must be one feature total in
#     the intersected featureset
#     '''

#     unit_conversions = {'meter': 1, 'kilometer': 1000, 'hectare': 10000}
#     if unit not in unit_conversions.keys():
#         raise ValueError('Invalid unit')

#     new_features = []
#     for f, p in zip(intersection['features'], intersection_proj['features']):
#         new_feat = dict(type='Feature',
#                         geometry=f['geometry'],
#                         properties=f['properties'])
#         new_feat['properties']['area'] = (p['geometry'].area /
#                                           unit_conversions[unit])
#         new_features.append(new_feat)

#     new_featureset = dict(type=intersection['type'],
#                           features=new_features)
#     if 'crs' in intersection.keys():
#         new_featureset['crs'] = intersection['crs']
#     return new_featureset

    # if category:
    #     area_overlap = {f['properties'][category]: f['properties']['area']
    #                     for f in intersection['features']}
    # else:
    #     f = intersection['features'][0]
    #     area_overlap = f['properties']['area']

    # return area_overlap


# def get_intersect_area_percent(intersection, intersection_proj, aoi_proj):
    # '''
    # Calculate the area overlap of an intersection with the user AOI. Can
    # calculate areas by category using a groupby field.

    # If calculating areas by category, there must be one feature per unique
    # value in the category field. If not, there must be one feature total in
    # the intersected featureset
    # '''

    # new_features = []
    # for f, p in zip(intersection['features'], intersection_proj['features']):
    #     new_feat = dict(type='Feature',
    #                     geometry=f['geometry'],
    #                     properties=f['properties'])
    #     i = f['properties']['id'] if 'id' in f['properties'].keys() else 0
    #     aoi_area = aoi_proj['features'][i]['geometry'].area
    #     new_feat['properties']['area-percent'] = (p['geometry'].area * 100. /
    #                                               aoi_area)
    #     new_features.append(new_feat)

    # new_featureset = dict(type=intersection['type'],
    #                       features=new_features)
    # if 'crs' in intersection.keys():
    #     new_featureset['crs'] = intersection['crs']
    # return new_featureset

    # if category:
    #     pct_overlap = {f['properties'][category]:
    #                    f['properties']['area_percent']
    #                    for f in intersection['features']}
    # else:
    #     f = intersection['features'][0]
    #     pct_overlap = f['properties']['area_percent']

    # return pct_overlap


def get_species_count(intersection, field):
    '''
    Count number of unique species found within the features of an
    intersection with the user AOI
    '''
    species_list = []
    for f in intersection['features']:
        species_string = f['properties'][field][1:-1].replace('"', '')
        species_list += species_string.split(',')
    species_set = set(species_list)
    return len(species_set)


# def get_z_scores(intersection, category, field):
    '''
    Get z score of numerical attribute from features of an intersection with
    the user AOI
    '''
    # if not validate_featureset(intersection, category):
    #     return 0

    # scores = stats.zscore([f['properties'][field]
    #                        for f in intersection['features']])
    # for i, f in enumerate(intersection['features']):
    #     f['properties']['z-score'] = scores[i]
    # return {f['properties'][category]: f['properties']['z-score']
    #         for f in intersection['features']}


def is_valid(analysis_method):
    '''
    Validate that method exists
    '''
    return analysis_method in __all__
