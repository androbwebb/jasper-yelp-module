# -*- coding: utf-8-*-

import re
from client.libs.yelp import search, get_business, parse_biz_tree, price_to_text
import webbrowser

WORDS = ["RESTAURANT", "FIND", "EAT", "FOOD"]


YELP_PRICE_RANGE = ["PRICE"]
YELP_REVIEW = ["REVIEW", "SAY", "SAID"]
YELP_ATTIRE = ["ATTIRE", "DRESS", "CODE", "WEAR", "CLOTHES"]
YELP_ALCOHOL = ["ALCOHOL", "BOOZE", "LIQUOR", "BEER", "WINE"]
YELP_RESERVATIONS = ["RESERVE", "RESERVATION"]

YELP_MORE_INFO = YELP_PRICE_RANGE + YELP_ATTIRE + YELP_ALCOHOL + YELP_RESERVATIONS

#DEFAULTS
YELP_CURRENT_LOCATION = "Brighton, MA"

def handle(text, mic, profile):
    """
        Reports movie times.

        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        profile -- contains information related to the user (e.g., phone
                   number)
    """
    mic.say("What kind of cuisine?")
    term = mic.activeListen()

    mic.say("Nearby?")
    nearby = mic.activeListen()

    if nearby in ["NO", "NEGATIVE", "NAH", "NA"]:
        mic.say("Where?")
        location = mic.activeListen()
    elif nearby in ["YES", "YAH", "YA", "SURE"]:
        location = YELP_CURRENT_LOCATION
    else:
        location = nearby

    mic.say("Great. Looking for {term} restaurants in {location}".format(term=term, location=location))
    response = search(location=location, term=term)
    results = response.get('businesses')

    #iterate through results
    for restaurant in results:

        # Initial restaurant introduction
        sayit = "How about this place " \
                + ("in {city}".format(city=restaurant['location']['city']) if restaurant['location']['city'] not in location and location not in restaurant['location']['city'] else "") \
                + ("at {cross}".format(cross=restaurant['location']['cross_streets']) if 'cross_streets' in restaurant['location'] else "") \
                + "It's called {name}. It has a {rating} on yelp."
        mic.say(sayit.format(name=restaurant['name'], rating=str(restaurant['rating'])))
        command = mic.activeListen()

        # Get data about restaurant
        full_restaurant = get_business(restaurant['id'])
        scraped_data = parse_biz_tree(restaurant['url'])

        # Loop while you're asking questions about the restaurant
        while any(info in command for info in YELP_MORE_INFO):

            # "What's the price?"
            if any(inf in command for inf in YELP_PRICE_RANGE):
                mic.say("The price range is " + price_to_text(scraped_data['price_range']))

            # "What's the attire?", "What should I wear?"
            if any(inf in command for inf in YELP_ATTIRE):
                if 'Attire' in scraped_data:
                    mic.say("The attire is " + scraped_data['Attire'])
                else:
                    mic.say("Not sure. Yelp doesn't have that data.")

            # "Do they have booze?", "What alcohol do they have?"
            if any(inf in command for inf in YELP_ALCOHOL):
                if 'Alcohol' in scraped_data:
                    if scraped_data['Alcohol'] != "No":
                        mic.say("They serve {alcohol}".format(alcohol=scraped_data['Alcohol']))
                    else:
                        mic.say("They don't have booze.")
                else:
                    mic.say("Not sure. Yelp doesn't have that data.")

            # "Do they take reservations?"
            if any(inf in command for inf in YELP_RESERVATIONS):
                if 'Takes Reservations' not in scraped_data:
                    mic.say("Not sure. Yelp doesn't have that data.")
                else:
                    if scraped_data['Takes Reservations'] == "No":
                        mic.say("They don't take reservations")
                    else:
                        sayit = "They take reservations."
                        if 'reservation_type' in scraped_data:
                            sayit += " They use " + scraped_data['reservation_type'] + ". "
                        if 'reservation_msg' in scraped_data:
                            sayit += scraped_data['reservation_msg']
                        if 'reservation_times' in scraped_data:
                            sayit += "The following times are available tonight: " + ', '.join(scraped_data['reservation_times'])
                        mic.say(sayit)

            # "What are people saying about it?", "What are the reviews like?"
            if any(inf in command for inf in YELP_REVIEW):
                mic.say("There are {num} reviews. Here's the first excerpt. {review_text}".format(num=full_restaurant['review_count'], review_text=full_restaurant['reviews'][0]['excerpt']))
                mic.say("{name}, did that review convince you?".format(name=profile['first_name']))

            command = mic.activeListen()

        # Confirm this restaurant
        if any(confirm in command for confirm in["YES", "YEAH", "SURE", "YAH", "OPEN", "WEB"]):
            webbrowser.open(restaurant['url'])
            break

        # "Nah, what else is there?"
        if any(negative in command for negative in["NAH", "NA", "NO", "GOING", "NOPE", "ELSE", "OTHER"]):
            continue

        # Bail
        if any(bail in command for bail in["CANCEL", "NEVERMIND", "QUIT", "STOP", "BAIL"]):
            break

    return True


def isValid(text):
    """
        Returns True if input is related to the time.

        Arguments:
        text -- user-input, typically transcribed speech
    """
    return bool(re.search(r'\bfind.*(restaurant|place.*to.*eat|food)\b', text, re.IGNORECASE))
