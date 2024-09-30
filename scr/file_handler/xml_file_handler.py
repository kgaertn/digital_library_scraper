import xml.etree.ElementTree as ET
import os

class File_Handler():
    def __init__(self, config_file):
        self.config_file = config_file
        self.search_config = self.load_config()
    def load_config(self):
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
            
    def display_categories(self):
        """Prints the current categories and their search terms."""
        for category, terms in self.categories.items():
            print(f"{category}: {', '.join(terms)}")

    def add_category(self, category):
        """Add a new category to the search"""
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
