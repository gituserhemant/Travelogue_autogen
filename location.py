# get location coordinates from google places api from given string, for example: "Eiffel Tower, Paris"
import json
import requests
from urllib.parse import urlencode, quote_plus
from enum import Enum
from datetime import datetime
from typing import List

MOBI_API_KEY = 'UUgWbqY4VW2wmSM7gv1zx2qJeDJdnpeslXkCDDK9'
GOOGLE_API_KEY = 'AIzaSyDBU6gh-_zdkIp50SQ4he1h7Ay6NF8xn8Q'


class GoogleAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url_autocomplete = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
        self.base_url_findplace = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"

    def get_location_coordinates(self, place_name):
        """
        Get the location coordinates (latitude and longitude) of a place using Google Places API.

        :param place_name: Name of the place (e.g., "Eiffel Tower, Paris").
        :return: A tuple (latitude, longitude) or an error message.
        """
        params = {
            'input': place_name,
            'inputtype': 'textquery',
            'fields': 'geometry',
            'key': self.api_key
        }

        response = requests.get(self.base_url_findplace, params=params)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'OK':
                location = data['candidates'][0]['geometry']['location']
                return location['lat'], location['lng']
            else:
                raise Exception(f"Error: {data['status']}")
        else:
            raise Exception(f"Error: {response.status_code}")

    def get_place_id(self, input_text):
        """
        Get the place ID using input text.

        :param input_text: The input text for place suggestions.
        :return: Place ID or an error message.
        """
        params = {
            "input": input_text,
            "key": self.api_key
        }

        response = requests.get(self.base_url_autocomplete, params=params)
        if response.status_code == 200:
            places = response.json().get("predictions")
            if places:
                # Typically, the first suggestion is the most relevant
                return places[0].get("place_id")
            else:
                return "No place ID found for this input."
        else:
            return f"Error: HTTP status code {response.status_code}"


class MobiAPIException(Exception):
    pass


class MobiliAPIException(Exception):
    pass


class Category(Enum):
    HOTEL = 'ACCOMMODATION'
    RESTAURANT = 'DINING'
    PLACE = 'EXPERIENCE'

    def __str__(self):
        return self.value


class MobiAPI:
    __base_url = "https://staging.takemobi.io/mobility-planner/demo/v2"

    def __init__(self, api_key):
        self.api_key = api_key

    @property
    def headers(self):
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'x-api-key': self.api_key
        }

    def _get(self, url, params=None):
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            return response
        else:
            raise MobiliAPIException(
                f"Error: HTTP status code {response.status_code}\n{response.text}")

    def _post(self, url, **kwargs):
        data = kwargs.pop('data', None)
        if type(data) == dict:
            data = json.dumps(data)

        response = requests.post(
            url, headers=self.headers, data=data, **kwargs)
        if response.status_code == 200:
            return response.json()
        else:
            raise MobiliAPIException(
                f"Error: HTTP status code {response.status_code}\n{response.text}")

    def __get_poi_recommendations(self, city_context, payload, category='EXPERIENCE'):
        url = f"{self.__base_url}/problem/poi-recommendations?context={city_context}&merge_categories=true&sort=best_match&category={category}"

        response = self._post(url, data=payload)

        return response

    def __get_city_context(self, city):
        url = f"{self.__base_url}/domain/contexts/suggestions"
        params = {
            'mode': 'MOBI_AGENT',
            'keyword': city,
            'source': '',
            'destination_only': False,
            'return_contexts': True,
        }
        return self._get(url, params=params)

    def __get_place_id(self, keyword, context, category: Category):
        path = "/domain/poi/suggestions"
        # mode=MOBI_AGENT&keyword=mum&source=&destination_only=false&return_contexts=false

        params = {
            'mode': 'MOBI_AGENT',
            'category': category,
            'keyword': keyword,
            'context': context,
        }
        # use urllib.parse.quote_plus to encode the keyword
        encoded_params = urlencode(params, quote_via=quote_plus, safe='+')

        url = f"{self.__base_url}{path}?{encoded_params}"
        return self._get(url)

    def __get_place_details(self, id):
        url = f"{self.__base_url}/domain/poi"
        params = {
            "id": id,
            "mode": "MOBI_AGENT"
        }
        return self._get(url, params)

    def test(self, id):
        url = f"{self.__base_url}/context/poi"
        params = {
            "id": id,
            "mode": "MOBI_AGENT"
        }
        return self._get(url, params)

    def __get_city_context_by_city_name(self, city: str):
        context_response = self.__get_city_context(city)

        if context_response.status_code == 200:
            candidates = context_response.json().get("candidates")
            if candidates:
                context = candidates[0].get("name")
                context = context.replace(" ", "+")
                return context
            else:
                return None

    def get_location_details(self, location_name, city, category: Category):
        city_context = self.__get_city_context_by_city_name(city)
        location_name = location_name.lower()
        location_name = location_name.replace(
            city.lower(), '').replace(category.name.lower(), '')
        print(f'Name: {location_name}')
        # get place id
        place_id_response = self.__get_place_id(
            keyword=location_name, context=city_context, category=category)

        if place_id_response.status_code == 200:
            candidates = place_id_response.json().get("candidates")
            if candidates:
                place_id = candidates[0].get("id")
                place_details_response = self.__get_place_details(place_id)
                if place_details_response.status_code == 200:
                    place_details = place_details_response.json()
                    return place_details
                else:
                    return None


if __name__ == '__main__':
    mobi_client = MobiAPI(MOBI_API_KEY)
    # Le Jules Verne, Paris - DINING
    city = 'Tokyo'
    location_name = 'Sukiyabashi Jiro'

    # response = mobi_client.get_location_details(
    #     location_name=location_name, city=city, category=Category.RESTAURANT)

    # if not response:
    #     print(f"Error: No details found for {location_name}")

    # print(response)


    mobi_id = '16026301-49af-3917-82b8-53022c514a81'

    response = mobi_client.get_place_details(mobi_id)
    
    print(response.json())