"""
--------------------------------------------------------------------------------
Title: Query of fecal calprotectin labs on cohort subjects
Author: Ryan Gan
Date Created: 2019-06-28

This script will generate permanent SQL table for fecal cal.
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
Query of fecal cal to create ibd_flare.fecal_cal data lab
"""

file_path = './sql_templates/fecal_cal/ibd_flare.fecal_cal.sql'

with open(file_path) as f:
    query = f.read()
    print(query)
    
# execute query
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
    
    
"""
Create pandas dataframe and save to AWS environment
"""
# sql table to pandas
fecal_cal = pd.read_sql('SELECT * FROM ibd_flare.fecal_cal', con)
# set columns to lower
fecal_cal.columns = map(str.lower, fecal_cal.columns)


# summary statistics on fecal cal on count of observations and unique patients
fecal_cal_count = fecal_cal.agg({'ptid': ['count', 'nunique']})
print(fecal_cal_count)

# save to dataframe in results folder
fecal_cal_count.to_csv('../../results/manuscript/fecal_cal_count.csv')

# write to data folder
fecal_cal.to_csv('../../data/fecal_cal.csv')
