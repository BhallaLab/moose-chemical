#!/bin/bash - 
#===============================================================================
#
#          FILE: run_test.sh
# 
#         USAGE: ./run_test.sh 
# 
#   DESCRIPTION: 
# 
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Dilawar Singh (), dilawars@ncbs.res.in
#  ORGANIZATION: NCBS Bangalore
#       CREATED: 06/04/2016 03:59:46 PM
#      REVISION:  ---
#===============================================================================

set -o nounset                              # Treat unset variables as an error
echo "Running test A"
python ./test/test_bnf_parser.py

