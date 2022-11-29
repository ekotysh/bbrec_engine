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


CSV_IN_FILENAME = 'final_consistent_data.csv'
CSV_OUT_FILENAME = 'final_geocoded_data.csv'


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


def get_csv_writeable_row(row):
    # Format:
    # ['Company Name', 'Company Size', 'Open Source', 'Company Revenue',
    #  'Company City', 'Company State', 'Company Country',
    #  'Bounty Awarded', 'Severity Rating', 'Severity Score', 'Weakness',
    #  'Report Title', 'Report Date', 'Report Description', 'URL']

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


def validate_final_data():
    # Read our CSV into a dataframe
    csv_df = pandas.read_csv(CSV_IN_FILENAME, parse_dates=['Report Date'])
    print(csv_df)

    # spot check all the unique values for each of these columns
    companies = set()
    sizes = set()
    revenues = set()
    locations = set()
    companies_to_location = {}
    companies_to_sizes = {}
    companies_to_revenues = {}
    severity_ratings = set()
    severity_scores = set()
    open_source_vals = set()

    data_rows = [[]]
    total_rows = 0

    for index, row in csv_df.iterrows():
        company_name = row['Company Name']
        size = row['Company Size']
        revenue = row['Company Revenue']
        location = row['Company Location']
        rating = row['Severity Rating']
        score = row['Severity Score']
        open_source_val = row['Open Source']

        companies.add(company_name)
        sizes.add(size)
        revenues.add(revenue)
        locations.add(location)
        severity_ratings.add(rating)
        if not math.isnan(score):
            severity_scores.add(score)
        open_source_vals.add(open_source_val)

        # collect locations for each company
        if company_name not in companies_to_location.keys():
            companies_to_location[company_name] = set()
            companies_to_location[company_name].add(location)
        else:
            companies_to_location[company_name].add(location)

        # collect sizes for each company
        if company_name not in companies_to_sizes.keys():
            companies_to_sizes[company_name] = set()
            companies_to_sizes[company_name].add(size)
        else:
            companies_to_sizes[company_name].add(size)

        # collect revenues for each company
        if company_name not in companies_to_revenues.keys():
            companies_to_revenues[company_name] = set()
            companies_to_revenues[company_name].add(revenue)
        else:
            companies_to_revenues[company_name].add(revenue)

        total_rows += 1

    # write_csv(data_rows)

    print(f"Done. Total records: {total_rows}")

    # check for inconsistent locations for each company
    for c in companies_to_location.keys():
        if len(companies_to_location[c]) > 1:
            print(f"Company {c} has multiple locs: {companies_to_location[c]}")

    # check for inconsistent sizes for each company
    for c in companies_to_sizes.keys():
        if len(companies_to_sizes[c]) > 1:
            print(f"Company {c} has multiple sizes: {companies_to_sizes[c]}")

    # check for inconsistent revenues for each company
    for c in companies_to_revenues.keys():
        if len(companies_to_revenues[c]) > 1:
            print(f"Company {c} has multiple revenues: {companies_to_revenues[c]}")

    print("All Companies:", companies)
    print("All Sizes:", sizes)
    print("All revenues:", revenues)
    print("All locations:", locations)
    print("All severity_ratings:", severity_ratings)
    print("All severity_scores:", severity_scores)
    print("All open_source_vals:", open_source_vals)

    print("Done.")


if __name__ == '__main__':
    validate_final_data()

