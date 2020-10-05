"""
Title: SHAP Values for Random Forest Model to Predict Flare 
Author: Ryan Gan
Date Created: 2020-01-14


Purpose: TreeSHAP based on model trained in 05_rf.py script.

Notes:

I need the test data to calculate shap values for. In future projects
it wouldn't hurt to modularize the test/train split and save those data
sets to use across items in the project (like in this case). However,
since I used a seed, I'll do that here to get the same withheld validation 
set.
"""


"""
Modules
"""
# import pandas and numpy
import pandas as pd
import numpy as np
# timing processes
import time
import os
import yaml
# plots
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap # for custom color maps
import seaborn as sns; sns.set_style('whitegrid')
# joblib for saving models
from joblib import dump, load
# import joblib for parallel processing
from joblib import Parallel, delayed
# SHAP python module
import shap
# initialize javascript output
shap.initjs()
# load function to make variables easier to read
from analysis_functions.custom_metrics import readable_variables

"""
Setup
"""
# define project root directory based on project structure; c
root_dir = os.path.dirname(os.path.dirname(os.getcwd()))
# load config yaml file
with open('analysis_config.yaml', 'r') as f:
    config = yaml.safe_load(f)
    
# set results folder to save results to
results_folder = root_dir + '/results/rf_shap/'

"""
Import test data; shape doesn't really need outcome values but i'll import
"""
# path to test dataset
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

# create features list
# define feature list; this is the same order fed in to the model
feature_list = num_cols + other_cols

# make readable list of variable names
readable_names = readable_variables(feature_list)

# split features and outcomes
x_test, y_test = test.loc[:, num_cols + other_cols], test.loc[:, outcome]


"""
Load saved random forest model
"""
rf_pipe = load(root_dir + '/models/rf.joblib') 

# extract rf model from pipeline
rf = rf_pipe.named_steps['rf']

# extract transformation pipe to handle variables
transform = rf_pipe.named_steps['transform_pipe']

# transfrom x_test; cast as array from sklearn array
x_validation = transform.transform(x_test)


"""
SHAP Tree Expaliner
"""
# initialze shap tree explainer
rf_explainer = shap.TreeExplainer(rf_pipe.named_steps['rf'])

"""
Calculate SHAP values based on TreeExplainer using the saved
path of trees in the rf model

Note for a binary classifier from a tree, it is my understanding that the
SHAP value represents the log odds. 

Using default tree-dependent calculation of conditional shap values
as i do not supply it data. Other option is intervential which uses
do-calculus, but takes a whole lot longer
"""
shap_vals = rf_explainer.shap_values(
    # use x_validation array
    x_validation,
    # using approximate=True to speed up computation time
    approximate=True)

"""
Overall Summary of top 10 SHAP Values

Plot for paper with custom color scheme
"""

# custom gradient from etro blue to etro purple based on hex key
N = 256
vals = np.ones((N, 4))
vals[:, 0] = np.linspace(0/256, 172/256, N)
vals[:, 1] = np.linspace(152/256, 67/256, N)
vals[:, 2] = np.linspace(205/256, 153/256, N)
newcmp = ListedColormap(vals)

# summary plot eps format
plt.figure()
fig = shap.summary_plot(
    shap_values=shap_vals[1], 
    features=x_validation, 
    feature_names=readable_names,
    max_display = 10,
    plot_size = (8,4),
    show=False, 
    plot_type='dot'
)

# Change the colormap of the artists
for fc in plt.gcf().get_children():
    for fcc in fc.get_children():
        if hasattr(fcc, "set_cmap"):
            fcc.set_cmap(newcmp)     

# change x axis
plt.xlabel('log(Odds of flare in 6 months)')
# save figure
plt.tight_layout()
plt.savefig(results_folder + "fig3_shap_summary.pdf", dpi=300) # pdf version
plt.savefig(results_folder + "fig3_shap_summary.png", dpi=300) # png version
# saving version in manuscript results folder
plt.savefig(root_dir + "/results/manuscript/fig3_shap_summary.png", dpi=300) # png version



"""
Plot of top 4 features
"""

# set up subplots
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(
    nrows=2, ncols=2, figsize=(8,6), facecolor='w', edgecolor='k'
)


# previous flare
shap.dependence_plot(
    ind=33,
    shap_values=shap_vals[1], 
    features=x_validation, 
    feature_names=readable_names,
    # no interaction
    interaction_index=None,
    show=False,
    ax=ax1
    )
# remove y label
ax1.set(ylabel='')
ax1.set_title('A', loc='left', size=14)
# age
shap.dependence_plot(
    ind=30,
    shap_values=shap_vals[1], 
    features=x_validation, 
    feature_names=readable_names,
    # no interaction
    interaction_index=None,
    show=False,
    ax=ax2
    )
# remove y label
ax2.set(ylabel='')
ax2.set_title('B', loc='left', size=14)

# potassium
shap.dependence_plot(
    ind=17,
    shap_values=shap_vals[1], 
    features=x_validation, 
    feature_names=readable_names,
    # no interaction
    interaction_index=None,
    show=False,
    ax=ax3
    )
ax3.set(ylabel='', xlabel='Potassium mmol/L Mean')
ax3.set_title('C', loc='left', size=14)

# wbc
shap.dependence_plot(
    ind=19,
    shap_values=shap_vals[1], 
    features=x_validation, 
    feature_names=readable_names,
    # no interaction
    interaction_index=None,
    show=False,
    ax=ax4
    )
ax4.set(ylabel='', xlabel='White Blood Cell Count $x 10^3$/ul Mean')
ax4.set_title('D', loc='left', size=14)

# add some padding
fig.tight_layout(pad=1)

fig.text(
    0, 0.5, 
    "log(Odds for flare in 6 months)", \
    ha="center", va="center", rotation=90, size = 12
)
# save plot
plt.savefig(results_folder + "fig4_dependence_plot.pdf", bbox_inches='tight', dpi=300) # pdf version
plt.savefig(results_folder + "fig4_dependence_plot.png", bbox_inches='tight', dpi=300) # png version
# saving version in manuscript results folder
plt.savefig(root_dir + "/results/manuscript/fig4_dependence_plot.png", bbox_inches='tight', dpi=300) 



"""
End plots for paper
"""

shap.dependence_plot(
    ind=30,
    shap_values=shap_vals[1], 
    features=x_validation, 
    feature_names=readable_names,
    # no interaction
    interaction_index=None,
    show=False
    )
plt.ylabel('Test')

"""
Dependency plots
"""
for i,s in enumerate(readable_names):
    print(s)

    shap.dependence_plot(
        ind=s,
        shap_values=shap_vals[1], 
        features=x_validation, 
        feature_names=readable_names,
        # no interaction
        interaction_index=None,
        show=False
        )
    # save plot
    plt.savefig(results_folder + '/dependency_plots/' + str(s) + '.png')
    
# saving previous flare and eps and pdf for publication; last element 33
shap.dependence_plot(
    ind=33,
    shap_values=shap_vals[1], 
    features=x_validation, 
    feature_names=readable_names,
    # no interaction
    interaction_index=None,
    show=False
    )
# save plot
plt.savefig(results_folder + 'Previous_Flare_Sum.eps')

# pdf version
shap.dependence_plot(
    ind=33,
    shap_values=shap_vals[1], 
    features=x_validation, 
    feature_names=readable_names,
    # no interaction
    interaction_index=None,
    show=False
    )
# save plot
plt.savefig(results_folder + 'Previous_Flare_Sum.pdf')


"""
Example Force Plots for flare events and non-flare events
"""

# set random seed; this one sort of gives a representative sensitivity
# with 20 random examples
np.random.seed(99)
flare_subset = np.random.choice(
    np.where(y_test == 1)[0], 
    size=20, 
    replace=False)


for idx in flare_subset:
    print('Observed Outcome:', np.where(y_test.iloc[idx]==1, 'Flare', 'No Flare'))
    # find 5 biggest shap values
    shap_idx = np.argpartition(abs(shap_vals[1][idx,:]), -5)[-5:]

    # individual level prediciton for first subject in testing set with a flare
    fig = shap.force_plot(base_value=rf_explainer.expected_value[0], 
                          # shap value
                          shap_values=shap_vals[1][idx,shap_idx], 
                          # need to use the transformer pipe to one hot code
                          features=np.round(
                              transform.transform(
                                  x_test.iloc[[idx]])[0][shap_idx],
                              1),
                          # output names
                          out_names=[''],
                          # feature names
                          feature_names=[readable_names[i] for i in shap_idx],
                          #link='logit',
                          matplotlib=True,
                          show=False,
                          figsize=(14,7),
                          # rotate text 
                          text_rotation=15)
    # save plot
    plt.tight_layout()
    plt.savefig(results_folder + '/example_force_plot/' + 
                'flare_example_'+ str(idx) + 'sn.png')

         


# set random seed; this one sort of gives a representative sensitivity
# with 20 random examples
np.random.seed(999)
no_flare_subset = np.random.choice(
    np.where(y_test == 0)[0], 
    size=20, 
    replace=False)


for idx in no_flare_subset:
    print('Observed Outcome:', np.where(y_test.iloc[idx]==1, 'Flare', 'No Flare'))
    # find 5 biggest shap values
    shap_idx = np.argpartition(abs(shap_vals[1][idx,:]), -5)[-5:]

    # individual level prediciton for first subject in testing set with a flare
    fig = shap.force_plot(base_value=rf_explainer.expected_value[0], 
                          # shap value
                          shap_values=shap_vals[1][idx,shap_idx], 
                          # need to use the transformer pipe
                          features=np.round(
                              transform.transform(
                                  x_test.iloc[[idx]])[0][shap_idx],
                              1),
                          # output names
                          out_names=[''],
                          # feature names
                          feature_names=[readable_names[i] for i in shap_idx],
                          #link='logit',
                          matplotlib=True,
                          show=False,
                          figsize=(14,7),
                          # rotate text 
                          text_rotation=15)
    # save plot
    plt.tight_layout()
    plt.savefig(results_folder + '/example_force_plot/' + 
                'noflare_example_'+ str(idx) + 'sn.png')
        