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


CRUNCHBASE_API_KEY = '83ee06273d4ff55dc4d7eeca7686feb3'
CRUNCHBASE_API_AUTOCOMPLETE_URL = 'https://api.crunchbase.com/api/v4/autocompletes?query='
CRUNCHBASE_API_ORG_SEARCH_URL = 'https://api.crunchbase.com/api/v4/searches/organizations'
CRUNCHBASE_PERMALINK_PREFIX = 'https://www.crunchbase.com/organization/'

RAPID_API_KEY = 'c5d8d54f75msh57dffbfecc7163ap138966jsn3fa1e8848698'
RAPID_API_URL = 'https://companies-datas.p.rapidapi.com/v2/company'
RAPID_API_HOST = 'companies-datas.p.rapidapi.com'

CSV_IN_FILENAME = 'prod_dataset_with_company_names_2022-11-19.csv'
CSV_OUT_FILENAME = 'final_train_data.csv'


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
              f"\trevenue: {self.revenue}\n"
              f"\tindustries: {self.industries}\n"
              f"\ttechnologies: {self.technologies}\n")


def get_wiki_company_data(company_name):
    print("Getting data from Wikipedia...")
    wiki_wiki = wikipediaapi.Wikipedia('en')
    company_page = wiki_wiki.page(company_name)

    print("\tPage - Summary: %s" % company_page.summary[0:60])

    print("\tCategories:")
    categories = company_page.categories
    for title in sorted(categories.keys()):
        print("\t%s: %s" % (title, categories[title]))


def get_crunchbase_permalink(company_name):
    # fix some company names
    if company_name == 'Staging.every.org':
        company_name = 'every.org'

    crunchbase_org_search_url = CRUNCHBASE_API_AUTOCOMPLETE_URL + company_name

    headers = {
        "accept": "application/json",
        "X-cb-user-key": CRUNCHBASE_API_KEY
    }

    # submit the autocomplete search request
    response = requests.get(crunchbase_org_search_url, headers=headers)
    resp_dict = response.json()

    # see if we got any results
    if 'entities' not in resp_dict.keys() or len(resp_dict.get('entities')) == 0:
        return ""

    # grab the first entity that comes out in the results and its identifier
    first_hit = resp_dict.get('entities')[0]
    crunchbase_identifier = first_hit.get('identifier')

    # pretty = json.dumps(first_hit, indent=4)
    # print(pretty)

    # permalink of the company is what we need to get more info on it
    perma_suffix = crunchbase_identifier.get('permalink')
    permalink = CRUNCHBASE_PERMALINK_PREFIX + perma_suffix
    print("Fetched permalink: ", permalink)
    return permalink


def get_crunchbase_company_data(name, permalink):
    print("Getting company data from Crunchbase...")

    if not permalink or len(permalink) == 0:
        return Company("", "")

    # crawl crunchbase permalink to get its website, size, location and industries
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:106.0) Gecko/20100101 Firefox/106.0",
               "Accept": "text/html;charset=utf-8",
               "Accept-Language": "en-US,en;q=0.5", "Accept-Encoding": "gzip, deflate", "DNT": "1",
               "Host": "www.crunchbase.com",
               "Connection": "close",
               "content-type": "text/html; charset=utf-8",
               "Cookie": "_pxhd=FQrXJ/RPEuzXOSKYTdSphNgaOS0FQfkKwtCPsuqZwXkxQd2kkJZPwM7WpLaHfM5rThNa0CwCyz3YTHWQtzzeOQ; cid=Cii/iGNmyIg9cwAvgzQ2Ag==; featureFlagOverride=%7B%7D; featureFlagOverrideCrossSite=%7B%7D; xsrf_token=/2fT2BFW8ljBt4xLArZgBr9ggYfoPrQ3FOawYhU+pqQ; authcookie=eyJhbGciOiJIUzUxMiJ9.eyJqdGkiOiI3NWU5ZjRlMC0xYmIzLTRmNmMtYWFmMi1kNmExMmUzZTcyZjIiLCJpc3MiOiJ1c2Vyc2VydmljZV82MDU1ZDNjYV82NDQiLCJzdWIiOiI2MGQxMzJlYS1jOWNmLTRjZWQtOTVkZi02MWQ1YjU5ZTBhZWEiLCJleHAiOjE2Njk0OTkzNDcsImlhdCI6MTY2OTQ5OTA0NywicHJpdmF0ZSI6IlhBbVRTc2V5enVsWjVuRE5BTnlJOTRuUjNoQ01tN0wvczVwaGdQekpFZDV2dS93Q3R0UWtjVktsakliZ0w3Q2hpRG5xUnk3ZXowUUpSSmorZmpUOVBpRzRZOSs1Q1IwL1JvUXUzV2hMZFFPaTEyMzVhWDEvZ1BPNCtydTRwd0h4MFFxZC9MekpuNVF3L1F4M1daTXhoNFpwYndQL0lET2pkM2twQ01WOEdBK0ErQmx4Q1lkZE1uTDZHT3lLejJ1S3NZcFp5YlJuVVVPc0tZWUtJSHFyc3ZCTVhzU3VlUEVUUHc5NzUxNVhHazZwemljckJuQ0ZXZGpvOHZUdFhta2p3QTV0RHR2bnpLQ0cxaDdqenphYXZsdnhJRnVyQTJwYVFONVhVR29SeEN6OFZzcEd2L2hSZExzak93aVhSQ2IzIiwicHVibGljIjp7InNlc3Npb25faGFzaCI6IjE3MDQzNjAwMzcifX0.1kgUXDktbeOg4RqbIneW5a290SR1GVmN6X1KNiQViGKb4gXFEXCj9emQIQVLSipZsEpf-GQ-6-uKehD61Ru1xw; __cflb=0H28vxzrpPtLNGTtMLYx4RBq4Wxh3KP156DmDXgmPg8; pxcts=aa5de7b8-6dd2-11ed-9a26-47764d4a7255; _pxvid=a806f7e1-6dd2-11ed-9a58-4d44725a656f",
               "Upgrade-Insecure-Requests": "1"}

    response = requests.request("GET", permalink, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    website = ""
    website_element = soup.find('a', href=True, class_="component--field-formatter link-accent ng-star-inserted")
    if website_element:
        website = website_element['href']

    num_employ_element = soup.find(class_="component--field-formatter field-type-enum link-accent ng-star-inserted")
    num_employees = 0
    if num_employ_element and num_employ_element.text:
        num_employees = num_employ_element.text.strip()

    headquarters_element = soup.find(class_="component--field-formatter field-type-identifier-multi")
    location = ""
    if headquarters_element and headquarters_element.text:
        location = headquarters_element.text.strip()

    industry_elements = soup.find_all('div', class_="cb-overflow-ellipsis")
    industries = []
    if industry_elements and len(industry_elements) > 0:
        for industry in industry_elements:
            industries.append(industry.text.strip())

    # Create a Company class and return the instance
    company = Company(name, website)
    company.size = num_employees
    company.location_str = location
    company.industries = industries

    return company


def get_rapid_financial_company_data(company):
    print("Getting financial data from Rapid API...")

    # use rapid api (companies dataset) to get supplemental data on revenue and technologies
    rapid_query = {"query": company.website}
    rapid_headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": RAPID_API_HOST
    }

    rapid_response = requests.request("GET", RAPID_API_URL, headers=rapid_headers, params=rapid_query)
    rapid_dict = json.loads(rapid_response.text)

    if 'revenue' in rapid_dict.keys():
        company.revenue = rapid_dict['revenue']

    if 'technologies' in rapid_dict.keys():
        company.technologies = rapid_dict['technologies']

    if 'location' in rapid_dict.keys():
        company.location_obj = rapid_dict['location']

    return company


def get_csv_writeable_row(company, bounty_report):
    # Format:
    # ['Company Name', 'Company Size', 'Company Revenue', 'Company Location',
    #  'Bounty Awarded', 'Severity Rating', 'Severity Score', 'Weakness',
    #  'Report Title', 'Report Date', 'Report Description', 'URL']

    city = None
    if company.location_obj and "city" in company.location_obj.keys():
        city = company.location_obj['city']

    return [company.name, company.size, company.revenue, city,
            bounty_report.amount, bounty_report.severity_rating, bounty_report.severity_score,
            bounty_report.weakness, bounty_report.title, bounty_report.date, bounty_report.description, bounty_report.URL]


def write_csv(data_rows):
    columns = ['Company Name', 'Company Size', 'Company Revenue', 'Company Location',
               'Bounty Awarded', 'Severity Rating', 'Severity Score', 'Weakness',
               'Report Title', 'Report Date', 'Report Description', 'URL']

    with open(CSV_OUT_FILENAME, 'w') as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile)

        # writing the columns
        csvwriter.writerow(columns)

        # writing the data rows
        csvwriter.writerows(data_rows)


def enrich_data():
    # Create a single instance of CrunchBase API bindings object
    cb = PyCrunchbase(CRUNCHBASE_API_KEY)

    # Read our CSV into a dataframe
    csv_df = pandas.read_csv(CSV_IN_FILENAME, parse_dates=['reportDate'])
    print(csv_df)

    # Cache company data, so we don't bombard crunchbase with requests
    companies_cache = {}

    # Go through each row of dataframe, grab companyName and lookup CB stuff on it
    data_rows = [[]]
    for index, row in csv_df.iterrows():
        company_name = row['companyName']

        print(f"Row {index}, Company: {company_name}")
        bounty_report = BountyReport(row)

        if type(company_name) == float and math.isnan(company_name):
            empty_company = Company("", "")
            data_rows.append(get_csv_writeable_row(empty_company, bounty_report))
        else:
            # search crunchbase api for company name to get its permalink
            permalink = get_crunchbase_permalink(company_name)

            # check if we already retrieved this company's info before
            if company_name in companies_cache.keys():
                company = companies_cache[company_name]
            else:
                # otherwise, retrieve from crunchbase via scraping data manually
                company = get_crunchbase_company_data(company_name, permalink)
                # add company to the cache
                companies_cache[company_name] = company
                # pace
                print("Sleeping...")
                wait_time = random.randint(13, 25)
                time.sleep(wait_time)  # be nice, wait a few sec before proceeding to the next request

            # get company data from wikipedia api
            # get_wiki_company_data(company_name)

            # Then use rapidapi to get supplemental financial data (revenue, # investors)
            company = get_rapid_financial_company_data(company)
            print(company.summary())

            # add it to the data rows to write to our final csv
            data_rows.append(get_csv_writeable_row(company, bounty_report))
            time.sleep(1)

        print("")

    write_csv(data_rows)


if __name__ == '__main__':
    enrich_data()

