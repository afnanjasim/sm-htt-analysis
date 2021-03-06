#!/bin/bash

source utils/setup_cmssw.sh
source utils/setup_python.sh

ERA=$1
CHANNELS=$2
VARIABLE=$3

python datacards/produce_datacard.py --stxs-signals 0 --stxs-categories 0 --era $ERA --channels $CHANNELS  --use-data-for-observation --gof $VARIABLE --shapes ${ERA}_${CHANNELS}_shapes.root
