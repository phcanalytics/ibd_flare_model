"""
--------------------------------------------------------------------------------
Title: Identifying IBD 
    
Author: Ryan Gan
Date Created: 2019-06-28

This script identifies the IBDcohort based on criteria of at least two IBD 
diagnoses at either outpatient or inpatient visits, with at least one diagnosis 
at an outpatient visit. This script also creates the attrition table to
understand sample size of patients based on inclusion/exclusion criteria.

This script will automatically generate the attrition table based on criteria.
--------------------------------------------------------------------------------
"""

# load teradatasql to establish connection to teradata
import teradatasql
# load pandas
import pandas as pd
# import jinja2 for looping in sql query
from jinja2 import Template
# os 
# import os functions
import os

from datetime import date, datetime
import timeit

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
--------------------------------------------------------------------------------
Build cohort using templates in sql query
--------------------------------------------------------------------------------
"""

# set file path
file_path = './sql_templates/ibd_cohort'
# set query order in list
query_list = ['ibd_enc_count', 'ibd_enc_date', 'ibd_pos', 'ibd_visit',
              'two_ibd_visits', 'ibd_cont_enroll', 'ibd_cohort']

start_time = timeit.default_timer()

# loop through list
for q in query_list:
    # Load query
    with open('./sql_templates/ibd_cohort/' + q + '.sql') as f:
        query = f.read()
    print(query)
    
    # if else
    if 'ibd_cohort' not in q:
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


print(
"""
Check and count of number of eligible subjects and metrics. 
Out of the unique patients identified, everyone is expected to have
at least 1 outpatient visit, and the minimum observed number of ibd_visits
should be at least 2. 
"""
)

aggregate_cohort_metrics = pd.read_sql_query(
"""
SELECT COUNT(DISTINCT ptid) AS n_ptid, 
    SUM(outpatient_flag) AS one_or_more_outpatient, 
    SUM(inpatient_flag) AS one_or_more_inpatient, 
    MIN(ibd_visit_n) AS min_number_of_ibd_vis 
FROM ibd_flare.ibd_cohort;
""", con)
    
print(aggregate_cohort_metrics)

# save aggregate cohort metrics
aggregate_cohort_metrics \
    .to_csv("../../results/query_metrics/cohort_query_metrics.csv", index = False)

"""
--------------------------------------------------------------------------------
Create Attrition Table Using Query Tables
--------------------------------------------------------------------------------
"""

#Step 1: Count of all patients in Optum IBD 2019 data cut
# initiate query of top row from ibd flare analysis 
n_ptid = pd.read_sql_query(
"""
SELECT 
    COUNT(DISTINCT ptid) AS n_ptid
FROM RWD_VDM_OPTUM_EHRIBD.IBD_PATIENT
WHERE batch_title = 'OPTUM EHR IBD 2019 Apr';
""", con)

# add category column
n_ptid['Criteria'] = "All Patients in Optum" 
    
# count of at least one ibd count between 2007-01-01 and 2018-12-30
n_one_ibd = pd.read_sql_query(
"""
SELECT 
    COUNT(DISTINCT ptid) AS n_ptid
FROM ibd_pos;
""", con)

n_one_ibd['Criteria'] = ('At least one inpatient or outpatient IBD ' +
                         'diagnosis between 2007-01-01 to 2017-12-31')

# count at least two visits
n_two_ibd = pd.read_sql_query(
"""
SELECT COUNT(DISTINCT ptid) as n_ptid FROM two_ibd_visits;
""", con)

n_two_ibd['Criteria'] = ('At least two IBD diagnoses, with at least ' +
                         'one office visit (outpatient)')

# 365 days after first ibd date
n_365 = pd.read_sql_query(
"""
SELECT COUNT(DISTINCT ptid) AS n_ptid FROM ibd_cont_enroll;
""", con)

n_365['Criteria'] = ('At least 365 days of follow up/activity in EHR ' +
                     '(last active date - first IBD date)')

# over 18 ibd cohort
n_over18 = pd.read_sql_query(
"""
SELECT COUNT(DISTINCT ptid) AS n_ptid FROM ibd_flare.ibd_cohort;
""", con)

n_over18['Criteria'] = ('Over the age of 18 at the index IBD date ' +
                        '(first date of IBD diagnosis)')

# create attrition table
attrition_tab = pd.concat([n_ptid, n_one_ibd, 
                           n_two_ibd, n_365, 
                           n_over18])[['Criteria', 'n_ptid']]

# print attrition tab
print(attrition_tab)

# save attrition table
attrition_tab.to_csv('../../results/attrition_table.csv', index = False)
