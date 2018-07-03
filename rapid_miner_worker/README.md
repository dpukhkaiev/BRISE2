### Worker node 

> All code that performs clearing work. The main objective is to reduce staff resources

- Dependancy: Python 3.6, [Flask](http://flask.pocoo.org/docs/0.12/ "Flask"), Docker, 

- [Service](../worker_service/README.md)

![service <==> worker](../worker_service/service.jpg "dependencies between the workers and the service")

In case of changing workers:
1. Add worker container
2. Write correct container name from `[alpha, beta, gamma, delta]`
3. Change `WORKER_COUNT`