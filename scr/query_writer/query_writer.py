# Author: Kaya Gärtner
# Date: 16.10.2024
# Description: Generates the queries for specified databases, based on the database, and search term inputs

class DatabaseQuery:
    def __init__(self, search_terms, databases):
        self.search_terms = search_terms
        self.databases = databases
        self.selected_database = ''
        self.selected_search_types = {}
        self.query = ""


    def generate_query(self, database, search_type_dict):
        # Convert input to lowercase for case-insensitive comparison
        database_to_check = database.lower()

        # Find the normalized database name (database name as saved in the xml file)
        self.selected_database = next((key for key in self.databases if key.lower() == database_to_check), None)
        
        if self.selected_database:
            # Update selected_search_types based on the provided search_type_dict
            for category, search_type in search_type_dict.items():
                search_type_to_check = search_type.lower()
                self.selected_search_types[category] = next(
                    (key for key in self.databases[self.selected_database]['syntax'] if key.lower() == search_type_to_check), None
                )
                if self.selected_search_types[category] is None:
                    raise ValueError(f"Search type '{search_type}' not found for category '{category}' in database '{database}'")

            # Create a query for each category of search terms
            for category in self.search_terms:
                category_terms = self.search_terms[category]
                if category in self.selected_search_types:
                    category_query = self._category_query(category_terms, self.selected_search_types[category])
                    
                    # Use 'AND' for all except the exclusion category
                    if self.query != '' and (category != 'exclusion_category'):
                        self.query += f" AND ({category_query})"
                    elif category == 'exclusion_category':
                        self.query += f" NOT ({category_query})"
                    else:
                        self.query += f"({category_query})"
        else:
            raise ValueError(f"Database '{database}' not found")

    def _category_query(self, category, search_type):
        # create the query for the category, based on the position of syntaxes
        search_syntaxes = self.databases[self.selected_database]['syntax'][search_type]
        syntax_before, syntax_after = self.split_syntax(search_syntaxes, search_type)
        category_query = ""
        if (len(syntax_before) > 0) & (len(syntax_after) == 0):
            category_query = self._query_before(category, syntax_before)
        elif (len(syntax_before) == 0) & (len(syntax_after) > 0):
            category_query = self._query_after(category, syntax_after)
        elif (len(syntax_before) > 0) & (len(syntax_after) == 1):
            category_query = self._query_both(category, syntax_before, syntax_after)
        
        return category_query         
        
    def split_syntax(self, search_syntaxes, search_type):
        # split the syntax into the elements that need to be placed before or after the search term
        term_position = self.databases[self.selected_database]['term_position'][search_type]
        index_before = []
        index_after = []
        syntax_after = []
        syntax_before = []

        # Iterate over the term_position list and collect indices in respective variables
        for index, term in enumerate(term_position):
            if term == 'Before':
                index_before.append(index)
            elif term == 'After':
                index_after.append(index)
        
        if index_before != None:    
            for index in index_before:
                syntax_before.append(search_syntaxes[index])
        if index_after != None:
            for index in index_after:
                syntax_after.append(search_syntaxes[index])
                
        return syntax_before, syntax_after
            
    def _query_before(self, category, syntax_before):
        # create the query for a category, when all elements of the syntax need to be before the search term
        category_query = ''
        for i, syntax in enumerate(syntax_before):
            formatted_terms = [f'{syntax}{term}' for term in category]
            combined_cat_Query = " OR ".join(formatted_terms)
            if i > 0:
                category_query = category_query + f" OR {combined_cat_Query}"
            else:
                category_query = combined_cat_Query
        return category_query
    
    def _query_after(self, category, syntax_after):   
        # create the query for a category, when all elements of the syntax need to be after the search term
        category_query = ''
        for i, syntax in enumerate(syntax_after):
            formatted_terms = [f'{term}{syntax}' for term in category]
            combined_cat_Query = " OR ".join(formatted_terms)
            if i > 0:
                category_query = category_query + f" OR {combined_cat_Query}"
            else:
                category_query = combined_cat_Query
        return category_query
        
    def _query_both(self, category, syntax_before, syntax_after):   
        # create the query for a category, when elements of the syntax need to be placed before and after the search term
        # only works for one element after (e.g. if a braket needs to be closed after the search term)
        category_query = ''
        for i, syntax in enumerate(syntax_before):
            formatted_terms = [f'{syntax}{term}{syntax_after[0]}' for term in category]
            combined_cat_Query = " OR ".join(formatted_terms)
            if i > 0:
                category_query = category_query + f" OR {combined_cat_Query}"
            else:
                category_query = combined_cat_Query
        return category_query