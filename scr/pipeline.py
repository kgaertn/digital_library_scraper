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

# TODO: split the main function into smaller chunks to enhance readability
def select_within_timespan(config: str, data: pd.DataFrame) -> pd.DataFrame:
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
    # Create a ConfigParser object
    config = configparser.ConfigParser()
    # Read the ini file
    config.read('config/search_param_config.ini')
    # Retrieve parameters for the search and convert to the appropriate types
    #min_year = config.get('search', 'start_year')   
    #min_year = None if min_year == 'None' else int(min_year)
    #max_year = config.get('search', 'end_year')   
    #max_year = None if max_year == 'None' else int(max_year)
    max_results = config.get('search', 'max_results')   
    max_results = None if max_results == 'None' else int(max_results)
    
    #search_type = config.get('search', 'search_type')
    
    articles_complete = pd.DataFrame(columns=['source', 'title', 'authors', 'date',	'year',	'journal_book',	'doi', 'pmid', 'url', 'abstract', 'keywords', 'citation'])
    # Load the default search terms from the XML config file
    current_path = Path(__file__).resolve().parent
    parent_path = current_path.parent
    config_file_path = os.path.join(parent_path, 'config', 'search_query_config.xml')
    
    search_config = Config_File_Handler(config_file_path)
    
    search_types = {}
    for category in search_config.categories:
        search_type = config.get('search', f'{category.lower()}_search_type')
        search_types[f'{category.lower()}'] = search_type

    # create a dataframe from the ieee file
    ieee_data_path = parent_path / 'input'
    file_list = [f.name for f in ieee_data_path.iterdir() if '.csv' in f.name]

    for file in file_list:
        filepath = os.path.join(ieee_data_path, file)
        ieee_file_handler = File_Handler(filepath, sep=',')
        ieee_df = ieee_file_handler.get_ieee_articles()
        ieee_df = ieee_df.map(lambda x: x.replace('; ', ', ') if isinstance(x, str) else x)
        articles_complete = pd.concat([articles_complete, ieee_df], axis=0, ignore_index=True)
    
    # generate queries for the other databases and fetch the articles 
    acm_query = None
    pubmed_query = None
    for database in search_config.databases:
        # Generate the query based on the selected database
        if database != 'IEEE':
            query_generator = DatabaseQuery(search_config.categories, search_config.databases)
            query_generator.generate_query(database, search_types)
            if database == 'PubMed':
                pubmed_query = query_generator.query
            elif database == 'ACM':
                acm_query = query_generator.query
    
    pubmed_crawler = Pubmed_Scraper(pubmed_query)
    articles_complete = pd.concat([articles_complete, pubmed_crawler.scrape_articles(max_results = max_results) ], axis=0, ignore_index=True) 
    
    #acm_crawler = ACM_Scraper(acm_query)
    #articles_complete = pd.concat([articles_complete, acm_crawler.scrape_articles(max_results = max_results) ], axis=0, ignore_index=True)
        
    # select only articles within the timespan
    #if min_year != None or max_year != None :
    #    if max_year == None:
    #        articles_complete = articles_complete[(articles_complete['year'] >= min_year) | (articles_complete['year'].isna())]
    #    elif min_year == None:
    #        articles_complete = articles_complete[(articles_complete['year'] <= max_year) | (articles_complete['year'].isna())]
    #    else:
    #        articles_complete = articles_complete[((articles_complete['year'] >= min_year) & (articles_complete['year'] <= max_year)) | 
    #                                              (articles_complete['year'].isna())]
    
    articles_complete = select_within_timespan(config, articles_complete)
    # Reset the index
    articles_complete.reset_index(drop=True, inplace=True)
    
    # create output folder if it doesn't exist
    output_dir = os.path.join(parent_path, 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
 
     # Get the current timestamp
    current_timestamp = datetime.now()

    # Format the timestamp (optional)
    formatted_timestamp = current_timestamp.strftime("%Y-%m-%d_%H%M%S")   
    
    file_name = f'{formatted_timestamp}_complete_articles.csv'
    save_path = os.path.join(output_dir, file_name)
    
    # save to csv file
    articles_complete.to_csv(save_path, index=True, sep=';', index_label='article_id')

    print(f'Saved articles to {file_name}')
    
if __name__ == "__main__":
    main()