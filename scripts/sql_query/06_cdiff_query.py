"""
--------------------------------------------------------------------------------
Title: Query to persons in the IBD cohort with a clostridium difficile diagnosis
Author: Ryan Gan
Date Created: 2019-06-28

This script will generate permanent SQL table persons in our IBD cohort with a 
diagnosis of C-diff in case we decide to exclude
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

file_path = './sql_templates/cdiff/ibd_flare.cdiff.sql'

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
Count up how many outpatient corticosteroid events may be misclassified
"""

cdiff_statistics = pd.read_sql("""
    SELECT COUNT(*) AS cortsteroid_count,
        COUNT(cdiff_flag) AS cdiff_count,
        cdiff_count*100.0/cortsteroid_count AS prop_cdiff
    FROM
        (
        SELECT a.*,
            b.diag_date AS cdiff_date, 
            b.cdiff_flag
        FROM ibd_flare.analysis AS a
        LEFT JOIN ibd_flare.cdiff AS b 
        ON (a.ptid = b.ptid) AND 
            (a.flare_date >= b.diag_date - 7 AND a.flare_date <= b.diag_date + 7)
        WHERE a.flare_cat = 'outpat_corticosteroid_flare'
        ) AS temp;
    """, con)

# save to results folder

print('Outpatient corticosteroid events with possible C-Diff misclassification\n\n', 
      cdiff_statistics, 
      file=open("../../results/cdiff_stats.txt", "w"))