# Trove newspaper totals

This repository contains an automated git scraper that uses the [Trove API](https://troveconsole.herokuapp.com/) to save information about the number of digitised newspaper articles currently available through [Trove](https://trove.nla.gov.au/). It runs every week and updates two datasets:

* [total_articles_by_year.csv](data/total_articles_by_year.csv)
* [total_articles_by_year_and_state.csv](data/total_articles_by_year_and_state.csv)
* [total_articles_by_newspaper.csv](data/total_articles_by_newspaper.csv)
* [total_articles_by_category.csv](data/total_articles_by_category.csv)

By retrieving all versions of these files from the commit history, you can analyse changes in Trove over time.

## Dataset details

### total_articles_by_year.csv

The dataset is saved as a CSV file containing the following columns:

* `year`: year of original publication of newspaper article
* `total`: total number of articles from that year available in Trove

### total_articles_by_year_and_state.csv

The dataset is saved as a CSV file containing the following columns:

* `state`: state in which newspaper article was originally published
* `year`: year of original publication of newspaper article
* `total`: total number of articles from that year and state available in Trove

Trove uses the following values for `state`:

* ACT
* International
* National
* New South Wales
* Northern Territory
* Queensland
* South Australia
* Tasmania
* Victoria
* Western Australia

### total_articles_by_newspaper.csv

This harvest uses the `title` facet to get the number of articles for each title. This information is supplemented with title data from the `newspapers` API endpoint. At the moment (20 April 2022), eight titles are missing from the `newspapers` endpoint, so the `title`, `state`, `issn`, `start_date`, and `end_date` fields will be blank for these records. Once this bug is fixed, the harvest should pick up the missing title data automatically.

The dataset is saved as a CSV file containing the following columns:

* `title_id`: the Trove newspaper title identifier
* `total`: total number of articles from this newspaper
* `title`: title of the newspaper
* `state`: state in which the newspaper was published
* `issn`: title ISSN (where there is no ISSN an internal identifier has been assigned))
* `start_date`: date of earliest issue in Trove
* `end_date`: date of latest issue in Trove

### total_articles_by_category.csv

The dataset is saved as a CSV file containing the following columns:

* `category`: article category (eg: 'Advertising', 'Article')
* `total`: total number of articles assigned to this category

## Method

The harvesting code is available in `get_article_totals.py`. It uses facets to fetch the number of articles available fromS Trove. For more information and examples see [Visualise the total number of newspaper articles in Trove by year and state](https://glam-workbench.net/trove-newspapers/#visualise-the-total-number-of-newspaper-articles-in-trove-by-year-and-state) in the GLAM Workbench.

## More datasets

I've also created a [repository of historical harvests](https://github.com/wragge/trove-newspaper-totals-historical), created between 2011 and 2022.

---

Created by [Tim Sherratt](https://timsherratt.org), April 2022. If you think this is useful, you can become a [GitHub sponsor](https://github.com/sponsors/wragge).

