from pathlib import Path
from file_handler.xml_file_handler import *
from file_handler.ieee_file_handler import *
from scrapers.acm_scraper import *
from scrapers.pubmed_scraper import *
from query_writer.query_writer import *
from datetime import datetime
import configparser


def main():
    # Create a ConfigParser object
    config = configparser.ConfigParser()
    # Read the ini file
    config.read('config/search_param_config.ini')
    # Retrieve parameters for the search and convert to the appropriate types
    min_year = config.get('search', 'start_year')   
    min_year = None if min_year == 'None' else int(min_year)
    max_year = config.get('search', 'end_year')   
    max_year = None if max_year == 'None' else int(max_year)
    max_results = config.get('search', 'max_results')   
    max_results = None if max_results == 'None' else int(max_results)
    search_type = config.get('search', 'search_type')
    
    # Load the default search terms from the XML config file
    current_path = Path(__file__).resolve().parent
    parent_path = current_path.parent
    config_file_path = os.path.join(parent_path, 'config', 'search_query_config.xml')
    
    #config_file = os.path.join(os.path.dirname(__file__), 'config', 'config.xml')
    search_config = File_Handler(config_file_path)

    ieee_data_path = parent_path / 'data'
    file_list = [f.name for f in ieee_data_path.iterdir() if '.csv' in f.name]
    
    ieee_articles = pd.DataFrame()
    for file in file_list:
        filepath = os.path.join(ieee_data_path, file)
        ieee_file_handler = IeeeFileHandler(filepath)
        ieee_articles = pd.concat([ieee_articles, ieee_file_handler.get_articles()], axis=0)

    
    acm_query = None
    pubmed_query = None
    for database in search_config.databases:
        # Generate the query based on the selected database
        if database != 'IEEE':
            query_generator = DatabaseQuery(search_config.categories, search_config.databases)
            query_generator.generate_query(database, search_type)
            if database == 'PubMed':
                pubmed_query = query_generator.query
            elif database == 'ACM':
                acm_query = query_generator.query
    
    # TODO: check how to include all 
    pubmed_crawler = Pubmed_Scraper(pubmed_query)
    pubmed_articles = pubmed_crawler.scrape_articles(max_results = max_results)   
    
    # TODO: check how to avoid getting blocked 
    acm_crawler = ACM_Scraper(acm_query)
    acm_articles = acm_crawler.scrape_articles(max_results = max_results)
    
    articles_complete = pd.concat([pubmed_articles, acm_articles, ieee_articles], axis=0, ignore_index=True)
    
    # select only articles within the timespan
    if min_year != None or max_year != None :
        if max_year == None:
            articles_complete = articles_complete[(articles_complete['year'] >= min_year) | (articles_complete['year'].isna())]
        elif min_year == None:
            articles_complete = articles_complete[(articles_complete['year'] <= max_year) | (articles_complete['year'].isna())]
        else:
            articles_complete = articles_complete[((articles_complete['year'] >= min_year) & (articles_complete['year'] <= max_year)) | 
                                                  (articles_complete['year'].isna())]
    
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
    
    articles_complete.to_csv(save_path, index=True, sep=';')

    print(f'Saved articles to {file_name}')
    
if __name__ == "__main__":
    main()

# TODO
# load xml config file
# create queries for all databases
# load ieee file
# scrape pubmed & acm