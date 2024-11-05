"""
This module provides classes for handling XML configuration files and processing data files,
particularly those from IEEE, with functionalities for managing search configurations, 
categories, terms, and handling multiple file formats.

Dependencies:
    - xml.etree.ElementTree as ET: Used for parsing XML configuration files.
    - pandas as pd: Required for handling dataframes when processing CSV, TSV, XML, and Excel files.
"""

# TODO: split the two classes into two scripts; one for config file handling, the other for data file handling
import xml.etree.ElementTree as ET
import pandas as pd
from lxml import etree

# class to handle the config xml file
class Config_File_Handler():
    """
    Class for managing XML configuration files.

    This class handles loading databases, categories, and search terms from a given 
    configuration file. It also provides methods for managing categories and search terms.
    
    Attributes:
        config_file (str): Path to the XML configuration file.
        databases (dict): A dictionary to store databases with their respective syntax terms and positions.
        categories (dict): A dictionary to store categories and their search terms.
    """
    def __init__(self, config_file: str):
        """
        Initialize the ConfigLoader with a configuration file path.

        Args:
            config_file (str): Path to the XML configuration file to load.
        """
        self.config_file = config_file
        self.databases = {}
        self.categories = {}
        self.search_config = self.load_config()
        
    
    def load_config(self):
        """
        Parse the XML configuration file to populate `databases` and `categories`.

        This function reads XML data from `config_file` and organizes it into:
            - `databases`: Contains syntax terms and term positions for each database.
            - `categories`: Contains search terms for each category.

        Returns:
            None

        Raises:
            FileNotFoundError: If the configuration file does not exist.
            ET.ParseError: If the XML file is improperly formatted.
        """
        
        tree = ET.parse(self.config_file)
        root = tree.getroot()
        self.databases = {}
        for database in root.find('Databases'):
            database_name = database.get('name')
            database_syntax = {}
            term_positions = {}
            for syntax in database:
                syntax_name = syntax.get('name')
                syntax_terms = [term.text for term in syntax]
                term_position = [term.get('position') for term in syntax]
                term_positions[syntax_name] = term_position
                database_syntax[syntax_name] = syntax_terms
                
            # Store the database information including the term position
            self.databases[database_name] = {
                'syntax': database_syntax,
                'term_position': term_positions
            }
        self.categories = {}
        for category in root.find('Categories'):
            category_name = category.get('name')
            search_terms = [term.text for term in category.find('SearchTerms')]
            self.categories[category_name] = search_terms

    #region ADDITIONAL FUNCTIONALITY
    """
    Additional utility functions for future use or potential adjustments. 

    Note:
        These functions are currently not used in the main scraping logic but are provided 
        for extensibility and may be incorporated into future versions or customized workflows.
    """
         
    def display_categories(self):
        """
        Prints the current categories and their search terms.
        
        Returns:
            None
        """
        for category, terms in self.categories.items():
            print(f"{category}: {', '.join(terms)}")

    def add_category(self, category):
        """
        Add a new category to the search
        
        
        """
        if category.lower() in [item.lower() for item in self.categories]:
            print(f"Category {category} already exists")
        else:
            self.categories[category] = None
            
            # move exclusion category to the end for better structure
            exclusion_category = self.categories.pop('Exclusion')
            self.categories['Exclusion'] = exclusion_category
            print(f"Category '{category}' was added.")
    def remove_category(self, category):
        """Remove a new category to the search"""
        categories_lower = [item.lower() for item in self.categories]
        category_lower = category.lower()
        if category_lower in categories_lower:
            index = categories_lower.index(category_lower)
            original_categories = [item for item in self.categories]
            self.categories.pop(original_categories[index])
            print(f"Category '{category}' was removed.")
        else:
            print(f"Category {category} not found.")
    def add_term(self, category, term):
        """Add a search term to a specific category."""
        
        categories_lower = [item.lower() for item in self.categories]
        category_lower = category.lower()
        index = categories_lower.index(category_lower)
        original_categories = [item for item in self.categories]
        if category_lower in categories_lower:
            if self.categories[original_categories[index]] == None:
                self.categories[original_categories[index]] = [term]
            elif not (term.lower() in [item.lower() for item in self.categories[original_categories[index]]]):
                self.categories[original_categories[index]].append(term)       
            else:
                print(f"Term {term} already in Category {category}")                   
        else:
            print(f"Category {category} not found.")

    def remove_term(self, category, term):
        """Remove a search term from a specific category, ignoring case sensitivity."""
        if category.lower() in [item.lower() for item in self.categories]:
            # Search for the term, ignoring case sensitivity
            terms_lower = [t.lower() for t in self.categories[category]]
            term_lower = term.lower()
            if self.categories[category] != None:
                if term.lower() in [item.lower() for item in self.categories[category]]:
                    # Find index of term to be removed
                    index = terms_lower.index(term_lower)
                    # Remove term from the category
                    removed_term = self.categories[category].pop(index)
                    print(f"Term '{removed_term}' removed from category '{category}'.")
                else:
                    print(f"Term '{term}' not found in category '{category}'.")
            else:
                print(f"There are no terms to remove in category {category}.")
        else:
            print(f"Category '{category}' not found.")
    def display_category_names(self):
        """Prints the current category names and their search terms."""
        categories = []
        for category in self.categories:
            categories.append(category)
        print(categories)

    def get_category_names(self):
        """Returns the current category names."""
        categories = []
        for category in self.categories:
            categories.append(category)
        return categories
    #endregion ADDITIONAL FUNCTIONALITY

class File_Handler:
    """
    Class for managing and processing various data file formats.

    This class handles loading data from different file formats (CSV, TSV, XML, Excel) 
    and processes IEEE files specifically to extract relevant article information.

    Attributes:
        file_path (str): The path to the file that should be loaded.
        data (pd.DataFrame): The raw data loaded from the file.
        processed_data (pd.DataFrame): The processed data after extraction and cleaning.
        sep (str): The separator used for CSV files (default is a comma).
    """
    def __init__(self, file_path: str, sep: str = ',', excel_sheet_Name: str|None = None):
        """
        Initialize the FileHandler for a filepath.

        Args:
            file_path (str): The path to the file that should be loaded.
            sep (str): the file seperator for the file to load (defaults to ',')
            excel_sheet_Name (str, Optional): the name of the excel sheet that should be loaded (defaults to None)
        """
        self.file_path = file_path
        self.data = None
        self.processed_data = None
        self.sep = sep
        self.excel_sheet_name = excel_sheet_Name
        self.load_file()
   
    def load_file(self):
        """Identify file format and call respective loader method"""
        if str(self.file_path).endswith('.csv'):
            if self.sep == ',':
                self.data = self._load_csv_comma()            
            elif self.sep == ';':
                self.data = self._load_csv_semic()
        elif str(self.file_path).endswith('.tsv'):
            self.data = self._load_tsv()
        elif str(self.file_path).endswith('.xml'):
            self.data = self._load_xml()
        elif str(self.file_path).endswith('.xlsx'):
            self.data = self._load_excel()
        # Add more formats as needed
        
    #region FILE LOADING
    """
    Functions for loading various file formats.

    Note:
        Some of these functions are placeholders and have not been tested yet.
    """
    def _load_csv_comma(self) -> pd.DataFrame:
        """Load a CSV file that uses commas as delimiters."""
        return pd.read_csv(self.file_path, delimiter=',')
    
    def _load_csv_semic(self) -> pd.DataFrame:
        """Load a CSV file that uses semicolons as delimiters."""
        return pd.read_csv(self.file_path, delimiter=';')
            
    def _load_tsv(self) -> pd.DataFrame:
        """Placeholder: Load a TSV (tab-separated values) file"""
        return pd.read_csv(self.file_path, delimiter='\t')
    
    def _load_xml(self):
        """Placeholder: Load XML file logic"""
        
    def _load_excel(self) -> pd.DataFrame:
        """Load Excel file logic"""
        if self.excel_sheet_name == None:
            return pd.read_excel(self.file_path)
        else:
            return pd.read_excel(self.file_path, sheet_name=self.excel_sheet_name)
    #endregion FILE LOADING
    
    def process_ieee_file(self):
        """
        Process the IEEE file, selecting relevant columns and renaming them.

        Returns:
            None
        """
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

    
    #region GETTER
    """
    Functions for retrieving data.

    Note:
        These functions provide access to processed and raw data for further analysis or manipulation.
    """
    def get_ieee_articles(self) -> pd.DataFrame:
        """Retrieve IEEE articles after processing the data."""
        self.process_ieee_file()
        return pd.DataFrame(self.processed_data)
    
    def get_processed_data(self) -> pd.DataFrame:
        """Return the processed data as a DataFrame."""
        return pd.DataFrame(self.processed_data)

    def get_raw_data(self) -> pd.DataFrame:
        """Return the raw data as a DataFrame."""
        return pd.DataFrame(self.data)
    #endregion

