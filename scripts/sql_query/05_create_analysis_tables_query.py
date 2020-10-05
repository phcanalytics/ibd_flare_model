"""
--------------------------------------------------------------------------------
Title: Creation of binary labs analysis table for IBD cohort for flare project
Author: Ryan Gan
Date Created: 2020-01-30

Purpose: The propose of this script is to join the visits, flares, categorical
labs, demographics, and immunosuppressive use in a final table for analysis.
All SQL templates can be found in the 'sql_template/analysis/' folder
--------------------------------------------------------------------------------
"""

# load teradatasql to establish connection to teradata
import teradatasql
# load pandas
import pandas as pd
# import jinja2 for looping in sql query
from jinja2 import Template
# os 
import os
from datetime import date, datetime
import timeit

# read hidden login info; not the best way to do this but it works
login = [line.rstrip('\n') for line in open('login.txt')]

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

print(    
"""
This script joins the visits with flare (ibd_flare.flare_vists) table with 
any prescription of immuosuppresive medications at or before visit temp table, 
demographics table, and baseline and categorical labs summary together. It then
subsets only to patient visits with at least one lab measurement. The final step
is to save a permanent table and csv file.
"""
)

print(
"""
Reading in the labs_wide table to extract names of labs.
""")

# extract variable names from labs_wide table as list
lab_names = list(
    pd.read_sql_query(
        'SELECT TOP 1 * FROM ibd_flare.labs_wide;', 
        con).columns
)[2:]


# file path
file_path = './sql_templates/analysis/'

# tables to loop through
tables = ['immuno_med_date_window', 'flare_predictors', 'ibd_flare.analysis']

# loop through sql scripts to run
for tab in tables:
    print('Reading in template ' + tab)

    with open(file_path + tab + '.sql') as f:
        template = f.read()
        
    # creating query from template
    sql_query = Template(template).render(labs = lab_names)

    start_time = timeit.default_timer()
    try:
        print('Submitting query')
        cur.execute(sql_query)
    except:
        print('Table alread exists; dropping table and trying again.')
        cur.execute('DROP TABLE ' + tab)
        cur.execute(sql_query)
        print('Finished query')
        
    stop_time = timeit.default_timer() 
    print('Time to run (minutes):', (stop_time-start_time)/60)

# write pandas analysis dataframe to Ryan's AWS environment
print(
"""
Writing analysis table to AWS drive to speed up read time.
"""
)
# try catch query
try:
    start_time = timeit.default_timer()
    # using read chunks of 100000 to build a pandas dataframe
    dfs_list = []
    count=0
    for chunk in pd.read_sql_query('SELECT * FROM ibd_flare.analysis', 
                                   con, chunksize=100000):
        count +=1
        print('Chunk', count)
        dfs_list.append(chunk)
    # concat dataframes list
    analysis_df = pd.concat(dfs_list)
    # print time the query and conversion to dataframe table takes
    print('Finished writing labs of size:', analysis_df.shape)
    stop_time = timeit.default_timer() 
    print('Time to run (minutes):', (stop_time-start_time)/60)
    print('Attempting to write dataframe to csv')
    
    
    # function to find quantile
    def q1(x):
        return x.quantile(0.25)
    def q2(x):
        return x.quantile(0.75)
    # find how many visits there are left
    visit_summary = analysis_df[['id', 'vis_date']] \
        .groupby(['id']) \
        .count() \
        .reset_index() \
        .agg({'vis_date': ['count', 'sum', 'mean', 'std', 
                           'median', q1, q2, 'min', 'max']}) \
        .round(1) \
        .rename(columns = {'vis_date':'post_lab_exclusion'},
                index = {'count':'n_ptid', 'sum':'n_visits',
                         'mean':'mean_vis', 'std':'std_vis', 
                         'median':'median_vis', 
                         'q1': 'perc_25',
                         'q2': 'perc_75',
                         'min':'min_vis', 
                         'max':'max_vis'})
    # print number of visits per sumbect after visit
    print(visit_summary)
    # write summary
    visit_summary.to_csv('../../results/query_metrics/visit_summary.csv')
    # writing analysis datatable to data folder for analysis
    write_path = '../../data/ibd_flare_analysis.csv' 
    analysis_df.to_csv(write_path)    
except Exception as e: print(e)
 
print(
"""
Query and writing the anlaysis tables to Ryan's AWS container. It's faster
to read the csv files from AWS than to convert to SQL table each time.
"""
)    
   


print(
"""

                      \`*-.                    
                       )  _`-.                 
                      .  : `. .                
                      : _   '  \               
                      ; *` _.   `*-._          
                      `-.-'          `-.       
     Script is done     ;       `       `.     
     meow!              :.       .        \    
                        . \  .   :   .-'   .   
                        '  `+.;  ;  '      :   
                        :  '  |    ;       ;-. 
                        ; '   : :`-:     _.`* ;
                      .*' /  .*' ; .*`- +'  `*' 
                     `*-*   `*-*  `*-*'                                     

""")