from query_writer import *
import sys
import os
# Append the root directory (parent directory of 'scr') to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from scr.file_handler.xml_file_handler import *  
from pathlib import Path
import configparser

def main(database):
    config = configparser.ConfigParser()
    # Read the ini file
    config.read('config/search_param_config.ini')
    # Retrieve parameters for the search and convert to the appropriate types
    search_type = config.get('search', 'search_type')

    # Load the default search terms from the XML config file
    current_path = Path(__file__).resolve().parent
    parent_path = current_path.parent.parent
    config_file_path = os.path.join(parent_path, 'config', 'search_query_config.xml')

    #config_file = os.path.join(os.path.dirname(__file__), 'config', 'config.xml')
    search_config = File_Handler(config_file_path)

    query_generator = DatabaseQuery(search_config.categories, search_config.databases)
    query_generator.generate_query(database, search_type)

    ieee_query = query_generator.query
    print('Resulting IEEE Query: \n' + ieee_query)
    
if __name__ == "__main__":
    database = 'IEEE'
    main(database)    

