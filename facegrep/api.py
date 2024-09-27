from pathlib import Path
from model import Embedding
from deepface import DeepFace



def embeddings_make(file_path:Path|str):
    results:list[dict] = DeepFace.represent(
        file_path,
        model_name = "VGG-Face",
        enforce_detection=False
    )
    embeddings = [Embedding(embedding=result["embedding"]) for result in results]
    return embeddings