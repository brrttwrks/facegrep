from pathlib import Path
from model import Embedding
from deepface import DeepFace

from sqlalchemy.orm import Session
from model import Person, Embedding

def make_embeddings(file_path:Path|str):
    results:list[dict] = DeepFace.represent(
        file_path,
        model_name = "VGG-Face",
        enforce_detection=False
    )
    embeddings = [Embedding(embedding=result["embedding"]) for result in results]
    return embeddings

def lookup_embeddings(embeddings:list[Embedding]):
    session = Session()

    for embedding in embeddings:
        top_match = get_cos_distance(embedding.embedding, limit=1)

        #session.query(Embedding).filter(Embedding.embedding == embedding.embedding).first()
    session.close()



def get_cos_distance(embedding, tags, threshold=0.3):
    with Session(engine) as session:
        query = (
            session.query(
                Person.id,
                Person.name,
                (1 - (Embedding.embedding % embedding)).label('cosine_similarity')
            )
            .outerjoin(Embedding, Embedding.person_id == Person.id)
            .filter((1 - (Embedding.embedding % embedding)) > threshold)
            )

        # Execute the query
        results = query.all()
        print(results)
        return results




    sql_tag = """
              SELECT ents.id,
                     ents.name,
                     1 - (embedding <=> %s) AS cosine_similarity 
              FROM (
                  SELECT DISTINCT (entities.id),
                         entities.name AS name
                  FROM tags
                  JOIN entities
                  ON entities.id = tags.entity_id
                  WHERE tags.name = ANY(%s)
              ) AS ents 
              JOIN embeddings
              ON ents.id = embeddings.entity_id
              WHERE 1 - (embedding <=> %s) > %s;
              """
    sql_notag = """
                SELECT entities.id AS id,
                       entities.name AS name,
                       1 - (embedding <=> %s) AS cosine_similarity
                FROM embeddings
                RIGHT JOIN entities
                ON embeddings.entity_id = entities.id
                WHERE 1 - (embedding <=> %s) > %s;
                """
    str_rep = "[" + ",".join(str(i) for i in embedding) + "]"
    sql_data_tag = (str_rep, list(tags),  str_rep, threshold)
    sql_data_notag = (str_rep, str_rep, threshold)
    with psycopg.connect(FACEGREP_POSTGRES_URI) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if len(tags) > 0:
                rows = cur.execute(sql_tag, sql_data_tag).fetchall()
            else:
                rows = cur.execute(sql_notag, sql_data_notag).fetchall()
    return rows