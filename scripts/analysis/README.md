## Prediction Model Overview
<b>Author/Coder:</b> Ryan Gan </br>
<b>Email:</b> ganr1@gene.com </br>
<b>Executive Director:</b> Diana Sun

### Background and Overview

<b>NOTE: We had a one year license to the Optum IBD database, which expired
   in 2020-03-01. We no longer have the data as we were required to 
   delete data upon on this date.
</b>

This folder contains python scripts that run the prediction models. I 
organized this folder slightly different than the creation of SQL
query where I've number the order of the prediction models run so it
can be executed with the 00_run_analyses.py script.

Note the tableone.py script is not run in the 00_run_analyses.py as
it needs a connection to the SQL database to get high-level numbers. As
we no longer have access to the relational database (see note above).

Run all analyses from command line:
`python3 00_run_analysis.py`

The analyses scripts read in data from a `data/` folder that is not include
in the repository for the reason above. 

Results from analyses are saved in the results scripts. 

#### Main Analyses
***

- ***analysis_functions/***: Directory that contains helper functions used
    in subsequent scripts.

- ***tableone.py***: Creates table one in manuscript. Results saved in 
  top-level `results` folder.

- ***analysis_config.yaml***: Created to pass variables to ML models. 

- ***00_run_analysis.py***: Runs all subsequent scripts in sequence.

- ***01_lab_selector.py***: Identifies candidate list of labs that have at least
    70% of labs measured across all visits. Results saved in folder 
    `query_metrics`.

- ***02_train_test.py***: Splits data by visit where models are trained on 70%
    and 30% is reserved for testing.
    
- ***03_logreg_clinical_benchmark.py***: Runs and evaluate logistic model on 
    demographic characteristics. Results saved in folder 
    `logreg_clinical_benchmark`.
    
- ***04_logreg_regularization.py***: Runs and evaluates logistic model with
    L2 regularization on demographic + longitudinal labs. Results saved in
    folder `logreg_regularization`.
    
- ***05_rf.py***: Runs and evaluations random forest model on demographics 
  and longitudinal labs. Results saved in folder `rf`.

#### Sensitivity Analyses
***

- ***05a_rf_cd.py***: Random forest model on Chron's disease subset.
  Results saved in `rf_cd`.

- ***05b_rf_uc.py***: Random forest model on ulcerative colitis subset.
  Results saved in `rf_uc`.

- ***05c_rf_ic.py***: Random forest model on indeterminate colitis subset.
  Results saved in `rf_ic`.

- ***06_manuscript_figures.py***: Makes pretty manuscript figures using
    ouptuts from models above. Results saved in `manuscript`. 
    
- ***07_rf_shap_values.py***: Runs TreeSHAP algorithm on model trained in
    05_rf.py and creates manuscript figures. Results saved in `rf_shap`.
    
- ***08_rf_replicate.py***: Runs a random forest model that prepares the 
    data as close as possible to the random forst model in Waljee et al. 2017. Results saved in `rf_replicate`.
    
- ***09_rf_mice.py***: Random forest model that is the same as 05_rf.py
    expect uses MICE imputation rather than simple median. 
    Results saved in `rf_mice`.
    