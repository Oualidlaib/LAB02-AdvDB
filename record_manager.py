import json
import re
import os
import struct
from heap_manager import create_heap_file, insert_record_to_file, get_all_records_from_file

# parse schema JSON file into a list of dictionaries
with open('schema.json') as schema_file:
    schema = json.load(schema_file)

# convert schema to a dictionary for lookup faster than looping through a list `O(1) in Average case`
schema_dict = {table["table_name"]: table for table in schema}

# {'Employee': 
#     {'table_name': 'Employee', 
#      'file_name': './Employee.sql', 
#      'fields': [{'name': 'id', 'type': 'int'}, 
#                 {'name': 'name', 'type': 'char(255)'}, 
#                 {'name': 'salary', 'type': 'float'}]}, 
#
# 'Mathematics': (...etc)

def get_table_schema(table_name, schema_dict):
    try:
        return schema_dict[table_name]
    except KeyError:  
        # table not in schema
        raise ValueError(f'There is no such a table named {table_name}')


def are_constraints_violated(record_dict, table_schema):
    
    # print(record_dict)

    # Define MIN and MAX int
    MIN_INT = -2_147_483_647
    MAX_INT = 2_147_483_647

    # Define the regex patterns of the types CHAR and VARCHAR
    char_type_pattern = r"^char\((\d+)\)$"
    varchar_type_pattern = r"^varchar\((\d+)\)$"

    # check record_dict contains all the necessary fields
    fields_of_table_schema = {}
    
    for field in table_schema["fields"]:

        field_name = field["name"]
        field_type = field["type"]

        fields_of_table_schema[field_name] = field_type
    
    if set(record_dict.keys()) != set(fields_of_table_schema.keys()):

        # a field does not exist or missing
        return True

    for field, value in record_dict.items():

        field_name = field

        # extract the expected type that the value should adhere to
        field_type = fields_of_table_schema[field_name]

        # check if the type of the field is of type char
        if (match := re.fullmatch(char_type_pattern, field_type)) is not None:

            # extract "n" in char(n) cast it to an int 
            n = int(match.group(1))

            if not isinstance(value, str):
                return True

            # encode the string using ASCII
            value_of_char_encoded = value.encode('ascii')

            # get the number bytes
            length_char_field_in_bytes = len(value_of_char_encoded)

            # check that the length of the string do not exceed n
            if length_char_field_in_bytes > n:
                return True

        # check if the type of the field is if type varchar
        elif (match := re.fullmatch(varchar_type_pattern, field_type)) is not None:

            # extract "n" in varchar(n) and cast it to an int 
            n = int(match.group(1))

            # ensure that n is less than 255, since we only have 1 byte to store the length of the string
            if not ( 0 <= n <= 255 ):
                return True

            if not isinstance(value, str):
                return True

            # encode the string using ASCII
            value_of_varchar_encoded = value.encode('ascii')

            # get the number bytes (it is ensured that it fits into one byte)
            length_varchar_field_in_bytes = len(value_of_varchar_encoded)

            # check that the length of the string do not exceed n
            if length_varchar_field_in_bytes > n:
                return True

        elif field_type  == "int":
            try:
                ivalue = int(value)

                # ensure that value fits into 4 bytes without any loss
                if not ( MIN_INT <= ivalue <= MAX_INT ):
                    return True
                
            except:
                return True
            
                
        elif field_type  == "float":

            # print(field_type)
            try:
                float(value)
            except:
                return True

        else:
            raise ValueError('Type is not valid')
          
    return False





def encode_record(record_dict, table_name, schema_dict) -> bytes:
    """
    Convert a Python dictionary record into binary form
    based on the JSON table description.
    """
    
    table_schema = get_table_schema(table_name, schema_dict)

    # check if the record adhere to the schema constraints 
    if are_constraints_violated(record_dict, table_schema):
        raise ValueError(f'One of the constraits are violated')
    

    # Define the regex patterns of the types CHAR and VARCHAR
    char_type_pattern = r"^char\((\d+)\)$"
    varchar_type_pattern = r"^varchar\((\d+)\)$"
    
    record_encoded = b""
    for field in table_schema["fields"]:

        # extract field name & type
        field_name = field["name"]
        field_type = field["type"]

        # check if the type of the field is of type char
        if (match := re.fullmatch(char_type_pattern, field_type)) is not None:

            # extract "n" in char(n) and cast it to an int 
            n = int(match.group(1))

            # Get the value of char(n) in the record 
            value_of_char = record_dict[field_name]

            # encode the string using ASCII
            value_of_char_encoded = value_of_char.encode('ascii')

            # get the number bytes
            length_char_field = len(value_of_char_encoded)

            # get the required null bytes to be added to the end of the string
            pad = b"\x00"
            padding_amount = n - length_char_field
            padding = pad * padding_amount

            # append to record_encoded
            record_encoded += value_of_char_encoded + padding

        # check if the type of the field is if type varchar
        elif (match := re.fullmatch(varchar_type_pattern, field_type)) is not None:

            # extract "n" in varchar(n) and cast it to an int 
            n = int(match.group(1))

            # Get the value of varchar(n) in the record 
            value_of_varchar = record_dict[field_name]

            # encode the string using ASCII
            value_of_varchar_encoded = value_of_varchar.encode('ascii')

            # get the number bytes (it is ensured that it fits into one byte)
            length_varchar_field_in_bytes = len(value_of_varchar_encoded).to_bytes(1, 'big')

            # append to record_encoded
            record_encoded += length_varchar_field_in_bytes + value_of_varchar_encoded 

        elif field_type  == "int":

            # append to record_encoded
            record_encoded += struct.pack('>i', int(record_dict[field_name]))

        elif field_type == "float":

            # append to record_encoded
            float_bytes = struct.pack('>f', float(record_dict[field_name]))
            record_encoded += float_bytes

        else:
            raise ValueError('Type is not valid')
    
    return record_encoded

def decode_record(record_bytes, table_name, schema_dict) -> dict:
    """
    Convert a binary record into a Python dictionary
    based on the JSON table description.
    """

    table_schema = schema_dict[table_name]

    # the decoded the record
    record_dict = {}

    for field in table_schema["fields"]:

        # extract field name & type
        field_name = field["name"]
        field_type = field["type"]

        # Define the regex patterns of the types CHAR and VARCHAR
        char_type_pattern = r"^char\((\d+)\)$"
        varchar_type_pattern = r"^varchar\((\d+)\)$"

        # check if the type of the field is of type char
        if (match := re.fullmatch(char_type_pattern, field_type)) is not None:

            # extract "n" in char(n) and cast it to an int 
            n = int(match.group(1))

            # get char bytes then decode
            char_bytes = record_bytes[:n]
            char_value = char_bytes.decode('ascii')

            # remove the trailing nulls
            char_value = char_value.rstrip('\x00')

            # store in record_dict
            record_dict[field_name] = char_value

            # advance the pointer for the next field
            record_bytes = record_bytes[n:]
            

        # check if the type of the field is if type varchar
        elif (match := re.fullmatch(varchar_type_pattern, field_type)) is not None:

            # get the length of the varchar value by reading the 1st byte
            varchar_length = int.from_bytes(record_bytes[0:1], 'big')

            # advance the pointer
            record_bytes = record_bytes[1:]

            # read the varchar bytes then decode
            varchar_bytes = record_bytes[:varchar_length]
            varchar_value = varchar_bytes.decode('ascii')

            # store in record_dict
            record_dict[field_name] = varchar_value

            # advance the pointer for the next field
            record_bytes = record_bytes[varchar_length:]

        elif field_type  == "int":

            # read the next 4 bytes as an integer
            int_bytes = record_bytes[:4]
            int_value = int.from_bytes(int_bytes, 'big')

            # store in record_dict
            record_dict[field_name] = int_value

            # advance the pointer for the next field
            record_bytes = record_bytes[4:]

        elif field_type == "float":

            # read the next 4 bytes as an integer
            float_bytes = record_bytes[:4]
            (float_value,) = struct.unpack('>f', float_bytes)

            # store in record_dict
            record_dict[field_name] = float_value

            # advance the pointer for the next field
            record_bytes = record_bytes[4:]

        else:
            raise ValueError('Type is not valid')
    
    return record_dict

def insert_structured_record(table_name, schema_dict, record_dict):
    """
    Encode a structured record and insert it into the heap file.
    """

    record_encoded = encode_record(record_dict, table_name, schema_dict)

    table_schema = schema_dict[table_name]

    table_file_path = table_schema["file_name"]

    # create heap file if it is not created before
    if not os.path.exists(table_file_path):
        create_heap_file(table_file_path)

    insert_record_to_file(table_file_path, record_encoded)



def read_all_structured_records(table_name, schema_dict):
    """
    Retrieve and decode all structured records from the heap file.
    """
    records = []

    table_schema = schema_dict[table_name]

    file_path = table_schema["file_name"]

    records_encoded = get_all_records_from_file(file_path)

    for record_encoded in records_encoded:

        # decode the record then append to records list
        records.append(
                        decode_record(record_encoded, table_name, schema_dict)
                      )

    return records





    




  