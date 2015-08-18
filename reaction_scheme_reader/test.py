import collections
from chem_parser import yacc

def test_equation(s):
    yacc.parse(s)

def main():
    text = """
    a[conc=1.0] + b[conc=12.01] <-- kf=0.12, kb=1.2 --> c[conc=0.0] ;
    """
    test_equation(text)


if __name__ == '__main__':
    main()
