"""
Title: Sensitivity Predictive Flare Random Forest Model
       on Ulcerative Colitis Patients
Author: Ryan Gan
Date Created: 2019-09-24

Sensitivity analysis of random forest predictive flare model
only in ulcerative colitis patients
"""


"""
Modules
"""
print('Importing modules/packages')
# import pandas and numpy
import pandas as pd
import numpy as np
# import rf classifier
from sklearn.ensemble import RandomForestClassifier
# import preprocessing
from sklearn.preprocessing import OneHotEncoder, StandardScaler
# simple imputer to fill in missing values
from sklearn.impute import SimpleImputer
# import pipeline and feature union
from sklearn.pipeline import FeatureUnion, Pipeline
# using random over sampling
from imblearn.under_sampling import RandomUnderSampler
# add model pipe for imblearn
from imblearn.pipeline import make_pipeline, Pipeline
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
from analysis_functions.custom_metrics import odds_ratio_plot

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
data_path = root_dir + '/data/train_test/train.csv'
# start time
start_time = time.time()
# read flare prediction csv using pandas; subset to ulcerative colitis
train = (pd.read_csv(data_path, 
                     dtype = {'birth_yr': str, 'date_of_death': str})
         # subset to ulcerative colitis using pandas query function
         .query('disease_category == "ulcerative colitis"'))

# assert that only ulcerative colitis subjects are in dataframe
assert(train['disease_category'].unique()[0] == "ulcerative colitis")

# create male_v_female binary variable; easier to interpret in this model
train['male_v_female'] = train['gender'].apply(lambda x: 1 if x=='Male' else 0)


# print run time
print("%s seconds" % (time.time()-start_time))


"""
RANDOM FOREST PIPELINE SETUP AND FIT

Steps:
1. Load train data.
2. Load predictor and outcome variable lists from config file

Preprocessing Steps:
1. Define numeric pipeline which imputes missing labs with median population value
Note that I did not standardize it doesn't matter that much in tree models and
because I want to retain the actual lab value.
2. Other pipeline passes variables as is
3. Run random undersampler to balance events vs non-events

Fit:
1. Fit features to outcome using random forest classifier
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

# split features and outcomes
x_train, y_train = train.loc[:, num_cols + other_cols], train.loc[:, outcome]

"""
Defining various pipelines using the custom transformers in transformers.py
"""

print("Setting up sklearn pipelines")
# numeric transformation pipeline to standardize
num_pipe = Pipeline(
    [('num_selector', FeatureSelector(feature_names = num_cols)),
     ('median_impute', SimpleImputer(missing_values = np.NaN, 
                                     strategy = 'median'))
    ])


# pipe for values that I don't want to transform
other_pipe = Pipeline(
    [('other_selector', FeatureSelector(feature_names = other_cols)),
     ('other_transformer', OtherTransformer())
    ])

# define transformation pipe
transform_pipe = FeatureUnion(
    [('numeric_pipeline', num_pipe),
     ('other_pipeline', other_pipe)
    ])

# using random undersampler for ml model; default option for replacement is false
rand_undersamp = RandomUnderSampler(random_state=0,
                                    sampling_strategy='auto')

# define RF model
rf = RandomForestClassifier(n_estimators = 500, n_jobs = 11)

# random forest pipe
model_pipe = Pipeline([
    ('transform_pipe', transform_pipe),
    ('random_undersample', rand_undersamp),
    ('rf', rf)
])

print("Fitting RF pipeline on x_train, y_train")
# fit y_train on x_train features on pipeline with rf cv pipe
model_pipe.fit(x_train, y_train)

"""
Import test data; putting this in the same script for sensitivity analysis
"""
data_path = root_dir + '/data/train_test/test.csv'
# start time
start_time = time.time()
# read flare prediction csv using pandas; subset to ulcerative colitis
test = (pd.read_csv(data_path, 
                     dtype = {'birth_yr': str, 'date_of_death': str})
         # subset to ulcerative colitis using pandas query function
         .query('disease_category == "ulcerative colitis"'))

# assert that only ulcerative colitis subjects are in dataframe
assert(test['disease_category'].unique()[0] == "ulcerative colitis")

# create male_v_female binary variable; easier to interpret in this model
test['male_v_female'] = test['gender'].apply(lambda x: 1 if x=='Male' else 0)

# print run time
print("%s seconds" % (time.time()-start_time))

# split features and outcomes
x_test, y_test = test.loc[:, num_cols + other_cols], test.loc[:, outcome]

"""
Predicted probability and class based on 0.5 threshold
"""
# predicted probability of y
y_pred = model_pipe.predict_proba(x_test)
y_pred_class = np.where(y_pred[:, 1] > 0.5, 1, 0)

# corrected probability based on risk proportion for flare in 
# next 6 months using bayes theorem
def bayes(obs_pred, pop_prop):
    bayes_pred = ((obs_pred * pop_prop)/
                  ((obs_pred * pop_prop) + 
                   (1-obs_pred)*(1-pop_prop)))
    return(bayes_pred)

# calculate pop_prop for flare
pop_prop_flare = y_test.sum()/y_test.count()

bayes_prob = [bayes(obs_pred=x, pop_prop=pop_prop_flare) for x in y_pred[:,1]]


print(
"""
Results of longitudinal logistic model with down sampling and L1 regularization
This section contains:
1. Classificaiton report and analagous diagnositic statistics
2. ROC curve for baseline model and summary stats
3. Logistic regression coeff

"""
)

# define results folder
results_folder = root_dir + '/results/rf_uc/'

# creating dataset to save for future use
preds_df = pd.DataFrame(
    np.stack((y_pred[:,1], y_pred_class, bayes_prob, y_test), axis = 1),
    columns = ['flare_pred_prob', 'flare_predict', 'bayes_prob', 'flare_true'])

# save dataframe for future results
preds_df.to_csv(results_folder + "rf_uc_pred.csv")

"""
1. Classification report and summary statistics
"""
# creating classification report
class_report = classification_report(y_test, y_pred_class)
print(class_report)
# write classification report
print(class_report, 
      file=open(results_folder + "rf_uc_classification_report.txt", "w"))

# define confusion matrix
cm = confusion_matrix(y_test, y_pred_class)

# run accuracy summary on confuxion matrix
dx_summary = dx_accuracy(cm)
print(dx_summary)
# save summary metrics
dx_summary.to_csv(results_folder + "rf_uc_dx_summary.csv")

"""
2. Brier score 
"""
brier_score = np.round(brier_score_loss(y_test, y_pred[:,1]),3)

print('Ulcerative Colitis RF Clinical + Labs Features Benchmark',
      '\nBrier Score:', brier_score,
      file=open(results_folder + 'brier_score.txt', 'w'))

"""
3. ROC
"""
# roc for prediction of y=1 (2nd part of 2d array)
fpr, tpr, thresholds = roc_curve(y_test, y_pred[:,1])
# auc
roc_auc = auc(fpr, tpr)

# create roc_df
roc_df = pd.DataFrame({'fpr': fpr, 'tpr': tpr, 'thresholds': thresholds})
# save roc_df
roc_df.to_csv(results_folder + "rf_uc_roc.csv")
# save auc
print(roc_auc, 
      file=open(results_folder + "roc_auc.txt", "w"))

# roc plot
roc_plot(fpr,
         tpr,
         roc_auc, 
         model_name='Random Forest: Clinical & Labs')
# save roc plot; pass white facecolor to save
plt.savefig(results_folder + "rf_uc_roc.pdf", facecolor = 'white')

"""
4. Variable Importance Plots
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
vif_df.to_csv(results_folder + 'rf_uc_vif.csv')

""" 
VIF plot 
"""

plt.subplots(figsize=(15,15))
sns.set_color_codes('muted')
sns.barplot(x='VIF', y='Features', data = vif_df.iloc[:10, :], color='b')
plt.title('Random Forest Variable Importance to Predict Flare')
plt.xlabel('Variable Importance')
plt.ylabel('Top 10 Features')
plt.tight_layout(pad=2, w_pad=2, h_pad=2)
# save odds ratiosplot; pass white facecolor to save
plt.savefig(results_folder + "rf_uc_vif_plot.pdf", 
            facecolor = 'white')


"""
1. RF Classification report and summary statistics
"""
# creating classification report
class_report = classification_report(y_test, y_pred_class)
print(class_report)
# write classification report
print(class_report,
    file=open(results_folder + 
              "rf_uc_classification_report.txt",
              "w"))

# define confusion matrix
cm = confusion_matrix(y_test, y_pred_class)

# run accuracy summary on confuxion matrix
rf_uc_dx_summary = dx_accuracy(cm)

print(rf_uc_dx_summary)
# save summary metrics
rf_uc_dx_summary.to_csv(results_folder + "rf_uc_dx_summary.csv")

"""
2. ROC RF 
"""

# roc for prediction of y=1 (2nd part of 2d array)
fpr, tpr, thresholds = roc_curve(y_test, y_pred[:,1])
# auc
roc_auc = auc(fpr, tpr)

# create roc_df
roc_df = pd.DataFrame({'fpr': fpr, 'tpr': tpr, 'thresholds': thresholds})
# save roc_df
roc_df.to_csv(results_folder + "rf_uc_roc.csv")
# save auc
print(roc_auc, 
      file=open(results_folder + "rf_uc_roc_auc.txt", "w"))

# ROC plot
plt.figure(figsize=(10,10))
lw = 2
plt.plot(fpr, tpr, color='darkblue',
         lw=lw, label='RF (area = %0.2f)' % roc_auc)
plt.plot([0, 1], [0, 1], color='grey', lw=lw, linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('1-Specificity')
plt.ylabel('Sensitivity')
plt.title('ROC')
plt.legend(loc="lower right")
# save roc plot; pass white facecolor to save
plt.savefig(results_folder + "rf_uc_roc_plot.pdf", 
            facecolor = 'white')


"""
5. Bootstrapped estimates of confidence intervals
"""
run_boot=True

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
    dx_intervals.to_csv(results_folder + "rf_uc_dx_intervals.csv")
    print('Bootstrap finished')
else:
    print('Bootstap already run. If you want to run it again, set ' +
          'run_boot to True. Caution in that it takes awhile to run for ' +
          'certain models.')

print('Script done running')