# Digital Library Scraper

### Scrapes information about publications found for specific search queries from Pubmed and ACM, loads a pre-downloaded file from IEEE libary and combines them into one complete CSV file

### Can e.g. scrape title, authors, abstract, keywords, publication year to simplify larger literature research

## Project installation:

1. Clone the repository:  
   ```bash
   git clone https://github.com/kgaertn/digital_library_scraper.git

2. Navigate into the project directory

    cd path_to_project_folder/digital_library_scraper

3. Install dependencies
    pip install -r requirements.txt

## Usage

1. Change search parameters in the config/search_param_config.ini
    - start_year: minimum publication year that will be included in the resulting csv file, set to 'None' if not needed
    - end_year: maximum publication year that will be included in the resulting csv file, set to 'None' if not needed
    - max_results: maximum number of results you want to receive, set to 'None' if not needed
    - search_type: type of search you want to perform, can be Title, Title/Abstract or Fulltext
    - database: the database for creating and printing a search query in the scr/query_writer/database_query_writer.py
    - screening: type of pilot screening to get a sample of randomized publications
    - nr_randomizations: the size of the sample of randomized publications
2. Change search query parameters in the config/search_query_config.xml
    - stores databases and their syntaxes for title, title/abstract and fulltext searches
    - stores the categories and terms for the search
    - terms within categories will be OR connected
    - categories will be AND connected
    - the exclusion category 'Exclusion' will be NOT connected
3. Get articles from the IEEE Xplore library if needed
    - run the scr/query_writer/database_query_writer.py to generate a query for the ieee database
    - copy the search into the ieee search 
    - export the results to a csv file and store in the data folder (NOTE: every csv file in the data folder will later be added to the resulting csv)
4. run the scr/pipeline.py
    - the ieee file will be loaded and added to the new csv file
    - a pubmed query will be created and the resulting publications will be added to the resulting csv file
    - a acm query will be created and the resulting publications will be added to the resulting csv file
    - the resulting csv file will be saved to the output folder
5. run the scr/post_processing.py
    - will add a column for the pilot screening that marks a randomized sample of the predefined size, if screening is not set to None (config file)
    - will mark duplicates based on the doi (NOTE: all duplicates will be marked, and so will publications without a doi, results need to be manually checked)
    - will read all files in the output folder and perform the postprocessing steps

