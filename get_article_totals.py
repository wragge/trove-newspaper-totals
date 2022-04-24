import os
import time
from operator import itemgetter  # used for sorting
from pathlib import Path

import pandas as pd  # makes manipulating the data easier
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from dotenv import load_dotenv

load_dotenv()

# Create a session that will automatically retry on server errors
s = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
s.mount("http://", HTTPAdapter(max_retries=retries))
s.mount("https://", HTTPAdapter(max_retries=retries))

API_KEY = os.getenv("TROVE_API_KEY")

STATES = sorted(['New South Wales',
          'Queensland',
          'Victoria',
          'Western Australia',
          'South Australia',
          'Tasmania',
          'ACT',
          'International',
          'National',
          'Northern Territory'])

def get_results(params):
    """
    Get JSON response data from the Trove API.
    Parameters:
        params
    Returns:
        JSON formatted response data from Trove API
    """
    response = s.get(
        "https://api.trove.nla.gov.au/v2/result", params=params, timeout=30
    )
    response.raise_for_status()
    # print(response.url) # This shows us the url that's sent to the API
    data = response.json()
    return data

def get_total_results(params):
    data = get_results(params)
    total = data['response']['zone'][0]['records']['total']
    return total

def get_facets(data):
    """
    Loop through facets in Trove API response, saving terms and counts.
    Parameters:
        data  - JSON formatted response data from Trove API
    Returns:
        A list of dictionaries containing: 'term', 'total_results'
    """
    facets = []
    try:
        # The facets are buried a fair way down in the results
        # Note that if you ask for more than one facet, you'll have use the facet['name'] param to find the one you want
        # In this case there's only one facet, so we can just grab the list of terms (which are in fact the results by year)
        for term in data["response"]["zone"][0]["facets"]["facet"]["term"]:

            # Get the year and the number of results, and convert them to integers, before adding to our results
            facets.append({"term": term["search"], "total": int(term["count"])})

        # Sort facets by year
        facets.sort(key=itemgetter("term"))
    except TypeError:
        pass
    return facets


def get_year_totals(start_decade=180, end_decade=201, state=None):
    """
    Loop throught the decades from 'start_decade' to 'end_decade',
    getting the number of search results for each year from the year facet.
    Combine all the results into a single list.
    Parameters:
        params - parameters to send to the API
        start_decade
        end_decade
    Returns:
        A list of dictionaries containing 'year', 'total_results' for the complete
        period between the start and end decades.
    """
    # Create a list to hold the facets data
    facet_data = []
    
    params = {
        "zone": "newspaper",
        "key": API_KEY,
        "encoding": "json",
        "q": " ",
        "facet": "year",
        "n": 0  # We don't need any records, just the facets!
    }

    if state:
        params["l-state"] = state
    
    # Loop through the decades
    for decade in range(start_decade, end_decade + 1):

        # Add decade value to params
        params["l-decade"] = decade

        # Get the data from the API
        data = get_results(params)

        # Get the facets from the data and add to facets_data
        facet_data += get_facets(data)

        # Try to avoid hitting the API rate limit - increase this if you get 403 errors
        time.sleep(0.2)

    df = pd.DataFrame(facet_data)
    df.columns = ['year', 'total']
    df = fill_missing_years(df)
    return df

def get_state_totals(start_decade=180, end_decade=202):
    dfs = []
    for state in STATES:
        facets = get_year_totals(state=state)
        df = pd.DataFrame(facets)
        df.columns = ['year', 'total']
        df = fill_missing_years(df)
        df['state'] = state
        dfs.append(df)
        time.sleep(1)
    df_all = pd.concat(dfs)
    df_all = df_all[['state', 'year', 'total']]
    return df_all

def get_newspaper_titles():
    params = {
        "key": API_KEY,
        "encoding": "json"
    }
    response = s.get('https://api.trove.nla.gov.au/v2/newspaper/titles', params=params)
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data['response']['records']['newspaper'])[['id', 'title', 'state', 'issn', 'startDate', 'endDate']]
    df['id'] = df['id'].astype('Int64')
    df.columns = ['title_id', 'title', 'state', 'issn', 'start_date', 'end_date']
    return df

def get_newspaper_totals():
    params = {
        "zone": "newspaper",
        "key": API_KEY,
        "encoding": "json",
        "q": " ",
        "facet": "title",
        "n": 0  # We don't need any records, just the facets!
    }

    # Get the data from the API
    data = get_results(params)
    facet_data = get_facets(data)
    df_totals = pd.DataFrame(facet_data)
    df_totals.columns = ['title_id', 'total']
    df_titles = get_newspaper_titles()
    df = pd.merge(df_totals, df_titles, how='left', on='title_id')
    # Some data is currently missing from the API newspapers endpoint
    df.fillna('', inplace=True)
    return df

def get_category_totals():
    params = {
        "zone": "newspaper",
        "key": API_KEY,
        "encoding": "json",
        "q": " ",
        "facet": "category",
        "n": 0  # We don't need any records, just the facets!
    }

    # Get the data from the API
    data = get_results(params)
    facet_data = get_facets(data)
    df = pd.DataFrame(facet_data)
    df.columns = ['category', 'total']
    return df

def get_total_articles():
    params = {
        "zone": "newspaper",
        "key": API_KEY,
        "encoding": "json",
        "q": " ",
        "n": 0  # We don't need any records, just the facets!
    }
    return get_total_results(params)

def get_overall_totals():
    totals = []
    totals.append({'harvest_type': 'all', 'total': get_total_articles()})
    params = {
        "zone": "newspaper",
        "key": API_KEY,
        "encoding": "json",
        "n": 0  # We don't need any records, just the facets!
    }
    for activity in ['corrections', 'tags', 'comments']:
        params['q'] = f'has:{activity}'
        total = get_total_results(params)
        totals.append({'harvest_type': params['q'], 'total': total})
    df = pd.DataFrame(totals)
    return df

def fill_missing_years(df):
    df = df.set_index('year')
    df = df.reindex(range(df.index.min(), df.index.max() +1)).reset_index()
    df.fillna(0, inplace=True)
    df['year']= df['year'].astype('Int64')
    df['total']= df['total'].astype('Int64')
    return df

def main():
    Path('data').mkdir(exist_ok=True)
    df_overall_totals = get_overall_totals()
    df_overall_totals.to_csv(Path('data', f'total_articles_by_activity.csv'), index=False)
    df_totals = get_year_totals()
    df_totals.to_csv(Path('data', f'total_articles_by_year.csv'), index=False)
    df_states = get_state_totals()
    df_states.to_csv(Path('data', f'total_articles_by_year_and_state.csv'), index=False)
    df_newspapers = get_newspaper_totals()
    df_newspapers.to_csv(Path('data', f'total_articles_by_newspaper.csv'), index=False)
    df_categories = get_category_totals()
    df_categories.to_csv(Path('data', f'total_articles_by_category.csv'), index=False)

if __name__ == "__main__":
    main()