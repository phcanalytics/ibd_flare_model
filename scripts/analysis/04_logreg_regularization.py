"""
Title: Logistic Regression with L1 Regularization to 
    Predict Flare with Clinical and Labs Training Script
    
Author: Ryan Gan
Date Created: 2019-09-16

This model fits the logistic regression with L1 regularization.

This model includes both clinical features and lab features of baseline,
mean, max that are measured across at least 70% of visits.
So the most commonly tested labs as a simple feature selection strategy.

I run simple imputation using the population (all observation) median.
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
train_data_path = root_dir + '/data/train_test/train.csv'
# start time
start_time = time.time()
# read flare prediction csv using pandas
train = pd.read_csv(train_data_path, dtype = {'birth_yr': str, 'date_of_death': str})

# create male_v_female binary variable; easier to interpret in this model
train['male_v_female'] = train['gender'].apply(lambda x: 1 if x=='Male' else 0)

# print run time
print("%s seconds" % (time.time()-start_time))

"""
LOGISTIC REGRESSION CLINICAL + LABS L1 REGULARIZATION 

Steps:
1. Load train data.
2. Load predictor and outcome variable lists from config file

Preprocessing Steps:
1. Define numeric pipeline which standardizes age and labs so that it can
be compared to other features on similar scale
2. Other pipeline passes variables as is (includes binary categorical vars)
3. Run random undersampler to balance events vs non-events

Fit:
1. Fit features to outcome using logistic regresion (L1 regularization added)
"""
# define predictors
labs_base = config['features']['labs']['labs_base']
labs_mean = config['features']['labs']['labs_mean']
labs_max = config['features']['labs']['labs_max']
age = config['features']['patient_indicator']['numeric']

# combine all numeric values in a single list
num_cols = labs_base + labs_mean + labs_max + age

# set other columns
other_cols = ['immuno_med', 'male_v_female', 'prev_flare_v1_sum']
# set outcome; leaving as a string
outcome = config['outcome']['flare_v1'] 

# split features and outcomes
x_train, y_train = train.loc[:, num_cols + other_cols], train.loc[:, outcome]

"""
Defining various pipelines using the custom transformers in transformers.py
"""

print("Setting up sklearn pipelines")
# numeric transformation pipeline to impute standardize
num_pipe = Pipeline(
    [('num_selector', FeatureSelector(feature_names = num_cols)),
     ('median_impute', SimpleImputer(missing_values = np.NaN, 
                                     strategy = 'median')),
     ('std_scaler', StandardScaler())
    ])

# pipe for values that I don't want to transform
other_pipe = Pipeline(
    [('other_selector', FeatureSelector(feature_names = other_cols))
    ])

# define transformation pipe
transform_pipe = FeatureUnion(
    [('numeric_pipeline', num_pipe),
     ('other_pipeline', other_pipe)
    ])

# using random undersampler for ml model
rand_undersamp = RandomUnderSampler(random_state=0)

# logistic regression; note I decided to use an undersampler
# rather than class weights but they should do the same thing
# also i took the crossvalidation out of this step because C 
# results in minimal accuracy gains and it's not worth the time
logreg = LogisticRegression(random_state=0, solver = 'saga',
                            penalty='l1', 
                            max_iter=1000, fit_intercept=False)

# add upsample pipeleine and cross validated cv
model_pipe = Pipeline([
    ('transform_pipe', transform_pipe),
    ('random_undersample', rand_undersamp),
    ('logreg', logreg)
])

# fit y_train on x_train features
model_pipe.fit(x_train, y_train)

"""
Saving final model
"""

model_filename = root_dir + '/models/logreg_regularization.joblib'
dump(model_pipe, model_filename)
print('Saving final model here:', model_filename)


"""
TESTING/VALIDATION

Import test data
"""
test_data_path = root_dir + '/data/train_test/test.csv'
# start time
start_time = time.time()
# read flare prediction csv using pandas
test = pd.read_csv(test_data_path, dtype = {'birth_yr': str, 'date_of_death': str})

# create male_v_female binary variable; easier to interpret in this model
test['male_v_female'] = test['gender'].apply(lambda x: 1 if x=='Male' else 0)

# print run time
print("%s seconds" % (time.time()-start_time))

"""
Subset x_features data and y_outcomes data
"""
# define predictors
labs_base = config['features']['labs']['labs_base']
labs_mean = config['features']['labs']['labs_mean']
labs_max = config['features']['labs']['labs_max']
age = config['features']['patient_indicator']['numeric']
# combine all numeric values in a single list
num_cols = labs_base + labs_mean + labs_max + age
# set other columns
other_cols = ['immuno_med', 'male_v_female', 'prev_flare_v1_sum']
# set outcome; leaving as a string
outcome = config['outcome']['flare_v1'] 

# split features and outcomes
x_test, y_test = test.loc[:, num_cols + other_cols], test.loc[:, outcome]

"""
Predict based on test data
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
results_folder = root_dir + '/results/logreg_regularization/'

# creating dataset to save for future use
preds_df = pd.DataFrame(
    np.stack((y_pred[:,1], y_pred_class, bayes_prob, y_test), axis = 1),
    columns = ['flare_pred_prob', 'flare_predict', 'bayes_prob', 'flare_true'])

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

print('Logsitic Regression L1 Clinical + Labs Features Benchmark',
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
roc_plot(fpr,
         tpr,
         roc_auc, 
         model_name='Logistic with L1 Regularization Clinical & Labs')
# save roc plot; pass white facecolor to save
plt.savefig(results_folder + "logreg_roc.pdf", facecolor = 'white')

"""
4. Odds ratios regularized, for colleagues' intepretation.
"""
# define feature list
feature_list = num_cols + other_cols

# extract coef from pipeline
coef = model_pipe.named_steps['logreg'].coef_[0]
# assert that feature list is the same length as the coef
assert(len(feature_list)==len(coef))

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
    dx_intervals.to_csv(results_folder + "dx_intervals.csv")
    print('Bootstrap finished')
else:
    print('Bootstap already run. If you want to run it again, set ' +
          'run_boot to True. Caution in that it takes awhile to run for ' +
          'certain models.')

print('Script done running')
