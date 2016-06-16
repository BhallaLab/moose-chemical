import moose
import yacml
import sys

def main( ):
    yacmlFile = sys.argv[1]
    yacml.loadModel( yacmlFile )
    print( '[INFO] Done ' )


if __name__ == '__main__':
    main()
