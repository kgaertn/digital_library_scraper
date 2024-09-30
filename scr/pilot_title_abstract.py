from file_handler.file_handler import *
from pathlib import Path

def main():
    current_path = Path(__file__).resolve().parent
    parent_path = current_path.parent
    config_file_path = os.path.join(parent_path, 'output')
    
    for file in config_file_path:
        print('file')