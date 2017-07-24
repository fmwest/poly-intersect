"""API ROUTER"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from flask import jsonify, request
from polyIntersect.routes.api.v1 import endpoints, error
from polyIntersect.validators import validate_greeting

from polyIntersect.micro_functions.poly_intersect import intersect_area_geom


@endpoints.route('/hello', strict_slashes=False, methods=['GET', 'POST'])
@validate_greeting
def hello():
    data = 'hello adnan'
    response = jsonify(data)
    response.status_code = 200
    return response


@endpoints.route('/', strict_slashes=False, methods=['POST'])
@validate_greeting
def polyIntersect_area():
    x = []
    try:
        user_poly = str(request.form['user_poly'])
        intersect_polys = str(request.form['intersect_polys'])
        data = intersect_area_geom(user_poly, intersect_polys)
    except Exception as e:
        logging.info('FAILED: {}'.format(e))
        return 'FAILED: {}\n  ERROR: {}'.format(x, e)

    if False:
        return error(status=400, detail='Not valid')

    response = jsonify(data)
    response.status_code = 200
    return response


@endpoints.route('/geom', strict_slashes=False, methods=['POST'])
@validate_greeting
def polyIntersect_area_geom():
    try:
        user_poly = str(request.form['user_poly'])
        intersect_polys = str(request.form['intersect_polys'])
        data = intersect_area_geom(user_poly, intersect_polys,
                                   return_intersect_geom=True)
    except Exception as e:
        logging.info('FAILED: {}'.format(e))
        return 'FAILED: {}'.format(e)

    if False:
        return error(status=400, detail='Not valid')

    response = jsonify(data)
    response.status_code = 200
    return response
