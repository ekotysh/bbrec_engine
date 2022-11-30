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


CSV_IN_FILENAME = 'final_nan_data.csv'
CSV_OUT_FILENAME = 'final_consistent_data.csv'


class BountyReport:
    amount = None
    severity_rating = None
    severity_score = None
    weakness = None
    title = None
    date = None
    description = None
    URL = None

    def __init__(self, csv_row):
        self.amount = str(csv_row['bountyAwarded'])

        # fix the crawl issue when I sometimes get a repeated bounty amount, i.e: '$600$600'
        if self.amount and not self.amount.isspace():
            if self.amount.count('$') > 1:
                # just take the first value, since they are both the same
                self.amount = "$" + self.amount.split('$')[1]

        self.date = csv_row['reportDate']
        self.description = csv_row['reportDescription']
        self.title = csv_row['title']
        self.URL = csv_row['url']
        self.weakness = csv_row['weakness']
        self.severity_score = csv_row['severityScore']
        self.severity_rating = csv_row['severityRating']


class Company:
    name = None
    website = None
    location_str = None
    location_obj = None
    size = None
    open_source = 0
    industries = None
    revenue = None
    technologies = None

    def __init__(self, name, website):
        self.name = name
        self.website = website

    def summary(self):
        print(f"Company name: {self.name}\n"
              f"\twebsite: {self.website}\n"
              f"\tlocation_str: {self.location_str}\n"
              f"\tlocation_obj: {self.location_obj}\n"
              f"\tsize: {self.size}\n"
              f"\topen_source: {self.open_source}\n"
              f"\trevenue: {self.revenue}\n"
              f"\tindustries: {self.industries}\n"
              f"\ttechnologies: {self.technologies}\n")


def get_csv_writeable_row(company, bounty_report):
    # Format:
    # ['Company Name', 'Company Size', 'Open Source', 'Company Revenue', 'Company Location',
    #  'Bounty Awarded', 'Severity Rating', 'Severity Score', 'Weakness',
    #  'Report Title', 'Report Date', 'Report Description', 'URL']

    city = None
    if company.location_obj and "city" in company.location_obj.keys():
        city = company.location_obj['city']

    return [company.name, company.size, company.open_source, company.revenue, city,
            bounty_report.amount, bounty_report.severity_rating, bounty_report.severity_score,
            bounty_report.weakness, bounty_report.title, bounty_report.date, bounty_report.description, bounty_report.URL]


def write_csv(data_rows):
    columns = ['Company Name', 'Company Size', 'Open Source', 'Company Revenue', 'Company Location',
               'Bounty Awarded', 'Severity Rating', 'Severity Score', 'Weakness',
               'Report Title', 'Report Date', 'Report Description', 'URL']

    with open(CSV_OUT_FILENAME, 'w') as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile)

        # writing the columns
        csvwriter.writerow(columns)

        # writing the data rows
        csvwriter.writerows(data_rows)


def fix_nans():
    # Read our CSV into a dataframe
    csv_df = pandas.read_csv(CSV_IN_FILENAME, parse_dates=['Report Date'])
    print(csv_df)

    data_rows = [[]]
    total_rows = 0

    empty_value = "No value"
    zero_value = 0

    for index, row in csv_df.iterrows():
        company_name = row['Company Name']
        size = row['Company Size']
        revenue = row['Company Revenue']
        location = row['Company Location']
        rating = row['Severity Rating']
        score = row['Severity Score']
        open_source_val = row['Open Source']

        if (company_name is None) \
                or (type(company_name) == str and company_name == 'None') \
                or (type(company_name) == float and math.isnan(company_name)):
            print(f"Fixing nan for field: company, row {index}")
            row_copy = row.copy()
            row_copy['Company Name'] = empty_value
            data_rows.append(row_copy)
        elif (size is None) \
                or (type(size) == str and size == 'None') \
                or (type(size) == float and math.isnan(size)):
            print(f"Fixing nan for field: size, row {index}")
            row_copy = row.copy()
            row_copy['Company Size'] = empty_value
            data_rows.append(row_copy)
        elif (revenue is None) \
                or (type(revenue) == str and revenue == 'None') \
                or (type(revenue) == float and math.isnan(revenue)):
            print(f"Fixing nan for field: revenue, row {index}")
            row_copy = row.copy()
            row_copy['Company Revenue'] = empty_value
            data_rows.append(row_copy)
        elif (location is None) \
                or (type(location) == str and location == 'None') \
                or (type(location) == float and math.isnan(location)):
            print(f"Fixing nan for field: location, row {index}")
            row_copy = row.copy()
            row_copy['Company Location'] = empty_value
            data_rows.append(row_copy)
        elif (rating is None) \
                or (type(rating) == str and rating == 'None') \
                or (type(rating) == float and math.isnan(rating)):
            print(f"Fixing nan for field: rating, row {index}")
            row_copy = row.copy()
            row_copy['Severity Rating'] = empty_value
            data_rows.append(row_copy)
        elif (score is None) \
                or (type(score) == str and score == 'None') \
                or (type(score) == float and math.isnan(score)):
            print(f"Fixing nan for field: score, row {index}")
            row_copy = row.copy()
            row_copy['Severity Score'] = zero_value
            data_rows.append(row_copy)
        else:
            # add it to the data rows to write to our final csv
            data_rows.append(row)

    # check for companies with more than one location

    write_csv(data_rows)

    print("Done.")


if __name__ == '__main__':
    fix_nans()

