"""
--------------------------------------------------------------------------------
Title: Identification of flare outcomes for IBD cohort
Author: Ryan Gan
Date Created: 2019-06-28

This script will generate permanent SQL table for flares.
--------------------------------------------------------------------------------
"""
# load teradatasql to establish connection to teradata
import teradatasql
# import jinja2 for looping in sql query
from jinja2 import Template
# os 
import os
# import timeit for timing
import timeit
# import pandas to save a table
import pandas as pd


# read hidden login info; not the best way to do this but it works
login = [line.rstrip('\n') for line in open('../sql_query/login.txt')]

# new connection info for teradatasql client
usertd = login[2]
passwordtd = login[3]
host = login[4]

# create connection to teradata
con = teradatasql.connect('{"host": "' + host + '",' + \
                          '"user": "' + usertd + '",' + \
                          '"password": "' + passwordtd + '",' + \
                          '"logmech":"LDAP"}')

# create cursor to submit scripts
cur = con.cursor()

"""
Build flare permanent table using templates in sql query
--------------------------------------------------------------------------------
"""

# set file path
file_path = './sql_templates/flare'

query_list = ['ibd_enc_count', 'ibd_enc_date', 'ibd_pos', 'inpat_flare',
              'outpatient_oral_cortsteroid', 'cortsteroid_no_comorb', 
              'flares']

# next step is to join inpatient and outpatient steroids 

start_time = timeit.default_timer()

# loop through list
for q in query_list:
    # Load query
    with open('./sql_templates/flare/' + q + '.sql') as f:
        query = f.read()
    print(query)
    
    # if else
    if 'flares' not in q:
        # submit query
        try:
            print('Attempting to submit query')
            cur.execute(query)
            print('Finished query')
        except:
            start_time = timeit.default_timer()
            print('Table alread exists; dropping table and trying again.')
            cur.execute('DROP TABLE ' + q)
            cur.execute(query)
            print('Finished query')

    # else to handle temp table
    else:
        # submit query
        try:
            print('Attempting to submit query')
            cur.execute(query)
            print('Finished query')
        except:
            start_time = timeit.default_timer()
            print('Table alread exists; dropping table and trying again.')
            cur.execute('DROP TABLE ibd_flare.' + q)
            cur.execute(query)
            print('Finished query')

stop_time = timeit.default_timer() 
print('Time to run (minutes):', (stop_time-start_time)/60)

"""
Calculate percent missing day supply and save as results as part of sensitivity
analyses to understand implications for our outpatient flare definition.
--------------------------------------------------------------------------------
"""

query = """
SELECT day_supply_criteria, 
    COUNT(*) as n_obs, 
    COUNT(DISTINCT ptid) as n_ptid
FROM outpatient_oral_cortsteroid
GROUP BY day_supply_criteria;
"""

day_supply_missing = pd.read_sql_query(query, con)

# precent obs with day supply
day_supply_missing['percent_n_obs'] = day_supply_missing['n_obs']*100.0/day_supply_missing['n_obs'].sum()
day_supply_missing['percent_n_ptid'] = day_supply_missing['n_ptid']*100.0/day_supply_missing['n_ptid'].sum()

# print attrition tab
print(day_supply_missing)
# write table
day_supply_missing.to_csv('../../results/query_metrics/steroid_daysup_missing.csv', 
                          index = False)

print("Script done running.")

