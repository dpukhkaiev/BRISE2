### RapidMiner worker setup guide

You can run [RapidMiner data science platform](https://rapidminer.com) as a worker in BRISE. Main node already contains experiment descriptions for 4 MachineLearning algorithms, that can be run with the help of RapidMiner:
* [NaiveBayes](../main-node/Resources/MLExperiments/NB/)
* [RandomForest](../main-node/Resources/MLExperiments/RF/)
* [SupportVectorMachine](../main-node/Resources/MLExperiments/SVM)
* [NeuralNet](../main-node/Resources/MLExperiments/NN)

You can find these descriptions in *./main-node/Resources/MLExperiments folder*.

**WARNING:** By default these experiments will not provide any result. You need to setup BRISE with RapidMiner according to this guide first.

In order to try RapidMiner, you will need **RapidMiner Studio** and some **input data** as well. Please, contact Dmytro Pukhkaiev to get access to the input data (*ServerRepository* folder).

In order to set up RapidMiner in container you need to perform 2 general steps:

<details>
<summary>1.  Preliminary RapidMiner setup on your host machine </summary>
    
*  Download RapidMiner Studio from: https://rapidminer.com/get-started/ (you will be asked to fill in some personal data here)
*  Unzip the downloaded archive on your host machine 
*  Run *your-unzipped-folder/rapidminer-studio/RapidMiner-Studio.sh* - RapidMiner Studio GUI will be opened after performing this step
*  In GUI you will be asked to sign up and confirm your email address. After performing these steps you will get a trial RapidMiner license, valid for 30 days 
*  Close RapidMiner Studio.
*  Go to *~/.RapidMiner* (it is a hidden folder that was created after your first RapidMiner launch) and copy *ServerRepository* folder with input data into *~/.RapidMiner/repositories/*: `cp -r ~/.RapidMiner/ServerRepository ~/.RapidMiner/repositories/`
*  Open *your_home_folder/.RapidMiner/repositories.xml* file and replace lines:
    
```
    <file>/home/username/.RapidMiner/repositories/Local Repository</file>
    <alias>Local Repository</alias>
```
with: 

```
    <file>/home/w_user/.RapidMiner/repositories/ServerRepository</file>
    <alias>ServerRepository</alias>
```
Now you have prepared everything locally and can move to the container setup!
</details>
<details>
<summary>2. RapidMiner setup in BRISE worker container</summary>

*  Copy and paste the whole *your_home_folder/.RapidMiner* folder into *./worker*
*  Copy and paste the whole *your-unzipped-folder/rapidminer-studio* folder into *./worker*
After a proper setup your worker folder tree should look as follows:

```
| 
worker
      | 
      .RapidMiner
            | 
            repositories
                    | 
                    ServerRepository
            | 
            repositories.xml
            | 
            ...
      | 
      rapidminer-studio
            |
            RapidMiner-Studio.sh
            |
            ...
      | 
      Dockerfile
      | ...
```

*  Run BRISE
(Note: You should better run only 1 worker instance on your local machine, because RapidMiner consumes quite a lot of memory. Please, see the minimum requirements for your worker machine here: https://docs.rapidminer.com/9.0/studio/installation/system-requirements.html)
*  After all containers are up and running, try to run one of the experiments from *./main-node/Resources/MLExperiments/* folder.
</details>
