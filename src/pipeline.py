"""
Article Scraper and Aggregator

This script is designed to scrape academic articles from various databases based 
on user-defined search parameters specified in a configuration file. The main 
functionality includes reading search criteria from an INI file, generating 
search queries for different databases (IEEE, PubMed, ACM), and aggregating 
the resulting articles into a single DataFrame. The final output is saved as a 
CSV file in the output directory.

Dependencies:
- pandas: for handling data in DataFrame format
- configparser: for reading configuration files
- pathlib: for handling file paths in a cross-platform manner
- datetime: for timestamping output files
- Custom modules:
  - file_handler.file_handler: Contains functions for reading and processing files.
  - scrapers.acm_scraper: Provides functionality to scrape articles from the ACM database.
  - scrapers.pubmed_scraper: Provides functionality to scrape articles from the PubMed database.
  - query_writer.query_writer: Manages the generation of search queries.

Usage:
1. Ensure that the required configuration files ('search_param_config.ini' and 
   'search_query_config.xml') are correctly set up.
2. Run the script. The aggregated articles will be saved in the 'output' 
   directory with a timestamped filename.

"""

from pathlib import Path
from file_handler.file_handler import *
from scrapers.acm_scraper import *
from scrapers.pubmed_scraper import *
from query_writer.query_writer import *
from datetime import datetime
import configparser

def get_search_types(search_config: Config_File_Handler, config: configparser.ConfigParser) -> dict[str, str]:
    """
    Extract search types for each category from the configuration file.

    Args:
        search_config (Config_File_Handler): Handler for the search configuration file.
        config (configparser.ConfigParser): Parsed INI configuration settings.

    Returns:
        dict[str, str]: A dictionary mapping each search category to its search type.
    """
    search_types = {}
    for category in search_config.categories:
        search_type = config.get('search', f'{category.lower()}_search_type')
        search_types[f'{category.lower()}'] = search_type
    return search_types

def add_ieee_data(parent_path: Path, df_to_concat: pd.DataFrame) -> pd.DataFrame:
    """
    Load IEEE articles from CSV file(s) in the input directory and concatenate them
    to the existing DataFrame.

    Args:
        parent_path (Path): Path to the parent directory containing the input files.
        df_to_concat (pd.DataFrame): DataFrame to which IEEE data will be concatenated.

    Returns:
        pd.DataFrame: Combined DataFrame with additional IEEE articles.
    
    Note: 
        all files in the input folder will be loaded and concatenated
    """
    ieee_data_path = parent_path / 'input'
    file_list = [f.name for f in ieee_data_path.iterdir() if '.csv' in f.name]

    for file in file_list:
        filepath = os.path.join(ieee_data_path, file)
        ieee_file_handler = File_Handler(filepath, sep=',')
        ieee_df = ieee_file_handler.get_ieee_articles()
        ieee_df = ieee_df.map(lambda x: x.replace('; ', ', ') if isinstance(x, str) else x)
        df_to_concat = pd.concat([df_to_concat, ieee_df], axis=0, ignore_index=True)
    return df_to_concat

def generate_queries(search_config: Config_File_Handler, search_types: dict[str, str]):
    """
    Generate search queries for databases other than IEEE based on search types.

    Args:
        search_config (Config_File_Handler): Handler for the search configuration file.
        search_types (dict[str, str]): Dictionary of search types by category.

    Returns:
        tuple: A tuple containing the PubMed and ACM queries.
    """
    for database in search_config.databases:
        if database != 'IEEE':
            query_generator = DatabaseQuery(search_config.categories, search_config.databases)
            query_generator.generate_query(database, search_types)
            if database == 'PubMed':
                pubmed_query = query_generator.query
            elif database == 'ACM':
                acm_query = query_generator.query
    return pubmed_query, acm_query

def select_within_timespan(config: str, data: pd.DataFrame) -> pd.DataFrame:
    """
    Filter articles within a specified publication year range.

    Args:
        config (configparser.ConfigParser): Configuration settings containing the year range.
        data (pd.DataFrame): DataFrame with articles to be filtered.

    Returns:
        pd.DataFrame: DataFrame filtered by publication year.
    """
    min_year = config.get('search', 'start_year')   
    min_year = None if min_year == 'None' else int(min_year)
    max_year = config.get('search', 'end_year')   
    max_year = None if max_year == 'None' else int(max_year)
    
    # select only articles within the timespan
    if min_year != None or max_year != None :
        if max_year == None:
            data = data[(data['year'] >= min_year) | (data['year'].isna())]
        elif min_year == None:
            data = data[(data['year'] <= max_year) | (data['year'].isna())]
        else:
            data = data[((data['year'] >= min_year) & (data['year'] <= max_year)) | 
                                                  (data['year'].isna())]
    
    return data

def save_results(files_path: str, data: pd.DataFrame):
    """
    Save the aggregated articles to a CSV file with a timestamp in the filename.

    Args:
        files_path (str): Directory where the resulting CSV file should be saved.
        resulting_df (pd.DataFrame): DataFrame containing the aggregated data.

    Returns:
        None
    """
    current_timestamp = datetime.now()
    formatted_timestamp = current_timestamp.strftime("%Y-%m-%d_%H%M%S")   
    
    file_name = f'{formatted_timestamp}_complete_articles.csv'
    save_path = os.path.join(files_path, file_name)

    data.to_csv(save_path, index=True, sep=';', index_label='article_id')

    print(f'Saved articles to {file_name}')
        
def main():
    """
    Main function to orchestrate the scraping and saving of academic articles 
    based on specified search parameters in a configuration file.

    This function reads search parameters from an INI configuration file, 
    retrieves articles from various databases (IEEE, PubMed, ACM), 
    concatenates the results into a single DataFrame, filters articles 
    based on year parameters, and saves the complete articles to a CSV file.

    The process involves:
        - Reading configuration settings from 'config/search_param_config.ini'
        - Loading search terms from 'config/search_query_config.xml'
        - Scraping articles from specified databases
        - Filtering the articles by publication year
        - Saving the results to a CSV file in the output directory
    """
    databases_to_search = ["PubMed"]
    #databases_to_search = ["PubMed", "IEEE", "ACM"]
    # Read the ini config file
    config = configparser.ConfigParser()
    config.read('config/search_param_config.ini')

    # Load the default search terms from the XML config file
    current_path = Path(__file__).resolve().parent
    parent_path = current_path.parent
    config_file_path = os.path.join(parent_path, 'config', 'search_query_config.xml')
    
    search_config = Config_File_Handler(config_file_path)
    
    search_types = get_search_types(search_config, config)

    articles_complete = pd.DataFrame(columns=['source', 'title', 'authors', 'date',	'year',	'journal_book',	'doi', 'pmid', 'url', 'abstract', 'keywords', 'citation'])
    max_results = config.get('search', 'max_results')   
    max_results = None if max_results == 'None' else int(max_results)
    
    if "IEEE" in databases_to_search:
        articles_complete = add_ieee_data(parent_path, articles_complete)
    
    # generate queries for the other databases and fetch the articles 
    pubmed_query, acm_query = generate_queries(search_config, search_types)
    
    if "PubMed" in databases_to_search:    
        pubmed_crawler = Pubmed_Scraper(pubmed_query)
        articles_complete = pd.concat([articles_complete, pubmed_crawler.scrape_articles(max_results = max_results) ], axis=0, ignore_index=True) 
    
    if "ACM" in databases_to_search:
        acm_crawler = ACM_Scraper(acm_query)
        articles_complete = pd.concat([articles_complete, acm_crawler.scrape_articles(max_results = max_results) ], axis=0, ignore_index=True)
          
    articles_complete = select_within_timespan(config, articles_complete)
    articles_complete.reset_index(drop=True, inplace=True)
    
    # create output folder if it doesn't exist
    output_dir = os.path.join(parent_path, 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    save_results(output_dir, articles_complete)
    
if __name__ == "__main__":
    main()