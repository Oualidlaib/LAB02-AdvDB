from abc import ABC, abstractmethod
from record_manager import get_table_schema
from record_manager import read_all_structured_records
from record_manager import insert_structured_record
import json

# parse schema JSON file into a list of dictionaries
with open('schema.json') as schema_file:
    schema = json.load(schema_file)

# convert schema to a dictionary for lookup faster than looping through a list `O(1) in Average case`
schema_dict = {table["table_name"]: table for table in schema}



# print(schema_dict.keys())

class Node(ABC):

    @abstractmethod
    def analyze(self, table_name=None):
        pass 

    @abstractmethod
    def evaluate(self):
        pass 

class Select(Node):

    def __init__(self, node_type, is_distinct, columns, source, where, orderby, limit):
        self.node_type = node_type

        # '*' or list of colummns
        self.columns = columns 
        self.source = source       
        self.where = where 
        self.orderby = orderby
        self.limit = limit
        self.distinct = is_distinct
    
    def analyze(self, table_name=None):
        table_name = self.source.analyze(table_name)
        table_schema = get_table_schema(table_name, schema_dict)
        if self.columns != '*':
            fields = []
            for field in table_schema['fields']:
                fields.append(field['name'])

            for column in self.columns:
                if column.value not in fields:
                    raise ValueError(f"There no such a column named {column.value} in {table_name}")
        
        
        if self.where is not None:
            self.where.analyze(table_name)

        if self.orderby is not None:   
            self.orderby.analyze(table_name)
        
        if self.limit is not None:
            self.limit.analyze(table_name)

        return None

    def evaluate(self):
         
        tuples = self.source.evaluate()

        # Filtering/Selection
        if self.where is not None:

            results = []
            for row in tuples:
                if self.where.evaluate(row) is not None:
                    results.append(row)
            
            tuples = results

        # Sorting
        if self.orderby is not None:

            tuples = self.orderby.evaluate(tuples)
        
        if self.limit is not None:

            tuples = self.limit.evaluate(tuples)
        
        # Projection
        if self.columns == '*':

            return tuples

        else:
            list_of_columns = []

            for column in self.columns:
                list_of_columns.append(column.value)

            # print(list_of_columns)

            results = []

            for row in tuples:

                projected_record = {k: v for k, v in row.items() if k in list_of_columns}

                results.append(projected_record)

            tuples = results
        
        if self.distinct is not None:

            unique_tuples = []

            results = { tuple(d.items()) for d in tuples }

            for t in results:
                unique_tuples.append(dict(t))

            tuples = unique_tuples
        
        return tuples

        
        




class From(Node):

    def __init__(self, node_type, table):
        self.node_type = node_type
        self.table = table

    def analyze(self, table_name=None):
        return self.table.analyze(table_name)
    
    def evaluate(self):
        return read_all_structured_records(self.table.tableName, schema_dict) 

class TableName(Node):

    def __init__(self, node_type, tableName):
        self.node_type = node_type
        self.tableName = tableName

    def analyze(self, table_name=None):

        if self.tableName not in schema_dict.keys():
            raise ValueError(f"There is no such a table named {self.tableName}")
        
        return self.tableName
    
    def evaluate(self):
        pass 

class Where(Node):

    def __init__(self, node_type, condition):
        self.node_type = node_type
        self.condition = condition
    
    def analyze(self, table_name=None):
        self.condition.analyze(table_name)
    
    def evaluate(self, tuple=None):
        return self.condition.evaluate(tuple)

class Condition(Node):

    def __init__(self, node_type, left, right):
        self.node_type = node_type
        self.left = left
        self.right = right
    
    def analyze(self, table_name=None):
        
        if(self.node_type == 'NOT' or self.node_type == 'BANG'):
            self.left.analyze(table_name)
        else:
            self.left.analyze(table_name)
            self.right.analyze(table_name)

            left_type = self.left.type(table_name)
            right_type = self.right.type(table_name)

            if not((left_type == 'NUMBER' and right_type == 'FLOAT') \
                or (left_type == 'FLOAT' and right_type == 'NUMBER')):

                if self.node_type in ['LESS', 'GREATER', 'LESS_EQ', 'GREATER_EQ'] and \
                    (left_type == 'STRING' or right_type == 'STRING'):

                    raise ValueError(f"YOU ARE DOING SOMETHING VERY STRANGE!!!")

                if left_type != right_type:
                    raise ValueError(f"Can't compare {left_type} with {right_type}")

    def type(self, table_name=None):
        return 'BOOLEAN'

    def evaluate(self, tuple=None):

        if self.node_type == 'NOT' or self.node_type == 'BANG':
            
            if self.left.evaluate(tuple) is None:
                return tuple
            else:
                return None
        
        elif self.node_type == 'AND':
            
            if (self.left.evaluate(tuple) is not None) and (self.right.evaluate(tuple) is not None):
                return tuple
            else:
                return None
        
        elif self.node_type == 'OR':
            
            if (self.left.evaluate(tuple) is not None) or (self.right.evaluate(tuple) is not None):
                return tuple
            else:
                return None
            
        elif self.node_type == 'LESS':

            if self.left.evaluate(tuple) < self.right.evaluate(tuple):
                return tuple
            else:
                return None
            
        elif self.node_type == 'LESS_EQ':

            if self.left.evaluate(tuple) <= self.right.evaluate(tuple):
                return tuple
            else:
                return None
            
        elif self.node_type == 'GREATER':

            if self.left.evaluate(tuple) > self.right.evaluate(tuple):
                return tuple
            else:
                return None
        
        elif self.node_type == 'GREATER_EQ':

            if self.left.evaluate(tuple) >= self.right.evaluate(tuple):
                return tuple
            else:
                return None
        
        elif self.node_type == 'EQ':

            if self.left.evaluate(tuple) == self.right.evaluate(tuple):
                return tuple
            else:
                return None


            


class Expression(Node):

    def __init__(self, node_type, left, right):
        self.node_type = node_type
        self.left = left
        self.right = right
    
    def analyze(self, table_name=None):

        self.left.analyze(table_name)
        self.right.analyze(table_name)

        left_type = self.left.type(table_name)
        right_type = self.right.type(table_name)

        if not((left_type == 'NUMBER' and right_type == 'FLOAT') \
            or (left_type == 'FLOAT' and right_type == 'NUMBER')):

            if left_type != right_type:
                raise ValueError(f"Can't evaluate {left_type} with {right_type}")
            
    def type(self, table_name=None):

        if not((self.left.type(table_name) == 'NUMBER' and self.right.type(table_name) == 'FLOAT') \
            or (self.left.type(table_name) == 'FLOAT' and self.right.type(table_name) == 'NUMBER')):

            left_type = self.left.type(table_name)
            right_type = self.right.type(table_name)

            if left_type != right_type:
                raise ValueError(f"Can't evaluate {left_type} with {right_type}")
            else:
                return left_type
        else:
            return 'FLOAT'
    
    def evaluate(self, tuple=None):
        
        if self.node_type == 'PLUS':
            return self.left.evaluate(tuple) + self.right.evaluate(tuple)
        
        elif self.node_type == 'MINUS':
            return self.left.evaluate(tuple) - self.right.evaluate(tuple)
        
        elif self.node_type == 'TIMES':
            return self.left.evaluate(tuple) * self.right.evaluate(tuple)
        
        elif self.node_type == 'DIVIDE':
            return self.left.evaluate(tuple) / self.right.evaluate(tuple)

class OrderBy(Node):

    def __init__(self, node_type, column_name):
        self.node_type = node_type
        self.columnName = column_name
    
    def analyze(self, table_name=None):
        self.columnName.analyze(table_name)

    def evaluate(self, tuples=None):

        sorted_records = sorted(tuples, key=lambda x: x[self.columnName.value])

        return sorted_records

class Limit(Node):

    def __init__(self, node_type, number):
        self.node_type = node_type
        self.number = number
    
    def analyze(self, table_name=None):
        pass

    def evaluate(self, tuples=None):
        return tuples[:self.number.value]

class StringLiteral(Node):

    def __init__(self, node_type, value):
        self.node_type = node_type
        self.value = value
    
    def analyze(self, table_name=None):
        pass

    def type(self, table_name=None):
        return self.node_type
    
    def evaluate(self, tuple=None):
        return self.value

class NumberLiteral(Node):

    def __init__(self, node_type, value):
        self.node_type = node_type
        self.value = value
    
    def analyze(self, table_name=None):
        pass

    def type(self, table_name=None):
        return self.node_type
    
    def evaluate(self, tuple=None):
        return self.value

class BooleanLiteral(Node):

    def __init__(self, node_type, value):
        self.node_type = node_type
        self.value = value
    
    def analyze(self, table_name=None):
        pass

    def type(self, table_name=None):
        return self.node_type
    
    def evaluate(self, tuple=None):
        return self.value

class FloatLiteral(Node):

    def __init__(self, node_type, value):
        self.node_type = node_type
        self.value = value
    
    def analyze(self, table_name=None):
        pass

    def type(self, table_name=None):
        return self.node_type
    
    def evaluate(self, tuple=None):
        return self.value

class ColumnName(Node):
     
    def __init__(self, node_type, columnName):
        self.node_type = node_type
        self.value = columnName
    
    def analyze(self, table_name=None):

        table_schema = get_table_schema(table_name, schema_dict)

        fields = []
        for field  in table_schema['fields']:
            fields.append(field['name'])

        if self.value not in fields:
            raise ValueError(f"There no such a column named {self.value} in {table_name}")
    
    def evaluate(self, tuple=None):
        return tuple[self.value]

    def type(self, table_name=None):

        if table_name is None :
            raise ValueError(f"Something went wrong")
        
        table_schema = get_table_schema(table_name, schema_dict)

        for field in table_schema['fields']:
            if field['name'] == self.value :
                if field['type'] == 'int':
                    return 'NUMBER'
                elif field['type'] == 'float':
                    return 'FLOAT'
                else:
                    return 'STRING'
        return None


class Insert(Node):
    
    def __init__(self, node_type, tableName, columns, values):
        self.node_type = node_type
        self.tableName = tableName
        self.columns = columns
        self.values = values
    
    def analyze(self, table_name=None):

        table_name = self.tableName.analyze()
        
        if self.columns is None :
            table_schema = get_table_schema(table_name, schema_dict)
            self.columns = []
            for field in table_schema['fields']:
                self.columns.append(
                        ColumnName('COLUMN', field['name'])
                    )
        else:
            for column in self.columns:
                column.analyze(table_name)
        
        i = 0
        if len(self.columns) != len(self.values):
            raise ValueError(f"Some columns or values are missed")
        
        while i < len(self.columns):
            col_type = self.columns[i].type(table_name)
            val_type = self.values[i].type(table_name)
            
            if not((col_type == 'NUMBER' and val_type == 'FLOAT') \
                or (col_type == 'FLOAT' and val_type == 'NUMBER')):

                if col_type != val_type:
                    raise ValueError(f"column {self.columns[i].value} is of type {col_type}")
                
            i += 1

    def evaluate(self):
    
        if self.columns is None:

            table_schema = get_table_schema(self.tableName.tableName)

            fields = []
            for field in table_schema['fields']:
                fields.append(field['name'])
            record = {}

            # print(fields)

            for i in range(len(fields)):
                record[fields[i]] = self.values[i].value
            
            insert_structured_record(self.tableName.tableName, schema_dict, record)

        else:

            record = {}

            for i in range(len(self.columns)):
                record[self.columns[i].value] = self.values[i].value
            
            insert_structured_record(self.tableName.tableName, schema_dict, record)
        
        return None


    


