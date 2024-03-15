import argparse
import asyncio
import base64
import os
import random
from pathlib import Path

import weaviate
import weaviate.classes as wvc
from tqdm import tqdm
from weaviate.collections import Collection

COLLECTION_NAME = 'Dishes'
# Set up the client
client = weaviate.connect_to_local()


def create_collection():
    # If collection already exists, delete it
    if client.collections.exists(COLLECTION_NAME):
        client.collections.delete(COLLECTION_NAME)

    # Create collection
    client.collections.create(
        name=COLLECTION_NAME,
        properties=[
            wvc.config.Property(
                name="image",
                data_type=wvc.config.DataType.BLOB,
                description="Image of food"
            ),
            wvc.config.Property(
                name="cuisine",
                data_type=wvc.config.DataType.TEXT,
                description="The dish origin"
            ),
            wvc.config.Property(
                name="filepath",
                data_type=wvc.config.DataType.TEXT,
                description="Image filepath",
                skip_vectorization=True
            )
        ],
        description="Different foods/dishes in the world",
        vectorizer_config=wvc.config.Configure.Vectorizer.multi2vec_clip(
            image_fields=[wvc.config.Multi2VecField(name='image', weight=0.95)],
            text_fields=[wvc.config.Multi2VecField(name='cuisine', weight=0.05)],
            vectorize_collection_name=False
        )
    )
    return client.collections.get(COLLECTION_NAME)


def base64_image_encode(image_file_path):
    with open(image_file_path, "rb") as image_file:
        image_binary = image_file.read()
    return base64.b64encode(image_binary).decode("utf-8")


async def process_file(file_path: str, dishes: Collection):
    cuisine_name = os.path.dirname(file_path).split(os.path.sep)[-1]
    base64_image = base64_image_encode(file_path)

    dishes.data.insert(
        properties={
            "image": base64_image,
            "cuisine": cuisine_name,
            "filepath": str(file_path),
        }
    )


async def insert_images(num_files_to_process: int, dishes: Collection):
    root_dir = Path('Dishes')
    all_picture_paths = list(root_dir.rglob('*.jpg'))
    sampled_pictures = random.sample(all_picture_paths, num_files_to_process)

    print(f'There are {len(all_picture_paths)} images of food available.\n'
          f'Out of them {num_files_to_process} randomly chosen images will be ingested')

    if len(all_picture_paths) < num_files_to_process:
        num_files_to_process = len(all_picture_paths)
        print(f'There are only {len(all_picture_paths)} pictures available. Ingesting them all.')

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


def main():
    num_files_to_process = args.image_number if args.image_number else 1000
    # Fetch CRUD collection object
    dishes = create_collection()
    asyncio.run(insert_images(num_files_to_process, dishes))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Add data with optional number of images to ingest. Default is 1000')
    parser.add_argument('--image-number', type=int, default=None, help='Number of images to ingest')
    args = parser.parse_args()
    try:
        main()
    finally:
        client.close()
