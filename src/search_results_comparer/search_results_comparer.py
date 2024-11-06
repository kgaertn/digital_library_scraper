"""
Script to compare search results between two files, e.g. excel and csv, then save the comparison results.
This script provides a workflow for loading search results, comparing them to identify additional and removed entries,
and saving the merged data with comparison notes.

Modules:
    - datetime: Provides date and time manipulation utilities.
    - pathlib: Provides object-oriented filesystem paths.
    - sys, os: Used for appending parent directories to system paths.
    - scr.file_handler.file_handler: Custom file handling module

Functions:
    - load_old_results: Loads previous search results from an Excel file.
    - load_new_results: Loads new search results from a CSV file.
    - load_results: General-purpose loader for CSV or Excel files.
    - save_results: Saves the comparison results to a timestamped CSV file.
    - compare_searches: Compares new and old results, marking new entries with 'Add' and removed entries with 'Remove'.
    - create_file_path: Finds and returns the path of a file in a directory based on a condition (e.g., file extension).
    - main: Main workflow function to execute the entire script.
Note:
    Results are compared based on the title. With some titles, if they contain special characters, this does not work perfectly. 
    Compare the marked publications manually, or use the post_processing script to find duplicates.
"""

from datetime import datetime
from pathlib import Path
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.file_handler.file_handler import *

def load_results(file_path: str, sep: str = ';', excel_sheet_name: str|None = None) -> pd.DataFrame:
    """
    Load data from a file, supporting both CSV and Excel formats based on the provided file path.

    Args:
        file_path (str): Path to the file.
        sep (str): Delimiter for the file, default is ';'.
        excel_sheet_name (str | None): Name of the Excel sheet to load (only used if loading an Excel file).

    Returns:
        pd.DataFrame: DataFrame containing data from the specified file.
    """
    if excel_sheet_name != None:
       file_handler = File_Handler(file_path, sep = sep, excel_sheet_Name=excel_sheet_name)
    else:   
       file_handler = File_Handler(file_path, sep = sep)
    return file_handler.data  

def save_results(files_path: str, resulting_df: pd.DataFrame):
    """
    Save the comparison results to a CSV file with a timestamp in the filename.

    Args:
        files_path (str): Directory where the resulting CSV file should be saved.
        resulting_df (pd.DataFrame): DataFrame containing the merged comparison results.

    Returns:
        None
    """
    current_timestamp = datetime.now()
    formatted_timestamp = current_timestamp.strftime("%Y-%m-%d_%H%M%S")   
    
    file_name = f'{formatted_timestamp}_combined_search_articles.csv'
    save_path = os.path.join(files_path, file_name)

    resulting_df.to_csv(save_path, index=True, sep=';', index_label='article_id')

    print(f'Saved articles to {file_name}')

def compare_searches(new_results_df: pd.DataFrame, old_results_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compare new and old search results DataFrames, identifying new entries and removed entries.

    Args:
        new_results_df (pd.DataFrame): DataFrame with new search results.
        old_results_df (pd.DataFrame): DataFrame with previous search results.

    Returns:
        pd.DataFrame: A merged DataFrame with 'Add' or 'Remove' notes indicating new or removed entries.
    """  
    add_results_df = new_results_df[~new_results_df['title'].isin(old_results_df['title'])]
    remove_results_df = old_results_df[~old_results_df['title'].isin(new_results_df['title'])]
    
    add_results_df.loc[:, 'Notes'] = 'Add'
    old_results_df.loc[old_results_df['title'].isin(remove_results_df['title']), 'Notes'] = 'Remove'
    
    resulting_df = pd.concat([old_results_df, add_results_df], axis=0, ignore_index=True)
    return resulting_df
    
def create_file_path(files_path: str, condition: str) -> str:
    """
    Locate and return the path of a file in the specified directory based on a given condition (e.g., file extension).

    Args:
        files_path (str): Path to the directory to search for the file.
        condition (str): Condition to filter files, typically a file extension (e.g., '.csv').

    Returns:
        str: Path to the file that matches the condition, if found.
    """
    file_names = [f.name for f in files_path.iterdir()]
    result_file_path = ''
    for file_name in file_names:
        if condition in file_name:
            result_file_path = files_path / file_name 
    return result_file_path

def main():    
    """
    Main function to execute the script workflow, including loading data, comparing results, and saving output.
    """
    current_path = Path(__file__).resolve().parent
    parent_path = current_path.parent.parent
    
    files_path = parent_path / 'input/compare_searches'
    excel_sheet_name = 'TitleAbstract'

    new_results_path = create_file_path(files_path, '.csv')
    old_results_path = create_file_path(files_path, '.xlsx')
    
    new_results_df = load_results(new_results_path)   
    old_results_df = load_results(old_results_path, excel_sheet_name=excel_sheet_name)
    
    resulting_df = compare_searches(new_results_df, old_results_df)
   
    # create output folder if it doesn't exist
    output_dir = os.path.join(parent_path, 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
 
    save_results(output_dir, resulting_df)
    print("")

if __name__ == "__main__":
    main()