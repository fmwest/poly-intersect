import requests

from sample_data import BRAZIL_USER_POLY


def test_hello():
    url = 'http://localhost:9000/v1/polyIntersect/hello'
    result = requests.get(url)
    print(result)


def test_fiona():
    url = 'http://localhost:9000/v1/polyIntersect/fiona'
    result = requests.get(url)
    print(result)


def test_brazil_biomes_local():
    url = 'http://localhost:5700/api/v1/polyIntersect/generic'
    run_request(url)


def test_brazil_biomes_control_tower():
    url = 'http://localhost:9000/v1/polyIntersect/generic'
    run_request(url)


def test_brazil_biomes_control_tower_remote():
    url = 'http://staging-api.globalforestwatch.org/v1/polyIntersect/generic'
    run_request(url)


def run_request(url):
    payload = {}
    payload['analysis'] = 'area-percentarea-category'
    payload['dataset'] = 'brazil-biomes'
    payload['user_json'] = BRAZIL_USER_POLY

    print(url)

    result = requests.post(url, json=payload,
                           allow_redirects=True)
    print(result)
    #result_obj = result.json()
    print(result.content)


if __name__ == '__main__':
    # test_hello()
    test_fiona()
    test_brazil_biomes_local()
    test_brazil_biomes_control_tower()
    # test_brazil_biomes_control_tower_remote()
