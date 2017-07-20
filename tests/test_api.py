import json

from polyIntersect import app

app = app.test_client()

def test_hello():
    url = '/api/v1/polyIntersect/hello?'
    result = app.get(url)
    assert result.status_code == 200
