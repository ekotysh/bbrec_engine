import math
from datetime import datetime

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


CSV_IN_FILENAME = 'datasets/final_consistent_data.csv'
CSV_OUT_FILENAME = 'datasets/final_data.csv'


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

    columns = ['Company Name', 'Company Size', 'Open Source', 'Company Revenue',
               'Bounty Awarded', 'Severity Rating', 'Severity Score', 'Weakness',
               'Report Title', 'Report Date', 'Report Description', 'URL',
               'Company State', 'Company Country', 'Company City',
               'Report Year', 'Report Month', 'Report Day', 'Report Hour', 'Report Minute']

    with open(CSV_OUT_FILENAME, 'w') as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile)

        # writing the columns
        csvwriter.writerow(columns)

        # writing the data rows
        csvwriter.writerows(data_rows)


def parse_date(date_input):
    # Date is in the format: 2020-06-24 11:47:00
    input_format = "%Y-%m-%d %H:%M:%S"

    try:
        parsed_date = datetime.strptime(date_input, input_format)
        return parsed_date
    except ValueError:
        print("Error parsing date for:", date_input)


def explode_dates():
    # Read our CSV into a dataframe
    csv_df = pandas.read_csv(CSV_IN_FILENAME)
    print(csv_df)

    # see how many different bounties we have
    bounties = set()

    data_rows = [[]]
    total_rows = 0

    for index, row in csv_df.iterrows():
        bounty = row['Bounty Awarded']
        print("Bounty:", bounty)

        bounties.add(bounty)
        # parsed_date = parse_date(date)

        """
        row_copy = row.copy()
        row_copy['Report Year'] = year
        row_copy['Report Month'] = month
        row_copy['Report Day'] = day
        row_copy['Report Hour'] = hour
        row_copy['Report Minute'] = minute
        
        data_rows.append(row_copy)
        """

    # check how many unique bounties we got
    print("Total unique bounties:", len(bounties))

    # write_csv(data_rows)

    print("Done.")


if __name__ == '__main__':
    explode_dates()

