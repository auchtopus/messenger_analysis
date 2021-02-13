#!/bin/bash
# pass directory containing messages to the script

find $1 -type f -iname "*.jpg" -exec rm -f {} \;
find $1 -type f -iname "*.png" -exec  rm -f {} \;
find $1 -type f -iname "*.gif" -exec rm -f {} \;
find $1 -type f -iname "*.mp4" -exec rm -f {} \;