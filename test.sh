#!/bin/bash

#cp ./microservice/register.json ./regtest.json
#register_file='./regtest.json'
register_file='./microservice/register.json'
register_template=$(<register_template_test.txt)

#cp ./polyIntersect/routes/api/v1/polyIntersect_router.py ./routertest.py
#router_file='./routertest.py'
router_file='./polyIntersect/routes/api/v1/polyIntersect_router.py'
router_template=$(<endpoint_template_test.txt)

# access analysis -> datasets dictionary
. endpoint_datasets.config
declare -A ANALYSES
echo $ANALYSIS

# loop through datasets, adding a view and registration entry for each
for dataset in ${!ANALYSES[$ANALYSIS]}; do
	echo $dataset

	# update register json
	register_addition=$(echo $register_template | sed "s/ENDPOINT_NAME/${dataset}/g")
	sed -i "s@}]@${register_addition}@" $register_file

	# update router file
	dataset_clean=$(echo $dataset | sed "s/-//g")
	router_addition=$(echo $router_template | sed "s/ENDPOINT_NAME/${dataset}/g" | sed "s/FUNCTION_NAME/${dataset_clean}/g")
	sed -i "$ a ${router_addition}" $router_file
done
