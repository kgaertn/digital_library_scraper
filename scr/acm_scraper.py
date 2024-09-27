import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)

class ACM_Scraper:
    def __init__(self, query='machine learning', max_results = None):
        self.query = query.replace(" ", "+")  # Ersetze Leerzeichen durch '+'
        self.query = self.query.replace(":", "%3A")
        self.auto_id = 1
        self.articles = []
        self.max_results = max_results
        # Setze die Start-URL basierend auf der Abfrage
        self.start_url = [f'https://dl.acm.org/action/doSearch?AllField={self.query}&startPage=0&pageSize=20']
    
    def parse_html(self, url):
        if url == '':
            url = self.start_url[0]
        response = requests.get(url)
        html_content = response.content  # This is the raw HTML.
        return BeautifulSoup(html_content, 'html.parser')
    
    def parse(self, url = ''):
        soup = self.parse_html(url)
        results_num = int(soup.find('span', class_='hitsLength').get_text(strip=True).replace(',', ''))
        
        articles = soup.find_all('li', class_='search__item issue-item-container')
        max_results_reached = False
        for res in articles:
            if self.max_results == None or self.auto_id <= self.max_results:
                logging.info(f'Scraping ACM DL: Article Nr. {self.auto_id} of {results_num}')
                date = self.extract_date(res)
                url = self.extract_url(res)
                item = {
                'id': self.auto_id,  # Assign the current ID
                'source': 'ACM',
                'title': self.extract_title(res),
                'authors': self.extract_authors(res),
                'date' : date,
                'year': self.extract_year(date),
                'journal_book': self.extract_journal(res), 
                'doi': self.extract_doi(res),
                'url' : url,
                'abstract': self.extract_full_abstract(url),
                'citation': self.extract_citation(res)
                }
                
                self.articles.append(item)
                self.auto_id += 1
            else:
                max_results_reached = True
                break     
        if not max_results_reached:
            if self.auto_id <= int(results_num):
                next_page = self.auto_id // 20
                next_url = f'https://dl.acm.org/action/doSearch?AllField={self.query}&startPage={next_page}&pageSize=20'
                self.parse(next_url)            
        print('')    
    
    
    def extract_title(self, res):
        res_span = res.find('span', class_='hlFld-Title')
        return ' '.join(res_span.stripped_strings) if res_span != None else None

    def extract_authors(self, res):
        res_list = res.find('ul', class_='rlist--inline loa truncate-list')
        return ', '.join([author.find('span').get_text(strip=True) for author in res_list.find_all('li')]) if res_list != None else None
    
    def extract_date(self, res):
        res_span = res.find('div', class_='bookPubDate simple-tooltip__block--b')
        return ' '.join(res_span.stripped_strings) if res_span != None else None
    
    def extract_year(self, date_str):
        return int(re.search(r'\b\d{4}\b', date_str).group())

    def extract_journal(self, res):
        res_span = res.find('span', class_='epub-section__title')
        return' '.join(res_span.stripped_strings) if res_span != None else None

    def extract_doi(self, res):
        res_span = res.find('a', class_='issue-item__doi dot-separator')
        doi_string = ' '.join(res_span.stripped_strings) if res_span != None else None
        return re.search(r'10\.\d{4,9}/[^\s]+', doi_string).group()
    
    def extract_url(self, res):
        href = res.find('span', class_='hlFld-Title').find('a').get('href') 
        return f"https://dl.acm.org{href}" 

    def extract_citation(self, res):
        res_span = res.find('span', class_='citation')
        return int(' '.join(res_span.stripped_strings)) if res_span != None else None

    def extract_full_abstract(self, url):
        soup = self.parse_html(url)
        abstract_section = soup.find('section', {'role': 'doc-abstract'})
        return abstract_section.find('div', {'role': 'paragraph'}).get_text(strip=True) if abstract_section != None else None

    def scrape_articles(self, url = '', max_results = 25):
        self.max_results = max_results
        self.parse(url)
        return pd.DataFrame(self.articles)
        
def main():
    query = '(Title:( Movement)  OR Title:( Kinesiology)  OR Title:( Physiotherapy)  OR Title:( "Physical Therapy")  OR Title:( Kinetic)  OR Title:( Kinematic)  OR Title:( Biomechanic)  OR Title:( "Motor Control")  OR Abstract:(Movement)  OR Abstract:(Kinesiology)  OR Abstract:(Physiotherapy)  OR Abstract:("Physical Therapy")  OR Abstract:(Kinetic)  OR Abstract:(Kinematic)  OR Abstract:(Biomechanic)  OR Abstract:("Motor Control") ) AND (Title:( "3D Movement Measurement*")  OR Title:( "3D Motion")  OR Title:( "Motion capture")  OR Title:( EMG)  OR Title:( Electromyography)  OR Title:( "Wearable Sensors")  OR Title:( "Motion analysis")  OR Title:( "Multimodal")  OR Title:( IMU)  OR Abstract:("3D Movement Measurement*")  OR Abstract:("3D Motion")  OR Abstract:("Motion capture")  OR Abstract:(EMG)  OR Abstract:(Electromyography)  OR Abstract:("Wearable Sensors")  OR Abstract:("Motion analysis")  OR Abstract:("Multimodal")  OR Abstract:(IMU) ) AND (Title:( "Pattern recognition")  OR Title:( "Dimension reduction")  OR Title:( "Data Science")  OR Title:( "Time series analysis")  OR Title:( Clustering)  OR Abstract:("Pattern recognition")  OR Abstract:("Dimension reduction")  OR Abstract:("Data Science")  OR Abstract:("Time series analysis")  OR Abstract:(Clustering) ) NOT (Title:( Gait)  OR Title:( Neuro*)  OR Title:( robot*)  OR Title:( prosthe*)  OR Abstract:(Gait)  OR Abstract:(Neuro*)  OR Abstract:(robot*)  OR Abstract:(prosthe*) )'
    
    acm_crawler = ACM_Scraper(query)
    #acm_crawler.parse()
    acm_articles = acm_crawler.scrape_articles(max_results = 25)
    
# Run the script
if __name__ == "__main__":
    main()



