import ply.lex as lex

reserved = {
   'select': 'SELECT',
   'distinct': 'DISTINCT',
   'from': 'FROM',
   'where': 'WHERE',
   'order': 'ORDER',
   'by': 'BY',
   'limit': 'LIMIT',
   'insert': 'INSERT',
   'into': 'INTO',
   'values': 'VALUES',
   # 'as': 'AS',    
   'and': 'AND',  
   'not' : 'NOT',
   'or': 'OR',
#    'true': 'BOOLEAN',
#    'false': 'BOOLEAN',
}

tokens = (
   'IDENTIFIER',

   'STRING',
   'NUMBER',
   'FLOAT',

   'PLUS',
   'MINUS',
   'DIVIDE',
   'TIMES',
   'LESS',
   'GREATER',
   'EQ',
   'LESS_EQ',
   'GREATER_EQ',
   'BANG',

   'LPAREN',
   'RPAREN',
   'COMMAS', 
   'SEMICOLON',
) + tuple(reserved.values())

t_PLUS    = r'\+'
t_MINUS   = r'-'
t_DIVIDE  = r'/'
t_TIMES   = r'\*'
t_LESS = r'<'
t_GREATER = r'>'
t_EQ = r'\='
t_LESS_EQ = r'<='
t_GREATER_EQ = r'>='
t_BANG = r'!'

t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_COMMAS = r','
t_SEMICOLON = r';'

def t_FLOAT(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_STRING(t):
    r"'(?:[^'])*'" 
    t.value = t.value[1:-1]
    return t

def t_IDENTIFIER(t):
    r'[a-zA-Z][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value.lower(), 'IDENTIFIER')
    
    # if t.type == 'BOOLEAN':
    #     t.value = (t.value.lower() == 'true')
    return t

# 2. Ignored characters
t_ignore = ' \t'


def t_error(t):
    raise ValueError(f"Illegal character '{t.value[0]}'")


def t_eof(t):
    current_text = t.lexer.lexdata
    
    if not current_text.strip().endswith(';'):
        more = input('... ') 
        t.lexer.input(more)
        return t.lexer.token()
    return None

# Build the lexer
lexer = lex.lex()
