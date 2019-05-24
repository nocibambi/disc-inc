# This script downloads city cost of living and purchasing power index
# information from Numbeo and uses them to calculate discretionary income
# estimates.
# It prints out the results and saves them into a csv.
# Currently it does not include tax rates.
# It also calculates years to achieve a particular financial goal
# (e.g. for retirement) in each city.

import pandas as pd
import numpy as np
import time
from datetime import date

from urllib.request import urlopen
from itertools import zip_longest

# Pulling Numbeo's cost of living index rankings
url = "https://www.numbeo.com/cost-of-living/rankings_current.jsp"
html = urlopen(url)
table = pd.read_html(html.read())
table = table[2].drop(columns="Rank")

# Arranging city and country information into two columns
citco = table.City.str.split(", ")
citco = pd.DataFrame.from_records(zip_longest(*citco.values)).T
citco[1] = np.where(citco[2].isna() == False, citco[2], citco[1])

table.City = citco[0]
table["Country"] = citco[1]

# Pulling tax information
taxurl = "https://tradingeconomics.com/country-list/personal-income-tax-rate"
html = urlopen(taxurl)
taxpage = pd.read_html(html)
tax = taxpage[0]

tax = tax.rename(columns={"Last": "Tax"})
tax.loc[:, "Tax"] = tax["Tax"] / 100

table = pd.merge(table, tax[["Country", "Tax"]], on="Country", how="left")

# The reference data
homecity = "San Francisco"

# Expected year to live
aimed_date = date(2082, 5, 7)
timeleft = aimed_date - date.today()

# Monthly cost and income in the reference city
monthly_col = 2500
monthly_sal = 142338 / 12

# Cost of living index in the home city
hmcolrix = table[table.City == homecity][
    "Cost of Living Plus Rent Index"
].values[0]

# Puchasing power index index in the home city
hmppix = (
    table[table.loc[:, "City"] == homecity]
    .loc[:, "Local Purchasing Power Index"]
    .values[0]
)

# Calculating cost of living figures for each city
ixval = monthly_col / hmcolrix
table["COLwR"] = table.loc[:, "Cost of Living Plus Rent Index"] * ixval

# Defining the financial aim
moneytoget = monthly_col * (timeleft.days / 365 * 12)

# New York cost and salary values
NYcol = monthly_col / hmcolrix * 100
NYsal = (monthly_sal * 10000) / (hmcolrix * hmppix)

query = table.drop(
    columns=[
        "Cost of Living Index",
        "Rent Index",
        "Groceries Index",
        "Restaurant Price Index",
    ]
)

###############
# ORIGINAL
# Assumptions for discretionary income calculation (need to be checked with
# Numbeo's own definitions). The 'ny' index stands for New York which is the
# benchmark.
# Purchasing power: PP_i = w_i / c_i * c_ny / w_ny * 100
# Living costs (not index!): CI_i = C_i / C_ny * 100
# DI_i = w_i - c_i
################

# Discretionary income
## Original
# disc = query.loc[:,'Cost of Living Plus Rent Index'] \
#     * (query.loc[:, 'Local Purchasing Power Index'] * NYsal - 100 * NYcol) \
# / 10000

###############
# Revised
# CI_i = C_i / C_ny
# PPI_i = (W_i / C_I) / PPI_ny
# PPI_ny = W_ny / C_ny
# W_i = PPI_i * C_i * W_ny / (C_ny)
# DISP_i = W_i - Tax_i
# DISC_i = DISP_i - C_i
###########3

query.loc[:, "Income"] = (
    query["COLwR"]
    * (query["Local Purchasing Power Index"] * NYsal)
    / NYcol
    / 100
)


query.loc[:, "DispInc"] = query["Income"] * (1 - query["Tax"])
query.loc[:, "DiscInc"] = query["DispInc"] - query["COLwR"]

# table.sort_values(by='CwR_x_LPPI', ascending=False).head(20)

query.loc[query["DiscInc"] < 0, "DiscInc"] = np.NaN

# Years to earn for given financial goal
# query.loc[:, "DiscInc"] = disc
query.loc[:, "YearsToWork"] = moneytoget / query.DiscInc / 12

# Writing the query to csv
query.to_csv(
    "disc_inc_{}.csv".format(time.strftime("%y%m%d-%H%M%S", time.localtime())),
    index=False,
)

print(query.sort_values("YearsToWork").head(30))
