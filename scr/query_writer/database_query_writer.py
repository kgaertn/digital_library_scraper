# Create and a single query for the configured search terms and a specified database
# can be used to create the query for ieee search 
from query_writer import *
import sys
import os
from pathlib import Path
import configparser

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from scr.file_handler.file_handler import *  


def main():
    config = configparser.ConfigParser()
    # Read the ini file
    config.read('config/search_param_config.ini')
    # Retrieve parameters for the search and convert to the appropriate types
    search_type = config.get('search', 'search_type')
    database = config.get('search', 'database')

    # Load the default search terms from the XML config file
    current_path = Path(__file__).resolve().parent
    parent_path = current_path.parent.parent
    config_file_path = os.path.join(parent_path, 'config', 'search_query_config.xml')

    search_config = Config_File_Handler(config_file_path)

    query_generator = DatabaseQuery(search_config.categories, search_config.databases)
    query_generator.generate_query(database, search_type)

    ieee_query = query_generator.query
    print(f'Resulting {database} Query: \n' + ieee_query)
    
if __name__ == "__main__":
    main()    

