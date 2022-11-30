import math

import requests
import json
import time
import csv
import pandas
import py_crunchbase
from py_crunchbase import PyCrunchbase, Collections, Cards
from bs4 import BeautifulSoup
import wikipediaapi
import random
import googlemaps
import json


GOOGLE_MAPS_API_KEY = 'AIzaSyCNcDeT5g5lSVIbpVVv6Er-adhphMQsVc0'

RAPID_API_KEY = 'c5d8d54f75msh57dffbfecc7163ap138966jsn3fa1e8848698'
RAPID_API_URL = 'https://google-maps-geocoding.p.rapidapi.com/geocode/json'
RAPID_API_HOST = 'google-maps-geocoding.p.rapidapi.com'

CSV_IN_FILENAME = 'final_denan_data.csv'
CSV_OUT_FILENAME = 'final_geocoded_data.csv'

gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)


class Location:
    city = None
    state = None
    country = None

    def __init__(self, city, state, country):
        self.city = city
        self.state = state
        self.country = country

    def summary(self):
        print(f"\tcity: {self.city}\n"
              f"\tstate: {self.state}\n"
              f"\tcountry: {self.country}\n")


def run_gmaps_api(city):
    # Geocoding an address
    geocode_result = gmaps.geocode(city)
    pretty = json.dumps(geocode_result, indent=4)
    # print(pretty)

    if not geocode_result or len(geocode_result) == 0:
        loc = Location(city, "", "")
        print(f"No match for {city}!")
    else:
        state = get_state(geocode_result[0]['address_components'])
        country = get_country(geocode_result[0]['address_components'])
        loc = Location(city, state, country)
        # print("Got a new location:")
        loc.summary()

    return loc


def get_state(address_components):

    for component in address_components:
        if 'administrative_area_level_1' in component['types']:
            return component['long_name']
    return ""


def get_country(address_components):
    for component in address_components:
        if 'country' in component['types']:
            return component['long_name']
    return ""


def get_google_maps_location_data(city):
    print(f"Getting location data for {city}")

    # use rapid api (google maps subset) to get supplemental state and country data
    rapid_query = {"address": city, "language": "en"}
    rapid_headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": RAPID_API_HOST
    }

    rapid_response = requests.request("GET", RAPID_API_URL, headers=rapid_headers, params=rapid_query)
    rapid_dict = json.loads(rapid_response.text)
    print(rapid_dict)

    loc = Location(city, "", "")
    print("Got:", loc.summary())
    return loc


def get_csv_writeable_row(row):
    # Format:
    # ['Company Name', 'Company Size', 'Open Source', 'Company Revenue',
    #  'Company City', 'Company State', 'Company Country',
    #  'Bounty Awarded', 'Severity Rating', 'Severity Score', 'Weakness',
    #  'Report Title', 'Report Date', 'Report Description', 'URL']
    """
    return [company.name, company.size, company.open_source, company.revenue, city,
            bounty_report.amount, bounty_report.severity_rating, bounty_report.severity_score,
            bounty_report.weakness, bounty_report.title, bounty_report.date, bounty_report.description, bounty_report.URL]
    """
    print("test")


def write_csv(data_rows):
    columns = ['Company Name', 'Company Size', 'Open Source', 'Company Revenue',
               'Company Location',
               'Bounty Awarded', 'Severity Rating', 'Severity Score', 'Weakness',
               'Report Title', 'Report Date', 'Report Description', 'URL',
               'Company State', 'Company Country', 'Company City']

    with open(CSV_OUT_FILENAME, 'w') as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile)

        # writing the columns
        csvwriter.writerow(columns)

        # writing the data rows
        csvwriter.writerows(data_rows)


def add_state_and_country():
    # Read our CSV into a dataframe
    csv_df = pandas.read_csv(CSV_IN_FILENAME, parse_dates=['Report Date'])
    print(csv_df)

    # cache retrieved geocoded locations
    locations = {}
    data_rows = [[]]
    total_rows = 0
    no_value = 'No value'

    for index, row in csv_df.iterrows():
        city = row['Company Location']
        loc = None
        if city in locations.keys():
            loc = locations[city]
        else:
            # invoke the api
            loc = run_gmaps_api(city)
            locations[city] = loc

        row_copy = row.copy()

        # if country exists, but state is missing, set state to city
        if (loc.country and loc.country != "") and (loc.state == "" or loc.state is None):
            row_copy['Company State'] = city
        else:
            row_copy['Company State'] = loc.state

        row_copy['Company Country'] = loc.country
        row_copy['Company City'] = city

        # override some exceptions that gmaps didn't handle properly
        if city == 'Burlington':
            row_copy['Company State'] = 'Massachusetts'
            row_copy['Company Country'] = 'United States'
        elif city == no_value:
            row_copy['Company State'] = no_value
            row_copy['Company Country'] = no_value
        elif city == 'Remote':
            row_copy['Company State'] = 'Remote'
            row_copy['Company Country'] = 'Remote'
        elif city == 'Dover':
            row_copy['Company State'] = 'Delaware'
            row_copy['Company Country'] = 'United States'
        elif city == 'Owen':
            row_copy['Company City'] = 'Houston'
            row_copy['Company State'] = 'Texas'
            row_copy['Company Country'] = 'United States'

        data_rows.append(row_copy)

        total_rows += 1

    write_csv(data_rows)

    print(f"Done. Total records: {total_rows}")

    print("All locations:", locations)

    print("Done.")


if __name__ == '__main__':
    add_state_and_country()

