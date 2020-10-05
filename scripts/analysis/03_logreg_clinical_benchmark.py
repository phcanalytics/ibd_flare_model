"""
Title: Logistic Regression Model (no l1/l2 penalty) Clinical Benchmark
    Training Script
Author: Ryan Gan
Date Created: 2019-09-16

This is a bench mark model that includes only clinical characteristics.
This script contains only code related to training.
"""

print('Importing modules/packages')
# import pandas and numpy
import pandas as pd
import numpy as np

# timing processes
import time
# import yaml
import yaml
# import os
import os 
# joblib for saving models and parallel for multi processing (bootstraps)
from joblib import dump, Parallel, delayed
# plot packages
import matplotlib.pyplot as plt
import seaborn as sns; sns.set_style('whitegrid')

# sklearn packages
# import logistic regression
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder, StandardScaler
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
# sklearn validation modules
from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report
from sklearn.metrics import roc_curve, auc
from sklearn.metrics import brier_score_loss


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
TRAINING

Import train data
"""

print('Fitting model on training data')

train_data_path = root_dir + '/data/train_test/train.csv'
# start time
start_time = time.time()
# read flare prediction csv using pandas
train = pd.read_csv(train_data_path, 
                    dtype = {'birth_yr': str, 'date_of_death': str})

# create male_v_female binary variable; easier to interpret in this model
train['male_v_female'] = train['gender'].apply(lambda x: 1 if x=='Male' else 0)

# print run time
print("%s seconds" % (time.time()-start_time))

"""
LOGISTIC REGRESSION CLINICAL CHARACTERISTICS

Steps:
1. Load train data.
2. Load predictor and outcome variable lists from config file

Preprocessing Steps:
1. Define numeric pipeline which standardizes age so that it can
be compared to other features on similar scale
2. Other pipeline passes variables as is
3. Run random undersampler to balance events vs non-events

Fit:
1. Fit features to outcome using logistic regresion (no regularization added)
"""

# define predictors
num_cols = config['features']['patient_indicator']['numeric']
# set other columns
other_cols = ['immuno_med', 'male_v_female', 'prev_flare_v1_sum']
# set outcome; leaving as a string
outcome = config['outcome']['flare_v1'] 


# split features and outcomes
x_train, y_train = train.loc[:, num_cols + other_cols], train.loc[:, outcome]

print("Setting up sklearn pipelines")
# numeric transformation pipeline to standardize
num_pipe = Pipeline(
    [('num_selector', FeatureSelector(feature_names = num_cols)),
     ('std_scaler', StandardScaler())
    ])

# pipe for values that I don't want to transform
other_pipe = Pipeline(
    [('other_selector', FeatureSelector(feature_names = other_cols)),
     ('other_transformer', OtherTransformer())
    ])

# define transformation pipe which is a feature union for numeric and other pipe
transform_pipe = FeatureUnion(
    [('numeric_pipeline', num_pipe),
     ('other_pipeline', other_pipe)
    ])

# using random undersampler for ml model
rand_undersamp = RandomUnderSampler(random_state=0)

# logistic regression; note I decided to use an explicit undersampler
# rather than class weights but they should do the same thing
logreg = LogisticRegression(solver='lbfgs', penalty='none',
                            max_iter=100, 
                            fit_intercept=False, 
                            verbose = 2)

# add upsample pipeleine
model_pipe = Pipeline([
    ('transform_pipe', transform_pipe),
    ('random_undersample', rand_undersamp),
    ('logistic_model', logreg)
])

"""
Fitting x_train and y_train through transformation pipeline
This model includes age, sex, immuno escalation medication use 
and previous flare.
"""

# fit y_train on x_train features
model_pipe.fit(x_train, y_train)

"""
Saving trained model
"""

model_filename = root_dir + '/models/logreg_clinical_benchmark.joblib'
dump(model_pipe, model_filename)
print('Saving final model here:', model_filename)


"""
TESTING/VALIDATION

Import test data
"""
    
data_path = root_dir + '/data/train_test/test.csv'
# start time
start_time = time.time()
# read flare prediction csv using pandas
test = pd.read_csv(data_path, dtype = {'birth_yr': str, 'date_of_death': str})

# create male_v_female binary variable; easier to interpret in this model
test['male_v_female'] = test['gender'].apply(lambda x: 1 if x=='Male' else 0)

# print run time
print("%s seconds" % (time.time()-start_time))


"""
Subset x_features data and y_outcomes data
"""
# define predictors
num_cols = config['features']['patient_indicator']['numeric']
# set other columns
other_cols = ['immuno_med', 'male_v_female', 'prev_flare_v1_sum']
# set outcome; leaving as a string
outcome = config['outcome']['flare_v1'] 

# split features and outcomes
x_test, y_test = test.loc[:, num_cols + other_cols], test.loc[:, outcome]

"""
Predict on test data
"""

# predicted probability of y
y_pred = model_pipe.predict_proba(x_test)
y_pred_class = np.where(y_pred[:, 1] > 0.5, 1, 0)

"""
Results for clinical benchmark model with undersampling
This section contains:
1. classificaiton report and analagous diagnositic statistics
2. Brier score
3. ROC curve for baseline model and summary stats
4. Logistic regression coeff
Results will be saved in rwds_1567/results/base_logistic/ folder.
"""
# define results folder
results_folder = root_dir + '/results/logreg_clinical_benchmark/'

# creating dataset to save for future use
preds_df = pd.DataFrame(
    np.stack((y_pred[:,1], y_pred_class, y_test), axis = 1),
    columns = ['flare_pred_prob', 'flare_predict', 'flare_true'])

# save dataframe for future results
preds_df.to_csv(results_folder + "logreg_pred.csv")

"""
1. Classification report and summary statistics
"""
# creating classification report
class_report = classification_report(y_test, y_pred_class)
print(class_report)
# write classification report
print(class_report, 
      file=open(results_folder + "logreg_classification_report.txt", "w"))

# define confusion matrix
cm = confusion_matrix(y_test, y_pred_class)

# run accuracy summary on confuxion matrix
dx_summary = dx_accuracy(cm)
print(dx_summary)
# save summary metrics
dx_summary.to_csv(results_folder + "logreg_dx_summary.csv")

"""
2. Brier score 
"""
brier_score = np.round(brier_score_loss(y_test, y_pred[:,1]),3)

print('Logsitic Regression Clinical Features Benchmark',
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
roc_df.to_csv(results_folder + "logreg_roc.csv")
# save auc
print(roc_auc, 
      file=open(results_folder + "roc_auc.txt", "w"))

# roc plot
roc_plot(fpr,tpr,roc_auc, model_name='Logistic Clinical Benchmark')
# save roc plot; pass white facecolor to save
plt.savefig(results_folder + "logreg_roc.pdf", facecolor = 'white')

"""
4. Odds ratios; note I did not use regularization, but this is for 
colleagues' intepretation.
"""
# define feature list
feature_list = num_cols + other_cols

coef = model_pipe.named_steps['logistic_model'].coef_[0]

# logistic model odds ratios
odds_ratios = (
    pd.DataFrame({'Features': feature_list, 
                  'Odds_Ratios': list(np.exp(coef))}) 
    .sort_values('Odds_Ratios', ascending=False)
)
             
# save odds ratios table
odds_ratios.to_csv(results_folder + "logreg_oddratio.csv")

# plot odds ratios
odds_ratio_plot(or_data=odds_ratios)
# save odds ratiosplot; pass white facecolor to save
plt.savefig(results_folder + "logreg_oddsratio.pdf", facecolor = 'white')


"""
Bootstrapped estimates of confidence intervals
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
    dx_intervals.to_csv(results_folder + "dx_intervals.csv")
    print('Bootstrap finished')
else:
    print('Bootstap already run. If you want to run it again, set ' +
          'run_boot to True. Caution in that it takes awhile to run for ' +
          'certain models.')
