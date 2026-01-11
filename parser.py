import ply.yacc as yacc
from lexer import tokens
from Nodes import *

precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('right', 'NOT', 'BANG'),
    ('left', 'LESS', 'GREATER', 'EQ', 'LESS_EQ', 'GREATER_EQ'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
)

def p_SelectQuery(p):
    'Query : SelectStmt SEMICOLON'
    p[0] = p[1]
def p_InsertQuery(p):
    'Query : InsertStmt SEMICOLON'
    p[0] = p[1]

def p_Select_statement(p):
    'SelectStmt : SELECT opt_DISTINCT ColumnsList FromStmt WhereStmt OrderByStmt LimitStmt'
    p[0] = Select('SELECT', p[2], p[3], p[4], p[5], p[6], p[7])

def p_opt_DISTINCT(p):
    'opt_DISTINCT : DISTINCT'
    p[0] = p[1]

def p_opt_DISTINCT1(p):
    'opt_DISTINCT : empty'
    p[0] = None

def p_ColumnsList_TIMES(p):
    'ColumnsList : TIMES'
    p[0] = '*'

def p_ColumnsList(p):
    'ColumnsList : ColumnsList1'
    p[0] = p[1]

def p_ColumnsList1(p):
    'ColumnsList1 : ColumnName'
    result = []
    result.append(p[1])
    p[0] = result

def p_ColumnsList2(p):
    'ColumnsList1 : ColumnsList1 COMMAS ColumnName'
    p[1].append(p[3])
    p[0] = p[1]

def p_From_statement(p):
    'FromStmt : FROM TableName'
    p[0] = From('FROM', p[2])

def p_Table_Name(p):
    'TableName : IDENTIFIER'
    p[0] = TableName('TABLE', p[1])

def p_Where_statement(p):
    'WhereStmt : WHERE condition'
    p[0] = Where('WHERE', p[2])

def p_OR_condition(p):
    'condition : condition OR condition'
    p[0] = Condition('OR', p[1], p[3])

def p_AND_condition(p):
    'condition : condition AND condition'
    p[0] = Condition('AND', p[1], p[3])

def p_NOT_condition(p):
    'condition : NOT condition'
    p[0] = Condition('NOT', p[2], None)

def p_BANG_condition(p):
    'condition : BANG condition'
    p[0] = Condition('BANG', p[2], None)

def p_Parenthesised_Condition(p):
    'condition : LPAREN condition RPAREN'
    p[0] = p[2]

def p_LESS_condition(p):
    'condition : expression LESS expression'
    p[0] = Condition('LESS', p[1], p[3])

def p_GREATER_condition(p):
    'condition : expression GREATER expression'
    p[0] = Condition('GREATER', p[1], p[3])

def p_EQ_condition1(p):
    'condition : expression EQ expression'
    p[0] = Condition('EQ', p[1], p[3])

def p_LESS_EQ_condition(p):
    'condition : expression LESS_EQ expression'
    p[0] = Condition('LESS_EQ', p[1], p[3])

def p_GREATER_EQ(p):
    'condition : expression GREATER_EQ expression'
    p[0] = Condition('GREATER_EQ', p[1], p[3])

def p_Empty_Where_statement(p):
    'WhereStmt : empty'
    p[0] = None

def p_ORDER_BY_statement(p):
    'OrderByStmt : ORDER BY ColumnName'
    p[0] = OrderBy('ORDERBY', p[3])

def p_Column_Name(p):
    'ColumnName : IDENTIFIER'
    p[0] = ColumnName('COLUMN', p[1])

def p_Empty_ORDER_BY_statement(p):
    'OrderByStmt : empty'
    p[0] = None

def p_Limit_statement(p):
    'LimitStmt : LIMIT NUMBER'
    p[0] = Limit('LIMIT', NumberLiteral('NUMBER', p[2]))

def p_Empty_Limit_statement(p):
    'LimitStmt : empty'
    p[0] = None

def p_expression_plus(p):
    'expression : expression PLUS expression'
    p[0] = Expression('PLUS', p[1], p[3])

def p_expression_minus(p):
    'expression : expression MINUS expression'
    p[0] = Expression('MINUS', p[1], p[3])

def p_expression_times(p):
    'expression : expression TIMES expression'
    p[0] = Expression('TIMES', p[1], p[3])

def p_expression_div(p):
    'expression : expression DIVIDE expression'
    p[0] = Expression('DIVIDE', p[1], p[3])

def p_Parenthesised_expression(p):
    'expression : LPAREN expression RPAREN'
    p[0] = p[2]

def p_expression_NUMBER(p):
    'expression : NUMBER'
    p[0] = NumberLiteral('NUMBER', p[1])

def p_expression_STRING(p):
    'expression : STRING'
    p[0] = StringLiteral('STRING', p[1])

# def p_expression_BOOLEAN(p):
#     'expression : BOOLEAN'
#     p[0] = BooleanLiteral('BOOLEAN', p[1])

def p_expression_FLOAT(p):
    'expression : FLOAT'
    p[0] = FloatLiteral('FLOAT', p[1])

def p_expression_ColumnName(p):
    'expression : ColumnName'
    p[0] = p[1]
    
def p_Insert_statement(p):
    'InsertStmt : INSERT INTO TableName opt_ColumnsList VALUES LPAREN Literals RPAREN'
    p[0] = Insert('INSERT', p[3], p[4], p[7])
    
def p_opt_ColumnsList1(p):
    'opt_ColumnsList : LPAREN ColumnsList1 RPAREN'
    p[0] = p[2]

def p_opt_ColumnsList2(p):
    'opt_ColumnsList : empty'
    p[0] = None

def p_Literals1(p):
    'Literals : Literal'
    result = []
    result.append(p[1])
    p[0] = result

def p_Literals2(p):
    'Literals : Literals COMMAS Literal'
    p[1].append(p[3])
    p[0] = p[1]

def p_String_Literal(p):
    'Literal : STRING'
    p[0] = StringLiteral('STRING', p[1])

def p_NUMBER_Literal(p):
    'Literal : NUMBER'
    p[0] = NumberLiteral('NUMBER', p[1])

def p_FLOAT_Literal(p):
    'Literal : FLOAT'
    p[0] = FloatLiteral('FLOAT', p[1])

# def p_BOOLEAN_Literal(p):
#     'Literal : BOOLEAN'
#     p[0] = BooleanLiteral('BOOLEAN', p[1])

def p_empty(p):
    'empty :'


def p_error(p):
    print(f'Unexpected token "{p.value}"')


parser = yacc.yacc()


