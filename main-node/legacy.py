import docker
import os
import fnmatch
import csv

def runRemoteContainer(host, image):

    # Creating client object that reflects connection to remote docker daemon
    # Verifying that connection is established
    try:
        client = docker.DockerClient(
            base_url='tcp://' + host['ip'] + ':' + str(host['port']))
        pingIsOk = client.ping()

        if pingIsOk: print("Ping is OK, remote daemon %s is available!" % host['ip'])
        else:
            print("Unable to recieve proper ping responce from %s, check script/docker configuration." % host['ip'])
            return 3
    except docker.errors.APIError as e:
        print(e)
        return 3

    #   Listing images in remote machine and downloading image from Docker hub if needed
    client_images = []
    for img in client.images.list():
        client_images += img.tags

    if str(image["name"] + image["tag"]) not in client_images:
        try:
            client.images.pull(image["name"], image["tag"])

        except docker.errors.APIError as e:
            print("Unable to load docker image from Docker hub: %s" % e)
            return 3

    else:
        print("Needed image already exists in %s" % host['ip'])

    # Running docker container on remote host.
    # TODO - change it to building normal container from normal dockerfile that will copy all needed files to remote host and rung entry point (Python script)
    container = client.containers.run(image=image["name"] + image["tag"], detach=True)
    # print "Container logs:"
    # print container.logs()
    return 0

def run_sobol(path_to_sobol_file="/home/sem/TMP/BRISE/"):
    # This method runs local sobol.R script for getting "pseudorandom" starting configuration

    # Prepare experiment number, will be used in following methods.
    experiment_number = 0
    for file in os.listdir('.'):
        if fnmatch.fnmatch(file, "sobol_output_*.csv"):
            tmp_experiment_number = int(file.replace("sobol_output_", "").replace(".csv", ""))
            if experiment_number <= tmp_experiment_number:
                experiment_number = tmp_experiment_number + 1

    #   sobol.R run to generate config file
    sobolFile = "sobol_output_" + str(experiment_number) + ".csv"

    execution_result = os.system("Rscript %ssobol.R 96 %s" % (path_to_sobol_file, sobolFile))

    #   If running sobol.R script failed - read the last one
    if execution_result != 0:
        # Finding the "freshest" "sobolFile..."
        sobolFile = ['sobol_output_.txt', 0] # [name, last modification time]
        for file in os.listdir('.'):
            if fnmatch.fnmatch(file, 'sobol_output_*.csv'):
                if os.stat(file).st_mtime > sobolFile[1]:
                    sobolFile[0] = file
                    sobolFile[1] = os.stat(file).st_mtime

    # Reading sobol script output to list [(#ofThreads, frequency)]
    with open(sobolFile, 'r') as f:
        sobol_output = []
        reader = csv.DictReader(f)
        for line in reader:
            sobol_output.append((float(line["TR"]), float(line["FR"])))

    # Mapping sobol.R output to real configuration
    # looks like something weird

    freqs = [1200., 1300., 1400., 1600., 1700., 1800., 1900., 2000., 2200., 2300., 2400., 2500., 2700., 2800.,
             2900., 2901.]
    threads = [1, 2, 4, 8, 16, 32]
    config = []
    for point in sobol_output:
        config.append([threads[int(point[0])-1], freqs[int(point[1]) - 1]])

    return [experiment_number, config]
