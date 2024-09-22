from pathlib import Path
import json
import multiprocessing as mp
from .model import (
    Report,
    Record,
    Entity,
    Embedding,
    Neo4j,
    Tag,
    get_cos_distance
)
from collections import OrderedDict
from deepface import DeepFace
from alephclient.api import AlephAPI
from alephclient.errors import AlephException
import requests
import click


api = AlephAPI()

def database_init():
    Report.init_database()
    Record.init_database()
    Entity.init_database()
    Embedding.init_database()
    Tag.init_database()


def embeddings_make(image):
    models = [
        "VGG-Face",
        "Facenet",
        "OpenFace",
        "ArcFace"
    ]
    embeddings = DeepFace.represent(
        image,
        model_name = models[0],
        enforce_detection=False
    )
    return embeddings


def get_name(file_stem):
    return file_stem.replace("_", " ").title()


def entity_add(file_path, tags):
    entity_name = get_name(file_path.stem)
    entity = Entity(entity_name, tags)
    embeddings = embeddings_make(file_path)
    entity.add_embedding(embeddings[0]["embedding"])
    print(f"Added entity: {entity.name} | tags: [{','.join(tags)}]")


def entity_search(report, file_path, source):
    file_path = Path(file_path)
    try:
        embeddings = embeddings_make(file_path)
        for embedding in embeddings:
            entities = get_cos_distance(embedding["embedding"], report.tags)
            if len(entities) >= 1:
                for entity in entities:
                    record = Record(
                        report.id,
                        str(file_path),
                        source,
                        entity["name"],
                        entity["cosine_similarity"],
                    )
                    if record in report.records:
                        continue
                    report.add(record)
    except ValueError as e:
        print(f"Error processing source: {source}")
    finally:
        report.update_record_count()
        click.echo(report.id)


def download_file(url, file_name):
    file_path = Path(file_name)
    with requests.get(url, stream=True) as r:
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                f.write(chunk)
    return file_path 


def worker(queue):
    click.echo(f"Initiating aleph crawl worker: {mp.current_process().name}")
    while True:
        item = queue.get()

        if item == "EOL":
            break

        aleph_search(*item)


def aleph_search(report, entity_id):
    entity = api.get_entity(entity_id)
    if not entity:
        raise Exception(f"Entity not found: {entity_id}")
    if entity["schema"] != "Image":
        raise Exception(f"Entity is not an image: {entity_id}")
    url = entity["links"]["file"]
    file_name = entity["properties"]["fileName"][0]
    file_path = download_file(url, file_name)
    entity_search(report, file_path, entity_id)


def aleph_crawl(report, tag, worker_count):
    queue = mp.Queue()

    workers = []
    for w in range(worker_count):
        p = mp.Process(
            name = f"worker_{w}",
            target = worker,
            args = (queue,),
        )
        workers.append(p)

    [w.start() for w in workers]

    try:
        collection = api.load_collection_by_foreign_id(report.name)
        for idx, entity in enumerate(api.stream_entities(
            collection,
            schema = "Image",
        )):

            if idx % 1_000 == 0 and idx != 0:
                click.echo(f"Enqueued batch: {idx} ...")

            queue.put((report, entity["id"]))


    except AlephException as e:
        raise Exception("Aleph stream failed")
    else:
        [queue.put("EOL") for _ in range(worker_count)]
        [w.join() for w in workers]


def entity_list():
    for entity in Entity.get_entities():
        entity["created_at"] = entity["created_at"].strftime("%Y-%m-%d")
        click.echo(json.dumps(entity))


def report_list():
    for report in Report.get_reports():
        report["created_at"] = report["created_at"].strftime("%Y-%m-%d")
        click.echo(json.dumps(report))


def report_export(report_id, output_format):
    neo4jdb = Neo4j.connect()

    for record in Report.get_records(report_id):
        record["created_at"] = record["created_at"].strftime("%Y-%m-%d")
        record["cosine_similarity"] = float(record["cosine_similarity"])

        if output_format == "neo4j":
            person = f'(p:Person {{name: \'{record["name"]}\'}})'
            merge_person = f'MERGE {person}'
            image = f'(i:Image {{name: \'{record["source"]}\'}})'
            merge_image = f'MERGE {image}'
            edge = f'[r:APPEARS_IN]'
            match = f"""
                    MATCH {person}, {image}
                    MERGE (p)-{edge}->(i)
                    RETURN p.name, type(r), i.name
                    """

            neo4jdb.execute_query(merge_person, database_="neo4j")
            neo4jdb.execute_query(merge_image, database_="neo4j")
            neo4jdb.execute_query(match, database_="neo4j")

        else:
            click.echo(json.dumps(record))

    neo4jdb.close()
