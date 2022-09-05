from preprocessing import load_table
from preprocessing import clean_table
from annotation import annotate
import glob
import os
import spacy
from config import Config
import pandas as pd
from elasticsearch import Elasticsearch
from data_load import connect_elastic
from elasticsearch.helpers import scan

def entity_lookup(es, df, annotations):
    
    """Use elasticsearch lookup to get candidate entities for a cell"""
    
    columns = df.keys()
    candidate_entities = []
    
    for i in range(len(annotations)):
        if annotations[i] != "LITERAL":
            
            for index, row in df.iterrows(): 
                entity = row[columns[i]]
                
                print(entity)
                
                query = {
                    "query": {
                        "match": {
                            "object.keyword": entity
                        }
                    }
                }
                
                rel = scan(client=es,             
                           query=query,                                     
                           scroll='1m',
                           index='names',
                           raise_on_error=True,
                           preserve_order=False,
                           clear_scroll=True)
                
                results = list(rel)
                #print(results)
                for result in results:
                    candidate_entities.append(result['_source']['subject'])
                
                print(candidate_entities)
                    
                break
            
        break
    
    
    return

if __name__ == '__main__':
    
    nlp = spacy.load('en_core_web_sm')
    input_dr = Config.INPUT_DIR
    es = connect_elastic()
    
    for file in glob.glob(os.path.join(input_dr, '*.csv')):
        df = load_table(file)
        df = clean_table(df)
        annotations = annotate(nlp, df)
        
        entity_lookup(es, df, annotations)
        break

