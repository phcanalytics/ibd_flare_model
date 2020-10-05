"""
Title: Selecting Labs Measures Features 
Author: Ryan Gan
Date Created: 2020-02-14

Script to identify labs measured on at least 70% of visits/observations.
Rational that these would be the most commonly tested labs in Optum
EHR and hence the most useful in practice.
"""


"""
Modules
"""
print('Importing modules/packages')
# import pandas and numpy
import pandas as pd
import os
import yaml
from datetime import date 

# define project root directory based on project structure; c
root_dir = os.path.dirname(os.path.dirname(os.getcwd()))

# read flare prediction csv using pandas
analysis_df = pd.read_csv(
    (root_dir + "/data/raw/ibd_flare_analysis.csv"), 
    dtype = {'birth_yr': str, 
             'date_of_death': str}
)

# drop unnamed variable
del(analysis_df['Unnamed: 0'])
del(analysis_df['PTID'])

"""
Calculation of variable completeness and identificaiton 
of labs measured on at least 70% of observations
"""
variable_completeness = (analysis_df.count()/analysis_df['id'].count())

# save variable completeness
variable_completeness.to_csv(
    root_dir + 
    # path to query metrics to save results
    '/results/query_metrics/variable_completeness.csv',
    index_label='variable', header=['proportion'])

# subset variable names with at least 70% complete
var_names = list(variable_completeness.loc[lambda x: x >= 0.7].index)

# creating list of wbc subset labs that will not be considered in the model 
# as they are a subset of wbc in general
wbc_subset = ['monocyte', 'lymphocyte', 'eosinophil', 'neutrophil', 'basophil']

# append list of wbc subsets to exclude from analysis
wbc_subset_list = [j for j in var_names if any(i in j for i in wbc_subset)]

"""
Create dictionary of lists of labs measured on at least 70% of visits to
add to yaml config file. These labs will be used in all models
"""

# create empty dictionry labs to append to config yaml file
labs = {}

for i in ['_base', '_mean', '_max', '_mean_acc', '_max_acc']:
    # this finds all labs with the lab version and excludes white bloodcell subsets 
    labs_list = list(set([j for j in var_names if i in j]) - set(wbc_subset_list))
    # sort labs list
    labs_list.sort()
    # append labs dictionary
    labs.update({'labs' + i: labs_list})


"""
Open analysis_config.yaml and update with labs that will
go into the model
"""
with open('analysis_config.yaml', 'r') as f:
    config = yaml.safe_load(f)
    
# add dictionary of labs list to yaml file
config['features']['labs'] = labs
# append date modified for features
print('Updated:', date.today())
config['features']['date_modified'] = date.today()

# write updated config file
with open('analysis_config.yaml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
