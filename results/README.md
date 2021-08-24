# Results folder overview

This folder contains results from the `scripts/analysis` folder. The table
below describes the minimal data set required by PLOS One and where those
results can be found in this project directory. 

The Optum EHR data used in this study were licensed from Optum and are not publicly available due to data licensing and use agreements; interested researchers can contact Optum to license the data. All interested researchers can access the data in the same manner as the authors. The authors had no special access privileges. [Optum EHR contact website](https://www.optum.com/business/solutions/government/federal/data-analytics-federal/clinical-data.html)


#### Minimal data set requirements table

`Results Table or Figure` column based on order of first mention in text. Links
in `Data Location` column will navigate to data used to create results tables and figures in manuscript.

| Results Table or Figure | Description | Data Location |
|-|-|-|
| Figure 1: Flow chart | Flow chart | [attrition_table.csv](https://github.com/phcanalytics/ibd_flare_model/blob/master/results/attrition_table.csv) |
|Table 1: Patient characeristics| Patient summary statistics | [table_one.csv](https://github.com/phcanalytics/ibd_flare_model/blob/master/results/table_one.csv) |
| Figure 2: AuROC and DCA | Model area under the curve and decision curve analysis.</br> Note 1: Folders linked that contains meta data for ROC curves are large .csv files and can be found in subdirectory folders. </br> Note 2: DCA curve calculated from ROC data. | [logreg_demographics](https://github.com/phcanalytics/ibd_flare_model/tree/master/results/logreg_clinical_benchmark)</br></br> [logreg_demographics_labs](https://github.com/phcanalytics/ibd_flare_model/tree/master/results/logreg_regularization)</br></br> [random_forest_demographics_labs](https://github.com/phcanalytics/ibd_flare_model/tree/master/results/rf) |
| Table 2: Model performance | Bootstrapped model performance metrics. | [logreg_demographics_dx_metrics.csv](https://github.com/phcanalytics/ibd_flare_model/blob/master/results/logreg_clinical_benchmark/dx_intervals.csv)</br></br> [logreg_demographics_labs_dx_metrics.csv](https://github.com/phcanalytics/ibd_flare_model/blob/master/results/logreg_regularization/dx_intervals.csv)</br></br> [random_forest_demographics_labs_dx_metrics.csv](https://github.com/phcanalytics/ibd_flare_model/blob/master/results/rf/dx_intervals.csv) |
| Figure 3: TreeSHAP summary| TreeSHAP random forest variable summary | Not available as it requires raw data prohibited from sharing under data use agreements |
| S1 Fig: RF variable importance | Random forest .csv variable importance by Gini impurity | [rf_vif.csv](https://github.com/phcanalytics/ibd_flare_model/blob/master/results/rf/rf_vif.csv) |
| S2 Fig: TreeSHAP conditional dependency plots | TreeSHAP random forest conditional dependency plots | Not available as it requires raw data prohibited from sharing under data use agreements |
| S3 Fig: Logistic regression odds ratios |  Odds ratio .csv files to create plot | Not available as it requires raw data prohibited from sharing under data use agreements |
| S4 Fig: IBD subgroup AuROC  | Random forest model area under the curve for IBD subgroups. </br></br> Note 1: Folders linked that contains meta data for ROC curves are large .csv files and can be found in subdirectory folders. </br> Note 2: DCA curve calculated from ROC data. | [rf_crohns_disease](https://github.com/phcanalytics/ibd_flare_model/tree/master/results/rf_cd)</br></br> [rf_ulcerative_colitis](https://github.com/phcanalytics/ibd_flare_model/tree/master/results/rf_uc)</br></br> [rf_indeterminate_colitis](https://github.com/phcanalytics/ibd_flare_model/tree/master/results/rf_ic) |
| S5 Fig: IBD subgroup VIF | Random forest .csv variable importance by Gini impurity by IBD subgroup | [rf_crohns_disease_vif.csv](https://github.com/phcanalytics/ibd_flare_model/tree/master/results/rf_cd_vif.csv)</br></br> [rf_ulcerative_colitis_vif.csv](https://github.com/phcanalytics/ibd_flare_model/tree/master/results/rf_uc_vif.csv)</br></br> [rf_indeterminate_colitis_vif.csv](https://github.com/phcanalytics/ibd_flare_model/tree/master/results/rf_ic_vif.csv) |
| S2 Table: Model performance RF imputation by MICE | Sensitivity analysis for an RF model using MICE imputation | [rf_dx_metrics_mice.csv](https://github.com/phcanalytics/ibd_flare_model/blob/master/results/rf_mice/rf_mice_dx_intervals.csv) |