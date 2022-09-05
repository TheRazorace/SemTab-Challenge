from config import Config
import pandas as pd
import os
import glob
import sys
import numpy as np
import ftfy
from bs4 import BeautifulSoup


def load_table(file):
    
    """Load CSV input file"""
    
    try:
        df = pd.read_csv(file, encoding='utf-8')
    except IOError:
        sys.exit('No such file in the directory!')
        
    return df


def clean_table(df):
    
    """Get rid of None values, weird characters and HTML tags"""
    
    for index, row in df.iterrows():
        for col in df.keys():
            text = row[col]
            if type(text) == str :
                text = BeautifulSoup(text, features="lxml").get_text()
                text = ftfy.fix_text(text)
                row[col] = text
                
    df = df.replace("", np.nan)
    df = df.replace(" ", np.nan)
    df = df.replace("-", np.nan)
    df = df.replace("NaN", np.nan)
    df = df.replace("none", np.nan)
    df = df.replace("None", np.nan)
    df = df.replace("uknown", np.nan)
    df = df.dropna()
    
    return df


# if __name__ == '__main__':
    
#     input_dr = Config.INPUT_DIR
#     for file in glob.glob(os.path.join(input_dr, '*.csv')):
#         df = load_table(file)
#         df = clean_table(df)
#         print(df)
        
        
        
        
        
        