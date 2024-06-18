# Standard library imports
from typing import Tuple
from langchain.callbacks import get_openai_callback
import random
from datetime import datetime, date
from typing import List, Type

# Pydantic imports for model creation
from pydantic import BaseModel, Field, create_model

from enum import Enum

# LangChain related imports
from langchain.chains import LLMChain
from langchain.chains.openai_functions import create_openai_fn_chain, create_openai_fn_runnable
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, PromptTemplate

# Additional utilities
from faker import Faker, Factory

# Your custom module imports
from interest import Interest, SubInterest
from settings import DEBUG, ORGANIZATION_ID
from prompts import PERSONA_PROMT,  TRAVEL_LOG_PROMPT


def get_llm(model, api_key, max_tokens=None, debug=True) -> ChatOpenAI:
    llm = ChatOpenAI(
        api_key=api_key,
        model=model,
        organization=ORGANIZATION_ID,
        verbose=debug,
    )
    if max_tokens is not None:
        llm.max_tokens = max_tokens
        

    return llm


def create_enum_based_model(enums: List[Type[Enum]]) -> Type[BaseModel]:
    """
    Dynamically creates a Pydantic model where each field corresponds to a provided Enum.
    The function takes a list of Enum types and generates a Pydantic model with fields
    whose types are these Enums. Each field in the model is required and is named after
    the corresponding Enum's class name. The docstring of each Enum is used as the
    description of the respective field in the model.

    :param enums: A list of Enum classes.
    :return: A dynamically created Pydantic model with Enum-based fields.
    """
    field_definitions = {}
    for enum in enums:
        field_name = enum.__name__
        field_description = enum.__doc__
        # Set fields as required
        field_definitions[field_name] = (
            enum, Field(..., description=field_description))

    DynamicModel = create_model('PersonInterests', **field_definitions)

    # Set the docstring of the model
    DynamicModel.__doc__ = "Extracted interests from the person's profile."

    return DynamicModel


def generate_fake_person() -> str:
    fake = Faker()
    fake.add_provider(Factory.create('en_US'))
    birthdate = fake.date_of_birth(minimum_age=20, maximum_age=80)
    person = fake.profile()
    return person['name'], person['job']


class BaseGeneratorModel(BaseModel):
    @classmethod
    def extract(cls, text, max_retries=1, gpt_model='gpt-4', api_key: str = '',  additional_model: BaseModel = None, query: str = '') -> 'BaseGeneratorModel':
        llm = get_llm(model=gpt_model, api_key=api_key, debug=DEBUG)
        
        retries = 0

        model = cls if additional_model is None else additional_model

        while retries < max_retries:
            print(f"Extracting Retrying {retries} out of {max_retries}")
            try:
                prompt = ChatPromptTemplate.from_messages(
                    [
                        ("system", "You are a world class algorithm for recording entities."),
                        ("human",
                         "Make calls to the relevant function to record the entities in the following input: {query}"),
                        ("human", "Tip: Make sure to answer in the correct format"),
                        ("human", text),
                    ]
                )

                chain = create_openai_fn_chain(
                    llm=llm,
                    prompt=prompt,
                    functions=[model],
                )

                result = chain.invoke({'query': query})
                return result['function']

            except Exception as e:
                retries += 1
                if retries >= max_retries:
                    raise e  # Re-raise the exception if max retries are reached

        # Optional: return some default value or handle the failed attempts differently


class PersonGeneratedContent(BaseGeneratorModel):
    """
    Record some identifing information about the person.
    """

    first_name: str = Field(..., description="First name of the person.",)
    last_name: str = Field(..., description="Last name of the person.")
    full_name: str = Field(..., description="Full name of the person.")
    city: str = Field(...,
                      description="City that the person lives in. generate one if not provided.")
    state: str = Field(...,
                       description="State of the city that the person lives in.")
    date_of_birth: date = Field(...,
                                description="Date of birth of the person. Format: YYYY-MM-DD")
    # about_me: str = Field(..., description="A first-person narrative that captures the essence of the person's character, interests, and what makes them unique. This should read as if it were written by the person themselves, reflecting their voice and personality.")
    about_me: str = Field(..., description="A brief, captivating description akin to an Instagram bio, showcasing the person's character, interests, and what makes them unique, all written in the first person.")
    interests: List[Interest] = Field(...,
                                      description="List of interests that the person need to choose from.")

    class Config:
        extra = 'allow'

    @property
    def email_id(self) -> str:
        return f'{self.first_name.lower()}.{self.last_name.lower()}@gmail.com'

    def select_interests(self):
        # for each interest we will select subinterest
        enum_subinterests_classes = [
            interest.get_subinterest_class() for interest in self.interests]

        PersonInterestsModel: BaseModel = create_enum_based_model(
            enum_subinterests_classes)

        # we will use extract function to extract subinterests
        query = "considering the person's known preferences and characteristics, which one of these interests is most likely to be chosen by them? Provide a brief rationale for your choice based on their profile."

        # 'If the person has to choose between the following interests, which interest would they choose?'
        sub_interests: BaseModel = self.extract(
            self.about_me, additional_model=PersonInterestsModel, query=query
        )

        sub_interests_list = list(sub_interests.dict().values())

        self.sub_interests: List[SubInterest] = sub_interests_list

        return self


class Category(Enum):
    RESTAURANT = 'DINING'
    PLACE = 'EXPERIENCE'

    def __str__(self):
        return self.value


class Location(BaseModel):
    """
    Location that the person has visited.
    """

    name: str = Field(..., description="Name of the location.")
    visit_date: str = Field(...,
                            description="Date of the visit in the location. Must be in format: YYYY-MM-DD")

    category: Category = Field(..., description="Category of the location.")


class Hotel(BaseModel):
    name: str = Field(..., description="Name of the hotel.")
    start_date: str = Field(...,
                            description="Start date of the stay. Format: YYYY-MM-DD")
    end_date: str = Field(...,
                          description="End date of the stay. Format: YYYY-MM-DD")


class Trip(BaseModel):
    """
    Trip that the person has taken.
    """
    trip_name: str = Field(
        ..., description="The name of the trip. This could be a custom name given to the trip by the person. for e.g Mindful Exploration, Japan, Sep")
    city: str = Field(..., description="The city name.")
    state: str = Field(..., description="The full name of the state.")
    country: str = Field(..., description="The country name.")
    locations: List[Location] = Field(..., description="List of locations.")
    hotels: List[Hotel] = Field(...,
                                description="List of hotels that the person has stayed in.")

    start_date: str = Field(...,
                            description="Start date of the trip. Format: YYYY-MM-DD")
    end_date: str = Field(...,
                          description="End date of the trip. Format: YYYY-MM-DD, can be the end date of the last hotel that the person has stayed in.")

    @property
    def duration(self) -> int:
        start_date = datetime.strptime(self.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(self.end_date, '%Y-%m-%d')
        return (end_date - start_date).days

    def get_context(self) -> Tuple[str, str]:
        context_1 = f'{self.city}_{self.country}'
        context_2 = f'{self.city}_{self.state}_{self.country}'

        return context_1, context_2


class TravelLog(BaseGeneratorModel):
    """
    All the trips that the person has taken.
    """
    trips: List[Trip] = Field(...,
                              description="List of trips that the person has taken.")

    class Config:
        extra = 'allow'


def generate_person_text(gpt_model: str, api_key: str) -> str:
    llm = get_llm(model=gpt_model, api_key=api_key,
                  max_tokens=400, debug=DEBUG)

    persona_table_prompt = PERSONA_PROMT

    persona_prompt_template = PromptTemplate(
        template=persona_table_prompt,
        input_variables=['full_name'],
    )

    persona_table_chain = LLMChain(llm=llm, prompt=persona_prompt_template,
                                   output_key="table", verbose=DEBUG)

    full_name, job = generate_fake_person()

    person_profile_text_result = persona_table_chain.run(
        full_name=full_name, job=job)

    return person_profile_text_result


def generate_travel_log_text(persona_text: str, model: str, api_key: str):
    num_of_cities = random.randint(2, 10)
    llm = get_llm(model=model, api_key=api_key, debug=DEBUG)

    travel_log_prompt = TRAVEL_LOG_PROMPT

    travel_log_prompt_template = PromptTemplate(
        template=travel_log_prompt,
        input_variables=['persona_text', 'num_of_cities'],
    )

    travel_log_chain = LLMChain(llm=llm, prompt=travel_log_prompt_template,
                                output_key="table", verbose=DEBUG)

    travel_log_text_result = travel_log_chain.run(
        persona_text=persona_text, num_of_cities=num_of_cities)

    return travel_log_text_result


def get_travel_log_from_persona_text(persona_text: str, model: str, api_key: str):
    travel_log_prompt = TRAVEL_LOG_PROMPT

    num_of_cities = random.randint(2, 10)
    llm = get_llm(model=model, api_key=api_key, debug=DEBUG)

    travel_log_prompt = TRAVEL_LOG_PROMPT

    travel_log_prompt_template = PromptTemplate(
        template=travel_log_prompt,
        input_variables=['persona_text', 'num_of_cities'],
    )

    travel_log_chain = create_openai_fn_chain(
        functions=[TravelLog], llm=llm, prompt=travel_log_prompt_template,)

    travel_log_result: TravelLog = travel_log_chain.invoke(input={
        'persona_text': persona_text,
        'num_of_cities': num_of_cities,
    })

    return travel_log_result['function']


if __name__ == '__main__':
    from examples import PERSONA_GENERATED_TEXT
    with get_openai_callback() as cb:
        person_text = PERSONA_GENERATED_TEXT

        travel_log = get_travel_log_from_persona_text(person_text)

        print(travel_log)

        print(cb)
