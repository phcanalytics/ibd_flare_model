"""
Title: Joining flare events to visits for IBD cohort
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
Build visits permanent table using templates in sql_template folder
1. Identify physical encounters for IBD cohort
2. Create permanent visit table
3. Find flares only in IBD cohort and restrict to only new events after 90 days
4. Join to visits table
--------------------------------------------------------------------------------
"""

# set file path
file_path = './sql_templates/visits/'

print("""
Reading in the sql query list found in the sql_template/visits/ folder.
I've ordered each script in the sequence in which they should
run.
""")


# order and name of sql queries to run
query_list = ['physical_encounters', 'visits',
              'previous_flare_sum', 'flare_visits']

print("List of scripts to run:")
print(query_list)

start_time = timeit.default_timer()

# loop through list
for q in query_list:
    # Load query
    with open(file_path + q + '.sql') as f:
        query = f.read()
    print(query)
    
    # if else for final script in sequence table
    if 'flare_visits' not in q:
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
Calculate number of visit type encounters and unique persons
--------------------------------------------------------------------------------
"""

query = """
SELECT interaction_type, SUM(n_enc), COUNT(visit_date), COUNT(DISTINCT ptid), 
    COUNT(visit_date)*1.0/COUNT(DISTINCT ptid) AS avg_visit_n
FROM
    (
     SELECT ptid, interaction_type, interaction_date AS visit_date, 
     COUNT(*) AS n_enc
     FROM physical_encounters
     GROUP BY ptid, interaction_date, interaction_type
    ) AS temp
GROUP BY interaction_type;  
"""

visit_obs = pd.read_sql_query(query, con)
# print attrition tab
print(visit_obs)
# write table
visit_obs.to_csv('../../results/query_metrics/visit_obs.csv', index = False)

print("Script done running.")
