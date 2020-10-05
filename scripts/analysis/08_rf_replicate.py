"""
Title: Replication as close as possible to Waljee et al.
Author: Ryan Gan
Date Created: 2019-09-01

This model is as close to possible as the original processing and modeling
strategy as Waljee et al 2017.

Running model with longitudinal lab summaries and previous flare included. 

Major difference is the splits of train and test by patients visits.
- Training set are earliest 70% of virst per patient. 
- Testing set are remaining 30% of later visit per patient

Also using past median imputation and setting cutoff based on threshold 
identified using the ROC curve.

"""


"""
Modules
"""
print('Importing modules/packages')
# import pandas and numpy
import pandas as pd
import numpy as np

# import groupshufflesplit for splitting of testtrain by subject id
from sklearn.model_selection import GroupShuffleSplit
# import rf classifier
from sklearn.ensemble import RandomForestClassifier
# import preprocessing
from sklearn.preprocessing import OneHotEncoder, StandardScaler
# import custom past median imputer
from analysis_functions.transformers import PastMedianLabs
# simple imputer to fill in missing values
from sklearn.impute import SimpleImputer
# import pipeline and feature union
from sklearn.pipeline import FeatureUnion, Pipeline
# custom package that uses sklearn baseestimator and transformermixin
from analysis_functions.transformers import CategoricalTransformer
from analysis_functions.transformers import FeatureSelector
from analysis_functions.transformers import OtherTransformer
# timing processes
import time
# import yaml
import yaml
# import os
import os 

# putting test validation code in here as well as this is a sensitivity analysis
# sklearn validation modules
from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report
from sklearn.metrics import roc_curve, auc
from sklearn.metrics import brier_score_loss
# plot packages
import matplotlib.pyplot as plt
import seaborn as sns; sns.set_style('whitegrid')
# from joblib import load for model, and parallel for multi processing
from joblib import Parallel, delayed
# import custom metrics function
from analysis_functions.custom_metrics import dx_accuracy
from analysis_functions.custom_metrics import model_metrics_boot
from analysis_functions.custom_metrics import boot_95
# custom roc plot
from analysis_functions.custom_metrics import roc_plot


"""
Setup
"""
# define project root directory based on project structure; c
root_dir = os.path.dirname(os.path.dirname(os.getcwd()))
# load config yaml file
with open('analysis_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

   
"""
Import train data
"""
data_path = root_dir + '/data/raw/ibd_flare_analysis.csv'
# start time
start_time = time.time()
# read flare prediction csv using pandas; subset to crohns disease
data = pd.read_csv(data_path, dtype = {'birth_yr': str, 'date_of_death': str})

# create male_v_female binary variable; easier to interpret in this model than one hot
data['male_v_female'] = data['gender'].apply(lambda x: 1 if x=='Male' else 0)

# print run time
print("%s seconds" % (time.time()-start_time))


"""
RANDOM FOREST EXTRATREES SENSIVITIY PIPELINE SETUP AND FIT

Steps:
1. Load full dataset.
2. Load predictor and outcome variable lists from config file
3. Random sample of dataframe to speed up extra trees imputer
4. Split sample data 70% train 30% test

Preprocessing Steps:
1. Define numeric pipeline which imputes labs using past median values on a per
subject basis.

Note that I did not standardize it doesn't matter that much in tree models and
because I want to retain the actual lab value.

2. Other pipeline passes variables as is

Fit:
1. Fit features to outcome using random forest classifier
"""



"""
Find participants with at least 2 visits with labs.
"""

# patients with at least 1 visit
multi_vis = data.groupby(['id']).agg({'vis_date': 'count'}).reset_index()
multi_vis = multi_vis.loc[multi_vis['vis_date'] >= 2, :]

# subset sample for those with at least 2 visits

print("Sample size: ", multi_vis.shape[0])
sample = (data.loc[data['id'].isin(multi_vis['id']), :]
          .sort_values(['id', 'vis_date'])
          # reset index after ordering for splitting of test train below
          .reset_index())

# add visit number for my info to make sure it's sorting right
sample['visit'] = sample.groupby('id').cumcount().add(1)

# make sure unique patients line up with number of patients in multivisit
assert sample['id'].nunique() == multi_vis['id'].nunique(), 'Persons with 1 visit'

flare_prop = (data['flare_v1'].sum()/data['flare_v1'].count())
samp_flare_prop = (sample['flare_v1'].sum()/sample['flare_v1'].count())
print("Flare event proportion:\n Full data: {:.3f}\n 2 visit sample: {:.3f}"
      .format(flare_prop, samp_flare_prop)) 


"""
Split using Waljee et al strategy where 70% of earlier visits per patient
is trained on and 30% of later visits are reserved for testing validation
"""
print('Spitting test train by patient')
print("Taking 30% sample of original dataframe")

# Find last 30% of values to reserve for testing
# note this takes a long time for the dataset
test_index = (sample.groupby('id')
              .apply(lambda x: x.tail(int(np.floor(x['visit'].max()*0.3))))
              .index.values)

# flatten list of lists in to one list; sorry this is confusing....
# this just returns one long vector/array of index's that will serve as 
# testing validation.
test_index_locs = [i for (pid, i) in test_index]

# sample test and train datasets  by group indicators
train = sample.iloc[~sample.index.isin(test_index_locs)]
test = sample.iloc[sample.index.isin(test_index_locs)]

# check that train and test contain unique ids
assert any((test['id'].isin(train['id']))), 'Subjects in both test and train'


"""
Setup ML pipeline
"""


# define predictors
labs_base = config['features']['labs']['labs_base']
labs_mean = config['features']['labs']['labs_mean']
labs_max = config['features']['labs']['labs_max']
age = config['features']['patient_indicator']['numeric']

# combine all numeric values in a single list
num_cols = labs_base + labs_mean + labs_max + age

# set other columns i don't want to impute 
other_cols = ['immuno_med', 'male_v_female', 'prev_flare_v1_sum']
# set outcome; leaving as a string
outcome = config['outcome']['flare_v1'] 

# variables necessary for past median imputation also includes patient id
labs = labs_base + labs_mean + labs_max
predictors = num_cols + other_cols + ['id', 'vis_date']


# split features and outcomes
x_train, y_train = train.loc[:, predictors], train.loc[:, outcome]


""""
Defining various pipelines using the custom transformers in transformers.py
"""

print("Setting up sklearn pipelines")
# numeric transformation pipeline to standardize
num_pipe = Pipeline(
    [('num_selector', FeatureSelector(feature_names = num_cols)),
     # RF itterative imputation with extratrees
          ('median_impute', SimpleImputer(missing_values = np.NaN, 
                                     strategy = 'median'))
    ])

# pipe for values that I don't want to transform
other_pipe = Pipeline(
    [('other_selector', FeatureSelector(feature_names = other_cols)),
     ('other_transformer', OtherTransformer())
    ])

# define transformation pipe; doesn't include previous flares
transform_pipe = FeatureUnion(
    [('numeric_pipeline', num_pipe),
     # adding other pipeline in to keep previous flare
     ('other_pipeline', other_pipe)
    ])


# define RF model
rf = RandomForestClassifier(n_estimators = 500, n_jobs = 11)

# random forest pipe
model_pipe = Pipeline([
    ('past_median_labs', PastMedianLabs(lab_vars = labs, 
                                        variables = predictors)),
    ('transform_pipe', transform_pipe),
    #('random_undersample', rand_undersamp),
    ('rf', rf)
])

print("Fitting RF pipeline on x_train, y_train")
# fit y_train on x_train features on pipeline with rf cv pipe
model_pipe.fit(x_train, y_train)

"""
Evaluation of model on test set
"""

# split features and outcomes
x_test, y_test = test.loc[:, predictors], test.loc[:, outcome]

"""
RESULTS

1. Identify optimal threshold and create ROC
"""

print('Define path where results will be saved')
results_folder = "../../results/rf_replicate/"

print('Flare events in the first 70% of patient early visits training set' + 
      ' and flare events in 30% of later visits in test set')


train_flare_prop = (train['flare_v1'].sum()/train['flare_v1'].count())
test_flare_prop = (test['flare_v1'].sum()/test['flare_v1'].count())
print("Flare event proportion:\n Full data: {:.3f}\n 2 visit sample: {:.3f}"
      .format(train_flare_prop, test_flare_prop), 
      file = open(results_folder + "flare_prop_test_train.txt", "w")) 


"""
Predicted probability based on x test set
"""
# predicted probability of y
y_pred = model_pipe.predict_proba(x_test)

# roc for prediction of y=1 (2nd part of 2d array)
fpr, tpr, thresholds = roc_curve(y_test, y_pred[:,1])
# auc
roc_auc = auc(fpr, tpr)

print("Identifying threshold for probability cutoff")
optimal_idx = np.argmax(tpr - fpr)
optimal_threshold = thresholds[optimal_idx]

# save threshold
print('Threshold:', optimal_threshold, 
      file=open(results_folder + "rf_threshold.txt", "w"))

# create roc_df
roc_df = pd.DataFrame({'fpr': fpr, 'tpr': tpr, 'thresholds': thresholds})
# save roc_df
roc_df.to_csv(results_folder + "rf_roc.csv")
# save auc
print('ROC AUC:', roc_auc, 
      file=open(results_folder + "rf_roc_auc.txt", "w"))

# ROC plot
plt.figure(figsize=(10,10))
lw = 2
plt.plot(fpr, tpr, color='darkblue',
         lw=lw, label='RF Flare (area = %0.2f)' % roc_auc)
plt.plot([0, 1], [0, 1], color='grey', lw=lw, linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('1-Specificity')
plt.ylabel('Sensitivity')
plt.title('ROC')
plt.legend(loc="lower right")
# save roc plot; pass white facecolor to save
plt.savefig(results_folder + "rf_roc_plot.pdf", 
            facecolor = 'white')

print('Defining class using threshold of ', optimal_threshold)
# define y_pred_class based on threshold
y_pred_class = np.where(y_pred[:,1] > optimal_threshold, 1, 0)

# creating dataset to save for future use
preds_df = pd.DataFrame(
    np.stack((y_pred[:,1], y_pred_class, y_test), axis = 1),
    columns = ['flare_pred_prob', 'flare_predict', 'flare_true'])

# save dataframe for future results
preds_df.to_csv(results_folder + "rf_pred.csv")

"""
1. Classification report and summary statistics
"""
# creating classification report
class_report = classification_report(y_test, y_pred_class)
print(class_report)
# write classification report
print(class_report, 
      file=open(results_folder + "rf_classification_report.txt", "w"))

# define confusion matrix
cm = confusion_matrix(y_test, y_pred_class)

# run accuracy summary on confuxion matrix
dx_summary = dx_accuracy(cm)
print(dx_summary)
# save summary metrics
dx_summary.to_csv(results_folder + "rf_summary.csv")

"""
2. Brier score 
"""
brier_score = np.round(brier_score_loss(y_test, y_pred[:,1]),3)

print('RF Clinical + Past Median Imputed Labs',
      '\nBrier Score:', brier_score,
      file=open(results_folder + 'brier_score.txt', 'w'))


"""
3. Variable Importance Plots
"""

# define feature list
feature_list = num_cols + other_cols

# extract variable importance
vif = model_pipe.named_steps['rf'].feature_importances_

assert(len(feature_list) == len(vif))

vif_df = (
    pd.DataFrame({'Features': feature_list, 'VIF': vif})
    .sort_values('VIF', ascending=False)
    .reset_index()
)

# saving variable importance dataframe to make plots in csv
vif_df.to_csv(results_folder + 'rf_vif.csv')

""" 
4. VIF plot 
"""

plt.subplots(figsize=(15,15))
sns.set_color_codes('muted')
sns.barplot(x='VIF', y='Features', data = vif_df.iloc[:10, :], color='b')
plt.title('Random Forest Variable Importance to Predict Flare')
plt.xlabel('Variable Importance')
plt.ylabel('Top 10 Features')
plt.tight_layout(pad=2, w_pad=2, h_pad=2)
# save odds ratiosplot; pass white facecolor to save
plt.savefig(results_folder + "rf_vif_plot.pdf", 
            facecolor = 'white')

"""
5. Bootstrapped estimates of confidence intervals

Not running bootstrap for this.
"""
run_boot=False

if run_boot==True:
    print('Running bootstrap')
    # using 11 workers on AWS environment to calculate performance metrics
    # create lists of metrics
    boot_list = Parallel(n_jobs=11)(
        # use joblib delayed to register function
        delayed(model_metrics_boot)
        # function parameters
        (model=model_pipe, 
         x_test=x_test, 
         y_test=y_test,
         boot_iteration=i) for i in range(100)
    )

    # use boot_95 function to calculate percentile boot list
    dx_intervals = boot_95(boot_list)
    # save dx_intervals
    dx_intervals.to_csv(results_folder + "rf_dx_intervals.csv")
    print('Bootstrap finished')
else:
    print('Bootstap already run. If you want to run it again, set ' +
          'run_boot to True. Caution in that it takes awhile to run for ' +
          'certain models.')

print('Script done running')
