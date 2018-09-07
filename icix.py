import pandas as pd
import numpy as np
import time
from datetime import date

from urllib.request import urlopen
from itertools import zip_longest

url = "https://www.numbeo.com/cost-of-living/rankings_current.jsp"
html = urlopen(url)
table = pd.read_html(html.read())
table = table[2].drop(columns='Rank')

citco = table.City.str.split(", ")
citco = pd.DataFrame.from_records(zip_longest(*citco.values)).T
citco[1] = np.where(citco[2].isna() == False, citco[2], citco[1])

table.City = citco[0]
table["Country"] = citco[1]

homecity = 'San Francisco'

aimed_date = date(2082, 5, 7)
timeleft = aimed_date - date.today()

monthly_col = 2500
monthly_sal = 7500

hmcolrix = table \
    [table.City == homecity]\
    ['Cost of Living Plus Rent Index']\
    .values[0]

hmppix = table \
    [table.loc[:,'City'] == homecity]\
    .loc[:,'Local Purchasing Power Index']\
    .values[0]

ixval = monthly_col / hmcolrix
table["COLwR"] = table.loc[:, 'Cost of Living Plus Rent Index'] * ixval

moneytoget = monthly_col * (timeleft.days / 365 * 12)

NYcol = monthly_col / hmcolrix * 100
NYsal = (monthly_sal * 10000) / (hmcolrix * hmppix)

query = table.drop(columns=['Cost of Living Index',
'Rent Index',
'Groceries Index',
'Restaurant Price Index'])

###############
# Assumptions
# PP_i = w_i / c_i * c_ny / w_ny * 100
# CI_i = C_i / C_ny * 100
# DI_i = w_i - c_i
##############33

disc = query.loc[:,'Cost of Living Plus Rent Index'] \
    * (query.loc[:, 'Local Purchasing Power Index'] * NYsal - 100 * NYcol) \
    / 10000

# table.sort_values(by='CwR_x_LPPI', ascending=False).head(20)

disc = query.loc[:,'Cost of Living Plus Rent Index'] \
    * (query.loc[:, 'Local Purchasing Power Index'] * NYsal - 100 * NYcol) \
    / 10000

disc[disc < 0] = np.NaN

query.loc[:, 'DiscInc'] = disc
query.loc[:, 'YearsToWork'] = moneytoget / query.DiscInc / 12

query.to_csv('disc_inc_{}.csv'.format(time.strftime("%y%m%d-%H%M%S",
                                                    time.localtime())),
            index=False)

print(query.sort_values('YearsToWork').head(30))
