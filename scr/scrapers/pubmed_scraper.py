"""
PubMed Scraper Script

This script provides a PubMed scraper implemented in the Pubmed_Scraper class. 
The scraper allows users to search for articles in the PubMed database based on a 
specified query. It retrieves relevant data including titles, authors, publication 
dates, abstracts, and more from the search results. 

Key Features:
- Search PubMed for articles based on a user-defined query.
- Handle server errors with retry mechanisms.
- Fetch detailed information about articles in batches.
- Extract specific information such as DOI, PMID, keywords, and full abstracts.

Usage:
1. Instantiate the Pubmed_Scraper class with a search query and optional max_results.
2. Call the scrape_articles method to fetch and return a DataFrame of articles.

Example:
    pubmed_crawler = Pubmed_Scraper(query='machine learning')
    articles_df = pubmed_crawler.scrape_articles(max_results=100)

Dependencies:
- requests: For making HTTP requests to the PubMed API.
- xml.etree.ElementTree: For parsing XML responses.
- pandas: For managing and organizing article data into a DataFrame.
- random, time, re: For handling delays and regular expressions in parsing.
- sys and os: For path manipulation.
- scr.color_logger: For logging purposes (custom logger).

"""
import requests
from xml.etree import ElementTree as ET
import pandas as pd
import time
import random
import re

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from scr.color_logger import logger

class Pubmed_Scraper:
    def __init__(self, query:str='machine learning', max_results:int|None = None):
        """
        Initializes the Pubmed_Scraper with a search query and optional maximum results.

        Args:
            query (str): The search term to query the PubMed database (default is 'machine learning').
            max_results (int, optional): The maximum number of results to retrieve (default is None).

        Notes:
            - The class initializes URLs for searching and fetching articles from the PubMed API.
            - An auto-incrementing ID is set to keep track of articles.
        """
        self.query = query
        self.auto_id = 1
        self.articles = []
        self.max_results = max_results
        # Set the start URL based on the query
        self.search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        self.fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        
    def fetch_with_retries(self, url: str, params: dict[str, str], retries: int = 3, delay: int = 5) -> requests.Response:
        """
        Fetches data from a specified URL, retrying the request on server errors (500) 
        up to a defined number of times, with a delay between attempts.

        Args:
            url (str): The URL to fetch data from.
            params (dict[str, str]): Query parameters to include in the request.
            retries (int, optional): The maximum number of retry attempts in case of 
                server errors (default is 3).
            delay (int, optional): The wait time (in seconds) between retries (default is 5).

        Returns:
            requests.Response: The HTTP response received from the server.

        Raises:
            requests.exceptions.HTTPError: If the server returns an error other than a 500 status.
            Exception: If all retry attempts fail with a server error (500).

        Notes:
            - This function retries only for HTTP 500 errors.
            - If any other HTTP error occurs, it is raised immediately without retries.
        """
        for attempt in range(retries):
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                return response
            except requests.exceptions.HTTPError as e:
                if response.status_code == 500:
                    print(f"Attempt {attempt + 1} failed with 500 error. Retrying after {delay} seconds...")
                    time.sleep(delay)
                else:
                    raise e
        raise Exception("Failed after multiple retries")

    def fetch_data_with_retry(self, url: str, params: dict[str, str], retries: int = 5, backoff_factor: int = 1) -> requests.Response:
        """
            Fetches data from a specified URL, retrying the request on HTTP errors 
            with exponential backoff.

            Args:
                url (str): The URL to fetch data from.
                params (dict[str, str]): Query parameters to include in the request.
                retries (int, optional): The maximum number of retry attempts in case of 
                    HTTP errors (default is 5).
                backoff_factor (int, optional): Factor by which the wait time increases
                    after each retry, calculated as `backoff_factor * (2 ** attempt)`. 
                    Defaults to 1.

            Returns:
                requests.Response: The HTTP response received from the server on a successful request.

            Raises:
                requests.exceptions.HTTPError: If the server returns a non-success status code 
                    after exhausting all retry attempts.

            Notes:
                - The function uses exponential backoff for retry delays, which increases the 
                wait time after each failed attempt.
                - The maximum wait time after the last retry is `backoff_factor * (2 ** (retries - 1))`.
        """
        for attempt in range(retries):
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                return response
            except requests.exceptions.HTTPError as e:
                if attempt < retries - 1:
                    wait_time = backoff_factor * (2 ** attempt)  # Exponential backoff
                    print(f"Error {e}, retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"Failed after {retries} attempts.")
                    raise  # Re-raise the last exception after all retries fail
   
    def parse(self):
        """
        Parses the PubMed database to search for articles based on the specified query,
        retrieves the total number of results, and fetches details for the articles in batches.

        This function performs the following steps:
        1. Searches the PubMed database for the given query and retrieves the total count of results.
        2. Iterates through the results in batches, fetching article IDs.
        3. Fetches detailed information for the articles in batches to avoid overloading the server.

        Returns:
            None: This function does not return a value but prints status messages and
            results to the console.

        Notes:
            - The batch size for fetching articles defaults to the maximum results specified
            or 200 if that is greater.
            - Random sleep times are introduced between requests to avoid hitting the server
            too quickly.
        """
        
        batch_size = self.max_results if (self.max_results != None) and (self.max_results < 200) else 200
        
        # setup the parameters for the PubMed API
        search_params = {
            'db': 'pubmed',
            'term': self.query,
            'retmode': 'xml',
            'retmax': batch_size,
        }
        
        # perform the search request
        search_response = self.fetch_with_retries(self.search_url, params=search_params)
        if self.request_error(search_response.text):
            return # exit if there was an error in the request
        
        # Parse the search results XML        
        search_tree = ET.fromstring(search_response.content)
        results_num = int(search_tree.find('.//Count').text)
        max_results = self.max_results if (self.max_results != None) else results_num
        print(f"Pubmed: total results found: {results_num}")

        all_id_list = []
        # Paginate through the results to fetch article IDs
        for start in range(0, max_results, batch_size):
            search_params['retstart'] = start  # Set the starting point for each batch
            
            # fetch the current batch of articles
            search_response = self.fetch_with_retries(self.search_url, params=search_params)
            search_tree = ET.fromstring(search_response.content)
            
            # Extract article IDs
            id_list = [id_elem.text for id_elem in search_tree.findall('.//Id')]
            all_id_list.extend(id_list) 
            
            # sleep to avoid overwhelming the server
            sleep_time = random.randint(1, 2)
            time.sleep(sleep_time)
            
        print(f"Fetching details for {len(all_id_list)} articles...")
        
        # Fetch article details in batches to avoid overloading the request
        for start in range(0, len(all_id_list), batch_size):
            batch_ids = all_id_list[start:start + batch_size]
            fetch_params = {
                'db': 'pubmed',
                'id': ','.join(batch_ids),
                'retmode': 'xml'
            }
            
            # Fetch the details for the current batch of articles
            fetch_response = self.fetch_data_with_retry(self.fetch_url, params=fetch_params)
            fetch_tree = ET.fromstring(fetch_response.content)

            self.extract_data_from_articles(fetch_tree)

            print('Next Batch')
            # Sleep to manage request frequency
            sleep_time = random.randint(1,10)
            time.sleep(sleep_time)
        

    def request_error(self, xml_string: str) -> bool:
        """
        Checks for request errors in the provided XML response string from the PubMed database.

        This function looks for specific error messages indicating that the request to 
        the PubMed API has failed, and extracts details about the error if available.

        Args:
            xml_string (str): The XML response string from the PubMed API.

        Returns:
            bool: True if an error is detected in the response, False otherwise.

        Notes:
            - If an error is found, a warning is logged with the details of the error.
            - This function specifically looks for the phrase "An error occurred while processing request"
            in the XML string to determine if a request error occurred.
        """
        if "An error occurred while processing request" in xml_string:
            # Regular expression to match text after the first occurrence of "Details:"
            match = re.search(r'Details:\s*(.*?)(?:</|$)', xml_string)

            # Extract and print the result if found
            if match:
                result = match.group(1)
                logger.warning(f"Pubmed Search request failed: {result}")
            else:
                logger.warning(f"Pubmed Search request failed: No 'Details' found.")
            
            return True
        else:
            return False
        
    def extract_data_from_articles(self, fetch_tree: ET.Element):
        """
        Extracts relevant data from articles in the provided XML tree from PubMed.

        This function iterates over the fetched XML data, extracting information from both
        `PubmedArticle` and `PubmedBookArticle` elements. It logs the scraping progress and
        stores the extracted information in a list of articles.

        Args:
            fetch_tree (ElementTree): The XML tree containing the fetched articles.

        Returns:
            None: This function does not return a value but appends extracted articles
            to the instance's articles list.

        Notes:
            - The maximum number of articles to extract can be controlled using the
            `max_results` attribute.
            - The `auto_id` attribute is incremented with each extracted article to
            ensure unique identification.
        """
        # iterate over each article and extract the needed information
        for res in fetch_tree.findall('.//PubmedArticle'):

            if self.max_results == None or self.auto_id <= self.max_results:
                logger.info(f'Scraping PubMed: Article Nr. {self.auto_id} of {self.max_results}')
                date, year = self.extract_date(res)
                #url = self.extract_url(res)
                item = {
                #'id': self.auto_id,  # Assign the current ID
                'source': 'PubMed',
                'title': self.extract_title(res),
                'authors': self.extract_authors(res),
                'date' : date,
                'year': year,
                'journal_book': self.extract_journal(res), 
                'doi': self.extract_doi(res),
                'url' : self.extract_url(res),
                'abstract': self.extract_full_abstract(res),
                'keywords': self.extract_keywords(res),
                'pmid' : self.extract_pmid(res)
                }
                
                self.articles.append(item)
                self.auto_id += 1
        # iterate over each book and extract the needed information
        for res in fetch_tree.findall('.//PubmedBookArticle'):
            
            if self.max_results == None or self.auto_id <= self.max_results:
                logger.info(f'Scraping PubMed: Article Nr. {self.auto_id} of {self.max_results}')
                date, year = self.extract_date(res)
                item = {
                'source': 'PubMed',
                'title': self.extract_title(res),
                'authors': self.extract_authors(res),
                'date' : date,
                'year': year,
                'journal_book': self.extract_journal(res), 
                'doi': self.extract_doi(res),
                'url' : self.extract_url(res),
                'abstract': self.extract_full_abstract(res),
                'keywords': self.extract_keywords(res),
                'pmid' : self.extract_pmid(res)
                }
                
                self.articles.append(item)
                self.auto_id += 1
        
    #region EXTRACTION FUNCTIONS
    """
        The functions below extract the detailed information from the search result.

        Args:
            res (Element): The XML element representing an article.
            url (str): The specific articles url

        Returns:
            str|int: The detail as string, or int (e.g. in case of year) or None if not found.
        """
    def extract_pmid(self, res:ET.Element) -> str | None:
        """
        Extracts the PubMed ID (PMID) from the given article element.
        """
        return res.find('.//PMID').text if res.find('.//PMID') is not None else None
        
    def extract_title(self, res:ET.Element) -> str | None:
        """
        Extracts the title from the given article element.
        """
        title = res.find('.//ArticleTitle').text if res.find('.//ArticleTitle') is not None else None
        return title
    
    def extract_authors(self, res:ET.Element) -> str | None:
        """
        Extracts the authors from the given article element.
        """
        res_list = [
                f"{author.find('.//ForeName').text} {author.find('.//LastName').text}" 
                for author in res.findall('.//Author')
                if author.find('.//ForeName') is not None and author.find('.//LastName') is not None
            ]
        return ', '.join(res_list) if res_list != None else None
    
    def extract_date(self, res:ET.Element) -> str | None:
        """
        Extracts the date from the given article element.
        """
        publication_date = res.find('.//PubDate')
        if publication_date is not None:
            month = publication_date.find('.//Month').text if publication_date.find('.//Month') is not None else None
            year = int(publication_date.find('.//Year').text) if publication_date.find('.//Year') is not None else None
            date = f"{month} {year}" if month is not None and year is not None else None
        else:
            date = None
            year = None
        return date, year

    def extract_type(self, res:ET.Element) -> str | None:
        """
        Extracts the publication type from the given article element.
        """
        return res.find('.//PublicationType').text
        
    def extract_keywords(self, res:ET.Element) -> str | None:
        """
        Extracts the keywords from the given article element.
        """
        res_list = [
                res_part.findall('.//Keyword')   
                for res_part in res.findall('.//KeywordList')
            ]
        keywords = [f"{res_part.text}" for res_part in res_list[0]] if res_list else None

        return ', '.join(keywords) if keywords != None else None

    def extract_journal(self, res:ET.Element) -> str | None:
        """
        Extracts the journal name from the given article element.
        """
        journal = res.find('.//Journal/Title').text if res.find('.//Journal/Title') is not None else None
        return journal

    def extract_doi(self, res:ET.Element) -> str | None:
        """
        Extracts the doi from the given article element.
        """
        return res.find('.//ArticleId[@IdType="doi"]').text if res.find('.//ArticleId[@IdType="doi"]') is not None else None
    
    def extract_url(self, res:ET.Element) -> str | None:
        """
        Extracts the url from the given article element.
        """
        href = res.find('.//ArticleId[@IdType="pubmed"]').text if res.find('.//ArticleId[@IdType="pubmed"]') is not None else None
        return f"https://pubmed.ncbi.nlm.nih.gov/{href}/" 

    def extract_full_abstract(self, article:ET.Element) -> str | None:
        """
        Extracts the abstract from the given article element.
        """
        abstract_list = []
        for abstract_part in article.findall('.//Abstract'):
            for elem in abstract_part.iter():
                if elem.tag in ['AbstractText', 'sup', 'i', 'strong.sub-title']:
                    if 'Label' in elem.attrib:
                        label = elem.attrib['Label'].title()
                        abstract_list.append(f"{label}: ")
                    text = elem.text or ''
                    abstract_list.append(text)
                if elem.tail:
                    abstract_list.append(elem.tail)
        return ''.join(abstract_list)
    #endregion EXTRACTION FUNCTIONS
    
    def scrape_articles(self, max_results = None):
        self.max_results = max_results
        self.parse()
        return pd.DataFrame(self.articles)

def main():
    """
    Main function to execute the Pubmed_Scraper alone and retrieve articles based on a specific query.

    This function initializes the Pubmed_Scraper with a predefined complex query, scrapes 
    articles from the Pubmed Library, and stores the results in a DataFrame.
    """
    query = """(Movement[Title/Abstract] OR Kinesiology[Title/Abstract] OR Physiotherapy[Title/Abstract] OR "Physical Therapy"[Title/Abstract] 
            OR Kinetic[Title/Abstract] OR Kinematic[Title/Abstract] OR Biomechanic[Title/Abstract] OR "Motor Control"[Title/Abstract]) 
            AND ("3D Movement Measurement*"[Title/Abstract] OR "3D Motion"[Title/Abstract] OR "Motion capture"[Title/Abstract] OR EMG[Title/Abstract] 
            OR Electromyography[Title/Abstract] OR "Wearable Sensors"[Title/Abstract] OR "Motion analysis"[Title/Abstract] OR "Multimodal"[Title/Abstract] 
            OR IMU[Title/Abstract] OR "inertial measurement unit"[Title/Abstract] OR "ground reaction force"[Title/Abstract] OR "GRF"[Title/Abstract]) 
            AND ("Pattern recognition"[Title/Abstract] OR "Dimension* reduction"[Title/Abstract] OR "Data Science"[Title/Abstract] 
            OR "Time series analysis"[Title/Abstract] OR Clustering[Title/Abstract] OR Classifier[Title/Abstract] OR prediction[Title/Abstract] 
            OR detection[Title/Abstract] OR "Machine Learning"[Title/Abstract] OR "Neural Network*"[Title/Abstract] OR "Deep Learning"[Title/Abstract]) 
            NOT (Gait[Title/Abstract] OR robot*[Title/Abstract] OR prosthe*[Title/Abstract])
"""
    
    pubmed_crawler = Pubmed_Scraper(query = query)
    pubmed_articles = pubmed_crawler.scrape_articles()
    
    print('')
    
if __name__ == "__main__":
    main()
