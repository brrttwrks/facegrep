from pathlib import Path
import multiprocessing as mp
from alephclient.api import AlephAPI
from alephclient.errors import AlephException
import requests


api = AlephAPI()


def download_file(url, file_name):
    file_path = Path(file_name)
    with requests.get(url, stream=True) as r:
        with open(file_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return file_path


def worker(queue):
    print(f"Initiating aleph crawl worker: {mp.current_process().name}")
    while True:
        item = queue.get()

        if item == "EOL":
            break

        aleph_search(*item)


def aleph_search(entity_id):
    entity = api.get_entity(entity_id)

    if not entity:
        raise Exception(f"Entity not found: {entity_id}")
    elif entity["schema"] != "Image":
        raise Exception(f"Entity is not an image: {entity_id}")

    url = entity["links"]["file"]
    file_name = entity["properties"]["fileName"][0]
    file_path = download_file(url, file_name)
    
    #entity_search(report, file_path, entity_id) ## update this!


def aleph_crawl(foreign_id, worker_count):
    queue = mp.Queue()

    workers = []
    for w in range(worker_count):
        p = mp.Process(
            name=f"worker_{w}",
            target=worker,
            args=(queue,),
        )
        workers.append(p)

    [w.start() for w in workers]

    try:
        collection = api.load_collection_by_foreign_id(foreign_id)
        for idx, entity in enumerate(
            api.stream_entities(
                collection,
                schema="Image",
            )
        ):

            if idx % 1_000 == 0 and idx != 0:
                print(f"Enqueued batch: {idx} ...")

            queue.put((entity["id"]))

    except AlephException as e:
        raise Exception("Aleph stream failed")
    else:
        [queue.put("EOL") for _ in range(worker_count)]
        [w.join() for w in workers]
