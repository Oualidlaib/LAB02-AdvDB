import re
from collections import deque
from record_manager import get_table_schema, read_all_structured_records, insert_structured_record
import json


def is_parentheses_valid(expression):

    # a queue implemented as a stack
    stack = deque()

    for c in expression:
        if c == '(':
            stack.append(c)
        elif c == ')':
            try:
                stack.pop()
            except:
                return False
    
    # check is stack is empty
    if len(stack) == 0:
        return True
    
    return False 

# define the only valid comparison operators
comparison_operators_of_length_1 = ('=', '<', '>')
comparison_operators_of_length_2 = ('<=', '>=', '!=')

def construct_AST_dict(expression):
    """
    Construct an Abtract Syntax Tree from the passed WHERE clause expression
    as a dictionary in a recursive way.
    """

    expression = expression.strip()

    # check paranthesis
    is_parentheses_valid(expression)

    # This will remove any paratheses that are not useful, like `WHERE ( ((id=3 AND name='Godel')) )`
    while expression[0] == '(' and expression[-1] == ')':
        if is_parentheses_valid(expression[1:-1]):
            expression = expression[1:-1]
            expression = expression.strip()
        else:
            break           

    if(expression == ""):
        raise ValueError('WHERE clause expression is not valid')

    i = 0

    # Parse `OR` if it exists
    while i < len(expression):

        if expression[i] == '(':
            # skip everything until a closing parathesis is found

            # create a queue but behaves as a stack
            stack = deque()

            # push to the stack
            stack.append(expression[i])

            # advance the pointer
            i = i + 1

            while(len(stack) != 0):
                if expression[i] == '(':
                    stack.append('(')
                elif expression[i] == ')':
                    stack.pop()
                i = i + 1

        elif expression[i] == " ":
            i = i + 1

        elif i + 3 < len(expression):
            if expression[i:i+2] == 'OR' and i > 0:

                # Eliminate a case like `WHERE name = "Ahmed"OR...` or `WHERE ...OR100 <= id`
                if (expression[i-1] == ')' or expression[i-1] == ' ') \
                    and (expression[i+2] == ')' or expression[i+2] == ' ') :

                    # return the Abstract Syntax Tree
                    return {
                                "operator" : "OR",

                                # contuct the left AST recursively
                                "left" : construct_AST_dict(expression[0:i]),

                                # contuct the right AST recursively
                                "right" : construct_AST_dict(expression[i+2:])
                            }
                else:
                    i = i + 1
            else:
                i = i + 1
        else:
            i = i + 1
    
    
    # Parse `AND` if there is any 
    i = 0
    while i < len(expression):

        if expression[i] == '(':

            # skip everything until a closing parathesis is found
            stack = deque()

            # push to the stack
            stack.append(expression[i])

            # advance the pointer
            i = i + 1

            while(len(stack) != 0):

                if expression[i] == '(':
                    stack.append('(')
                elif expression[i] == ')':
                    stack.pop()
                
                i = i + 1

        elif expression[i] == " ":
            i = i + 1

        elif i + 4 < len(expression):
            if expression[i:i+3] == 'AND' and i > 0:

                # Eliminate a case like `WHERE name = "Ahmed"AND...` or `WHERE ...AND100 <= id`
                if (expression[i-1] == ')' or expression[i-1] == ' ') \
                    and (expression[i+3] == ')' or expression[i+3] == ' ') :
                    
                    # return the Abstract Syntax Tree
                    return {
                                "operator" : "AND",

                                # contuct the left AST recursively
                                "left" : construct_AST_dict(expression[0:i]),

                                # contuct the right AST recursively
                                "right" : construct_AST_dict(expression[i+3:])
                            }
                else:
                    i = i + 1 
            else:
                i = i + 1
        else:
            i = i + 1

    # check now for comparison operators since no `OR` or `AND` keywords are found in the expression
    i = 0
    while i < len(expression):

        if expression[i:i+2] in comparison_operators_of_length_2 and (i + 2) < len(expression):

            # return the AST
            return {
                        "operator" : expression[i:i+2],

                        # no recursive call
                        "left" : expression[0:i].strip().strip("'").strip('"'),

                        # same as here
                        "right" : expression[i+2:].strip().strip("'").strip('"')
                    }

        elif expression[i] in comparison_operators_of_length_1 and (i + 1) < len(expression):
            
            # return the AST
            return {
                        "operator" : expression[i],

                        # no recursive call
                        "left" : expression[0:i].strip().strip("'").strip('"'),

                        # same as here
                        "right" : expression[i+1:].strip().strip("'").strip('"')
                    }
        else:
            i = i + 1
    

    # if no operator is found then the expression has to be NOT VALID !!
    raise ValueError('WHERE clause expression is not valid')



def are_fields_match(ast, fields_dict):
    if ast['operator'] in comparison_operators_of_length_1 \
       or ast['operator'] in comparison_operators_of_length_2 :
        
        # Assuming the field name always on the left side for simplicity
        if ast["left"] not in fields_dict.keys():
            raise ValueError('One of the fields in WHERE clause not in the table')
                
        # Assuming the only possible types of fields are `int`, `flaot`, `char(n)`, and `varchar(n)`
        if fields_dict[ast['left']] == 'int':
            try:
                int(ast['right'])
            except:
                raise ValueError(f"the field {ast['left']} is of type int")
            
        elif fields_dict[ast['left']] == 'float':
            try:
                float(ast['right'])
            except:
                raise ValueError(f"the field {ast['left']} is of type float")
        else:
            return
        
    else:
        are_fields_match(ast['left'], fields_dict)
        are_fields_match(ast['right'], fields_dict)
        return



def parse_select_query(query, schema_dict) -> dict:
    """
    Parse a simple SELECT query into a structured dictionary.

    Here the condition is an Abstract Syntax Tree encoded as a dictionary, 
    it will make life easier when it comes to evaluate the WHERE clause expression

    Here is a simple SELECT query :
                                    "
                                     SELECT name, salary FROM Employee
                                     WHERE ((name='Oualid') AND (id<3)) OR (id>=5);
                                    "
    And here is its corresponding output,
    {
        "fields": ["name", "salary"],
        "table": "Employee",
        "conditions": {
                        'operator': 'OR', 
                        'left': {
                                    'operator': 'AND', 
                                    'left': {
                                                'operator': '=', 
                                                'left': 'name', 
                                                'right': "'Oualid'"
                                            }, 
                                    'right': {
                                                'operator': '<', 
                                                'left': 'id', 
                                                'right': '3'
                                             }
                                }, 
                        'right': {
                                    'operator': '>=', 
                                    'left': 'id', 
                                    'right': '5'
                                }
                        }
    }
    As you can see, the condition attribute is basically a tree, with this tree-based structure, we can evaluate
    the condition clause recursively
    """



    # strip the query if there are trailing or leading spaces
    query = query.strip()

    # define a regex pattern used to extract the arguments from a select statement
    select_statement_regex_pattern = r"""
                                            ^SELECT\s+(.*)\s+
                                            FROM\s+(\w+)
                                            (?:\s+WHERE\s+(.*))?
                                            ;$
                                      """

    match = re.fullmatch(select_statement_regex_pattern, query, re.VERBOSE)

    if match is None:
        raise ValueError("The Select Query is not valid")

    # fields to be select, seperated by commas
    fields_in_the_query = match.group(1).strip()
    
    # extract the table after the FROM clause, assuming there is only one table
    table_name = match.group(2)

    # if there is a WHERE clause, extract the condition expression
    condition_expression = match.group(3)
    
    table_name = table_name.strip()

    # check if the table does exist
    table_schema = get_table_schema(table_name, schema_dict)

    

    # check if the fields in the query is a subset of table fields
    columns_of_table = set()
    for field in table_schema["fields"]:
        columns_of_table.add(field["name"])
    
    if fields_in_the_query != '*':
        fields = fields_in_the_query.split(',')

        for i in range(len(fields)):
            fields[i] = fields[i].strip()

        if not set(fields).issubset(columns_of_table):
            raise ValueError('fields mismatch')

    else:
        fields = list(columns_of_table)   

    # Build the corresponding Abstract Syntax Tree of the condition expression
    conditions = None
    if condition_expression is not None:
        conditions = construct_AST_dict(condition_expression)

    # Check fields in WHERE clause do exist in the table as well as the values being compared to match the field type
    if conditions is not None:
        # construct a dict of field names and their corresponding types of the table
        fields_dict = {}
        for field in table_schema["fields"]:
            fields_dict[field["name"]] = field["type"]

        are_fields_match(conditions, fields_dict)

    return {
                "fields" : fields,
                "table_name" : table_name,
                "conditions": conditions
           }


def is_there_a_type_mismatch(record, fields_dict):
    for key in record.keys():
        if fields_dict[key] == 'int':
            try:
                int(record[key])
            except:
                raise ValueError(f"the field {key} is of type int")
            
        elif fields_dict[key] == 'float':
            try:
                float(record[key])
            except:
                raise ValueError(f"the field {key} is of type float")
        else:
            record[key] = record[key].strip()
            record[key] = record[key].strip("'")
            record[key] = record[key].strip('"')
    
    return 

    
def parse_insert_query(query, schema_dict) -> dict:
    """
    Parse a simple INSERT query into a structured dictionary.
    Example output:
    {
        "table": "Employee",
        "fields": ["id", "name", "salary"],
        "values": [4, "Alice", 4500]
    }
    """

    # strip the query if there are trailing or leading spaces
    query = query.strip()

    # define a regex pattern used to extract the arguments from a insert statement
    insert_statement_regex_pattern = r"""
                                        ^INSERT\s+INTO\s+
                                        (\w+)\s*
                                        \(\s*(.*?)\s*\)\s*       
                                        VALUES\s*
                                        \(\s*(.*?)\s*\)\s*       
                                        ;$
                                     """

    match = re.fullmatch(insert_statement_regex_pattern, query, re.VERBOSE)

    if match is None:
        raise ValueError('The insert query is not valid')
    
    # extract the table name in the insert query
    table_name = match.group(1).strip()

    # extract the fields in the query ( Note that it is assumed the user enter all the fields \
    # of the table, no columns can be set with a default value )
    fields_in_the_query = match.group(2)
    fields = fields_in_the_query.split(',')
    for i in range(len(fields)):
        fields[i] = fields[i].strip()

    # extract the values to be inserted into the relation
    values_to_inserted = match.group(3)
    values = values_to_inserted.split(',')
    for i in range(len(values)):
        values[i] = values[i].strip()
    
    # check that the table does exist in the schema
    table_schema = get_table_schema(table_name, schema_dict)

    # check the query cover all fields of the target relation
    columns_of_table = set()
    for field in table_schema["fields"]:
        columns_of_table.add(field["name"])
    
    if set(fields) != columns_of_table:
        raise ValueError('Some of the fields missing/not exist')

    # check the number of fields in the insert statement equal to the number of values to be inserted
    if len(fields) != len(values):
        raise ValueError('There is a mismatch between number fields and values in the statement')

    # map each field to its correspoding value, then check there not type mismatch
    record = {}
    for i in range(len(fields)):
        record[fields[i]] = values[i]
    
    fields_dict = {}
    for field in table_schema["fields"]:
        fields_dict[field["name"]] = field["type"]
    is_there_a_type_mismatch(record, fields_dict)

    fields = []
    values = []
    for key, value in record.items():
        fields.append(key)
        values.append(value)

    # return the result
    return {
                "table_name" : table_name,
                "fields" : fields,
                "values" : values
           }




def is_select_query(query):

    query = query.strip()

    # define a regex pattern used to extract the arguments from a select statement
    select_statement_regex_pattern = r"""
                                            ^SELECT\s+(.*)\s+
                                            FROM\s+(\w+)
                                            (?:\s+WHERE\s+(.*))?
                                            ;$
                                      """

    match = re.fullmatch(select_statement_regex_pattern, query, re.VERBOSE)

    if match is None:
        return False
    else:
        return True

def is_insert_query(query):

    query = query.strip()

    # define the pattern of the insert statement
    insert_statement_regex_pattern = r"""
                                        ^INSERT\s+INTO\s+
                                        (\w+)\s*
                                        \(\s*(.*?)\s*\)\s*       
                                        VALUES\s*
                                        \(\s*(.*?)\s*\)\s*       
                                        ;$
                                     """
    match = re.fullmatch(insert_statement_regex_pattern, query, re.VERBOSE) 

    if match is None:
        return False
    else:
        return True



def is_condition_satisfied(record, condition, fields_dict):

    if condition is None:
        return True

    op = condition['operator']

    if op == 'OR':
        return is_condition_satisfied(record, condition['left'], fields_dict) or is_condition_satisfied(record, condition['right'], fields_dict)
    elif op == 'AND':
        return is_condition_satisfied(record, condition['left'], fields_dict) and is_condition_satisfied(record, condition['right'], fields_dict)
    else:
        if fields_dict[condition['left']] == 'int':
            condition['right'] = int(condition['right'])

        elif fields_dict[condition['left']] == 'float':
            condition['right'] = float(condition['right'])

        if op == '=':
            return record[condition['left']] == condition['right']
        
        elif op == '!=':
            return record[condition['left']] != condition['right']
        
        elif op == '<':
            return record[condition['left']] < condition['right']
        
        elif op == '>':
            return record[condition['left']] > condition['right']
        
        elif op == '<=':
            return record[condition['left']] <= condition['right']
        
        elif op == '>=':
            return record[condition['left']] >= condition['right']


def execute_query(query, schema_dict):
    """
    Execute a SELECT or INSERT query on the structured records stored in the heap file.
    """

    if is_select_query(query):
        
        # parse the query
        query_parsed = parse_select_query(query, schema_dict)

        # get the name of the table
        table_name = query_parsed['table_name']

        # get table schema
        table_schema = schema_dict[table_name]

        fields_dict = {}
        for field in table_schema["fields"]:
            fields_dict[field["name"]] = field["type"]

        # extract query condition
        condition = query_parsed['conditions']

        # extract the fields
        fields = query_parsed['fields']

        # read all records of that table
        records = read_all_structured_records(table_name, schema_dict)

        # filter only those match the condition in the where clause
        filtered_records = []
        for record in records:
            # check if the record 
            if is_condition_satisfied(record, condition, fields_dict):

                # filter only the required columns
                record_projected = {k: record[k] for k in fields}

                # append to the result record list
                filtered_records.append(record_projected)

        # return the reuslting records
        return filtered_records
        
            

    elif is_insert_query(query):

        # parse the inset query
        query_parsed = parse_insert_query(query, schema_dict)

        # extract table name
        table_name = query_parsed['table_name']

        # exctract fields
        fields = query_parsed['fields']

        # extracy values to be inserted
        values = query_parsed['values']

        # build the record
        record_dict = {}
        for i in range(len(fields)):
            record_dict[fields[i]] = values[i]

        # insert the record into the table
        insert_structured_record(table_name, schema_dict, record_dict)
    else:
        raise ValueError("YOUR QUERY IS NOT VALID ! DO NOT EXPECT THAT I HAVE BUILT an Oracle-like DATABASE !\nTHIS IS JUST A VERY SIMPLE AND MINIMALIST RDBMS")


