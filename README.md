# Similar images search

## Overview
TODO

### CLIP model
TODO

## Technology stack
- Python
- Weaviate
- Streamlit

### Used Weaviate modules/models

[multi2vec-clip vectorizer](https://weaviate.io/developers/weaviate/modules/retriever-vectorizer-modules/multi2vec-clip)  
The multi2vec-clip module enables Weaviate to obtain vectors locally from text or images using a Sentence-BERT CLIP model.

To be able to use it you need to enable it in the [docker compose file](docker-compose.yml)

## Prerequisites
1. Python3 interpreter installed
1. Ability to execute docker compose 
(The most straightforward way to do it on Windows/Mac is to install 
[Docker Desktop](https://www.docker.com/products/docker-desktop/))

## Setup instructions 

### Start up
1. Clone the repository
1. Download the dataset 
[from this link](https://www.kaggle.com/datasets/abhijeetbhilare/world-cuisines/download?datasetVersionNumber=3) 
and unzip it to the project root

1. Create a virtual environment and activate it
    ```shell
    python3 -m venv venv
    source venv/bin/activate
    ```
1. Install all required dependencies 
    ```shell
    pip install -r requirements.txt
    ```
1. Run containerized instance of Weaviate. It also includes vectorizer module to compute the embeddings.

   > **Note**: Make sure you don't have anything occupying port 8080   
   > If you do, you have the option to either stop that process or change the port that Weaviate is using.
    ```shell
    docker compose up
    ```
1. Index the dataset in Weaviate
    ```shell
    python add_data.py
    ```
1. Run the Streamlit demo
   ```shell
   streamlit run app.py
   ```

### Shut down
1. Both streamlit app and docker compose can be stopped with `Ctrl+C` in the corresponding terminal window
2. To remove created docker containers and volumes use
```shell
docker compose down -v
```

## Usage instructions
TODO

## Dataset license

The dataset used for this example is available on Kaggle: 
https://www.kaggle.com/datasets/abhijeetbhilare/world-cuisines/
