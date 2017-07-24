from setuptools import find_packages, setup

with open('requirements.txt') as f:
    install_requires = f.read().strip().split('\n')

setup(name='poly-intersect',
      version='0.1.1',
      description='geospatial web service',
      url='http://github.com/blueraster/poly-intersect',
      install_requires=install_requires,
      packages=find_packages(),
      zip_safe=False,
      include_package_data=True)
