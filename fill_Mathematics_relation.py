import csv
from parser import parser

file_path = 'MOCK_DATA_Mathematics.csv'

with open(file_path, mode='r', encoding='utf-8') as f:
    
    reader = csv.DictReader(f)
    
    for row in reader:

        query = f"INSERT INTO Mathematics VALUES ({row['id']}, '{row['book_name']}', '{row['author']}', {row['price']});"

        # Parse the input
        ast = parser.parse(query)

        if ast is not None:
            
            # Semantic Analysis
            ast.analyze()

            ast.evaluate()