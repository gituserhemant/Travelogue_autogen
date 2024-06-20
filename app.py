from utils import (
    create_user, create_user_profile, create_user_trip, create_trip_destination,create_trip_destination_place,
    create_user_interests, create_trip_location, generate_profile_image,
    execute_sql
)
from persona import generate_travel_log_text, TravelLog, PersonGeneratedContent, get_travel_log_from_persona_text
import streamlit as st
import time
from langchain.chat_models import ChatOpenAI
from settings import (
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT
)
from queue import Queue
import threading
from langchain.callbacks import get_openai_callback
from persona import PersonGeneratedContent, generate_person_text
from settings import OPEN_AI_API_KEY

# Travelogue
st.set_page_config(
    page_title="Travelogue",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

DEBUG = st.sidebar.checkbox('Debug', value=False)

# DEBUG = st.checkbox('Debug', value=False)


# DB Credentials


def generate():
    # validate api key
    if not open_ai_api_key:
        st.error('Error: Please enter a valid OpenAI API Key')

    with get_openai_callback() as cb:
        start_time = time.time()
        # Step 1 - Generate Persona Text
        person_text = generate_person_text(
            gpt_model=gpt_model, api_key=open_ai_api_key)
        # from examples import PERSONA_GENERATED_TEXT
        # person_text = PERSONA_GENERATED_TEXT

        # Step 2 - Initialize output queue for threaded operations
        output_queue = Queue()

        # Step 2a - Start Thread for Generating Travel Log Text
        travel_log_text = generate_travel_log_text(
            persona_text=person_text, api_key=open_ai_api_key, model=gpt_model)

        extract_travel_log = TravelLog.extract(travel_log_text)

        # Step 2b - Select Interests (can be done in the main thread)
        person_obj: PersonGeneratedContent = PersonGeneratedContent.extract(
            person_text)

        profile_image_url, source_url = generate_profile_image(
            full_name=person_obj.full_name, about_me=person_obj.about_me, dob=person_obj.date_of_birth)

        # show profile image
        # st.image(source_url, caption=f'{person_obj.full_name}\'s profile picture for travel application', use_column_width=True)

        # show the image 200x200
        if DEBUG:
            st.image(
                source_url, caption=f'{person_obj.full_name}\'s profile picture', width=200)

        person_obj = person_obj.select_interests()
        if DEBUG:
            st.write(person_obj.dict())

        # Wait for the Travel Log Text Generation Thread to complete

        # Step 3 - Extract Travel Log
        travel_log_obj: TravelLog = extract_travel_log
        if DEBUG:
            st.write(travel_log_obj.dict())

        # info cb at the top of the page

        end_time = time.time()
        time_elapsed = end_time - start_time
        # add time elapsed to the usage info
        usage = f'Time Elapsed: {time_elapsed} seconds\n\n' + str(cb)

        if DEBUG:
            st.info(body=usage)

        # sql commands

        # person to User
        user = create_user(person_obj)

        user_interests = create_user_interests(person_obj)

        user_profile = create_user_profile(person_obj, profile_image_url)

        sql_code = """DO $$
DECLARE
v_user_id bigint;
v_trip_id bigint;
v_location_id bigint;
v_user_trip_id bigint;
v_trip_destination_id bigint;
BEGIN\n
"""

        # st.code(user.to_sql(save_id=True), language='sql')

        sql_code += user.to_sql(save_id=True)

        for interest in user_interests:
            sql_code += interest.to_sql()
        # st.code(sql_1, language='sql')

        # st.code(user_profile.to_sql(), language='sql')
        sql_code += user_profile.to_sql()

        # create location for each trip location
        # sql_2 = ''
        for trip in travel_log_obj.trips:
            user_trip = create_user_trip(trip=trip)
            sql_code += user_trip.to_sql(save_id=True)
            for location in trip.locations:
                location_obj, location_images = create_trip_location(
                    location_name=location.name, category=location.category, city=trip.city, state=trip.state, country=trip.country)
                # if there's no location images don't create the location
                if not location_images:
                    print(
                        f'Error: No images found for {location.name} in {trip.city}, {location.category}, skipping...')
                    continue
                if not location_obj:
                    print(
                        f'Error: No details found for {location.name} in {trip.city}, {location.category}, skipping...')
                    continue
                sql_code += location_obj.to_sql(save_id=True)
                trip_destination = create_trip_destination(
                    location=location, city=trip.city)
                sql_code += trip_destination.to_sql(save_id=True)
                trip_destination_places = create_trip_destination_place(location=location)
                sql_code += trip_destination_places.to_sql()
                for image in location_images:
                    sql_code += image.to_sql()   

        # st.code(sql_2, language='sql')

        sql_code += """END $$;"""

        # st.code(sql_code, language='sql')

        return sql_code

        # create location images for each trip location

        # create trip destination

        # sql_2 = ''
        # for trip in travel_log_obj.trips:
        #     user_trip = create_user_trip(trip=trip)
        #     user_trip_destinations = create_trip_destination(trip=trip)
        #     sql_2 += user_trip.to_sql(save_id=True)
        #     for dest in user_trip_destinations:
        #         sql_2 += dest.to_sql()
        # st.code(sql_2, language='sql')




# add sidebar with options
st.sidebar.title('Travelogue')

# add a selectbox to the sidebar with options to select gpt model, gpt-4 or gpt-3.5-turbo-1106
gpt_model = st.sidebar.selectbox(
    'Select GPT Model',
    ('gpt-3.5-turbo-1106', 'gpt-4')
)


# input for number of personas to generate
num_personas = st.sidebar.number_input(
    'Number of Personas to Generate',
    min_value=1,
    max_value=10,
    value=1,
    step=1,
    # disabled=True
)

# log = st.sidebar.checkbox('Log Output', value=False)

open_ai_api_key = st.sidebar.text_input(
    'OpenAI API Key', value='', type='password')


def get_llm(model, debug=True) -> ChatOpenAI:
    llm = ChatOpenAI(
        api_key=open_ai_api_key,
        model=model,
        verbose=debug
    )

    return llm


def generate_travel_log_text_thread(persona_text, output_queue):
    travel_log = get_travel_log_from_persona_text(
        persona_text=persona_text, model=gpt_model, api_key=open_ai_api_key)
    output_queue.put(('travel_log', travel_log))


# V2
def generate_travel_log_text_thread_v2(persona_text, output_queue):
    travel_log = get_travel_log_from_persona_text(
        persona_text=persona_text, model=gpt_model, api_key=open_ai_api_key)
    output_queue.put(('travel_log', travel_log))


# button to generate personas
generate_personas = st.sidebar.button('Generate Personas')

# if generate_personas:
#     from examples import PERSONA_GENERATED_TEXT
#     from utils import create_user

#     # generate text
#     person_text = PERSONA_GENERATED_TEXT
#     person_obj: PersonGeneratedContent = PersonGeneratedContent.extract(
#         person_text)

#     st.write(person_obj.dict())

#     user_tabl = create_user(person_obj)

#     st.write(user_tabl.dict())

#     st.code(user_tabl.to_sql(), language='sql')


def insert_to_db(sql_code):
    # insert to db
    st.write('Inserting to Database...')
    try:
        # execute sql code
        if DEBUG:
            st.code(sql_code, language='sql')
        execute_sql(sql_code)
        st.success('Successfully inserted to database')
    except Exception as e:
        st.error('Failed to insert to database')
        if DEBUG:
            st.error(e)


if generate_personas:
    for i in range(num_personas):
        st.write(f'Generating Persona {i + 1}')
        try:
            sql_code = generate()

            # insert to db
            insert_to_db(sql_code)
        except Exception as e:
            # st.error('Failed to generate persona')
            st.error(f'Failed to generate persona: {e}')
            if DEBUG:
                st.error(e)
