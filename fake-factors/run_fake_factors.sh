#!/bin/bash

ERA=$1
CONFIGKEY=$2

./fake-factors/produce_shapes.sh $ERA $CONFIGKEY
./fake-factors/calculate_fake_factors.sh $ERA $CONFIGKEY
