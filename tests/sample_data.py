from os import path

fixtures = path.abspath(path.join(path.dirname(__file__), 'fixtures'))

with open(path.join(fixtures, 'maine.geojson')) as f:
    MAINE_GEOJSON = "".join(f.read().split())

with open(path.join(fixtures, 'self-intersecting.geojson')) as f:
    SELF_INTERSECTING_GEOJSON = "".join(f.read().split())

with open(path.join(fixtures, 'dissolve_me.geojson')) as f:
    DISSOLVE_GEOJSON = "".join(f.read().split())

with open(path.join(fixtures, 'intersect_base.geojson')) as f:
    INTERSECT_BASE_GEOJSON = "".join(f.read().split())

with open(path.join(fixtures, 'intersect_fully_within.geojson')) as f:
    INTERSECT_FULLY_WITHIN_GEOJSON = "".join(f.read().split())

with open(path.join(fixtures, 'intersect_partially_within.geojson')) as f:
    INTERSECT_PARTIALLY_WITHIN_GEOJSON = "".join(f.read().split())

with open(path.join(fixtures, 'intersect_multiple_features.geojson')) as f:
	INTERSECT_MULTIPLE_FEATURES = "".join(f.read().split())