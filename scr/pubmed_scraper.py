import requests
from xml.etree import ElementTree
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

    def parse(self, query):
        
        if self.max_results == None:
            search_params = {
                'db': 'pubmed',
                'term': query,
                'retmode': 'xml'
            }
        else:
            search_params = {
                'db': 'pubmed',
                'term': query,
                'retmax': self.max_results,
                'retmode': 'xml'
            }

        search_response = requests.get(self.search_url, params=search_params)
        search_tree = ElementTree.fromstring(search_response.content)
        results_num = int(search_tree.find('.//Count').text)
        
        
        id_list = [id_elem.text for id_elem in search_tree.findall('.//Id')]

        fetch_params = {
            'db': 'pubmed',
            'id': ','.join(id_list),
            'retmode': 'xml'
        }

        fetch_response = requests.get(self.fetch_url, params=fetch_params)
        fetch_tree = ElementTree.fromstring(fetch_response.content)

        

        #articles = []
        for res in fetch_tree.findall('.//PubmedArticle'):
            if self.max_results == None or self.auto_id <= self.max_results:
                logging.info(f'Scraping PubMed: Article Nr. {self.auto_id} of {results_num}')
                date, year = self.extract_date(res)
                #url = self.extract_url(res)
                item = {
                'id': self.auto_id,  # Assign the current ID
                'source': 'PubMed',
                'title': self.extract_title(res),
                'authors': self.extract_authors(res),
                'date' : date,
                'year': year,
                'journal_book': self.extract_journal(res), 
                'doi': self.extract_doi(res),
                'url' : self.extract_url(res),
                'abstract': self.extract_full_abstract(res),
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
            date = f"{month} {year}"
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
        keywords = [
            f"{res_part.text}"
            for res_part in res_list[0]
        ]

        return ', '.join(keywords) if keywords != None else None
    
    #def extract_year(self, date_str):
    #    return int(re.search(r'\b\d{4}\b', date_str).group())

    def extract_journal(self, res):
        journal = res.find('.//Journal/Title').text if res.find('.//Journal/Title') is not None else None
        return journal

    def extract_doi(self, res):
        return res.find('.//ArticleId[@IdType="doi"]').text if res.find('.//ArticleId[@IdType="doi"]') is not None else None
    
    def extract_url(self, res):
        href = res.find('.//ArticleId[@IdType="pubmed"]').text if res.find('.//ArticleId[@IdType="pubmed"]') is not None else None
        return f"https://dl.acm.org/{href}/" 

    #def extract_citation(self, res):
    #    res_span = res.find('span', class_='citation')
    #    return int(' '.join(res_span.stripped_strings)) if res_span != None else None

    def extract_full_abstract(self, article):
        abstract_list = [
                abstract_part.findall('.//AbstractText')   
                for abstract_part in article.findall('.//Abstract')
            ]
        if abstract_list != []: 
            abstract = [
                f"{abstract_part.text}"
                if abstract_list is not None else None
                for abstract_part in abstract_list[0] 
            ]
        else:
            abstract = None
        return ' '.join(abstract) if abstract != None else None
    
    def scrape_articles(self, url = '', max_results = 25):
        self.max_results = max_results
        self.parse(url)
        return pd.DataFrame(self.articles)

def main():
    query = 'machine learning'
    
    pubmed_crawler = Pubmed_Scraper(query)
    #acm_crawler.parse()
    pubmed_articles = pubmed_crawler.scrape_articles(query, max_results = 25)
    
    print('')
    
# Run the script
if __name__ == "__main__":
    main()
