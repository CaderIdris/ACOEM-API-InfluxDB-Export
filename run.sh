#!/bin/bash

venv=venv/bin/python3

echo "Start Date? (YYYY-MM-DD): "
read startdate
echo "End Date? (YYYY-MM-DD): "
read enddate

$venv main.py -s $startdate -e $enddate
