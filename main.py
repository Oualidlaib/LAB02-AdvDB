from dotenv import load_dotenv
import os
import json
from query_processor import execute_query

# Load the .env file from the current working direcotory
load_dotenv()


# read the schema from the enviroment variable file
schema_file_path = os.getenv("SCHEMA_PATH")


if schema_file_path is None:
    raise ValueError("SCHEMA_PATH is missing in the .env file")


# parse schema JSON file into a list of dictionaries
with open(schema_file_path) as schema_file:
    schema = json.load(schema_file)

# convert schema to a dictionary for lookup faster than looping through a list `O(1) in Average case`
schema_dict = {table["table_name"]: table for table in schema}


def main():

    # the number of the query
    query_count = 0

    print("\nWelcome to my simple and minimalist RDBMS Query Interface.")
    print("Type your query and press ENTER. Type 'EXIT' to quit.\n")
    print("VERY IMPORTANT NTOE : YOU HAVE TO END YOUR QUERY WITH A SEMI-COLON")
    print("-" * 40)
    
    while True:
        try:
            # Prompt the user for input
            query = input("LaibSQL> ")
            
            if not query.strip():
                continue

            # Check for exit command
            if query.strip().upper() == 'EXIT':
                print("Goodbye!")
                break
                
            # Increment the query number
            query_count += 1
            result_dict = execute_query(query, schema_dict)
            
            # Print the result to the console
            print("\n--- Execution Result ---")
            print(result_dict)
            print("------------------------")
            
        except Exception as e:
            print(e)

main()