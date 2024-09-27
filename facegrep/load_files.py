import hashlib
from pathlib import Path
import requests

from model import File
from api import embeddings_make
import settings

from sqlalchemy import create_engine
from sqlalchemy.orm import Session


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
    embeddings = embeddings_make(file_path)
    file_record = File(hash=file_hash, 
                       filetags=file_tags, 
                       embeddings=embeddings
                )
    with Session(engine) as session:
        session.add(file_record)
        session.commit()



if __name__ == "__main__":
    engine = create_engine(settings.FACEGREP_POSTGRES_URI)
    load_file("test_data/signal-2024-09-22-215929_002.jpeg")
