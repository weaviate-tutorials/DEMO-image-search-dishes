import asyncio
import base64
import os
import random
from pathlib import Path

import weaviate
import weaviate.classes as wvc
from tqdm import tqdm
from weaviate import Config
from weaviate.collection.collection import CollectionObject

COLLECTION_NAME = 'Dishes'
# Set up the client
client = weaviate.Client("http://localhost:8080",
                         additional_config=Config(grpc_port_experimental=50051),
                         )


def create_collection():
    # If collection already exists, delete it
    if client.collection.exists(COLLECTION_NAME):
        client.collection.delete(COLLECTION_NAME)

    # Create collection
    client.collection.create(
        name=COLLECTION_NAME,
        properties=[
            wvc.Property(
                name="image",
                data_type=wvc.DataType.BLOB,
                description="Image of food"
            ),
            wvc.Property(
                name="cuisine",
                data_type=wvc.DataType.TEXT,
                description="The dish origin"
            ),
            wvc.Property(
                name="filepath",
                data_type=wvc.DataType.TEXT,
                description="Image filepath",
                skip_vectorization=True
            )
        ],
        description="Different foods/dishes in the world",
        vectorizer_config=wvc.ConfigFactory.Vectorizer.multi2vec_clip(
            image_fields=[wvc.Multi2VecField(name='image', weight=0.7)],
            text_fields=[wvc.Multi2VecField(name='cuisine', weight=0.3)]
        ),
        generative_config=wvc.ConfigFactory.Generative.openai()
    )
    return client.collection.get(COLLECTION_NAME)


def base64_image_encode(image_file_path):
    with open(image_file_path, "rb") as image_file:
        image_binary = image_file.read()
    return base64.b64encode(image_binary).decode("utf-8")


async def process_file(file_path: str, dishes: CollectionObject):
    cuisine_name = os.path.dirname(file_path).split(os.path.sep)[-1]
    base64_image = base64_image_encode(file_path)

    dishes.data.insert(
        properties={
            "image": base64_image,
            "cuisine": cuisine_name,
            "filepath": file_path,
        }
    )


async def insert_images(num_files_to_process: int, dishes: CollectionObject):
    root_dir = Path('Dishes')
    all_picture_paths = list(root_dir.rglob('*.jpg'))
    sampled_pictures = random.sample(all_picture_paths, num_files_to_process)

    print(f'There are {len(all_picture_paths)} images of food available.\n'
          f'Out of them {num_files_to_process} randomly chosen images will be ingested')

    # Create a tqdm progress bar
    with tqdm(total=num_files_to_process) as pbar:
        async def process_file_with_progress(file_path, dishes):
            result = await process_file(file_path, dishes)
            pbar.update(1)
            pbar.set_description(result)

        tasks = [process_file_with_progress(file_path, dishes) for file_path in sampled_pictures]
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)
        pbar.close()
    print(f"Finished ingesting {len(results)} random files.")


def main(num_files_to_process: int):
    # Fetch CRUD collection object
    dishes = create_collection()
    asyncio.run(insert_images(num_files_to_process, dishes))


if __name__ == '__main__':
    main(1000)
