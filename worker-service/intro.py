
import requests

payload = {'fr': '2700.0', 'tr': '32'}
r = requests.get('http://alpha:8080', params=payload)

print("Content", r.content)

# Set in docker-compose. Aliases for worker containers in the network
workers = ["alpha", "beta"]
tasks-stack
