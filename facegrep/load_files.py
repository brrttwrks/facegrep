import hashlib
from pathlib import Path
import requests

from model import File, Embedding, Person
from api import make_embeddings
import settings
from sqlalchemy import func
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
import numpy as np


def download_file(url, file_name):
    file_path = Path(file_name)
    with requests.get(url, stream=True) as r:
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                f.write(chunk)
    return file_path 

def load_file(file_path:Path|str, file_tags:list[str|None]=[]) -> None:
    session = Session()
    with open(file_path, "rb") as file:
        file_hash = hashlib.sha3_256(file.read()).hexdigest()
        file.seek(0)
    embeddings = make_embeddings(file_path)
    for embedding in embeddings:
        top_match = get_cos_distance(embedding.embedding)
        embedding.person_id = top_match.id

    file_record = File(hash=file_hash, 
                       filetags=file_tags, 
                       embeddings=embeddings,
                )
    with Session(engine) as session:
        session.add(file_record)
        session.commit()

def get_cos_distance(embedding):
    query = text("""
        SELECT persons.id, persons.name, 1 - (embeddings.embedding <=> :embedding) as cosine_similarity
        FROM persons
        JOIN embeddings ON persons.id = embeddings.person_id
        WHERE (1 - (embeddings.embedding <=> :embedding)) > :threshold
        ORDER BY cosine_similarity DESC
        LIMIT 1
    """)
    
    params = {"embedding": "[" + ",".join(str(i) for i in embedding) + "]", "threshold": 0.5} 
    
    with Session(engine) as session:
        result = session.execute(query, params)
    return result

if __name__ == "__main__":
    engine = create_engine(settings.FACEGREP_POSTGRES_URI)
    load_file("test_data/signal-2024-09-22-215929_002.jpeg")
