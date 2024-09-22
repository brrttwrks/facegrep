# facegrep

A CLI tool to grep for faces in images. Works with [Aleph](https://github.com/alephdata/aleph).

## Installation

```sh
pip install .
```

### To launch pgvector database and neo4j database using Docker

```sh
cd docker/
docker-compose up -d
```

### To init the database and create tables

```sh
facegrep init
```

## Usage

### Use help to list the commands and options

```sh
facegrep --help
```

### Add entity to pgvector database for searching

```sh
facegrep entity add path/to/image.png
```

Optionally, you can  tag the entity for the option to filter search by tag(s)

```sh
facegrep entity add path/to/image.png -t occrp
```

### List all entities you have in your pgvector database

```sh
facegrep entity list
```

This returns JSONL new-line delimited objects you can do things with. Like use with jq.

### Search an image for matches against your pgvector database

```sh
facegrep entity search path/to/image.png
```

Optionally, you can filter the search to only search for entities containing one or more tags.

```sh
facegrep entity search path/to/image.png -t occrp -t fraud_factory
```

This stores any matches found into a report and returns a report ID you can use to list the records of the report.

```sh
facegrep report export -r $(facegrep entity search path/to/image.png)
```

You can also just list all the reports.

```sh
facegrep report list
```

### Search an Image entity in Aleph against yoru pgvector database

This requires you have permission to read the entities in the dataset. To read more about using [alephclient](https://docs.alephdata.org/developers/alephclient), check out its documentation. The main thing is to have the alephclient env variables set.

```sh
facegrep aleph search <entity_id>
````

### Search all the images in a dataset

This can take a while depending on the dataset. You can increase the number of workers accordingly.

```sh
facegrep aleph crawl <foreign_id> --workers 4
```

### Export report records

```sh
facegrep report export -r <report_id> -o json
```

This outputs JSONL new-line delimited JSON record objects. This is the default and the -o json is optional.

```sh
facebook report export -r 42 -o neo4j
```

This will write the matched person and the source as nodes and the relationship between them as an edge. On a good day, this will enable you to see if someone is related to another person directly or indirectly via other people in images. You'll kneed to add set the env variables to connect to your neo4j database, as described in the settings.py file.

