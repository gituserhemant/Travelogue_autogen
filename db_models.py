from typing import Optional, Tuple
from faker import Faker, Factory
from pydantic import BaseModel, Field, EmailStr, root_validator
from pydantic.fields import ModelField
from typing import Optional, List
from datetime import datetime, timedelta, date, time
import random
from langchain.output_parsers import PydanticOutputParser


table_primary_keys = {
    't_user': 'user_id',
    't_user_profile': 'user_id',
    't_user_interest': 'interest_id',
    't_user_trip': 'trip_id',
    't_location': 'location_id',
    't_trip_destination': 'trip_id',
    't_location_images': 'location_id',
}


class BaseSQLModel(BaseModel):
    __tablename__: str

    def escape(self, value):
        """
        Escape strings for SQL statements.
        """
        new_value = value.replace("'", "''")
        # remove any $ signs
        new_value = new_value.replace("$", "")

        return new_value

    def to_sql(self, exclude_none=True, save_id=False) -> str:
        """
        Generate an SQL INSERT statement for this model instance.

        :return: SQL INSERT command as a string.
        """
        table_name = self.__tablename__
        columns = []
        values = []

        for key, value in self.dict(exclude_none=exclude_none).items():
            columns.append(key)
            if key in ['user_id', 'location_id', 'trip_id']:
                values.append(f"v_{value}")
            elif key in ['created_by',]:
                values.append(f"v_user_id")
            elif isinstance(value, datetime):
                values.append(f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'")
            elif isinstance(value, str):
                # Escape single quotes by doubling them
                #
                escaped_value = self.escape(value)
                values.append(f"'{escaped_value}'")
            else:
                values.append(str(value))

        columns_str = ', '.join(columns)
        values_str = ', '.join(values)
        sql_command = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str})\n"

        # Set last inserted id of the table
        if save_id:
            # Adjust the RETURNING clause based on the primary key field name
            # Ensure table_primary_keys dict is defined elsewhere
            table_primary_key = table_primary_keys[table_name]
            sql_command += f"RETURNING {table_primary_key} INTO v_{table_primary_key};\n"
        else:
            sql_command += f";\n"

        return sql_command

    @classmethod
    def get_created_date(cls) -> str:
        """
        Generate a random date in the last 365 days.

        :return: Random date in the last 365 days as a isoformat string.
        """
        return (datetime.now() - timedelta(days=random.randint(0, 365))).isoformat()


class ListBaseSQLModel(BaseModel):
    models: List[BaseSQLModel]

    def to_sql(self, exclude_none=True, save_id=False) -> str:
        sql_command = f"""BEGIN TRANSACTION;\n\n"""
        for model in self.models:
            sql_command += model.to_sql(exclude_none=exclude_none,
                                        save_id=save_id)
        sql_command += f"""\nCOMMIT TRANSACTION;"""
        return sql_command

    @root_validator
    def validate_models(cls, values):
        for model in values['models']:
            if not isinstance(model, BaseSQLModel):
                raise ValueError('All models must be of type BaseSQLModel')
        return values


class User(BaseSQLModel):
    __tablename__ = 't_user'

    email_id: EmailStr = None
    firebase_id: Optional[str] = None
    title: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    is_locked: bool = False
    is_deleted: bool = False
    created_by: Optional[int] = None
    created_date: datetime = None
    updated_by: Optional[int] = None
    updated_date: Optional[datetime] = None
    is_approved: bool = True
    full_name: Optional[str] = None
    user_code: Optional[str] = None
    authentication_type: Optional[str] = None
    fcm_token: Optional[str] = None
    deleted_date: Optional[datetime] = None


class UserProfile(BaseSQLModel):
    __tablename__ = 't_user_profile'

    user_id: str = Field('user_id', description="User ID")

    nick_name: Optional[str] = None
    mobile_no: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    profile_pic_image: Optional[str] = None
    profile_pic_url: Optional[str] = None
    no_of_followers: int = 0
    no_of_post: int = 0
    country: Optional[str] = None
    profile_cover_url: Optional[str] = None
    lang_preference: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    location_cords: Optional[str] = None
    is_notification_allowed: bool = True
    is_notification_allowed_date: Optional[datetime] = None
    is_pna_accepted: bool = True
    is_pna_accepted_date: Optional[datetime] = None
    country_code_alpha: Optional[str] = None
    country_code_num: Optional[int] = None
    about_me: Optional[str] = None
    link: Optional[str] = None

    # method to generate user, will return (User, Thisclass)

    @classmethod
    def generate_user_profile(cls) -> Tuple[User, 'UserProfile']:
        faker = Faker()
        faker.add_provider(Factory.create('en_US'))
        birthdate = faker.date_of_birth(minimum_age=20, maximum_age=80)
        current_year = datetime.now().year
        age = current_year - birthdate.year
        person = faker.profile()
        # person_str = f'Name: {person["name"]}\nJob: {person["job"]}\nAge: {age}\n'
        first_name = person['name'].split(' ')[0]
        last_name = person['name'].split(' ')[1]
        email = f'{first_name.lower()}.{last_name.lower()}@gmail.com'
        user = User(
            email_id=email,
        )
        user_profile = cls(
            dob=str(birthdate),
            country='United States',
        )
        return user, user_profile


class UserInterest(BaseSQLModel):
    __tablename__ = 't_user_interest'
    user_id: User = Field('user_id', description="User ID")
    interest_key: str = None
    is_enabled: bool = True
    interest_id: int


class UserTrip(BaseSQLModel):
    __tablename__ = 't_user_trip'

    user_id: User = Field('user_id', description="User ID")
    created_by: User = Field('user_id', description="User ID")

    trip_name: str
    trip_start_date: Optional[datetime] = None
    trip_end_date: Optional[datetime] = None
    created_on: datetime = Field(default_factory=datetime.now)
    updated_on: Optional[datetime] = None
    updated_by: Optional[int] = None
    is_deleted: bool = False
    trip_description: Optional[str] = None
    trip_image_url: Optional[str] = None
    trip_type: Optional[str] = None
    trip_tags: Optional[str] = None
    is_bookmarked: Optional[bool] = None
    ref_trip_id: Optional[int] = None
    is_private: bool = False
    is_published: bool = True
    notes: Optional[str] = None
    conversation_id: Optional[int] = None
    is_collaborator_trip: bool = False
    is_stock_img: Optional[bool] = None
    published_date: Optional[datetime] = None

    @classmethod
    def create(cls: 'UserTrip', trip) -> 'UserTrip':
        """
        Create a UserTrip instance from a Trip object.

        :param trip: Trip object with trip details.
        :return: UserTrip instance.
        """
        # Create the UserTrip instance
        user_trip = cls(
            trip_name=trip.trip_name,
            trip_start_date=datetime.strptime(trip.start_date, '%Y-%m-%d'),
            trip_end_date=datetime.strptime(trip.end_date, '%Y-%m-%d'),
            created_on=datetime.now(),
            is_deleted=False,
            is_private=False,
            is_published=True,
            is_collaborator_trip=False,
        )

        # Process locations and hotels
        destinations = cls.process_destinations(trip)

        # Return the UserTrip instance
        return user_trip

    @staticmethod
    def process_destinations(trip) -> List['TripDestination']:
        """
        Process locations and hotels into TripDestination instances.

        :param trip: Trip object with trip details.
        :return: List of TripDestination instances.
        """
        destinations = []
        # Process locations
        locations = trip.locations
        for location in locations:
            destination = TripDestination(
                trip=trip,
                dest_name=location.name,
                dest_stay_start_date=datetime.strptime(
                    location.visit_date, '%Y-%m-%d'),
                created_on=datetime.now(),
            )
            destinations.append(destination)

        # Process hotels
        hotels = trip.hotels
        for hotel in hotels:
            destination = TripDestination(
                trip=trip,
                dest_name=hotel.name,
                dest_stay_start_date=datetime.strptime(
                    hotel.start_date, '%Y-%m-%d'),
                dest_stay_end_date=datetime.strptime(
                    hotel.end_date, '%Y-%m-%d'),
                created_on=datetime.now(),
                is_deleted=False
            )
            destinations.append(destination)

        return destinations


class Location(BaseSQLModel):
    __tablename__ = 't_location'

    # location_id = Field('location_id', description="Location ID")

    address: Optional[str] = None
    country: Optional[str] = None
    photo_url: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    coordinates: Optional[str] = None
    place_id: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    tags: Optional[str] = None
    tags_arr: Optional[str] = None
    location_name: Optional[str] = None
    mobi_id: Optional[str] = None
    description: Optional[str] = None

    @classmethod
    def from_mobi_response(cls, response, city=None, country=None, state=None):
        """
        Create a Location object from a MOBI API response.
        """
        poi = response.get('poi', {})
        location = poi.get('location', {})
        tags = poi.get('tags', [])

        # Convert tags list to a string representation of a set
        tags_arr = '{' + ','.join(f'"{tag}"' for tag in tags) + '}'

        photo_url = list(poi.get('images', {}).values())[
            0] if poi.get('images') else None

        city = city if city else location.get('city')
        country = country if country else location.get('country')
        state = state if state else location.get('state_province')

        return cls(
            address=location.get('address_line1'),
            country=country,
            # get the first image url
            photo_url=photo_url,
            website=poi.get('website'),
            # Assuming phone number is part of the response
            phone=poi.get('phone'),
            coordinates=f"({location.get('lat')}, {location.get('lng')})" if location.get(
                'lat') and location.get('lng') else None,
            place_id=None,
            city=city,
            state=state,
            tags=None,  # Set tags to be empty
            tags_arr=tags_arr,  # Use the formatted tags_arr
            location_name=poi.get('name'),
            # Assuming 'source_id' is the mobi_id
            mobi_id=poi.get('id'),
            description=poi.get('description')
        )


class TripDestination(BaseSQLModel):
    __tablename__ = 't_trip_destination'
    trip_id: UserTrip = Field('trip_id', description="Trip ID")
    location_id: Location = Field('location_id', description="Location ID")
    created_by: User = Field('user_id', description="User ID")

    dest_name: str = None
    dest_desc: Optional[str] = None
    dest_stay_start_date: Optional[datetime] = None
    dest_stay_end_date: Optional[datetime] = None
    is_deleted: bool = False
    created_on: datetime = Field(default_factory=datetime.now)
    updated_on: Optional[datetime] = None
    updated_by: Optional[int] = None
    notes: Optional[str] = None
    sequence_no: int = None
    mobi_context: Optional[str] = None


class LocationImages(BaseSQLModel):
    __tablename__ = 't_location_images'

    location_id: Location = Field('location_id', description="Location ID")

    image_url: Optional[str] = None

    @classmethod
    def from_mobi_response(cls, response) -> List['LocationImages']:
        """
        Create a list of LocationImages objects from a MOBI API response.
        """
        images = response.get('poi', {}).get('images', {})
        return [
            cls(image_url=image_url)
            for image_url in images.values()
        ]


def main():
    user, user_profile = UserProfile.generate_user_profile()
    # print(user.to_sql())

    # print(user_profile.to_sql())

    interest = UserInterest(
        interest_id=1324,
    )

    print(interest.to_sql())


if __name__ == '__main__':
    main()

