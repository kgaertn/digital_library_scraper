from datetime import datetime
from pathlib import Path
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from scr.file_handler.file_handler import *

def load_old_results(files_path: str, excel_sheet_name: str) -> pd.DataFrame:
    
    excel_file_name = [f.name for f in files_path.iterdir() if '.xlsx' in f.name][0]
    excel_file_path = files_path / excel_file_name
    excel_file_handler = File_Handler(excel_file_path, sep = ';', excel_sheet_Name=excel_sheet_name)
    return excel_file_handler.data

def load_new_results2(files_path: str) -> pd.DataFrame:
    csv_file_name = [f.name for f in files_path.iterdir() if '.csv' in f.name][1]
    csv_file_path = files_path / csv_file_name
    csv_file_handler = File_Handler(csv_file_path, sep = ';')
    return csv_file_handler.data

def load_new_results(files_path: str) -> pd.DataFrame:
    csv_file_name = [f.name for f in files_path.iterdir() if '.csv' in f.name][0]
    csv_file_path = files_path / csv_file_name
    csv_file_handler = File_Handler(csv_file_path, sep = ';')
    return csv_file_handler.data

def main():    
    current_path = Path(__file__).resolve().parent
    parent_path = current_path.parent.parent
    
    files_path = parent_path / 'input/compare_searches'
    excel_sheet_name = 'TitleAbstract'
   
    new_results_df = load_new_results(files_path)   
    old_results_df = load_old_results(files_path, excel_sheet_name)
    
    # Select rows in new_results_df where 'title' is not in old_results_df's 'title' column
    #equal_results_df = new_results_df[new_results_df['title'].isin(old_results_df['title'])]
    #other_equal_results_df = old_results_df[old_results_df['title'].isin(new_results_df['title'])]
    
    add_results_df = new_results_df[~new_results_df['title'].isin(old_results_df['title'])]
    remove_results_df = old_results_df[~old_results_df['title'].isin(new_results_df['title'])]
    
    add_results_df['Notes'] = 'Add'
    old_results_df.loc[old_results_df['title'].isin(remove_results_df['title']), 'Notes'] = 'Remove'
    
    resulting_df = pd.concat([old_results_df, add_results_df], axis=0, ignore_index=True)
    
    
    # Reset the index
    #resulting_df.reset_index(drop=True, inplace=True)
    
    # create output folder if it doesn't exist
    output_dir = os.path.join(parent_path, 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
 
     # Get the current timestamp
    current_timestamp = datetime.now()

    # Format the timestamp (optional)
    formatted_timestamp = current_timestamp.strftime("%Y-%m-%d_%H%M%S")   
    
    file_name = f'{formatted_timestamp}_combined_search_articles.csv'
    save_path = os.path.join(output_dir, file_name)
    
    # save to csv file
    resulting_df.to_csv(save_path, index=True, sep=';', index_label='article_id')

    print(f'Saved articles to {file_name}')
    print("")

if __name__ == "__main__":
    main()