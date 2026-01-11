from parser import parser

if __name__ == "__main__":
    
    while(True):
        
        data = input('LaibSQL>')

        # Parse the input
        ast = parser.parse(data)

        if ast is not None:
            
            # Semantic Analysis
            ast.analyze()

            print(ast.evaluate())
    

    

