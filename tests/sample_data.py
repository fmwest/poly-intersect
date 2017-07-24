from os import path

fixtures = path.abspath(path.join(path.dirname(__file__), 'fixtures'))

with open(path.join(fixtures, 'maine.geojson')) as f:
    MAINE_GEOJSON = "".join(f.read().split())

with open(path.join(fixtures, 'self-intersecting.geojson')) as f:
    SELF_INTERSECTING_GEOJSON = "".join(f.read().split())

with open(path.join(fixtures, 'dissolve_me.geojson')) as f:
    DISSOLVE_GEOJSON = "".join(f.read().split())
