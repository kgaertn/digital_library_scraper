from file_handler.file_handler import *
from pathlib import Path
import random


def get_randomization_list(nr_randomizations, min_value, max_value):
    if nr_randomizations > (max_value - min_value + 1):
        raise ValueError("Number of randomizations exceeds the range of unique values.")
    
    random_values = random.sample(range(min_value, max_value+1), nr_randomizations)
    return random_values
        
        

def main():
    
    nr_randomizations = 25
    
    current_path = Path(__file__).resolve().parent
    parent_path = current_path.parent
    
    config_file_path = parent_path / 'output'
    file_list = [f.name for f in config_file_path.iterdir() if '.csv' in f.name]
    
    for file in file_list:
        filepath = os.path.join(config_file_path, file)
        file_handler = File_Handler(filepath, sep=';')
        file_handler.get_raw_data()
        df = file_handler.get_raw_data()
        
        min_value = min(df['article_id'])        
        max_value = max(df['article_id'])

        random_values = get_randomization_list(nr_randomizations,min_value, max_value)
        
        df['pilot'] = None  # Initialize with None
        df.loc[df['article_id'].isin(random_values), 'pilot'] = 'x'
        
        df.to_csv(filepath, index=False, sep=';')
        print('Randomization for pilot screening finished')


if __name__ == "__main__":
    main()