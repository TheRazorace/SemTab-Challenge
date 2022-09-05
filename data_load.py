import bz2
from config import Config
from elasticsearch import Elasticsearch
import sys
import os
import re
from elasticsearch import helpers

class DataLoader:
    
    PREFIX_ENT = b"<http://www.wikidata.org/entity/Q"
    PREFIX_PROP = b"<http://www.wikidata.org/prop/direct/P"
    
    #RDFS_LABEL = b'<http://www.w3.org/2000/01/rdf-schema#label>'
    SCHEMA_NAME = b'<http://schema.org/name>'
    #SKOS_ALT = b'<http://www.w3.org/2004/02/skos/core#altLabel>'
    #SCHEMA_DES = b'<http://schema.org/description>'
    SAME_AS = b'<http://www.w3.org/2002/07/owl#sameAs>'
    
    REGEX = re.compile(r'[À-žß\w\s.\-()\[\]{}]+')
    
    NEW_PROPS ={0, 2, 31, 279, 361, 373, 460, 463, 527, 1448, 1552,
                1647, 1659, 1813, 1889, 2561, 3729, 8408}
    
    NAME_PROPS = {0, 373, 1448, 1813, 2561, 8408}
    INSTANCE_PROP = 31
    HIERARCHY_PROPS = {279, 361, 463, 527, 1552, 1647, 1659, 3729}
    HS_PROPS = {2, 460, 1889}
    
    IGNORE_ENTS = {14782, 4167836, 9476502, 13442814, 27020041}
    
    def __init__(self, es):
        self.es = es
        
    def read_wikidata(self, file):
        
        # self.es.options(ignore_status=[400,404]).indices.delete(index='names')
        # self.es.options(ignore_status=[400,404]).indices.delete(index='instances')
        # self.es.options(ignore_status=[400,404]).indices.delete(index='hierarchy')
        # self.es.options(ignore_status=[400,404]).indices.delete(index='hs')
        
        print(f"Reading {os.path.basename(file)}...")
        
        at_line = 0
        bulk_chunk = 10000000
        #checkpoint = 373000000
        total_lines = 7020000000
        
        name_id = 1
        instance_id = 1
        hierarchy_id = 1
        hs_id = 1
        
        entries = []
        
        #Open file
        with bz2.open(file) as fin:
            for line in fin:
                at_line += 1
                
                #Print loading milestones
                if at_line % 1000000 == 0:
                    print(f"At line {at_line}/{total_lines} [{100*at_line/total_lines:.2f}%];")
                    
                # if at_line < checkpoint :
                #     continue
            
            
                #Load elasticseach bulk    
                if at_line % bulk_chunk == 0:
                    print("Adding bulk to elasticsearch...")
                    helpers.bulk(self.es, entries)
                    entries = []
                    print("Bulk added to elasticsearch!")
                    
                line = line.decode('unicode-escape').encode('utf8')
                
                #Skip non-english literals
                if ("@" in line.decode()[-15:-1].strip()):
                    if (line.decode()[-5:-2].strip() != "en"):
                        continue
                
                #Get subject ID
                if line.startswith(self.PREFIX_ENT):
                    subject_id = self.extract_subject_id(line)
                    #Disposal of fault entries
                    if subject_id < 0:
                        continue
                    
                    #Get property ID
                    parts = line.strip().split(maxsplit=2)
                    parts[2] = parts[2][:-2]
                    property_id = self.extract_property_id(parts[1])
                    
                    #If property is important
                    if property_id != -1:
                        #Get object ID
                        object_id = self._extract_name(parts[2])
                        
                        #Discrimination between entity and literal objects
                        if object_id.startswith(self.PREFIX_ENT):
                            object_id = 'Q' + str(self.extract_subject_id(object_id))                       
                        else:
                            object_id = object_id.decode('utf-8')
                        
                        #Create 'names' entry
                        if property_id in self.NAME_PROPS:   
                            
                            entry = {
                                    "_index": "names",
                                    "document": "doc",
                                    "_id": name_id,
                                    "_source": {
                                        "subject": subject_id,
                                        "property": property_id,
                                        "object": object_id
                                        }
                                    }                          
                            name_id += 1
                         
                        #Create 'instances' entry    
                        elif property_id == self.INSTANCE_PROP:
                            
                            try:
                                if int(object_id[1:]) in self.IGNORE_ENTS:
                                    continue
                            except Exception:
                                continue

                            entry = {
                                    "_index": "instances",
                                    "document": "doc",
                                    "_id": instance_id,
                                    "_source": {
                                        "subject": subject_id,
                                        "object": object_id
                                        }
                                    }
                            instance_id += 1
                        
                        #Create 'hierarchy' entry
                        elif property_id in self.HIERARCHY_PROPS:
                            
                            entry = {
                                    "_index": "hierarchy",
                                    "document": "doc",
                                    "_id": hierarchy_id,
                                    "_source": {
                                        "subject": subject_id,
                                        "property": property_id,
                                        "object": object_id
                                        }
                                    }
                            hierarchy_id += 1
                         
                        #Create 'hs' entry    
                        elif property_id in self.HS_PROPS:
                            
                            entry = {
                                    "_index": "hs",
                                    "document": "doc",
                                    "_id": hs_id,
                                    "_source": {
                                        "subject": subject_id,
                                        "property": property_id,
                                        "object": object_id
                                        }
                                    }
                            hs_id += 1
                            
                        entries.append(entry)
                    
        return
    
    
    def find_last_line(self, file):
        
        """Find entries around a line-checkpoint, to check whether
        they are on elasticsearch"""
        
        at_line = 0
        checkpoint = 373000000
        total_lines = 7020000000
        
        print(f"Reading {os.path.basename(file)}...")
        
        #Open file
        with bz2.open(file) as fin:
            for line in fin:
                at_line += 1
                
                #Print loading milestones
                if at_line % 10000000 == 0:
                    print(f"At line {at_line}/{total_lines} [{100*at_line/total_lines:.2f}%];")
                 
                #Skip lines before checkpoint area
                if at_line < checkpoint - 60 :
                    continue
                
                #Skip non-english literals
                if ("@" in line.decode()[-15:-1].strip()):
                    if (line.decode()[-5:-2].strip() != "en"):
                        continue
                
                #Get subject ID
                if line.startswith(self.PREFIX_ENT):
                    subject_id = self.extract_subject_id(line)
                    #Disposal of fault entries
                    if subject_id < 0:
                        continue
                
                    #Get property ID
                    parts = line.strip().split(maxsplit=2)
                    parts[2] = parts[2][:-2]
                    property_id = self.extract_property_id(parts[1])
                    
                    #If property is important
                    if property_id != -1:
                        #Get object ID
                        object_id = self._extract_name(parts[2])
                        
                        #Discrimination between entity and literal objects
                        if object_id.startswith(self.PREFIX_ENT):
                            object_id = 'Q' + str(self.extract_subject_id(object_id))                       
                        else:
                            object_id = object_id.decode('utf-8')
                         
                        #Print entries around checkpoint
                        print(at_line)
                        print(subject_id, property_id, object_id)
                        print()
                 
                #Break after checkpoint area
                if at_line > checkpoint + 60 :
                    break
                            
                
        return     
                    
                   
    @classmethod
    def extract_subject_id(cls, l):
        
        """Extract entity property of subjects"""
        
        try:
            id = int(l.split()[0][len(cls.PREFIX_ENT):-1])
        except Exception:
            id = -1
        
        return id
    
    @classmethod
    def extract_property_id(cls, l):
        
        """Extract property id if it belongs to the wanted properties"""
        
        try:
            if not l.startswith(cls.PREFIX_PROP):
                if l.startswith(cls.SCHEMA_NAME): return 0
                #elif l.startswith(cls.RDFS_LABEL): return 1
                elif l.startswith(cls.SAME_AS): return 2
                else:
                    return -1
            id = int(l[len(cls.PREFIX_PROP):-1])
            if id not in cls.NEW_PROPS: return -1
        except Exception:
            id = -1

        return id
    
    @staticmethod
    def _extract_name(part: bytes):
        
        """ Extract string from object's bute form"""
        
        part = part.strip()
        if part.startswith(b'"'):
            if b'"@' in part:
                part = part.rsplit(b'"@', 1)[0]
                part = part[1:]
            elif part.endswith(b'"'):
                part = part[1:-1]

        return part
        
     
    
def connect_elastic():
    
    """Connect with elasticsearch server"""
    
    print("Connecting with Elasticsearch...")
    es = Elasticsearch([{"host" : "localhost",
                          "port" : 9200,
                          "scheme": "http"}])
                       #basic_auth=('elastic', 'wd6QF7c5eskMyqFyPvji'))   
    
    #Exit in case of failure
    if not es.ping():
        sys.exit('Connection with ElasticSearch failed!')   
    
    return es
    
if __name__ == '__main__':
    
    es = connect_elastic()
    dl = DataLoader(es)
    dl.read_wikidata(Config.FILE_WD)
    #dl.find_last_line(Config.FILE_WD)
    es.transport.close()

    