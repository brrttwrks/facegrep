import os

FACEGREP_POSTGRES_URI = os.getenv("FACEGREP_POSTGRES_URI")
FACEGREP_WORKER_COUNT = int(os.getenv("FACEGREP_WORKER_COUNT"))
FACEGREP_NEO4J_URI = os.getenv("FACEGREP_NEO4J_URI")
FACEGREP_NEO4J_USERNAME = os.getenv("FACEGREP_NEO4J_USERNAME")
FACEGREP_NEO4J_PASSWORD = os.getenv("FACEGREP_NEO4J_PASSWORD")
