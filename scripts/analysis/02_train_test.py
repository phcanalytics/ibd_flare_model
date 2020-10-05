"""
Title: Splitting raw analysis dataframe to training and testing
Author: Ryan Gan
Date Created: 2020-02-14

Script to split the analysis dataframe to training and testing
using a seed so that the 70% of data are used for training
and same 30% of data used for testing are the same across
models. This script also excludes observations with an
outpatient corticosteroid prescription, but that did not have
the 7 day supply to reduce misclassification of outcome.
"""

"""
Modules
"""
print('Importing modules/packages')
# import pandas and numpy
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split 
import os
import joblib # for saving train_test split
import yaml

"""
Read in analysis dataframe and process dataframe
"""
# define project root directory based on project structure; c
root_dir = os.path.dirname(os.path.dirname(os.getcwd()))
# define results folder as query metrics
results_folder = root_dir + '/results/query_metrics/'

# read flare prediction csv using pandas
analysis_df = pd.read_csv(
    (root_dir + "/data/raw/ibd_flare_analysis.csv"), 
    dtype = {'birth_yr': str, 
             'date_of_death': str}
)

# delete Unnamed: 0 column
try:
    del(analysis_df['Unnamed: 0'])
except:
    print('Already deleted column')

print("Filtering out observations of corticosteroid without 7 day supply")
# count number of observations before filter
obs_pre_filter = analysis_df.shape[0] 

# remove observations where flare_v1 = 0 and steorid_flare is present, but day supply is missing
analysis_df = (
    analysis_df
    # ~ inverts the logic operator
    .loc[~analysis_df[['flare_v1', 'day_supply_criteria']]
    .apply(lambda x: x['flare_v1'] == 0 and x['day_supply_criteria']=='no',
           axis=1)]
)
# count up rows post filter
obs_post_filter = analysis_df.shape[0]

print('Corticosteroid missing 7 day supply filter',
      '\nNumber of rows before filter:', obs_pre_filter,
      '\nNmber of rows after filter:', obs_post_filter,
      '\nPercent excluded:', 
      np.round(((obs_pre_filter-obs_post_filter)/obs_pre_filter), 3)*100.0,
      file=open(results_folder + "cortsteroid_7day_exlcude.txt", "w"))

"""
Calculation of proportion with event
"""
# count up number of flare events
events_count = (analysis_df[['id','flare_v1']]
               .groupby('flare_v1').agg(['count', 'nunique'])) 
# proportion of events
events_prop = (events_count/(analysis_df['id'].count(), 
                            analysis_df['id'].nunique())) 

# event summary
events_summary = pd.concat([events_count, events_prop],
                           axis=1).reset_index()
# rename columns
events_summary.columns = ['flare_v1', 'n_visits', 'n_unique_persons', 
                          'prop_visits', 'prop_unique_person']

print(events_summary)

# save events summar
events_summary.to_csv(results_folder + 'flare_events_summary.csv')

"""
IBD subtypes summary
"""

subtype_counts = (analysis_df[['id','flare_v1', 'disease_category']]
                  .groupby(['disease_category', 'flare_v1']).agg(['count', 'nunique'])) 

subtype_prop = (subtype_counts.groupby(level=[0])
                .apply(lambda g:  round(g/ g.sum(),3)))

# events summary 
subtype_summary = pd.concat([subtype_counts, subtype_prop], axis=1).reset_index()

# rename columns
subtype_summary.columns = ['disease_category', 'flare_v1', 'n_visits', 
                           'n_unique_persons', 'prop_visits', 'prop_unique_person']

print(subtype_summary)

# save events summar
subtype_summary.to_csv(results_folder + 'flare_events_ibd_subtype_summary.csv')

"""
Split and save permanent train test datasets
"""
# load yaml file that contains list of variables
# labs must meet measured on at least 70% of observations 
# requirement to be included
with open('analysis_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# set outcome column name
outcome = config['outcome']['flare_v1']

# set features names
cat_vars = config['features']['patient_indicator']['categorical']
num_vars = config['features']['patient_indicator']['numeric']
other_vars = config['features']['patient_indicator']['other']
# set base, mean, and max labs list
labs_base = config['features']['labs']['labs_base']
labs_mean = config['features']['labs']['labs_mean']
labs_max = config['features']['labs']['labs_max']

# combine all columns together
predictors = (cat_vars + num_vars + other_vars + 
              labs_base + labs_mean + labs_max)

print('Splitting training (70%) and testing set (30%)')
# split to train test split; including outcome with predictors
train, test = train_test_split(
    # features + outcome + disease category for subset analyses later on
    analysis_df.loc[:, [outcome] + predictors + ['disease_category']], 
    # random state for replicability
    random_state = 12, 
    # reserve 30% for testing
    test_size = 0.3)

print('Saving train and test data in datafolder for use with models')
# define data directory to save train and test
data_dir = root_dir + '/data/train_test/'
# save 70% train
train.to_csv(data_dir + 'train.csv')
# save 30% test
test.to_csv(data_dir + 'test.csv')

print('Finished writting train and test')