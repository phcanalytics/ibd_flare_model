"""
Title: Run analyses
Author: Ryan Gan 
Email: ganr1@gene.com

Purpose: 00_run_analyses.py runs the subsequent splitting of
testing and training data, prediction models for manuscript,
and subsequent sensitivity analyses.

You can run the sequence of scripts using a command from the terminal:

'python3 00_run_analyses.py'

Note: The tableone.py script creates the table one of the manuscript.
This is not executed as this depends on the relational OPTUM EHR database.
"""


"""
Execute modularized scripts
"""
print('\n 01: Running script to select labs measured on 70% of visits' +
      '\n Saving labs to evaluate to config yaml file. \n')
exec(open('01_lab_selector.py').read())

print('\n 02: Running script to split visits randomly in to test and train.' +
      '\n Train/test will be used in subsequent models. \n')
exec(open('02_train_test.py').read())

"""
Models
"""

print('\n 03: Running benchmark logistic model \n')
exec(open('03_logreg_clinical_benchmark.py').read())


print('\n 04: Running logistic model with labs \n')
exec(open('04_logreg_regularization.py').read())


print('\n 05: Running random forest main model \n')
exec(open('05_rf.py').read())


print('\n 05a: Running random forest on chrons disease subgroup \n')
exec(open('05a_rf_cd.py').read())


print('\n 05b: Running random forest on ulcerative colitis subgroup \n')
exec(open('05b_rf_uc.py').read())


print('\n 05c: Running random forest on indeterminate colitis subgroup \n')
exec(open('05c_rf_ic.py').read())


print('\n 06: Running script to build most figures for manuscript \n')
exec(open('06_manuscript_figures.py').read())


print('\n 07: Running TreeSHAP script. Also creates results for treeshap \n')
exec(open('07_rf_shap_values.py').read())

"""
Sensitivity Analysis Models
"""

print('\n 08: Running sensitivity model of random forest model' +
      '\n\n This model is as close to replicating the Waljee 2017 model' + 
      '\n as possible with the Optum EHR')
exec(open('08_rf_replicate.py').read())


print('\n 09: Running sensitivity model of random forest model with' + 
      '\n MICE imputation')
exec(open('09_rf_mice.py').read())
