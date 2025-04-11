# Filling Test Database
* Start a local docker-compose configuration:
`./brise.sh up -m docker-compose` from the root folder.
* Run benchmark [`fill_db`](../../../../benchmark/benchmark_runner.py) scenario. Each test search space type is executed once.
    * Results of the runs are stored within the main BRISE database.
* Run script [`dump_db.py`](dump_db.py) to create bson-representations of the collections.
* Use [`restore_db()`](../../../tools/restore_db.py) function to populate the test database from bson-dumps.