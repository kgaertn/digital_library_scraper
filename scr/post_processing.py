from file_handler.file_handler import *
from pathlib import Path
import random
import configparser

def get_randomization_list(nr_randomizations, min_value, max_value):
    if nr_randomizations > (max_value - min_value + 1):
        raise ValueError("Number of randomizations exceeds the range of unique values.")
    
    random_values = random.sample(range(min_value, max_value+1), nr_randomizations)
    return random_values
        
def pilot_randomizing(df, nr_randomizations):
    min_value = min(df['article_id'])        
    max_value = max(df['article_id'])

    random_values = get_randomization_list(nr_randomizations,min_value, max_value)
    
    df['pilot'] = None  # Initialize with None
    df.loc[df['article_id'].isin(random_values), 'pilot'] = 'x'   
    return df     

def mark_duplicates(df):
    # Create a new column 'duplicate' and mark duplicates with 'x'
    # Create a new column 'is_duplicate_or_empty'
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