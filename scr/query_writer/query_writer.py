class DatabaseQuery:
    def __init__(self, search_terms, databases):
        self.search_terms = search_terms
        self.databases = databases
        self.selected_database = ''
        self.selected_search_type = ''
        self.query = ""

    def generate_query(self, database, search_type):

        # Convert input to lowercase for case-insensitive comparison
        database_to_check = database.lower()
        search_type_to_ckeck = search_type.lower()

        # Find the normalized database name (database name how it is saved in the xml file)
        self.selected_database = next((key for key in self.databases if key.lower() == database_to_check), None)
        
        if self.selected_database:
            self.selected_search_type  = next((key for key in self.databases[self.selected_database]['syntax'] if key.lower() == search_type_to_ckeck), None)
            if self.selected_search_type:
                # create a query for each category of search terms
                for category in self.search_terms:
                    category_terms = self.search_terms[category]
                    category_query = self._category_query(category_terms)
                    
                    # Use 'AND' for all except the last category
                    if self.query != '' and (category != 'Exclusion'):
                        self.query +=f" AND ({category_query})"
                    elif (category == 'Exclusion'):
                        self.query +=f" NOT ({category_query})"
                    else:
                        self.query +=f"({category_query})"
            else: 
                raise ValueError(f"Search type '{search_type}' not found in database '{database}'")
        else:
            raise ValueError(f"Database '{database}' not found")

    def _category_query(self, category):
        search_syntaxes = self.databases[self.selected_database]['syntax'][self.selected_search_type]
        syntax_before, syntax_after = self.split_syntax(search_syntaxes)
        category_query = ""
        if (len(syntax_before) > 0) & (len(syntax_after) == 0):
            category_query = self._query_before(category, syntax_before)
        elif (len(syntax_before) == 0) & (len(syntax_after) > 0):
            category_query = self._query_after(category, syntax_after)
        elif (len(syntax_before) > 0) & (len(syntax_after) == 1):
            category_query = self._query_both(category, syntax_before, syntax_after)
        
        return category_query         
        
    def split_syntax(self, search_syntaxes):
        term_position = self.databases[self.selected_database]['term_position'][self.selected_search_type]
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
        category_query = ''
        for i, syntax in enumerate(syntax_before):
            formatted_terms = [f'{syntax}{term}{syntax_after[0]}' for term in category]
            combined_cat_Query = " OR ".join(formatted_terms)
            if i > 0:
                category_query = category_query + f" OR {combined_cat_Query}"
            else:
                category_query = combined_cat_Query
        return category_query
        
#from scr.file_handler.xml_file_handler import *        
#def main():
#    # Load the default search terms from the XML config file
#    config_file = os.path.join(os.path.dirname(__file__), 'config', 'config.xml')
#    search_config = File_Handler(config_file)
#    
#    # Display the current categories and search terms
#    print("Current search terms:")
#    search_config.display_categories()
#    
#    adjust_categories = input("Would you like to adjust the categories? (yes/no): ")
#    adjusting_categories = True if adjust_categories.lower() == 'yes' else False
#    
#    # allow user to add or remove search categories
#    while adjusting_categories:
#        action = input("Would you like to add or remove a search categories? (add | remove | none): ")
#        if action == "none":
#            break
#        print("Current search categories: ")
#        search_config.display_category_names()
#        category_name = input("Enter the category name: ").lower()
#
#        if action == "add":
#            search_config.add_category(category_name)
#        elif action == "remove":
#            search_config.remove_category(category_name)
#        else:
#            print("Invalid action.")
#
#    
#    # Allow user to add or remove search terms
#    while adjusting_categories:
#        action = input("Do you want to add or remove a term? (add | remove | none): ").lower()
#        if action == "none":
#            break
#        category = input(f"Enter the category name {search_config.get_category_names()}: ").lower()
#        term = input("Enter the search term: ")
#        
#        if action == "add":
#            search_config.add_term(category, term)
#        elif action == "remove":
#            search_config.remove_term(category, term)
#        else:
#            print("Invalid action.")
#
#    # Enter database and type of search that the query should be generated for
#    database = input("Enter the database (PubMed | IEEE | ACM): ")
#    search_type = input("Enter the type of search you want to perform (Title | Title/Abstract | FullText): ")
#
#    # Generate the query based on the selected database
#    query_generator = DatabaseQuery(search_config.categories, search_config.databases)
#    query_generator.generate_query(database, search_type)
#    query = query_generator.query
#
#    # Print the generated query
#    print("\nGenerated query:")
#    print(query)
#
#if __name__ == "__main__":
#    main()