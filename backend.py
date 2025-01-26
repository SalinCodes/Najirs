#Importing libraries
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine
import pandas as pd
import unicodedata
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
import ast
from configparser import ConfigParser

web = FastAPI()

#Initialize config parser
config = ConfigParser()
config.read('config.ini')

#Accessing database details
db_config = config['database']
username = db_config['username']
pwd = db_config['password']
hostname = db_config['hostname']
port_id = int(db_config['port_id'])
database = db_config['database']

#Creating SQLAlchemy engine
from sqlalchemy import create_engine, Column, String
engine = create_engine(f'postgresql://{username}:{pwd}@{hostname}:{port_id}/{database}')

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

#Creating a session
Session = sessionmaker(bind=engine)
session = Session()

#Defining ORM model
Base = declarative_base()

class Najirs(Base):
    __tablename__ = "document_similarities"

    document_id = Column(String, primary_key=True)
    similar_document_ids = Column(String)

#Query data safely
results = session.query(Najirs.document_id, Najirs.similar_document_ids).all()
df = pd.DataFrame(results, columns= ["document_id", "similar_document_ids"])

#Function to check if a string is in Devanagari
def is_devanagari(text):
    for char in text:
        if not unicodedata.name(char).startswith('DEVANAGARI'):
            return False
    return True

#Conversion to devnagari
def convert_to_devanagari(text):
    return transliterate(text, sanscript.ITRANS, sanscript.DEVANAGARI)

#Function to get similar documents
def get_similar_documents(query_index):
    similar_document_ids = df.iloc[query_index]['similar_document_ids']

    similar_document_ids = ast.literal_eval(similar_document_ids) #Convert string to list

    return similar_document_ids


#FastAPI route to get similar najirs
@web.get("/najirs/{najir_id}")
async def get_similar_najirs(najir_id: str):
    
    if not is_devanagari(najir_id):
        najir_id = convert_to_devanagari(najir_id)

    if najir_id not in df['document_id'].values:
        raise HTTPException(status_code=404, detail="Najir ID not found")

    query_index = df.index[df['document_id'] == najir_id].tolist()[0]

    similar_docs = get_similar_documents(query_index)

    results = [{"id": doc_id} for doc_id in similar_docs]

    return {
        "query_id": najir_id,
        "similar_documents": results
    }

    #To start: uvicorn backend:web --reload
    #To test: http://127.0.0.1:8000/najirs/{najir_id}