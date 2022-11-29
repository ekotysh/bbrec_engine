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


CSV_IN_FILENAME = 'non_pruned_data.csv'
CSV_OUT_FILENAME = 'final_pruned_data.csv'


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


def prune_empty_rewards():
    # Read our CSV into a dataframe
    csv_df = pandas.read_csv(CSV_IN_FILENAME, parse_dates=['Report Date'])
    print(csv_df)

    # Go through each row of dataframe, grab Bounty Awarded and if it's nan, drop it
    companies = set()
    open_source_companies = ['Homebrew', 'Ruby', 'RubyGems', 'Ruby on Rails', 'curl', 'Tor', 'Django', 'Notepad++', 'FileZilla', 'Internet Bug Bounty', 'h1-ctf', 'Phabricator']
    data_rows = [[]]
    total_rows = 0
    total_removed = 0
    for index, row in csv_df.iterrows():
        company_name = row['Company Name']
        bounty_awarded = row['Bounty Awarded']
        companies.add(company_name)

        if company_name == 'Ian Dunn' or (type(bounty_awarded) == float and math.isnan(bounty_awarded)):
            # print(f"Removing row {index}, Company: {company_name}")
            total_removed += 1
        else:
            # initialize open source column values to 0, unless there is already a 1
            open_source = row['Open Source']
            if open_source and open_source == 1:
                # Existing Open Source entry - keep the value 1
                print(f"Found existing open source entry for {company_name}. Keeping it.")
                data_rows.append(row)
            elif company_name in open_source_companies:
                # set Open Source to 1
                print(f"Found an open source entry for {company_name}. Setting to 1.")
                row_copy = row.copy()
                row_copy['Open Source'] = 1

                # add it to the data rows to write to our final csv
                data_rows.append(row_copy)
            else:
                # Non-OS, initialize value to be default of 0
                row_copy = row.copy()
                row_copy['Open Source'] = 0

                # add it to the data rows to write to our final csv
                data_rows.append(row_copy)

        total_rows += 1

    write_csv(data_rows)
    print(f"Done. Total pruned: {total_removed} out of {total_rows}")
    print("All Companies:")
    print(companies)


if __name__ == '__main__':
    prune_empty_rewards()

