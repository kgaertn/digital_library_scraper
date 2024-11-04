# Author: Kaya Gärtner
# Date: 16.10.2024
# Description: Create and a single query for the configured search terms and a specified database
#              can be used to create the query for ieee search
 
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
    database = config.get('search', 'manual_database')

    # Load the default search terms from the XML config file
    current_path = Path(__file__).resolve().parent
    parent_path = current_path.parent.parent
    config_file_path = os.path.join(parent_path, 'config', 'search_query_config.xml')
    
    # Retrieve parameters for the search and convert to the appropriate types
    search_config = Config_File_Handler(config_file_path)
    search_types = {}
    for category in search_config.categories:
        search_type = config.get('search', f'{category.lower()}_search_type')
        search_types[f'{category.lower()}'] = search_type
    
    # generate the database query
    query_generator = DatabaseQuery(search_config.categories, search_config.databases)
    query_generator.generate_query(database, search_types)

    search_query = query_generator.query
    print(f'Resulting {database} Query: \n' + search_query)
    
if __name__ == "__main__":
    main()    

