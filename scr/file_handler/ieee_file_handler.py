import pandas as pd
from lxml import etree

class IeeeFileHandler:
    def __init__(self, file_path):
        """
        Initialize the FileHandler for a filepath.

        Parameters:
        - file_path: The path to the file that should be loaded.
        """
        self.file_path = file_path
        self.data = None
        self.processed_data = None

    def parse_data(self, data_str):
        """convert comma-separated string to list of floats"""
        if data_str:
            return [float(x) for x in data_str.split(',')]
        return []
    
    def load_file(self):
        """Identify file format and call respective loader method"""
        if str(self.file_path).endswith('.csv'):
            self.data = self._load_csv()
        elif str(self.file_path).endswith('.tsv'):
            self.data = self._load_tsv()
        elif str(self.file_path).endswith('.xml'):
            self.data = self._load_xml()
        elif str(self.file_path).endswith('.xlsx'):
            self.data = self._load_excel()
        # Add more formats as needed
        #return self.data

    def _load_csv(self):
        """Load CSV file logic"""
        return pd.read_csv(self.file_path, delimiter=',')
    
    def _load_tsv(self):
        """Load TSV file logic"""
        return pd.read_csv(self.file_path, delimiter='\t')

    def _load_xml(self):
        """Load XML file logic"""

    def _load_excel(self):
        """Load Excel file logic"""
        return pd.read_excel(self.file_path)
    
    def process_file(self):
        """Process the file"""
        self.processed_data = self.data.drop(columns=['Author Affiliations', 'Date Added To Xplore','Volume', 'Issue',
            'Start Page', 'End Page', 'Volume', 'Issue','Start Page', 'End Page', 'ISSN', 'ISBNs', 'Funding Information', 'IEEE Terms',
            'Mesh_Terms', 'Patent Citation Count',
            'Reference Count', 'License', 'Online Date', 'Issue Date',
            'Meeting Date', 'Publisher', 'Document Identifier'])
        
        self.processed_data = self.processed_data.rename(columns={
            'Document Title': 'title',
            'Authors': 'authors',
            'Publication Title': 'journal_book',
            'Publication Year': 'year',
            'Abstract': 'abstract',
            'DOI': 'doi',
            'Article Citation Count': 'citation',
            'PDF Link': 'url',
            'Author Keywords': 'keywords'
        })
        self.processed_data['source'] = 'IEEE'
        
        #print()
    
    def get_articles(self):
        self.load_file()
        self.process_file()
        return self.processed_data
        

# TEMP
# used to test the script
def main():
    from pathlib import Path
    # Get the path of the current script
    current_path = Path(__file__).resolve().parent

    # Navigate to the parent folder
    parent_path = current_path.parent

    # Construct the path to the data folder
    filepath = parent_path / 'data/2024_09_24_Pilot_Search_IEEE.csv'
    #filepath_tsv = parent_path / 'Sample_Data_PAH/MusikPhysioAnalysis/00_VIOLIN/00_JOINT_ANGLE/RIGHT_ELBOW_JOINT_ANGLE_Z.tsv'

    # Create Filehandler
    filehandler = FileHandler(filepath)
    #filehandler = FileHandler(filepath_tsv)
    ieee_articles = filehandler.get_articles()
    print(ieee_articles.head())
    #filehandler.load_file()
    #filehandler_tsv.load_file()
    
    #filehandler.process_file()



if __name__ == "__main__":
    main()