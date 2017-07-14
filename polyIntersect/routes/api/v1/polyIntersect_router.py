"""API ROUTER"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from flask import jsonify, request
from polyIntersect.routes.api.v1 import endpoints, error
from polyIntersect.validators import validate_greeting
from polyIntersect.serializers import serialize_greeting
from polyIntersect.micro_functions.poly_intersect import intersect_area_geom, intersect_area_geom_from_endpoint

@endpoints.route('/hello', strict_slashes=False, methods=['GET', 'POST'])
@validate_greeting
def hello():
    data = 'hello adnan'
    return data



@endpoints.route('/', strict_slashes=False, methods=['POST'])
@validate_greeting
def polyIntersect_area():
    x = []
    try:
        # Get parameters from POST
        user_poly = str(request.form['user_poly'])
        intersect_polys = str(request.form['intersect_polys'])
        
        # Verify that return geom_geom is True or False, if not defined, make it False
        try: return_geom = str(request.form['return_geom'])
        except: return_geom = 'False'
        assert return_geom=='False' or return_geom=='True', 'return_geom is {}, must be True or False (type string)'.format(return_geom)
        if return_geom=='False': return_intersect_geom = False
        elif return_geom=='True':  return_intersect_geom = True

        data = intersect_area_geom(user_poly, intersect_polys, return_intersect_geom, fields='*')
    except Exception as e:
        logging.info('FAILED: {}'.format(e))
        return 'FAILED: {}\n  ERROR: {}'.format(x, e)
    
    if False:
        return error(status=400, detail='Not valid')
    return data



@endpoints.route('/endpoint', strict_slashes=False, methods=['POST'])
@validate_greeting
def polyIntersect_area_from_endpoint():
    x = []
    try:
        # Get parameters from POST 
        user_poly = str(request.form['user_poly'])
        arcgis_server_layer = str(request.form['arcgis_server_layer'])

        # Verify that return geom_geom is True or False, if not defined, make it False
        try: return_geom = str(request.form['return_geom'])
        except: return_geom = 'False'
        assert return_geom=='False' or return_geom=='True', 'return_geom is {}, must be True or False (type string)'.format(return_geom)
        if return_geom=='False': return_intersect_geom = False
        elif return_geom=='True':  return_intersect_geom = True


        data = intersect_area_geom_from_endpoint(user_poly, arcgis_server_layer, return_intersect_geom, fields='*')
    except Exception as e:
        logging.info('FAILED: {}'.format(e))
        return 'FAILED: {}\n  ERROR: {}'.format(x, e)
    
    if False:
        return error(status=400, detail='Not valid')
    return data