"""API ROUTER"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from flask import jsonify, request
from landrights.routes.api.v1 import endpoints, error
from landrights.validators import validate_greeting
from landrights.serializers import serialize_greeting

@endpoints.route('/hello', strict_slashes=False, methods=['GET', 'POST'])
@validate_greeting
def hello():
    data = 'hello adnan'
    return data

@endpoints.route('/landRights', strict_slashes=False, methods=['POST'])
@validate_greeting
def landRights():
    try: 
        from landrights.micro_functions.land_rights import land_rights
        user_poly = str(request.form['user_poly'])
        land_rights_polys = str(request.form['land_rights'])
        data = land_rights(user_poly, land_rights_polys)
    except Exception as e:
        logging.info('FAILED: {}'.format(e))
        return 'FAILED: {}'.format(e)
    
    if False:
        return error(status=400, detail='Not valid')
    return data