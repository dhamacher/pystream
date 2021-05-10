# pystream
Deploy Pods on AKS to stream incoming data on TCP/UDP ports to Azure Event Hub


# Setup
Open a terminal and login to Azure

    az login

## Create an Azure Container Registry
Use the Azure CLI to create a container registry that we will use to store our images for AKS and ACI

    az acr create --resource-group rg-aks-pystream --name dhamacher --sku Basic

# Overview of Python Scripts
## aiompnode.py
This script runs a producer and consumer pattern using asynchronous IO and multiprocessing to send data from incoming UDP socket to Azure Event Hub

## aiospnode.py
This script runs the same as above; however, rather than using multiprocessing it uses asyncrhonous IO on a single thread.

## tcp-load-tst.py and udp-load-tst.py
This script is used to send UDP/TCP traffic to a host IP and port.

# Build and Run Container
To build this project into a Docker image, use the **make** below:

    make build

After the build is complete, use a docker command to bring up the pystream node. The default port which is **1444**

    docker run --rm -d -p 1444:1444/udp aiasonarstreamingestion:pystream

# Tag and push to Azure
Run the make command that will build, tag, and push your image to Azure Cotnainer Registry. **NOTE** that you change the container registry name in the **Makefile** to push the image to the correct registry.

    make build-azure
