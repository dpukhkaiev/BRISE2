# benchmark
The basic architecture for testing approaches to reducing a benchmarking costs

###### TODO : Start a cluster. Launch the API, Master, a Proxy and DNS discovery
Start: 
1. 
    ``` 
    kubectl apply -f deployment.yaml 
    ```

    - List the pods created by the deployment: `kubectl get pods -l app=nginx`
    - Display information about the Deployment: `kubectl describe deployment nginx-deployment`
    - Update deployment: `kubectl apply -f deployment.yaml`
    - Delete the deployment by name: `kubectl delete deployment nginx-deployment`

2. Deploy the Service 
    ``` 
    kubectl create -f service.yaml 
    ```

    - As before, details of all the Service objects deployed with `kubectl get svc`
    - By describing the object it's possible to discover more details about the configuration `kubectl describe svc test_app-svc`


Instantly, the desired state of our cluster has been updated, viewable with `kubectl get deployment`