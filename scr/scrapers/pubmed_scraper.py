import requests
from xml.etree import ElementTree as ET
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO)

class Pubmed_Scraper:
    def __init__(self, query='machine learning', max_results = None):
        self.query = query
        self.auto_id = 1
        self.articles = []
        self.max_results = max_results
        # Setze die Start-URL basierend auf der Abfrage
        self.search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        self.fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    def parse(self):
        # Initial search to get the total number of results
        
        batch_size = self.max_results if (self.max_results != None) and (self.max_results < 200) else 200
        
        search_params = {
            'db': 'pubmed',
            'term': self.query,
            'retmode': 'xml',
            'retmax': batch_size,
        }
        
        search_response = requests.get(self.search_url, params=search_params)
        search_tree = ET.fromstring(search_response.content)
        results_num = int(search_tree.find('.//Count').text)
        max_results = self.max_results if (self.max_results != None) else results_num
        # Get total number of results
        print(f"Pubmed: total results found: {results_num}")

        # Initialize variables
        all_id_list = []

        # Paginate through the results
        for start in range(0, max_results, batch_size):
            search_params['retstart'] = start  # Set the starting point for each batch
            search_response = requests.get(self.search_url, params=search_params)
            search_tree = ET.fromstring(search_response.content)
            
            # Extract article IDs
            id_list = [id_elem.text for id_elem in search_tree.findall('.//Id')]
            all_id_list.extend(id_list)  # Append to the list of all article IDs

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
            
            fetch_response = requests.get(self.fetch_url, params=fetch_params)
            fetch_tree = ET.fromstring(fetch_response.content)
            
            # Extract details for each article
            for res in fetch_tree.findall('.//PubmedArticle'):
                if self.max_results == None or self.auto_id <= self.max_results:
                    logging.info(f'Scraping PubMed: Article Nr. {self.auto_id} of {results_num}')
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
                    'keywords': self.extract_keywords(res)
                    #'citation': self.extract_citation(res)
                    }
                    
                    self.articles.append(item)
                    self.auto_id += 1

    def extract_title(self, res):
        return res.find('.//ArticleTitle').text if res.find('.//ArticleTitle') is not None else None

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
    query = 'Kinematical alignment better restores native patellar tracking pattern than mechanical alignment.'
    
    pubmed_crawler = Pubmed_Scraper(query = query)
    pubmed_articles = pubmed_crawler.scrape_articles(10)
    
    print('')
    
# Run the script
if __name__ == "__main__":
    main()
