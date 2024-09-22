from .settings import FACEGREP_POSTGRES_URI
from .settings import FACEGREP_NEO4J_URI
from .settings import FACEGREP_NEO4J_USERNAME
from .settings import FACEGREP_NEO4J_PASSWORD
import psycopg
from psycopg.sql import SQL, Literal
from psycopg.rows import dict_row
from enum import Enum
from neo4j import GraphDatabase


class Neo4j:
    def connect():
        uri = FACEGREP_NEO4J_URI
        auth = (FACEGREP_NEO4J_USERNAME, FACEGREP_NEO4J_PASSWORD)
        return GraphDatabase.driver(uri, auth=auth)


class Tag:
    def __init__(self, entity_id, name):
        self.entity_id = entity_id
        self.name = name

    @classmethod
    def init_database(cls):
        sql = """
              CREATE TABLE IF NOT EXISTS tags (
                  id BIGSERIAL PRIMARY KEY,
                  entity_id BIGSERIAL NOT NULL REFERENCES entities (id),
                  name TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT NOW(),
                  UNIQUE (entity_id, name)
              );
              """
        with psycopg.connect(FACEGREP_POSTGRES_URI) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql)

    def store(self):
        sql = """
              INSERT INTO tags (entity_id, name) VALUES (%s, %s);
              """
        sql_data = (self.entity_id, self.name)
        with psycopg.connect(FACEGREP_POSTGRES_URI) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                try:
                    cur.execute(sql, sql_data)
                except psycopg.errors.UniqueViolation as e:
                    print(f"Tag already exists for entity: {self.name}")


class Entity:
    def __init__(self, name, tag, id=None ):
        self.id = id
        self.name = name
        self.embeddings = list()
        self.tags = list()
        
        self.store()
        self.add_tags(tag)

    def add_embedding(self, embedding):
        embedding = Embedding(self.id, embedding)
        embedding.store()
        self.embeddings.append(embedding)

    @classmethod
    def get_entity_by_id(cls, entity_id):
        sql = """
                   SELECT *
                   FROM entities
                   WHERE id = {};
                   """
        sql_data = (entity_id,)
        with psycopg.connect(FACEGREP_POSTGRES_URI) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                record = cur.execute(sql, sql_data).fetchone()
        entity = cls__init__(record["id"], record["name"])
        return entity

    @classmethod
    def get_entities(cls):
        sql = """
              SELECT entities.id,
                     name,
                     created_at,
                     COUNT(name) AS embeddings_count
              FROM embeddings
              RIGHT JOIN entities
              ON embeddings.entity_id = entities.id
              GROUP BY entities.id, name, created_at
              ORDER BY name ASC;
              """
        with psycopg.connect(FACEGREP_POSTGRES_URI) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                rows = cur.execute(sql).fetchall()
        for row in rows:
            yield row


    def store(self):
        sql = """
              INSERT INTO entities (name) VALUES (%s)
              ON CONFLICT (name)
              DO UPDATE
              SET name = EXCLUDED.name
              RETURNING id;
              """
        sql_data = (self.name,)
        with psycopg.connect(FACEGREP_POSTGRES_URI) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                record = cur.execute(sql, sql_data).fetchone()
        self.id = record["id"]
        return self


    def add_tags(self, tags):
        for t in tags:
            tag = Tag(self.id, t)
            self.tags.append(tag)
            tag.store()


    def __repr__(self):
        return f"Entity(\"{self.name}\", \"tags\": \"[{','.join([t.name for t in self.tags])}]\")"

    @classmethod
    def init_database(cls):
        sql = """
              CREATE TABLE IF NOT EXISTS entities (
                  id BIGSERIAL PRIMARY KEY,
                  name TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT NOW(),
                  UNIQUE (name)
              );
              """
        with psycopg.connect(FACEGREP_POSTGRES_URI) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)


class Embedding:
    def __init__(self, entity_id, embedding):
        self.entity_id = entity_id
        self.embedding = embedding

    @classmethod
    def init_database(cls):
        sql_ext = "CREATE EXTENSION IF NOT EXISTS vector"
        sql = """
              CREATE TABLE IF NOT EXISTS embeddings (
                  id BIGSERIAL PRIMARY KEY,
                  entity_id BIGSERIAL NOT NULL REFERENCES entities (id),
                  embedding VECTOR(4096) NOT NULL
              );
              """
        with psycopg.connect(FACEGREP_POSTGRES_URI) as conn:
            with conn.cursor() as cur:
                cur.execute(sql_ext)
                cur.execute(sql)

    def store(self):
        sql = """
              INSERT INTO embeddings (entity_id, embedding)
              VALUES (%s, %s);
              """
        sql_data = (self.entity_id, self.embedding)
        with psycopg.connect(FACEGREP_POSTGRES_URI) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, sql_data)


def get_cos_distance(embedding, tags, threshold=0.3):
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

class Record:
    def __init__(self, file_path, source, name, cosine_similarity):
        self.file_path = file_path
        self.source = source
        self.name = name
        self.cosine_similarity = cosine_similarity

    @classmethod
    def init_database(cls):
        sql = """
              CREATE TABLE IF NOT EXISTS records (
                  id BIGSERIAL PRIMARY KEY,
                  report_id BIGSERIAL NOT NULL REFERENCES reports (id),
                  file_path TEXT NOT NULL,
                  source TEXT NOT NULL,
                  name TEXT NOT NULL,
                  cosine_similarity NUMERIC NOT NULL,
                  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                  UNIQUE (report_id, file_path, source, name, cosine_similarity)
              );
              """
        with psycopg.connect(FACEGREP_POSTGRES_URI) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)


    def __str__(self):
        return f"Record(\"{self.file_path}\", \"{self.source}\", \"{self.name}\", \"{self.cosine_similarity}\")"

ReportType = Enum("ReportType", "Entity AlephEntity AlephCrawl")

class Report:
    def __init__(self, name, tags, report_type):
        report = self.store(name, tags, report_type, 0)
        self.id = report["id"]
        self.type = report_type
        self.name = report["name"]
        self.created_at = report["created_at"]
        self.tags = tags
        self.record_count = 0
        self.records = list()


    def __str__(self):
        txt = ""
        txt += f"Report ID: {self.id}\n"
        for record in self.records:
            txt += f"\t{record}\n"
        return txt



    def store(self, name, tags, report_type, record_count):
        sql = """
              INSERT INTO reports (name, tags, type, record_count) VALUES (%s, %s, %s, %s)
              RETURNING id, type, name, created_at, tags, record_count;
              """
        sql_data = (name, "|".join(tags), report_type, 0)
        with psycopg.connect(FACEGREP_POSTGRES_URI) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                report = cur.execute(sql, sql_data).fetchone()
        return report

    def update_record_count(self):
        sql = """
              UPDATE reports
              SET record_count = %s
              WHERE id = %s;
              """
        sql_data = (self.record_count, self.id)
        with psycopg.connect(FACEGREP_POSTGRES_URI) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, sql_data)


    def store_records(self):
        sql = """
              INSERT INTO records
              (report_id, file_path, source, name, cosine_similarity)
              VALUES (%s, %s, %s, %s, %s)
              ON CONFLICT (report_id, file_path, source, name, cosine_similarity)
              DO UPDATE
              SET name = EXCLUDED.name
              RETURNING *;
              """
        values = []
        for r in self.records:
           values.append((self.id, r.file_path, r.source, r.name, r.cosine_similarity))
        with psycopg.connect(FACEGREP_POSTGRES_URI) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.executemany(sql, values)
        self.update_record_count()


    def add(self, record):
        self.records.append(record)
        self.record_count += 1

    @classmethod
    def get_records(cls, report_id):
        sql = """
              SELECT *
              FROM records
              WHERE report_id = %s;
              """
        sql_data = (report_id,)
        with psycopg.connect(FACEGREP_POSTGRES_URI) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                records = cur.execute(sql, sql_data).fetchall()
        for record in records:
            yield record


    @classmethod
    def get_reports(cls):
        sql = """
              SELECT *
              FROM reports;
              """
        with psycopg.connect(FACEGREP_POSTGRES_URI) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                rows = cur.execute(sql).fetchall()
        for row in rows:
            yield row


    @classmethod
    def init_database(cls):
        sql = """
              CREATE TABLE IF NOT EXISTS reports (
                  id BIGSERIAL PRIMARY KEY,
                  type TEXT NOT NULL,
                  name TEXT NOT NULL,
                  record_count INT NOT NULL,
                  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                  tags TEXT
              );
              """
        with psycopg.connect(FACEGREP_POSTGRES_URI) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
