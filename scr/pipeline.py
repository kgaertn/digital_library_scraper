from pathlib import Path
from file_handler.file_handler import *
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
    
    articles_complete = pd.DataFrame(columns=['source', 'title', 'authors', 'date',	'year',	'journal_book',	'doi', 'url', 'abstract', 'keywords', 'citation'])
    # Load the default search terms from the XML config file
    current_path = Path(__file__).resolve().parent
    parent_path = current_path.parent
    config_file_path = os.path.join(parent_path, 'config', 'search_query_config.xml')
    
    #config_file = os.path.join(os.path.dirname(__file__), 'config', 'config.xml')
    search_config = Config_File_Handler(config_file_path)

    ieee_data_path = parent_path / 'data'
    file_list = [f.name for f in ieee_data_path.iterdir() if '.csv' in f.name]
    
    #ieee_articles = pd.DataFrame()
    for file in file_list:
        filepath = os.path.join(ieee_data_path, file)
        ieee_file_handler = File_Handler(filepath, sep=',')
        ieee_df = ieee_file_handler.get_ieee_articles()
        #for column in ieee_df.columns:
        ieee_df = ieee_df.applymap(lambda x: x.replace('; ', ', ') if isinstance(x, str) else x)
        articles_complete = pd.concat([articles_complete, ieee_df], axis=0, ignore_index=True)
        #ieee_articles = pd.concat([ieee_articles, ieee_file_handler.get_ieee_articles()], axis=0)

    
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
    
    pubmed_crawler = Pubmed_Scraper(pubmed_query)
    articles_complete = pd.concat([articles_complete, pubmed_crawler.scrape_articles(max_results = max_results) ], axis=0, ignore_index=True) 
    
    acm_crawler = ACM_Scraper(acm_query)
    articles_complete = pd.concat([articles_complete, acm_crawler.scrape_articles(max_results = max_results) ], axis=0, ignore_index=True)
        
    # select only articles within the timespan
    if min_year != None or max_year != None :
        if max_year == None:
            articles_complete = articles_complete[(articles_complete['year'] >= min_year) | (articles_complete['year'].isna())]
        elif min_year == None:
            articles_complete = articles_complete[(articles_complete['year'] <= max_year) | (articles_complete['year'].isna())]
        else:
            articles_complete = articles_complete[((articles_complete['year'] >= min_year) & (articles_complete['year'] <= max_year)) | 
                                                  (articles_complete['year'].isna())]
    
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
    
    articles_complete.to_csv(save_path, index=True, sep=';', index_label='article_id')

    print(f'Saved articles to {file_name}')
    
if __name__ == "__main__":
    main()