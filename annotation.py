from config import Config
import pandas as pd
from preprocessing import load_table
from preprocessing import clean_table
import glob
import os
import spacy

def annotate(nlp, df):
    
    """Column annotation to help scoring"""
    
    ent_labels = []
    
    #For every csv column
    for col in df.keys():
        col_content = ""
        #literal_content = "Properties are "
        possible_labels = ["NE"] * int(df[col].count() / 5)
        if len(possible_labels) == 0:
            possible_labels = ["NE"]
        
        #For every row
        for index, row in df.iterrows():     
            text = row[col]
            if type(text) == str :
                col_content += text + " "
            # else: 
            #     literal_content += str(text) + ". "
        
        #If column is entity, try to extract entity type using NLP
        if len(col_content) > 1:
            col_doc = nlp(col_content)
            
            if col_doc.ents: 
                for ent in col_doc.ents:
                    possible_labels.append(ent.label_)
                
                ent_labels.append(max(set(possible_labels), key = possible_labels.count))
             
            #If results are mixed, assign it as Named Entity (NE)
            else:
                ent_labels.append("NE")
         
        #Else assign it as Literal (will improve)
        else :
            ent_labels.append("LITERAL")
            
    #print(ent_labels)
            
 
    return ent_labels

# if __name__ == '__main__':
        
#     nlp = spacy.load('en_core_web_sm')
#     input_dr = Config.INPUT_DIR
    
#     for file in glob.glob(os.path.join(input_dr, '*.csv')):
#         df = load_table(file)
#         df = clean_table(df)
#         print(df)
#         annotate(nlp, df)
#         print()
