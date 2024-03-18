import base64
import random
from io import BytesIO

import streamlit as st
import weaviate
import weaviate.classes as wvc
from PIL import Image
from streamlit_image_select import image_select

COLLECTION_NAME = 'Dishes'
NUM_RANDOM_PICS = 10

search_params = {
    'return_properties': ['image', 'cuisine'],
    'return_metadata': wvc.query.MetadataQuery(distance=True)
}


@st.cache_resource
def get_collection():
    # setting up client
    client = weaviate.connect_to_local()
    # Fetch CRUD collection object
    return client.collections.get(COLLECTION_NAME)


# Function to get label for a certain text
def search_by_description(description):
    response = dishes.query.near_text(
        query=description,
        limit=NUM_RANDOM_PICS,
        **search_params
    )
    return response.objects


def search_by_object(dish):
    response = dishes.query.near_object(near_object=dish.uuid,
                                        limit=NUM_RANDOM_PICS + 1,
                                        **search_params)
    return response.objects


def search_by_image():
    response = dishes.query.near_image(near_image=base64_image,
                                       limit=NUM_RANDOM_PICS,
                                       **search_params)
    return response.objects


def visualize_response(response_iterable, no_show_first=False):
    cols = st.columns(5)
    for _ in range((NUM_RANDOM_PICS - 5) // 5):
        cols.extend(st.columns(5))

    if no_show_first:
        response_iterable.pop(0)

    for obj, col in zip(response_iterable, cols):
        with col:
            st.image(decode_image_to_bytes(obj))
            st.write(f"{obj.properties['cuisine']} cuisine  \n"
                     f'distance {round(obj.metadata.distance, 3)}')


def get_random_objects(num_of_objects: int):
    all_uuids = [dish.uuid for dish in dishes.iterator()]
    return [dishes.query.fetch_object_by_id(uuid=uuid, return_properties=['image', 'cuisine']) for uuid in
            random.sample(all_uuids, num_of_objects)]


def get_selected_image_index() -> int:
    return image_select(label='Random images',
                        images=[Image.open(decode_image_to_bytes(obj)) for obj in st.session_state.random_images],
                        return_value='index',
                        index=-1,
                        use_container_width=False)


def decode_image_to_bytes(obj):
    return BytesIO(base64.b64decode(obj.properties['image']))


st.set_page_config(
    page_title="Weaviate Dishes Search",
    page_icon=":stuffed_flatbread:",
    layout="wide",
)

dishes = get_collection()

col1, col2 = st.columns([1, 7])
col1.image(
    'https://avatars.githubusercontent.com/u/37794290?s=200&v=4')
col2.title("Weaviate Dishes Search")
col2.header("Multimodal :camera_with_flash: and Multilingual :globe_with_meridians:")
col2.subheader("Discover a dish that appeals to you through its description, "
               "a picture, or by finding one similar to one you already enjoy.")
st.subheader('How do you want to search?')
selection = st.radio("How do you want to search?",
                     ["By description", "By eye", "By picture"],
                     horizontal=True,
                     label_visibility='collapsed')

# random_images = get_random_objects(10)
if selection == "By description":
    with st.form('description_form'):
        st.subheader('Describe the dish you want to find :')
        dish_description = st.text_input(label='Describe the dish you want to find :',
                                         label_visibility='collapsed')
        submitted = st.form_submit_button('Search')
    if submitted and dish_description != '':
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
        st.image(decode_image_to_bytes(selected_image_object))
        st.subheader("Dishes that you would like:")
        result = search_by_object(selected_image_object)
        visualize_response(result, no_show_first=True)

if selection == "By picture":
    col1, col2 = st.columns([1, 2])
    image_file = col1.file_uploader(label="upload a picture of your dish to find a similar one",
                                    type=['png', 'jpg'])
    if image_file is not None:
        image_bytes = image_file.getvalue()
        col2.image(image=image_bytes,
                   width=256)
        if st.button("Search"):
            base64_image = base64.b64encode(image_bytes).decode()
            result = search_by_image()
            visualize_response(result)
