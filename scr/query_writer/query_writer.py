class DatabaseQuery:
    """
    Class for generating database queries based on search terms and database configurations.

    Attributes:
        search_terms (dict): A dictionary mapping categories to their respective search terms.
        databases (dict): A dictionary containing database configurations including syntax and term positions.
        selected_database (str): The name of the currently selected database.
        selected_search_types (dict): A dictionary mapping categories to their respective search types.
        query (str): The generated query string.
    """
    
    def __init__(self, search_terms:dict[str, list[str]], databases:dict[str, dict[str, list[str]]]):
        """
        Initialize the DatabaseQuery with search terms and database configurations.

        Args:
            search_terms (dict): Search terms categorized by their respective categories.
            databases (dict): Database configurations including search syntax and term positions.
        """
        self.search_terms = search_terms
        self.databases = databases
        self.selected_database = ''
        self.selected_search_types = {}
        self.query = ""


    def generate_query(self, database: str, search_type_dict: dict[str, str]):
        """
        Generate a query for the specified database using the provided search types.

        Args:
            database (str): The name of the database to generate the query for.
            search_type_dict (dict): A dictionary mapping categories to their search types.

        Raises:
            ValueError: If the database or search type is not found in the configurations.
        """
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

    def _category_query(self, category: list[str], search_type: str) -> str:
        """
        Create a query for a specific category based on its associated search syntax.

        Args:
            category (str): The category for which the query is being created.
            search_type (str): The search type syntax to apply for the category.

        Returns:
            str: The constructed query string for the specified category.
        """
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
        
    def split_syntax(self, search_syntaxes: list[str], search_type: str) -> tuple[list[str], list[str]]:
        """
        Split the search syntax into elements that need to be placed before or after the search term.

        Args:
            search_syntaxes (list): A list of syntax elements for the specified search type.
            search_type (str): The search type being processed.

        Returns:
            tuple: A tuple containing two lists: syntax_before and syntax_after.
        """
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
            
    def _query_before(self, category: list[str], syntax_before: list[str]) -> str:
        """
        Create a query for a category where syntax elements appear before the search term.

        Args:
            category (list): The list of search terms for the category.
            syntax_before (list): The syntax elements that should precede the terms.

        Returns:
            str: The constructed query string for the specified category.
        """
        category_query = ''
        for i, syntax in enumerate(syntax_before):
            formatted_terms = [f'{syntax}{term}' for term in category]
            combined_cat_Query = " OR ".join(formatted_terms)
            if i > 0:
                category_query = category_query + f" OR {combined_cat_Query}"
            else:
                category_query = combined_cat_Query
        return category_query
    
    def _query_after(self, category: list[str], syntax_after: list[str]) -> str:   
        """
        Create a query for a category where syntax elements appear after the search term.

        Args:
            category (list): The list of search terms for the category.
            syntax_after (list): The syntax elements that should follow the terms.

        Returns:
            str: The constructed query string for the specified category.
        """
        category_query = ''
        for i, syntax in enumerate(syntax_after):
            formatted_terms = [f'{term}{syntax}' for term in category]
            combined_cat_Query = " OR ".join(formatted_terms)
            if i > 0:
                category_query = category_query + f" OR {combined_cat_Query}"
            else:
                category_query = combined_cat_Query
        return category_query
        
    def _query_both(self, category: list[str], syntax_before: list[str], syntax_after: list[str]) -> str:   
        """
        Create a query for a category with syntax elements placed both before and after the search term.

        Args:
            category (list): The list of search terms for the category.
            syntax_before (list): The syntax elements that should precede the terms.
            syntax_after (list): The syntax elements that should follow the terms.

        Returns:
            str: The constructed query string for the specified category.
            
        Note:
            this function only works if there is exactly one element after the search term (e.g. a closing braket)
        """
        category_query = ''
        for i, syntax in enumerate(syntax_before):
            formatted_terms = [f'{syntax}{term}{syntax_after[0]}' for term in category]
            combined_cat_Query = " OR ".join(formatted_terms)
            if i > 0:
                category_query = category_query + f" OR {combined_cat_Query}"
            else:
                category_query = combined_cat_Query
        return category_query