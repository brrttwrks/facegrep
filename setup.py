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
        "Click",
        "psycopg[binary]",
        "opencv-python",
    ],
    entry_points={
        'console_scripts': [
            'facegrep = facegrep.cli:cli',
        ],
    },
)
