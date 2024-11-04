"""
This script processes article files by performing randomization and duplicate marking,
guided by parameters from a configuration file.

Functions:
    - get_randomization_list(nr_randomizations, min_value, max_value): Generates a list of unique randomized numbers within a given range.
    - pilot_randomizing(df, nr_randomizations): Adds a "pilot" column to a DataFrame, marking a specified number of articles with "x".
    - mark_duplicates(df): Adds a "duplicate" column to a DataFrame, marking articles with missing or duplicate DOIs as duplicates.
    - main(): Main function that loads configuration parameters, processes files to add "pilot" and "duplicate" markings, and saves results.

Dependencies:
    - random: For generating random numbers for article randomization.
    - configparser: For reading configuration settings.
    - pathlib.Path: For file path handling.
    - pandas (pd): For DataFrame operations and file handling.
    - file_handler: Custom module containing the File_Handler class for loading and processing files.

Usage:
    This script can be run directly. It reads search configuration settings, performs randomization and duplicate marking on articles,
    and saves updated files back to the specified directory.
"""

from file_handler.file_handler import *
from pathlib import Path
import random
import configparser

def get_randomization_list(nr_randomizations: int, min_value: int, max_value: int) -> list[int]:
    """
    create a list of randomized numbers

    Args:
        nr_randomizations (int): the number of randomized numbers; equivalent to the length of the resulting list
        min_value (int): the minimum value for the randomization range
        max_value (int): the maximum value for the randomization range
    
    Returns:
        list of int:  list of randomized numbers
    """ 
    if nr_randomizations > (max_value - min_value + 1):
        raise ValueError("Number of randomizations exceeds the range of unique values.")
    
    random_values = random.sample(range(min_value, max_value+1), nr_randomizations)
    return random_values
        
def pilot_randomizing(df: pd.DataFrame, nr_randomizations: int)-> pd.DataFrame:
    """
    Marks a specified number of articles with "x" in a newly created column "pilot".

    Args:
        df (pd.DataFrame): The DataFrame containing the articles to be modified.
        nr_randomizations (int): The number of articles to mark with "x".
        
    Returns:
        pd.DataFrame: The modified DataFrame with the new "pilot" column.
    """
    min_value = min(df['article_id'])        
    max_value = max(df['article_id'])

    random_values = get_randomization_list(nr_randomizations,min_value, max_value)
    
    df['pilot'] = None
    df.loc[df['article_id'].isin(random_values), 'pilot'] = 'x'   
    return df     

def mark_duplicates(df: pd.DataFrame)-> pd.DataFrame:
    """
    mark a duplicate articles with "x", in a newly created column "duplicate"

    Args:
        df (pd.DataFrame): The DataFrame containing the articles to be modified.
    
    Returns:
        pd.DataFrame:  The modified DataFrame with the new "duplicate" column.
    """ 
    df['duplicate'] = df.apply(
        lambda row: 'x' if pd.isna(row['doi']) or row['doi'] == '' or df.duplicated(subset='doi', keep=False).loc[row.name] 
        else '', axis=1
    )
    return df


def main():
    
    # Create a ConfigParser object
    config = configparser.ConfigParser()
    # Read the ini file
    config.read('config/search_param_config.ini')
    # Retrieve parameters for the search and convert to the appropriate types
    screening = config.get('pilot', 'screening') 

    
    current_path = Path(__file__).resolve().parent
    parent_path = current_path.parent
    
    config_file_path = parent_path / 'output'
    file_list = [f.name for f in config_file_path.iterdir() if '.csv' in f.name]
    
    for file in file_list:
        filepath = os.path.join(config_file_path, file)
        file_handler = File_Handler(filepath, sep=';')
        file_handler.get_raw_data()
        df = file_handler.get_raw_data()
        
        if screening != 'None': 
            nr_randomizations = config.getint('pilot', 'nr_randomizations') 
            df = pilot_randomizing(df, nr_randomizations)
        
        df = mark_duplicates(df)
        
        df.to_csv(filepath, index=False, sep=';')
        print(f'Duplicates and/or randomization finished')


if __name__ == "__main__":
    main()