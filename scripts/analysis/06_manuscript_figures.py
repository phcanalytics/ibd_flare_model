"""
Title: IBD Manuscript Figures
Author: Ryan Gan
Date Created: 2020-01-29

This script consolidates results found in the results folders for the
03 logistic benchmark model, 04 logistic model, and 05 random forest model

"""

"""
Modules
"""
# %%
import pandas as pd
import numpy as np
# plots
import matplotlib.pyplot as plt
from matplotlib import gridspec
import seaborn as sns; sns.set_style('whitegrid')
# import custom function to make names easier to read
from analysis_functions.custom_metrics import readable_variables
from analysis_functions.custom_metrics import dca
# os and yaml
import os
import yaml
# %%
"""
Setup
"""
# define project root directory based on project structure; c
root_dir = os.path.dirname(os.path.dirname(os.getcwd()))
# load config yaml file
with open('analysis_config.yaml', 'r') as f:
    config = yaml.safe_load(f)
    
# set results folder to save results to
results_folder = root_dir + '/results/manuscript/'

"""
FIGURE 2:

Combined ROC curve for RF model and Logistic with L1 penalization (lasso) model.
Note as of 2021-05-10 added DCA plot as well.

This figure uses the sensivity (tpr), 1-specificity (fpr) dataframes generated
in model scripts for rf_longituindal_flarev1_prev_flare and 
logreg_regularization
"""
### Load ROC results ###
# %%
# benchmark clinical features logistic regression
benchmark_path = (root_dir + "/results/logreg_clinical_benchmark/" + 
                  "logreg_roc.csv")
# read benchmark model roc data
benchmark_roc_df = pd.read_csv(benchmark_path)

# read in 95% CI for AUC
benchmark_intervals = (root_dir + "/results/logreg_clinical_benchmark/" + 
                      "dx_intervals.csv")

benchmark_auc_intervals = pd.read_csv(benchmark_intervals).loc[5]

# prepare string
benchmark_auc = ('Benchmark Logistic: Demographic (AUC={0}, 95%CI: {1}-{2})'
                 .format(benchmark_auc_intervals[1].round(3),
                         benchmark_auc_intervals[2].round(3),
                         benchmark_auc_intervals[3].round(3)))

# define path to logreg_regularization_model
lr_path = (root_dir + "/results/logreg_regularization/" + "logreg_roc.csv")

# read logreg lasso model roc data
lr_roc_df = pd.read_csv(lr_path)

# read in 95% CI for AUC
lr_intervals = (root_dir + "/results/logreg_regularization/" + 
                "dx_intervals.csv")

lr_auc_intervals = pd.read_csv(lr_intervals).loc[5]

# prepare string
lr_auc = ('Logistic: Demographic+Lab (AUC={0}, 95%CI: {1}-{2})'
          .format(lr_auc_intervals[1].round(3),
                  lr_auc_intervals[2].round(3),
                  lr_auc_intervals[3].round(3)))

# define path to rf model
rf_path = (root_dir + "/results/rf/rf_roc.csv")

# read rf roc data
rf_roc_df = pd.read_csv(rf_path)

# read in 95% CI for AUC
rf_intervals = (root_dir + "/results/rf/" + 
                "dx_intervals.csv")

rf_auc_intervals = pd.read_csv(rf_intervals).loc[5]

# prepare auc string
rf_auc = ('Random Forest : Demographic+Lab (AUC={0}, 95%CI: {1}-{2})'
          .format(rf_auc_intervals[1].round(3),
                  rf_auc_intervals[2].round(3),
                  rf_auc_intervals[3].round(3)))


### DCA calculations ###

# benchmark clinical values only
logreg_bench = pd.read_csv('../../results/logreg_clinical_benchmark/logreg_pred.csv')

# add in bayes corrected probability to benchmark model
def bayes(obs_pred, pop_prop):
    bayes_pred = (
        (obs_pred * pop_prop) / ((obs_pred * pop_prop) + (1-obs_pred)*(1-pop_prop))
    )
    return(bayes_pred)

# calculate pop_prop for flare (this is also the prevalence)
pop_prop_flare = logreg_bench['flare_true'].sum() / logreg_bench['flare_true'].count()


# apply formula to add bayes corrected probablity back in to the benchmark dataframe
logreg_bench['bayes_prob'] = [
    bayes(obs_pred = x, pop_prop = pop_prop_flare) 
    for x in logreg_bench['flare_pred_prob']
]

# logreg lasso
logreg = pd.read_csv('../../results/logreg_regularization/logreg_pred.csv')

# random forest
rf = pd.read_csv('../../results/rf/rf_pred.csv')

### Calculate net benefits for models based on bayes probabilities ### 

# logreg benchmark clinical only
logreg_bench_net_ben = dca(
    true_class = logreg_bench['flare_true'], 
    model_pred_prob = logreg_bench['bayes_prob']
)

# logistic clinical + labs
logreg_net_ben = dca(
    true_class = logreg['flare_true'], 
    model_pred_prob = logreg['bayes_prob']
)

# random forest net benefit
rf_net_ben = dca(
    true_class = rf['flare_true'],
    model_pred_prob = rf['bayes_prob']
)


# All treatment net benefit
# note the prevalence of flare events in the testing dataset is the same across models
pt_vals = np.linspace(0.01, 0.99, 100)

pt_odds = pt_vals / (1 - pt_vals)

# all treated net benefit based on pt_val thresholds
all_treat_net_benefit = pop_prop_flare - (1 - pop_prop_flare) * pt_odds


### FIGURE 2: A. ROC plot B. DCA plot ####

### ROC plot ###

fig = plt.figure(figsize=(8,10), constrained_layout=True)
# add grid spec
gs = fig.add_gridspec(nrows = 3, ncols = 1)

# roc plot
ax1 = fig.add_subplot(gs[:2, :])
# set title
ax1.set_title('A', size = 15, loc = 'left')
# line width
lw = 2
# benchmark plot
plt.plot(benchmark_roc_df['fpr'], 
         benchmark_roc_df['tpr'],
         color='#00C9FF',
         lw=lw, 
         linestyle=':',
         label=benchmark_auc)

# logreg lasso plot
plt.plot(lr_roc_df['fpr'], 
         lr_roc_df['tpr'],
         color='#f80759',
         lw=lw, 
         linestyle='-.',
         label=lr_auc)
# rf plot
plt.plot(rf_roc_df['fpr'], 
         rf_roc_df['tpr'],
         color='#203A43',
         lw=lw, 
         label=rf_auc)
plt.plot([0, 1], [0, 1], color='grey', lw=lw, linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.0])
plt.xlabel('1-Specificity')
plt.ylabel('Sensitivity')
#plt.title('A. Receiver Operating Characteristics Curve', loc = 'left')
plt.legend(loc="lower right")

### DCA Plot ###
ax2 = fig.add_subplot(gs[2, :])
# add title
ax2.set_title('B', size = 15, loc = 'left')
# all treated net benefit threshold
plt.plot(
    pt_vals , # thresholds
    all_treat_net_benefit , 
    color = 'darkblue' , 
    lw = lw , 
    linestyle = '--' , 
    label = 'Intervention for All'
)

# no treatment net benefit
plt.plot(
    [0, 1],
    [0, 0], 
    color = 'grey', 
    lw = lw, 
    linestyle='--', 
    label = 'Intervention for None'
)

# benchmark plot
plt.plot(
    logreg_bench_net_ben['prob_thresh'], 
    logreg_bench_net_ben['net_benefit'],
    color = '#00C9FF',
    lw = lw, 
    linestyle = ':',
    label = 'Benchmark Logistic: Demographic'
)

# logreg lasso plot
plt.plot(
    logreg_net_ben['prob_thresh'], 
    logreg_net_ben['net_benefit'],
    color = '#f80759',
    lw = lw, 
    linestyle = '-.',
    label = 'Logistic: Demographic+Lab'
)

# rf plot
plt.plot(
    rf_net_ben['prob_thresh'], 
    rf_net_ben['net_benefit'],
    color = '#203A43',
    lw = lw, 
    label = 'Random Forest : Demographic+Lab'
)


plt.xlim([0.0, 0.5])
plt.ylim([-0.025, 0.125])
plt.xlabel('Probability Threshold')
plt.ylabel('Net Benfit')
plt.legend(loc="upper right")

# save roc plot; pass white facecolor to save
plt.savefig(results_folder + "fig2_roc_dca_plot.png", 
            facecolor = 'white', dpi = 300)

# jpg save roc plot; pass white facecolor to save
plt.savefig(results_folder + "fig2_roc_dca_plot.jpg", 
            facecolor = 'white', dpi = 300)

"""
Combined ROC curve for ulcerative colitis, crohn's disease,
and indeterminate colitis subgroups using random forest model
for each subgroup
"""

# read uc roc dataframe and calculate auc
uc_path = (root_dir + "/results/rf_uc/rf_uc_roc.csv")
# read logreg lasso model roc data
uc_roc_df = pd.read_csv(uc_path)
# auc
uc_intervals = (root_dir + "/results/rf_uc/" + 
                "rf_uc_dx_intervals.csv")

uc_auc_intervals = pd.read_csv(uc_intervals).loc[5]

# prepare auc string
uc_auc = ('Ulcerative Colitis: Clinical+Lab (AUC={0}, 95%CI: {1}-{2})'
          .format(uc_auc_intervals[1].round(3),
                  uc_auc_intervals[2].round(3),
                  uc_auc_intervals[3].round(3)))

# read cd roc dataframe and calculate auc
cd_path = (root_dir + "/results/rf_cd/rf_cd_roc.csv")
# read logreg lasso model roc data
cd_roc_df = pd.read_csv(cd_path)
# auc
cd_intervals = (root_dir + "/results/rf_cd/" + 
                "rf_cd_dx_intervals.csv")

cd_auc_intervals = pd.read_csv(cd_intervals).loc[5]

# prepare auc string
cd_auc = ("Crohn's Disease: Clinical+Lab (AUC={0}, 95%CI: {1}-{2})"
          .format(cd_auc_intervals[1].round(3),
                  cd_auc_intervals[2].round(3),
                  cd_auc_intervals[3].round(3)))

# read ic roc dataframe and calculate auc
ic_path = (root_dir + "/results/rf_ic/rf_ic_roc.csv")
# read logreg lasso model roc data
ic_roc_df = pd.read_csv(ic_path)
# auc
ic_intervals = (root_dir + "/results/rf_ic/" + 
                "rf_ic_dx_intervals.csv")

ic_auc_intervals = pd.read_csv(ic_intervals).loc[5]

# prepare auc string
ic_auc = ("Indeterminate Colitis: Clinical+Lab (AUC={0}, 95%CI: {1}-{2})"
          .format(ic_auc_intervals[1].round(3),
                  ic_auc_intervals[2].round(3),
                  ic_auc_intervals[3].round(3)))

# ROC plot
plt.figure(figsize=(10,10))
lw = 2
# uc plot
plt.plot(uc_roc_df['fpr'], 
         uc_roc_df['tpr'],
         color='#00C9FF',
         lw=lw, 
         label=uc_auc)
# cd plot
plt.plot(cd_roc_df['fpr'], 
         cd_roc_df['tpr'],
         color='#f80759',
         lw=lw, 
         linestyle='-.',
         label=cd_auc)
# ic subgroup
plt.plot(cd_roc_df['fpr'], 
         cd_roc_df['tpr'],
         color='#203A43',
         lw=lw, 
         linestyle=':',
         label=ic_auc)
plt.plot([0, 1], [0, 1], color='grey', lw=lw, linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.0])
plt.xlabel('1-Specificity')
plt.ylabel('Sensitivity')
plt.title('Random Forest ROC for IBD Subgroups')
plt.legend(loc="lower right")
# %%
# save roc plot; pass white facecolor to save
plt.savefig(results_folder + "ibd_subgroup_rf_roc_plot.png", 
            facecolor = 'white', dpi = 300)


"""
RF VIF plot and Combined VIF plots for IBD Subgroups
"""
# main RF VIF plot
vif = pd.read_csv(root_dir + '/results/rf/rf_vif.csv')
# assign readable vars name
vif['readable_vars'] = readable_variables(vif['Features'])

# plot
plt.subplots(figsize=(10,6))
sns.set_color_codes('muted')
sns.barplot(x='VIF', y='readable_vars', data = vif.iloc[:9], color='#FC466B')
plt.title('Random Forest Variable Importance to Predict Flare\n' +
          'in Patients with IBD')
plt.xlabel('Variable Importance')
plt.ylabel('Top 10 Variables')
plt.tight_layout(pad=2, w_pad=2, h_pad=2)
# save odds ratiosplot; pass white facecolor to save
plt.savefig(results_folder + "rf_vif_plot.png", 
            facecolor = 'white')


"""
Subgroup plots these models need to be ran again with subset of 
labs
"""
# read ulcerative colitis vif csv
uc_vif = pd.read_csv(root_dir + '/results/rf_uc/rf_uc_vif.csv')
# assign readable vars name
uc_vif['readable_vars'] = readable_variables(uc_vif['Features'])
# read crohn's disease vif csv 
cd_vif = pd.read_csv(root_dir + '/results/rf_cd/rf_cd_vif.csv')
cd_vif['readable_vars'] = readable_variables(cd_vif['Features'])
# read indeterminate colitis vif csv
ic_vif = pd.read_csv(root_dir + '/results/rf_ic/rf_ic_vif.csv')
ic_vif['readable_vars'] = readable_variables(ic_vif['Features'])

# set up subplot
fig, ax = plt.subplots(nrows=3, ncols=1, figsize=(10,10), sharex=True)
# uc plot
sns.barplot(x='VIF', y='readable_vars', 
            data = uc_vif.loc[:9], color='#00C9FF', ax=ax[0])
ax[0].set_ylabel('')
# hide vif x label
ax[0].xaxis.label.set_visible(False)
# cd plot
sns.barplot(x='VIF', y='readable_vars', 
            data = cd_vif.loc[:9], color='#f80759', ax=ax[1])
ax[1].set_ylabel("Top 10 Features for Crohn's Disease")
ax[1].xaxis.label.set_visible(False)
# ic plot
sns.barplot(x='VIF', y='readable_vars', 
            data = ic_vif.loc[:9], color='#203A43', ax=ax[2])
ax[2].set_ylabel("")
# set overall title above top plot
ax[0].set_title("Random Forest Variable Importance to Predict Flare\n" +
                "by Inflammatory Bowel Disease Subgroup")
# align y label
fig.align_ylabels(ax)
plt.tight_layout(pad=2, w_pad=2, h_pad=2)

# save vif plot; pass white facecolor to save
# note, I saved as png
plt.savefig(results_folder + "rf_vif_ibd_subgroups_plot.png", 
            facecolor = 'white')

"""
Logistic model standardized coefficients
"""
# load coefficients
lr = pd.read_csv(
    root_dir + '/results/logreg_clinical_benchmark/logreg_oddratio.csv'
)

# use readable names function
lr['readable_name'] = readable_variables(lr['Features'])

lasso = pd.read_csv(
    root_dir + '/results/logreg_regularization/logreg_oddratio.csv'
)
lasso['readable_name'] = readable_variables(lasso['Features'])

# plot
fig, (ax1, ax2) = plt.subplots(
    nrows=2, ncols=1,
    figsize=(6.5,10),
    gridspec_kw=dict(height_ratios=[1,5])
)
# baseline model demo only
sns.set_color_codes('muted')
sns.pointplot(x='Odds_Ratios', y='readable_name', data = lr,
           color='darkblue', join=False, ax=ax1)
ax1.axvline(1.0, color='red', label = 'No Association')
ax1.set(ylabel='',xlabel='', xlim=(0.6,1.4))
ax1.set_title('Demographics only', loc='left', size=12)
# demo + labs
sns.set_color_codes('muted')
sns.pointplot(x='Odds_Ratios', y='readable_name', data = lasso,
           color='darkblue', join=False, ax=ax2)
ax2.axvline(1.0, color='red', label = 'No Association')
ax2.set(ylabel='',xlabel='', xlim=(0.6,1.4))
ax2.set_title('Demographics+Labs', loc='left', size=12)

plt.legend(loc="lower right")
plt.xlabel('Odds Ratios')
fig.tight_layout(pad=2)
fig.text(
    0, 0.5, 
    "Variables", \
    ha="center", va="center", rotation=90, size = 12
)

# saving version in manuscript results folder
plt.savefig(root_dir + "/results/manuscript/logistic_or_plot.png",
            bbox_inches='tight', dpi=300) 


"""
Note: SHAP plots are made in the rf_shap script and results are saved in that folder.
"""

"""
Combined VIF plots for IBD Subgroups
"""
# read ulcerative colitis vif csv
uc_vif = pd.read_csv('../../results/rf_uc/rf_uc_vif.csv')
# read crohn's disease vif csv 
cd_vif = pd.read_csv('../../results/rf_cd/rf_cd_vif.csv')
# read indeterminate colitis vif csv
ic_vif = pd.read_csv('../../results/rf_ic/rf_ic_vif.csv')

# set up subplot
fig, ax = plt.subplots(nrows=3, ncols=1, figsize=(8,8), sharex=True)
# uc plot
sns.barplot(x='VIF', y='Features', data = uc_vif.loc[:10], color='darkblue', ax=ax[0])
ax[0].set_ylabel('Top 10 Features for Ulcerative Colitis')
# hide vif x label
ax[0].xaxis.label.set_visible(False)
# cd plot
sns.barplot(x='VIF', y='Features', data = cd_vif.loc[:10], color='red', ax=ax[1])
ax[1].set_ylabel("Top 10 Features for Crohn's Disease")
ax[1].xaxis.label.set_visible(False)
# ic plot
sns.barplot(x='VIF', y='Features', data = ic_vif.loc[:10], color='grey', ax=ax[2])
ax[2].set_ylabel("Top 10 Features for Indeterminate Colitis")
# set overall title above top plot
ax[0].set_title("Random Forest Variable Importance to Predict Flare\n" +
                "by Inflammatory Bowel Disease Subgroup")
# align y label
fig.align_ylabels(ax)
plt.tight_layout(pad=2, w_pad=2, h_pad=2)

# save vif plot; pass white facecolor to save
# note, I saved as png
plt.savefig(results_folder + "rf_vif_ibd_subgroups_plot.png", 
            facecolor = 'white')



# %%
