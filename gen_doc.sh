#!/bin/bash

cd docs
rm -f source/_modules/*.rst
sphinx-apidoc -o source/_modules ../sp
make clean
make html