from settings import (
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT

)
import psycopg2
from psycopg2 import OperationalError
import time
from typing import Tuple, List
import json
from settings import MOBI_API_KEY
from location import MobiAPI
from persona import PersonGeneratedContent, Trip, Hotel, Location, TravelLog
from db_models import User, UserProfile, UserTrip, TripDestination, UserInterest, Location as DBLocation, LocationImages
from datetime import datetime
from typing import List
from location import Category
from image_generator import S3Bucket, DeepAIClient

# def create_user_trip(trip: Trip) -> (UserTrip, List[TripDestination]):
#     user_trip = UserTrip(
#         trip_name=trip.trip_name,
#         trip_start_date=datetime.strptime(trip.start_date, '%Y-%m-%d'),
#         trip_end_date=datetime.strptime(trip.end_date, '%Y-%m-%d'),
#     )

#     destinations = []
#     for location in trip.locations:
#         destinations.append(TripDestination(
#             dest_name=location.name,
#             dest_stay_start_date=datetime.strptime(location.visit_date, '%Y-%m-%d'),
#             dest_stay_end_date=datetime.strptime(location.visit_date, '%Y-%m-%d'),
#         ))

#     for hotel in trip.hotels:
#         destinations.append(TripDestination(
#             dest_name=hotel.name,
#             dest_stay_start_date=datetime.strptime(hotel.start_date, '%Y-%m-%d'),
#             dest_stay_end_date=datetime.strptime(hotel.end_date, '%Y-%m-%d'),
#         ))

#     return user_trip, destinations


def create_user(persona: PersonGeneratedContent) -> User:
    # create user from persona object
    user = User(
        email_id=persona.email_id,
        first_name=persona.first_name,
        last_name=persona.last_name,
        full_name=persona.full_name,
        about_me=persona.about_me,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    return user


def create_user_profile(persona: PersonGeneratedContent, image_url=None) -> UserProfile:
    # create user profile from persona object
    user_profile = UserProfile(
        about_me=persona.about_me,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        profile_pic_url=image_url,
    )

    return user_profile


def create_user_interests(persona: PersonGeneratedContent) -> List[UserInterest]:
    # create user interests from persona object
    user_interests = []
    for interest in persona.sub_interests:
        user_interests.append(UserInterest(
            interest_id=interest.name,
            interest_key=interest.value,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ))

    return user_interests


def escape_characters(text: str) -> str:
    # escape special characters to fit sql query
    return text.replace("'", "''")


def create_user_trip(trip: Trip) -> UserTrip:
    # trip name format, trip_name, City, Month
    trip_start_date = datetime.strptime(trip.start_date, '%Y-%m-%d')

    # get name of the month, May, June, etc.
    month_name = trip_start_date.strftime("%B")
    trip_name = escape_characters(trip.trip_name)
    user_trip = UserTrip(
        trip_name=trip_name,
        trip_start_date=datetime.strptime(trip.start_date, '%Y-%m-%d'),
        trip_end_date=datetime.strptime(trip.end_date, '%Y-%m-%d'),
        created_on=datetime.now(),
    )

    return user_trip


def get_context(city):
    mobi_client = MobiAPI(MOBI_API_KEY)
    context_response = mobi_client.get_city_context(city)

    if context_response.status_code == 200:
        candidates = context_response.json().get("candidates")
        if candidates:
            context = candidates[0].get("name")
            context = context.replace(" ", "+")
            return context
        else:
            return None


def get_place_details(location_name, context, category):
    # get location details from mobi api
    mobi_client = MobiAPI(MOBI_API_KEY)
    place_response = mobi_client.get_place_id(
        keyword=location_name, category=category, context=context)
    return place_response
    if place_response.status_code == 200:
        candidates = place_response.json().get("candidates")
        if candidates:
            place_id = candidates[0].get("id")
            place_details_response = mobi_client.get_place_details(place_id)
            if place_details_response.status_code == 200:
                place_details = place_details_response.json()
                return place_details
            else:
                return None


def create_trip_location(location_name: str, city: str, category: Category) -> TripDestination:

    mobi_client = MobiAPI(MOBI_API_KEY)

    mobi_location_response = mobi_client.get_location_details(
        location_name, city, category)

    location = DBLocation.from_mobi_response(mobi_location_response)

    return location


def create_trip_destination(location: Location, city: str) -> TripDestination:
    # create trip destination from location object
    dest_name = f'{location.name}, {city}'
    trip_destination = TripDestination(
        dest_name=dest_name,
        dest_stay_start_date=datetime.strptime(
            location.visit_date, '%Y-%m-%d'),
        dest_stay_end_date=datetime.strptime(location.visit_date, '%Y-%m-%d'),
        created_on=datetime.now(),
    )

    return trip_destination


def create_trip_location(location_name: str, category: Category, city: str, country: str, state: str) -> Tuple[DBLocation, List[LocationImages]]:
    # create trip destination from location object
    mobi_client = MobiAPI(MOBI_API_KEY)

    print(f'Getting location details for {location_name} in {city}... ')

    mobi_location_response = mobi_client.get_location_details(
        location_name, city, category)
    if not mobi_location_response:
        return None, None

    location = DBLocation.from_mobi_response(
        mobi_location_response, city, country, state)

    location_images = LocationImages.from_mobi_response(mobi_location_response)

    return location, location_images


def create_trip_destinations(trip: Trip) -> List[TripDestination]:
    trip_destinations = []
    for location in trip.locations:
        dest_name = f'{location.name}, {trip.city}'
        trip_destinations.append(TripDestination(
            dest_name=dest_name,
            dest_stay_start_date=datetime.strptime(
                location.visit_date, '%Y-%m-%d'),
            dest_stay_end_date=datetime.strptime(
                location.visit_date, '%Y-%m-%d'),
            created_on=datetime.now(),
        ))

    for hotel in trip.hotels:
        dest_name = f'{hotel.name}, {trip.city}'
        trip_destinations.append(TripDestination(
            dest_name=dest_name,
            dest_stay_start_date=datetime.strptime(
                hotel.start_date, '%Y-%m-%d'),
            dest_stay_end_date=datetime.strptime(hotel.end_date, '%Y-%m-%d'),
            created_on=datetime.now(),
        ))

    return trip_destinations


def generate_profile_image(full_name, about_me, dob: datetime):
    age = datetime.now().year - dob.year

    prompt = f"{full_name}'s {age}yo profile picture for travel application:\n{about_me}"
    client = DeepAIClient()
    response = client.generate_image(prompt)
    # upload image to s3
    s3 = S3Bucket()
    image_url = s3.upload_image_from_url(response['output_url'])
    return image_url, response['output_url']


if __name__ == '__main__':
    # from examples import example_travel_log2 as example_travel_log
    from examples import example_travel_log1 as example_travel_log
    mobi_client = MobiAPI(MOBI_API_KEY)

    locations = 0
    location_with_no_images = 0
    for trip in example_travel_log['trips']:
        for location in trip['locations']:
            locations += 1
            print(
                f'Getting location details for {location["name"]} in {trip["city"]}...')

            mobi_location_response = mobi_client.get_location_details(
                location["name"], trip["city"], Category(location["category"]))

            if not mobi_location_response:
                print(
                    f'Error: No details found for {location["name"]} in {trip["city"]}, {Category(location["category"])}')
                continue

            has_images = mobi_location_response.get('poi').get('images')
            if not has_images:
                location_with_no_images += 1
                print('No images found for this location')
                continue

            else:
                print('Success!')

            time.sleep(0.5)

        for hotel in trip['hotels']:
            locations += 1
            print(
                f'Getting location details for {hotel["name"]} in {trip["city"]}...')

            mobi_location_response = mobi_client.get_location_details(
                hotel["name"], trip["city"], Category.HOTEL)

            if not mobi_location_response:
                print(
                    f'Error: No details found for {hotel["name"]} in {trip["city"]}, {Category.HOTEL}')
                continue

            has_images = mobi_location_response.get('poi').get('images')
            if not has_images:
                location_with_no_images += 1
                print('No images found for this location')
                continue

            else:
                print('Success!')

            time.sleep(0.5)
    print(f'Locations with no images: {location_with_no_images}')
    percent = (location_with_no_images / locations) * 100
    # totla locations: 20
    print(f'Total Locations Number: {locations}')
    print(f'Percent: {percent}%')


def execute_sql(sql_code):
    connection = None
    try:
        # Connect to the PostgreSQL database server using environment variables
        connection = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = connection.cursor()

        # Execute the SQL code
        cursor.execute(sql_code)
        connection.commit()  # Commit the transaction
        print("SQL code executed successfully.")
    except OperationalError as e:
        print(f"An error occurred: {e}")
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            print("Database connection closed.")
