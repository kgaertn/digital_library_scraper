import requests
from xml.etree import ElementTree as ET
import logging
import pandas as pd
import time
import random
import re

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from scr.color_logger import logger

#logging.basicConfig(level=logging.INFO)

class Pubmed_Scraper:
    def __init__(self, query='machine learning', max_results = None):
        self.query = query
        self.auto_id = 1
        self.articles = []
        self.max_results = max_results
        # Setze die Start-URL basierend auf der Abfrage
        self.search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        self.fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        
    def fetch_with_retries(self, url, params, retries=3, delay=5):
        for attempt in range(retries):
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()  # Raise an error for bad HTTP codes
                return response
            except requests.exceptions.HTTPError as e:
                if response.status_code == 500:
                    print(f"Attempt {attempt + 1} failed with 500 error. Retrying after {delay} seconds...")
                    time.sleep(delay)
                else:
                    raise e
        raise Exception("Failed after multiple retries")

    def fetch_data_with_retry(self, url, params, retries=5, backoff_factor=1):
        for attempt in range(retries):
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                return response  # Exit on success
            except requests.exceptions.HTTPError as e:
                if attempt < retries - 1:
                    wait_time = backoff_factor * (2 ** attempt)  # Exponential backoff
                    print(f"Error {e}, retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"Failed after {retries} attempts.")
                    raise  # Re-raise the last exception after all retries fail

    def fetch_missing_articles(self, missing_ids):
        if not missing_ids:
            print("No missing articles to fetch.")
            return
        
        print(f"Fetching missing articles: {missing_ids}")
        # Split into batches to avoid overloading the request
        batch_size = 200  # You can adjust this as needed
        for start in range(0, len(missing_ids), batch_size):
            batch_ids = missing_ids[start:start + batch_size]
            fetch_params = {
                'db': 'pubmed',
                'id': ','.join(batch_ids),
                'retmode': 'xml'
            }
            
            try:
                fetch_response = self.fetch_data_with_retry(self.fetch_url, params=fetch_params)
                fetch_tree = ET.fromstring(fetch_response.content)
                
                articles_fetched = fetch_tree.findall('.//PubmedArticle')
                print(f"Fetched {len(articles_fetched)} articles for IDs: {batch_ids}")

                self.extract_data_from_articles(fetch_tree, self.max_results)
                
            except Exception as e:
                print(f"Error fetching articles: {e}")
    
    def parse(self):
        # Initial search to get the total number of results
        
        batch_size = self.max_results if (self.max_results != None) and (self.max_results < 200) else 200
        
        search_params = {
            'db': 'pubmed',
            'term': self.query,
            'retmode': 'xml',
            'retmax': batch_size,
        }
        
        search_response = self.fetch_with_retries(self.search_url, params=search_params)
        if self.request_error(search_response.text):
            return
        
        #search_response = requests.get(self.search_url, params=search_params)
        search_tree = ET.fromstring(search_response.content)
        results_num = int(search_tree.find('.//Count').text)
        max_results = self.max_results if (self.max_results != None) else results_num
        # Get total number of results
        print(f"Pubmed: total results found: {results_num}")

        # Initialize variables
        all_id_list = []
        #missing_ids_set = []
        # Paginate through the results
        for start in range(0, max_results, batch_size):
            search_params['retstart'] = start  # Set the starting point for each batch
            #search_response = requests.get(self.search_url, params=search_params)
            search_response = self.fetch_with_retries(self.search_url, params=search_params)
            search_tree = ET.fromstring(search_response.content)
            
            # Extract article IDs
            id_list = [id_elem.text for id_elem in search_tree.findall('.//Id')]
            all_id_list.extend(id_list)  # Append to the list of all article IDs
            sleep_time = random.randint(1, 2)
            time.sleep(sleep_time)
        # Now we have all article IDs, we can fetch the details
        print(f"Fetching details for {len(all_id_list)} articles...")
        
        # Split into batches to avoid overloading the request
        for start in range(0, len(all_id_list), batch_size):
            batch_ids = all_id_list[start:start + batch_size]
            fetch_params = {
                'db': 'pubmed',
                'id': ','.join(batch_ids),
                'retmode': 'xml'
            }
            
            fetch_response = self.fetch_data_with_retry(self.fetch_url, params=fetch_params)
            #fetch_response = requests.get(self.fetch_url, params=fetch_params)
            fetch_tree = ET.fromstring(fetch_response.content)

            self.extract_data_from_articles(fetch_tree)
            #missing_ids_to_append = self.check_missing_articles(fetch_tree, batch_ids)
            #if missing_ids_to_append is not None:
            #    missing_ids_set.append(missing_ids_to_append)

            print('Next Batch')
            sleep_time = random.randint(1,10)
            time.sleep(sleep_time)
        
        #missing_ids = [str(missing_id) for article_set in missing_ids_set for missing_id in article_set]

# Output the result
        #self.fetch_missing_articles(missing_ids)
        #print('All done')


    def request_error(self, xml_string):
        if "An error occurred while processing request" in xml_string:
            # Regular expression to match text after the first occurrence of "Details:"
            match = re.search(r'Details:\s*(.*?)(?:</|$)', xml_string)

            # Extract and print the result if found
            if match:
                result = match.group(1)
                logger.warning(f"Pubmed Search request failed: {result}")
                #print(result)
            else:
                logger.warning(f"Pubmed Search request failed: No 'Details' found.")
            
            return True
        else:
            return False
                #print("No 'Details' found.")
            
    # Function to recursively print XML structure
    def print_xml_tree(self, element, indent=""):
        # Print the current element and its tag
        print(f"{indent}<{element.tag}>")
        
        # Print element attributes if they exist
        if element.attrib:
            print(f"{indent}  Attributes: {element.attrib}")
        
        # Print text content if available
        if element.text and element.text.strip():
            print(f"{indent}  Text: {element.text.strip()}")
        
        # Recursively print child elements
        for child in element:
            self.print_xml_tree(child, indent + "  ")
        
    def extract_data_from_articles(self, fetch_tree):
        # Extract details for each article
        for res in fetch_tree.findall('.//PubmedArticle'):
            #TEMP: 
            #self.print_xml_tree(fetch_tree)
            #END TEMP
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
                #'citation': self.extract_citation(res)
                }
                
                self.articles.append(item)
                self.auto_id += 1
        for res in fetch_tree.findall('.//PubmedBookArticle'):
            #TEMP: 
            #self.print_xml_tree(res)
            #END TEMP
            
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
                #'citation': self.extract_citation(res)
                }
                
                self.articles.append(item)
                self.auto_id += 1
        
    #def check_missing_articles(self, fetch_tree, batch_ids):
    #    articles_fetched = fetch_tree.findall('.//PubmedArticle | .//Book')
    #    fetched_ids = [article.find('.//PMID').text for article in articles_fetched]
    #    missing_ids = set(batch_ids) - set(fetched_ids)
        
        
    #    if not missing_ids:
    #        print("No missing articles to fetch.")
    #        return None
    #    else: 
    #        return missing_ids
    
    def extract_pmid(self, res):
        return res.find('.//PMID').text if res.find('.//PMID') is not None else None
        
    def extract_title(self, res):
        title = res.find('.//ArticleTitle').text if res.find('.//ArticleTitle') is not None else None
        return title
    
    def extract_authors(self, res):
        res_list = [
                f"{author.find('.//ForeName').text} {author.find('.//LastName').text}" 
                for author in res.findall('.//Author')
                if author.find('.//ForeName') is not None and author.find('.//LastName') is not None
            ]
        return ', '.join(res_list) if res_list != None else None
    
    def extract_date(self, res):
        publication_date = res.find('.//PubDate')
        if publication_date is not None:
            month = publication_date.find('.//Month').text if publication_date.find('.//Month') is not None else None
            year = int(publication_date.find('.//Year').text) if publication_date.find('.//Year') is not None else None
            date = f"{month} {year}" if month is not None and year is not None else None
        else:
            date = None
            year = None
        return date, year

    def extract_type(self, res):
        return res.find('.//PublicationType').text
        
    def extract_keywords(self, res):
        res_list = [
                res_part.findall('.//Keyword')   
                for res_part in res.findall('.//KeywordList')
            ]
        keywords = [f"{res_part.text}" for res_part in res_list[0]] if res_list else None

        return ', '.join(keywords) if keywords != None else None

    def extract_journal(self, res):
        journal = res.find('.//Journal/Title').text if res.find('.//Journal/Title') is not None else None
        return journal

    def extract_doi(self, res):
        return res.find('.//ArticleId[@IdType="doi"]').text if res.find('.//ArticleId[@IdType="doi"]') is not None else None
    
    def extract_url(self, res):
        href = res.find('.//ArticleId[@IdType="pubmed"]').text if res.find('.//ArticleId[@IdType="pubmed"]') is not None else None
        return f"https://pubmed.ncbi.nlm.nih.gov/{href}/" 

    def extract_full_abstract(self, article):
        abstract_list = []
                # Iterate over each abstract part
        for abstract_part in article.findall('.//Abstract'):
            # Use the .iter() method to get all elements in the correct order
            for elem in abstract_part.iter():
                # If the element is of interest (AbstractText, sup, or i), extract its text
                if elem.tag in ['AbstractText', 'sup', 'i', 'strong.sub-title']:
                    if 'Label' in elem.attrib:
                        # Format the label in title case and append it
                        label = elem.attrib['Label'].title()
                        abstract_list.append(f"{label}: ")
                    text = elem.text or ''  # Get the text, handling cases where text might be None
                    abstract_list.append(text)
                # Also, append any tail text (text after the closing tag)
                if elem.tail:
                    abstract_list.append(elem.tail)
        # Join the parts into a full abstract string
        return ''.join(abstract_list)
    
    def scrape_articles(self, max_results = None):
        self.max_results = max_results
        self.parse()
        return pd.DataFrame(self.articles)

def main():
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
    
# Run the script
if __name__ == "__main__":
    main()
