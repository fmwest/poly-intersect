from flask import Blueprint, jsonify


def error(status=400, detail='Bad Request'):
    return jsonify(errors=[{
        'status': status,
        'detail': detail,
        'david': 'david'
    }]), status


endpoints = Blueprint('endpoints', __name__)
import polyIntersect.routes.api.v1.polyIntersect_router  # noqa
