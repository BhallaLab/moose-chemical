"""chem_lexer.py: 

    Lexer for chemical reactions.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2015, Dilawar Singh and NCBS Bangalore"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

import ply.lex as lex

tokens = (
    'NAME','NUMBER', 'DECIMAL',
    'COMMA',
    'PLUS','MINUS','TIMES','DIVIDE','EQUALS',
    'LPAREN','RPAREN',
    'LEFT_REAC' , 'RIGHT_REAC',
    )

# Tokens

t_PLUS       = r'\+'
t_MINUS      = r'-'
t_TIMES      = r'\*'
t_DIVIDE     = r'/'
t_EQUALS     = r'= '
t_LPAREN     = r'\['
t_RPAREN     = r'\]'
t_NAME       = r'[a-zA-Z_][a-zA-Z0-9_]*'
t_LEFT_REAC  = r'<-'
t_RIGHT_REAC = r'->'
t_COMMA      = r','
t_DECIMAL    = r'(\+|-)?[0-9]\+(\.[0-9]\+)?'

def t_NUMBER(t):
    r'\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        print("Integer value too large %d", t.value)
        t.value = 0
    return t

# Ignored characters
t_ignore = " \t"

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")
    
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

precedence = (
    ('left','PLUS','MINUS'),
    ('left','TIMES','DIVIDE'),
    ('right','UMINUS'),
    )


lexer = lex.lex()
