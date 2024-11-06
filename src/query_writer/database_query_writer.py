"""
This script generates database queries based on configuration settings 
defined in an INI file and search terms from an XML configuration file.

It serves as the entry point for executing the query generation process, 
loading necessary configurations, and printing the resulting database query.

Dependencies:
    - configparser: For reading INI configuration files.
    - os: For file path manipulations.
    - sys: For modifying the system path.
    - pathlib: For handling file system paths in an object-oriented way.
    - query_writer: For generating queries.
    - file_handler: For handling file-related operations.

Usage:
    Execute this script as a standalone program to generate queries.
"""
from query_writer import *
import sys
import os
from pathlib import Path
import configparser

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.file_handler.file_handler import *  


def main():
    """
    Entry point for generating database queries based on configuration.

    This function reads search parameters from an INI file, loads search 
    terms from an XML configuration file, and generates a query for the 
    specified database, printing the resulting query.
    """
    config = configparser.ConfigParser()
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

