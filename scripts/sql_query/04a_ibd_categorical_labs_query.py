"""
Title: Preperation of Categorical Labs for IBD between visits and flares 
Author: Ryan Gan
Date Created: 2020-01-15

This script will generate permanent SQL table of categorical labs for IBD cohort 
to predict flares.

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
Build permanent labs with flare table using templates in sql_template folder
1. Identify lab tests in Waljee et al. 2017 with valid values
2. Query baseline lab tests within 7 days of a visit
3. Query lab tests that occur within 6 months or until flare event of visit date
--------------------------------------------------------------------------------
"""
)

print(
"""
Step 1. Query of most common labs tested in Waljee et al. 2017 with valid values
defined as having a value within physiologically possible range of results (Y)
using the 'value_within_range' variable
"""
)

# set file path
file_path = './sql_templates/labs/'

# create lab list to search through; added fecal calprotecin
labs_search_list = ['(WBC)', '(MCH)', '(MCHC)', '(MCV)', '(Na)', '(K)', 
                    'Glucose', '(BUN)', 'Creatinine', 'Calcium', 
                    'Bicarbonate', 'Chloride', 'Albumin', '(AST)', '(ALT)', 
                    '(CRP)', '(ALP)', 'Bilirubin.total', 'Platelet', 
                    'Neutrophil', 'Lymphocyte', 'Eosinophil', 'Basophil', 
                    'Monocyte', 'Calprotectin']

# Note, there were no observations of calprotectin available in the April 2019
# release. I will make a seperate query for these data.

print('Wildcard search list for labs =^o.o^=')
print(labs_search_list)

# open query of lab counts; uses same list of labs numeric lab summary 
with open(file_path + 'id_labs_of_interest.sql') as f:
    find_labs_template = f.read()
    
# build query using jinja2
find_query = Template(find_labs_template).render(labs=labs_search_list) 

print("Running query to find lab listed in Waljee et al with valid values")
# convert labs list query to pandas dataframe    
labs_list = pd.read_sql_query(find_query, con)

print("""
Excluding the following labs due to small
number collected and based on feedback from Diana.
""")

# labs to exclude
labs_exclude = ['Albumin.CSF', 'Creatinine clearance',
                'Glucose.tolerance test.2 hour']

# subset to labs to extract from sql query
labs_to_extract = labs_list[labs_list['TEST_NAME'].isin(labs_exclude)==False]

# save labs extracted to query metrics
print('Printing labs to extract; already saved in the numeric labs pipeline')
print(labs_to_extract)

# extract test name to loop through
labs_loop_list = labs_to_extract['TEST_NAME'].tolist()


# create variable names that are a combo name without special chars
# units are not needed as the categorical variables are based on 
# normal ranges relative to the test observation
var_name_list = [
    i.lower()
    # take first element before ()
    .split('(')[0]
    # strip trailing whitespace
    .strip()
    # replace spaces and other characters with _
    .replace(' ', '_')
    .replace('.', '_')
    .replace('-', '_')
    for i in labs_loop_list
]

print("""
List of labs to extract from database for each IBD cohort patient.

""")
print(labs_loop_list)


print("""
List of names to give lab variables.

""")
print(var_name_list)

print(
"""
Create permanent labs table that contains longitudinal 
summaries and baseline (at visit) binary and categorical 
values for labs
"""
)

# define file path with sql templates
file_path = './sql_templates/labs/'

# tables to loop through
tables = ['categorical_labs', 'ibd_flare.categorical_labs_wide']

# loop through sql scripts to run
for tab in tables:
    print('Reading in template ' + tab)

    with open(file_path + tab + '.sql') as f:
        template = f.read()

    # creating baseline labs query from full labs table
    sql_query = Template(template).render(
        # loop for lab variables
        labs = labs_loop_list, 
        # zipped loop that contains full lab name and list
        labs_zip = zip(labs_loop_list, var_name_list)
    )
    
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

    
print("""
Permanent table ibd_flare.labs_wide created.
""")
