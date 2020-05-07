### General information about the database usage in BRISE

BRISE uses [MongoDB](https://www.mongodb.com/), which has a convenient [Python driver](https://api.mongodb.com/python/current/), as a database system. 

**The purpose of using the database in BRISE** is to store the states and results of multiple experiments being executed and to allow BRISE services to exchange their data.

By default the database with the name `BRISE_db` is created on BRISE start up and filled in during the Experiments' run. The name of the database, its address and port can be customized (please, see the run options of the `./brise.sh up` command).

#### BRISE database structure

An overview of the information stored in the database is shown in the following diagram:

![Database instances and relations](./img/BRISE_db_scheme.png)

#### BRISE database clean up

By default the data is being appended to the database as long as the `mongo-db` container exists. If you want to clean the database, please, use `./brise.sh clean_database`. The details you may find using `./brise.sh help` command.

#### Useful commands
If you are running BRISE in containers on your local machine, you may get into database container using `$ docker exec -it mongo-db /bin/bash`. To run the MongoDB console type `mongo db --port 'used_port'` - the standard MongoDB port is 27017, but if BRISE uses the custom port it is needed to be specified. If you use the standard port for MongoDB, you may run just `mongo db` to run the console. 
When the console is running, switch to the used database with `use database_name` (`database_name`=`BRISE_db` by default). Here you can list the collections or perform other actions you may be interested in. Useful mongo Shell commands you may find at [mongo Shell Quick Reference](https://docs.mongodb.com/manual/reference/mongo-shell/).
