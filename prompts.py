# PERSONA_PROMT = """
# create a fictional profile table for {full_name} and build persona profile for {full_name} include all
# relevant parameters like, income level, martial statues, date of birth, city of residence, etc. detailed as possible.
# below the table add a short description 3-5 lines max about {full_name}, his/her personality, hobbies, interests. in the desctription don't mention private information like income, salary, etc.
# the description should be written in first person, as if {full_name} is talking about himself/herself.
# {full_name}'s age should be between 20 and 80 years old.
# {full_name} works as a {job}.
# """

PERSONA_PROMT = """Create a detailed fictional profile for {full_name}, who is between 20 and 80 years old and works as a {job}. First, present a table including all relevant parameters such as income level, marital status, date of birth, city of residence. Ensure the table is comprehensive but concise. 

Then, craft a first-person, conversational bio for {full_name}, limited to 3-5 lines. This bio should weave together {full_name}'s personality traits, passions, and daily life, reflecting their professional background and personal interests. The tone should be light, genuine, and engaging, capturing the essence of {full_name} as if they were introducing themselves on a social platform. Avoid including sensitive financial information and focus on aspects that would resonate on a social level, considering the age and profession of {full_name}.

For example:
- "Tech enthusiast and amateur chef 🍳. Love turning ideas into code at work and recipes into meals at home. Exploring New York one street at a time. Dreaming of my next mountain hike 🌄."

Remember, the goal is to create an inviting snapshot of {full_name}'s life that highlights their unique personality and interests, encouraging connections and interactions on the social app."""


# TRAVEL_LOG_PROMPT = """
# Person:\n
# "{persona_text}"

# Please construct a nested table featuring {num_of_cities} international cities (outside the USA) that the person plans to visit, including Trip Name, Start Date (past date), Duration (days), Restaurants (with visit dates), Experiences (with dates), and 1 to 3 Hotel options per city with flexibility for one or multiple stays (including check-in date and duration for each hotel).
# """


TRAVEL_LOG_PROMPT = """
Based on the profile provided:
"{persona_text}"


Craft a personalized travel log for visiting {num_of_cities} international destinations, with each detail tailored to the user's life and preferences. Include the following for each destination:

1. **Trip Name**: Create a trip name that person has gave to the trip in the travel app.
2. **Start Date**: Choose an appropriate start date, formatted as YYYY-MM-DD, that accommodates the individual’s schedule and preferred travel periods.
3. **Duration**: Assign the duration of the stay in days, considering the user's availability for travel and their interest in immersive experiences.
4. **Restaurants**: List recommended restaurants that align with the user's taste preferences, including specific visit dates in the format YYYY-MM-DD to fit the trip's schedule.
5. **Experiences**: Detail engaging and relevant activities, with each experience assigned a specific visit date in the format YYYY-MM-DD. These should reflect the user's interests, offer new challenges, and enable cultural immersion.
6. **Hotels**: Suggest hotels that meet the user's accommodation preferences, detailing check-in dates and stay durations for each, presented in the format YYYY-MM-DD for clarity and planning efficiency.

This itinerary should not only reflect the user's lifestyle and interests but also provide a structured, enriching travel experience, with dates clearly defined to facilitate planning and ensure a seamless trip.

[NOTE] *all locations should be real location from the world, no fictional locations allowed*
"""
