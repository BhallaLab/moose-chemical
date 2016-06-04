all: build test
	echo "Done all"

build : 
	python setup.py build

test : ./test/*.py
	python -m yacml ./test/test_bnf_parser.py 

.PHONY :
	build all test

