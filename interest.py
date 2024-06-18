import slugify
from pydantic import BaseModel, Field, create_model
from typing import List, Type
import random
from enum import Enum
import pandas as pd
CSV_PATH = './data/t_master_interest.csv'


def create_enum_from_csv(feature_name) -> 'SubInterest':
    """
    Create a dynamic enum based on a given feature name from a CSV file using Pandas.

    :param feature_name: The name of the feature to create an enum for.
    :param csv_file_path: Path to the CSV file.
    :return: A new enum class based on the specified feature.
    """
    # Read the CSV file into a DataFrame
    df = pd.read_csv(CSV_PATH)
    # Filter rows based on the feature name
    filtered_df = df[df['travelogue_feature'] == feature_name]

    # Create a dictionary for enum members
    members = {str(row['interest_id']): row['mobi_sub_feature']
               for _, row in filtered_df.iterrows()}

    # Create and return the dynamic enum
    return SubInterest(slugify.slugify(feature_name, separator='_'), members)


class SubInterest(Enum):
    pass

    def __str__(self):
        return f'{self.name} - {self.value}'

    def get_id(self) -> int:
        return int(self.name)


class Interest(Enum):
    On_a_Budget = 'On_a_Budget'
    Luxury = 'Luxury'
    Family_Friendly = 'Family_Friendly'
    Nature = 'Nature'
    Relaxing = 'Relaxing'
    Outdoors = 'Outdoors'
    Nightlife = 'Nightlife'
    Water = 'Water'
    Shopping = 'Shopping'
    Food_and_Drink = 'Food_and_Drink'
    Woodsy = 'Woodsy'
    History_and_Culture = 'History_and_Culture'
    Wellness = 'Wellness'
    Parks = 'Parks'
    Adventure = 'Adventure'
    Artsy = 'Artsy'
    Tours = 'Tours'
    Activities = 'Activities'
    Fun_and_Games = 'Fun_and_Games'
    Museums = 'Museums'
    Action_Packed = 'Action_Packed'
    Beaches = 'Beaches'
    Scenic = 'Scenic'
    Snow = 'Snow'
    With_Friends = 'With_Friends'
    Business = 'Business'

    def get_subinterest_class(self) -> SubInterest:
        return create_enum_from_csv(self.value)


if __name__ == '__main__':
    for interest in Interest:
        sub_interest = interest.get_subinterest_class()
        print(len(list(sub_interest)) != 0)

    # selected_sub_interest = [list(sub_interest)[0]]

    # print(selected_sub_interest[0].name)
