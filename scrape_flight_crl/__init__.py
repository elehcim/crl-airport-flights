import urllib
import requests
from bs4 import BeautifulSoup
import pandas as pd

URL = 'https://www.charleroi-airport.com/en/flights/timetable/index.html'


def is_url(url):
    return urllib.parse.urlparse(url).scheme in ('http', 'https',)

def parse_table(table):
    col_names = [col.text for col in table.find_all('thead')[0].find_all("th")]
    flight = table.previous_sibling.previous_sibling.h2.string
    content = list()
    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        row = list(td.string for td in tds)
        if len(row):
            content.append(row)
    return flight, col_names, content

def shorten_flight(flight):
    new_flight = flight[5:]  # It starts always with 'From '
    new_flight = new_flight.replace("Brussels South Charleroi", "CRL").replace(" to ", "->")
    return new_flight

def generate_df(tables):
    dfs = list()
    for table in tables:
        flight, col_names, content = parse_table(table)
        flight = shorten_flight(flight)
        index = pd.MultiIndex.from_arrays([[flight]*len(content), list(range(len(content)))], names=("connection", "#"))
        df = pd.DataFrame(content, columns=col_names, index=index)
        df['Mon.'] = df['Mon.'].astype(bool)
        df.loc[:, 'Mon.':'Sun.'] = df.loc[:, 'Mon.':'Sun.'].applymap(bool) #.astype(bool) # I have to do this after having explicitly converted (only) one column otherwise it does not work
        df['Start'] = pd.to_datetime(df['Start'])
        df['End'] = pd.to_datetime(df['End'])
        dfs.append(df)
    return pd.concat(dfs)

def parse_flights(url=URL, save_page=True):
    if is_url(url):
        page = urllib.request.urlopen(url)
    else:
        page = open(url)
        save_page = False
    soup = BeautifulSoup(page, 'html.parser')
    if save_page:
        dump_page(url)
    tables = soup.find_all('table')
    return generate_df(tables[:-1])

def dump_page(url):
    from datetime import datetime
    page = urllib.request.urlopen(url)
    soup = BeautifulSoup(page, 'html.parser')
    filename = "backup/url_{}.html".format(datetime.now().isoformat(timespec='hours'))
    with open(filename, "w", encoding="utf-8") as f:
        f.write(str(soup))
        f.close()
    return filename

def get_arrivals(df):
    return df[df.index.get_level_values('connection').str.endswith('CRL')]

def get_departures(df):
    return df[df.index.get_level_values('connection').str.startswith('CRL')]