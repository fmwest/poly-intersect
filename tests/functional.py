import json
import requests

from tests.sample_data import BRAZIL_USER_POLY


def test_brazil_biomes():
    host = 'https://staging-api.globalforestwatch.org'
    url = '{}/v1/polyIntersect/brazil-biomes?'.format(host)
    url = 'http://localhost:5700/api/v1/polyIntersect/brazil-biomes'

    feats1 = json.loads(BRAZIL_USER_POLY)

    payload = {}
    payload['user_json'] = json.dumps(feats1)
    payload['category'] = 'name'

    result = requests.post(url, data=payload)
    result_obj = result.json()

    assert 'intersect-area' in list(result_obj.keys())
    assert 'intersect-area-percent' in list(result_obj.keys())

if __name__ == '__main__':
    test_brazil_biomes()
