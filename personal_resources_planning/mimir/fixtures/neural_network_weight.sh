#!/bin/bash

fixtureDir="mimir/fixtures"

python "$fixtureDir/neural_network_weight_gen.py" > "$fixtureDir/neural_network_weight_test.json"