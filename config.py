import os

#Configuration for paths
class Config:
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(ROOT_DIR, 'Data')
    
    FILE_WD = os.path.join(DATA_DIR, 'wikidata-20220521-truthy.nt.bz2')
    INPUT_DIR = os.path.join(DATA_DIR, 'Input Files')
    
