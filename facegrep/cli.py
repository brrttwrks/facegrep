from .api import database_init
from .api import person_add
from .api import person_search
from .api import person_list
from .api import aleph_search
from .api import aleph_crawl
from .api import report_list
from .api import report_export
from .model import Report, ReportType
from pathlib import Path
import click


@click.group(invoke_without_command=True)
def cli():
    pass


@cli.command()
def init():
    """ Create tables in database """
    database_init()


@cli.group()
def person():
    """ person operations """
    pass


@cli.group()
def aleph():
    """ Aleph entity operations """
    pass


@aleph.command()
@click.argument("entity_id")
@click.option('--tag', '-t', multiple=True)
def search(entity_id, tag):
    report = Report(entity_id, tag, ReportType.AlephEntity)
    aleph_search(report)


@aleph.command()
@click.option("--foreign_id", "-f", required=True)
@click.option('--tag', '-t', multiple=True)
@click.option('--workers', '-w', default=1)
def crawl(foreign_id, tag, workers):
    report = Report(foreign_id, tag, ReportType.AlephCrawl)
    aleph_crawl(report, tag, workers)


@person.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option('--tag', '-t', multiple=True)
def add(file_path, tag):
    """ Add new person or new embedding """
    file_path = Path(file_path)
    person_add(file_path, tag)


@person.command()
def list():
    """ List all entities in database """
    person_list()


@person.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option('--tag', '-t', multiple=True)
def search(file_path, tag):
    """ Compare image faces against database """
    report = Report(file_path, tag, ReportType.Entity)
    person_search(report, file_path, file_path)

@cli.group()
def report():
    """ Report operations """
    pass


@report.command()
def list():
    report_list()

@report.command()
@click.option("--report_id", "-r", required=True)
@click.option("--format", "-o", default="json", required=False)
def export(report_id, format):
    """ Export report as JSON """
    report_export(report_id, format)


if __name__ == "__main__":
    cli(obj={})
