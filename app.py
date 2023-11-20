import base64
import random

import streamlit as st
import weaviate
from streamlit_image_select import image_select
from weaviate import Config

COLLECTION_NAME = 'Dishes'
NUM_RANDOM_PICS = 10


@st.cache_resource
def get_collection():
    # setting up client
    client = weaviate.Client("http://localhost:8080",
                             additional_config=Config(grpc_port_experimental=50051),
                             )
    # Fetch CRUD collection object
    return client.collection.get(COLLECTION_NAME)


def base64_image_encode(image_file_path):
    with open(image_file_path, "rb") as image_file:
        image_binary = image_file.read()
    return base64.b64encode(image_binary).decode("utf-8")


# Function to get label for a certain text
def search_by_description(description):
    response = dishes.query.near_text(
        query=description,
        limit=NUM_RANDOM_PICS
    )
    return response.objects


def search_by_object(dish):
    response = dishes.query.near_object(near_object=dish.metadata.uuid,
                                        limit=NUM_RANDOM_PICS)
    visualize_response(response.objects, no_show_first=True)


def visualize_response(response_iterable, no_show_first=False):
    cols = st.columns(5)
    for _ in range((NUM_RANDOM_PICS - 5) // 5):
        cols.extend(st.columns(5))

    if no_show_first:
        response_iterable.pop(0)

    for obj, col in zip(response_iterable, cols):
        with col:
            found_img_filepath = obj.properties['filepath']
            st.image(found_img_filepath)
            if hasattr(obj.metadata, 'certainty'):
                st.write(f'certainty {round(obj.metadata.certainty, 2)}')


def get_random_objects(num_of_objects: int):
    all_uuids = [dish.metadata.uuid for dish in dishes.iterator()]
    return [dishes.query.fetch_object_by_id(uuid=uuid) for uuid in random.sample(all_uuids, num_of_objects)]


def get_selected_image_index() -> int:
    return image_select(label='Random images',
                        images=[obj.properties['filepath'] for obj in st.session_state.random_images],
                        return_value='index',
                        index=-1,
                        use_container_width=False)


st.set_page_config(
    page_title="Weaviate Dishes Search",
    page_icon=":stuffed_flatbread:",
    layout="wide",
)

dishes = get_collection()

st.title("Weaviate Similar Dishes Search")
st.subheader("Find a dish that you like by description, picture or finding a similar to existing one")

selection = st.radio("How do you want to search?",
                     ["By description", "By eye", "By picture"])

# random_images = get_random_objects(10)
if selection == "By description":
    dish_description = st.text_input(label="Describe the dish you want to find :")
    if st.button('Search') and dish_description != '':
        search_result = search_by_description(dish_description)
        visualize_response(search_result)

if selection == "By eye":
    if 'random_images' not in st.session_state:
        st.session_state.random_images = get_random_objects(NUM_RANDOM_PICS)

    st.subheader("Choose food that you like to search for similar ones")
    if st.button("Show me more of what you have"):
        st.session_state.random_images = get_random_objects(NUM_RANDOM_PICS)
    selected_image = get_selected_image_index()
    st.subheader("Selected image:")
    if selected_image != -1:
        selected_image_object = st.session_state.random_images[selected_image]
        st.image(selected_image_object.properties['filepath'])
        st.subheader("Dishes that you would like:")
        search_by_object(selected_image_object)

if selection == "By picture":
    image_file = st.file_uploader(label="upload a picture of your dish to find a similar one",
                                  type=['png', 'jpg'])
    if image_file is not None:
        image_bytes = image_file.getvalue()
        st.image(image=image_bytes,
                 width=256)
        if st.button("Search"):
            base64_image = base64.b64encode(image_bytes).decode()
            res = dishes.query.near_image(near_image=base64_image, limit=NUM_RANDOM_PICS)
            visualize_response(res.objects)
