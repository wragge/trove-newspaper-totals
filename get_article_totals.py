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
            facets.append({"year": term["search"], "total": int(term["count"])})

        # Sort facets by year
        facets.sort(key=itemgetter("year"))
    except TypeError:
        pass
    return facets


def get_facet_data(start_decade=180, end_decade=201, state=None):
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
    df = fill_missing_years(df)
    return df

def get_states_data(start_decade=180, end_decade=202):
    '''
    Loop through a list of states getting the number of articles per year for each.
    '''
    dfs = []
    for state in STATES:
        facets = get_facet_data(state=state)
        df = pd.DataFrame(facets)
        # Fill in missing years
        df = fill_missing_years(df)
        df['state'] = state
        dfs.append(df)
        time.sleep(1)
    df_all = pd.concat(dfs)
    # Order columns
    df_all = df_all[['state', 'year', 'total']]
    return df_all

def fill_missing_years(df):
    '''
    Fills in any missing years in the current range.
    Gives missing years a total value of 0.
    '''
    df = df.set_index('year')
    df = df.reindex(range(df.index.min(), df.index.max() +1)).reset_index()
    df.fillna(0, inplace=True)
    df.columns = ['year', 'total']
    df['year']= df['year'].astype('Int64')
    df['total']= df['total'].astype('Int64')
    return df

def main():
    Path('data').mkdir(exist_ok=True)
    df_totals = get_facet_data()
    df_totals.to_csv(Path('data', f'total_articles_by_year.csv'), index=False)
    df_states = get_states_data()
    df_states.to_csv(Path('data', f'total_articles_by_year_and_state.csv'), index=False)

if __name__ == "__main__":
    main()