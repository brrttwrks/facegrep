import setuptools

setuptools.setup(
    name='facegrep',
    version='0.1.0',
    packages = setuptools.find_packages(),
    py_modules=[
        "facegrep.api",
        "facegrep.cli",
        "facegrep.model",
        "facegrep.settings",
    ],
    install_requires=[
        "tf-keras",
        "Click",
        "psycopg[binary]",
        "neo4j",
        "deepface",
        "alephclient",
        "followthemoney",
        "requests",
        "sqlalchemy",
        "pgvector"
    ],
    entry_points={
        'console_scripts': [
            'facegrep = facegrep.cli:cli',
        ],
    },
)
