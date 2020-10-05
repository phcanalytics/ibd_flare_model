## SQL Query Overview
<b>Author/Coder:</b> Ryan Gan </br>
<b>Email:</b> ganr1@gene.com </br>
<b>Executive Director:</b> Diana Sun

### Background and Overview

<b>NOTE: We had a one year license to the Optum IBD database, which expired
   in 2019-03-01. We no longer have the data as we were required to 
   delete data upon completion of this project. This codebase is how the 
   analysis table was constructed.
</b>


This folder contains python scripts that imports and execute SQL queries using 
templates stored in their respective sql_template folders. The primary reason 
for using python and SQL is that I want to reduce the amount of copy/paste and
redundant SQL commands. I want to follow the 'do not repeat yourself' (DRY) 
prinicple as much as possible. I do this using the jinja2 module/package, 
where I am able to provide lists of labs to build itterative SQL queries.

I also tried a couple different ways of organizing and submitting queries. 
The first was to submit one large query for each step. This did not work with
python as I need to build temporary tables at certain steps, which required 
separate scripts. I eventually settled on listing out the sql file template 
names in the order they need to be executed. 

All sql queries use the Optum data release from 2019 April. Queries from the 
master tables in the Roche/Genentech Teradata server need to contain the sql 
command `WHERE batch_title = 'Optum EHR IBD 2019 Apr'`. 

Note on SQL engine: TERADATA was the SQL database used for data manipulation. 
It has some custom window functions that may not be available in other SQL engines.


### SQL Template Overview

This is a general overview of the purpose of each python submission
script and the different sql template files called in each step.

- ***01_ibd_cohort_query.py*** </br>
This script calls and executes the various sql templates found in the file path
`sql_template/ibd_cohort`. The script executes the following `.sql` files in
order.

    1. `ibd_enc_count` </br>
    The Optum table used in this script is the
    `RWD_VDM_OPTUM_EHRIBD.IBD_DIAGNOSIS` table. The script creates temporary
    table *ibd_enc_count* that identifies all diagnoses codes that are either
    ulcerative colitis (abbr. UC, ICD9 = 556xx or ICD10 = K51x) or Crohn's 
    disease (abbr. CD, ICD9 = 555xx or ICD10 = K50x) and counts up the number
    of encounters each subject/patient has over the entire study period. The 
    important part of this script is that it identifies the patients with at 
    least 1 UC or CD diagnosis.

    2. `ibd_enc_date` </br>
    The Optum table used in this script is the
    `RWD_VDM_OPTUM_EHRIBD.IBD_ENCOUNTER` table. Creates temporary 
    table *ibd_enc_date* that joins interaction type and interaction date to 
    the *ibd_enc_count* temporary table. The important part of this script is 
    that it retains encounter types and dates only for patients with at least 
    one IBD encounter.
    
    3. `ibd_pos` </br>
    This script uses the temporary table *ibd_enc_date* created in the previous
    step. This script limits the service place to the following: ambulatory
    patient services, day surgery patient, office or clinic patient, urgent care,
    inpatient, observation patient, emergency patient.
    
    4. `ibd_visit` </br>
    This script uses the previously created temporary table *ibd_pos*. This 
    script orders and creates a sequential visit number per patient and 
    ordered by visit date. It also creates flag variables for the place of 
    service as outpatient, inpatient, or emergency room.
    
    5. `two_ibd_visits` </br>
    This script uses the previous temporary tables of *ibd_visit* and the Optum
    table *ibd_patient*. This applies the two visits criteria, with at least
    one of those visits being an outpatient visit.
    
    6. `ibd_cont_enroll` </br>
    This script uses the temporary *two_ibd_visits* table and finds the patients
    with at least 365 days of follow-up time post index date (first IBD visit).
    
    7. `ibd_cohort` </br>
    This script uses the temporary table *ibd_cont_enroll* and applies final
    inclusion/exclusion criteria by only keeping patients over the age of 18
    by age at first IBD date (index date) as well as excluding those patients
    missing age. This creates a permanent table in Ryan's data lab for future
    use with other queries.
    
- ***02_flare_query.py*** </br>
This script calls and executes the various sql templates found in the file path
`sql_template/flare`. The script executes the following .sql files in order.

    1. `ibd_enc_count` </br>
    Same script and same purpose as above. The Optum table used in this script 
    is the RWD_VDM_OPTUM_EHRIBD.IBD_DIAGNOSIS table. The script creates temporary
    table ibd_enc_count that identifies all diagnoses codes that are either 
    ulcerative colitis (abbr. UC, ICD9 = 556xx or ICD10 = K51x) or Crohn's 
    disease (abbr. CD, ICD9 = 555xx or ICD10 = K50x) and counts up the number of
    encounters each subject/patient has over the entire study period. The 
    important part of this script is that it identifies the patients with at 
    least 1 UC or CD diagnosis.
    
    2. `ibd_enc_date` </br>
    Same script as above. The Optum table used in this script is the
    `RWD_VDM_OPTUM_EHRIBD.IBD_ENCOUNTER` table. Creates temporary 
    table *ibd_enc_date* that joins interaction type and interaction date to 
    the *ibd_enc_count* temporary table. The important part of this script is 
    that it retains encounter types and dates only for patients with at least 
    one IBD encounter.
    
    3. `ibd_pos` </br>
    Same script above. This script uses the temporary table *ibd_enc_date* 
    created in the previous step. This script limits the service place to the 
    following: ambulatory patient services, day surgery patient, office or 
    clinic patient, urgent care, inpatient, observation patient, emergency 
    patient.
    
    4. `inpat_flare` </br>
    This script finds the inpatient or ER IBD visits, which are considered a 
    flare event as it is serious enough to require acute medical care and
    hospitalization. This table queries the *ibd_pos* table.
    
    5. `outpatient_oral_cortsteroid` </br>
    This script finds the outpatient corticosteroid prescriptions. We consider
    the following generic names: prednisone, methylprednisolone, hydrocortisone,
    cortisone, tixocortol pivalate, prednisolone, budesonide, pivalone, 
    methylprednisone. This script also excludes the corticosteroid Medrol 
    as it is not used to treat IBD flares. This script also creates a flag 
    variable to indicate if the corticosteroid prescription had a valid 
    'day supply'. Waljee et al. 2017 required a day supply of >7 days but
    Optum EHR had a lot of missing values. We created the flag to allow us
    to run sensitivity analyses.
    
    6. `cortsteroid_no_comorb` </br>
    This script applies an additional exclusion criteria that uses the 
    temp table generated in *outpatient_oral_cortsteroid* script. It excludes
    corticosteroid prescriptions with other inflammatory disease/conditions that
    take place in a 7 day window prior to prescription. These conditions are as
    follows: COPD, asthma, RA, lupus, dermatitis, bronchitis, sinusitis,
    rhinitis, polymyalgia rheumatica, cluster headaches, and autoimmune
    hepatitis.
    
    7. `flares` </br>
    This script creates a permanent table in Ryan's data lab of inpatient/ER 
    and outpatient corticosteroid flare events. It also has columns to help 
    categorize flares and other criteria that was met or not met (i.e. day 
    supply) for running sensitivity analyes.
    
- ***03_visits_w_flares_query.py*** </br>
General purpose of this script is to join flare outcomes to physical visits of 
the IBD cohort. This script calls and executes the various sql templates found 
in `sql_templates/flare`. 

    1. `physical_encounters` </br>
    This script limits IBD encounters for the defined cohort to only physical
    encounters as follows: ambulatory patient services, day surgery patient, 
    office or clinic, urgent care, inpatient, observation patient, emergency 
    patient.
    
    2. `visits` </br>
    This script aggregates physcial enounters in the table created in the previous 
    step by date.
    
    3. `previous_flare_sum` </br>
    This script sums up both versions of past flares for each subject 
    using the permanent table `flares`
    
    4. `flare_visits` </br>
    This script joins visit to flare information and creates some additional 
    variables for sensitivity analysis.
    
- ***04_ibd_labs_query.py (numeric labs)*** </br>
General purpose of this script is to join labs taken at patient visits as well 
as calculate past summaries of labs for each patient. This script calls and
executes the sql templates found in `sql_templates/labs`. This script also makes
the most use of the jinja2 framework to stay DRY.

    1. `id_labs_of_interest` </br>
    This script takes a list of general lab names and uses wildcard matching to 
    find the labs in the Optum lab list. It then applies some additional criteria 
    of only keeping labs with valid values and the most common version of lab spelling
    (which gets rid of typos of different lab names). 
    
    2. `longitudinal_labs` </br>
    This scrip uses identifies labs of interest for each patient as well as the date
    the sample was collected. I use the jinja2 framework so I don't have to copy-paste 
    labs of interest in to the same functions. This script also calculates aggregated
    metrics (mean, max, acceleration, etc) for each patient on a particular date.
    
    3. `ibd_flare.labs_wide` </br>
    This script pivots labs long to wide for each patient and date.
    
- ***04a_ibd_categorical_labs_query.py (binary/categorical)*** </br>
Note this script is very similar to the `ibd_labs_query scrip`. The major difference
is that it uses the lab ranges at a given observation to determine if the test results
are within the normal range or not. There is another categorical variable to determine
if the test result is low, normal, or high. There is also a variable capturing past
abnormal lab values. This script calls and executes the sql templates found in 
`sql_templates/labs`. This script also makes the most use of the jinja2 framework.

    1. `id_labs_of_interest` </br>
    This script takes a list of general lab names and uses wildcard matching to 
    find the labs in the Optum lab list. It then applies some additional criteria 
    of only keeping labs with valid values and the most common version of lab spelling
    (which gets rid of typos of different lab names). Same scirpt used as above.
    
    2. `categorical_labs` </br>
    This scrip uses identifies labs of interest for each patient as well as the date
    the sample was collected. I use the jinja2 framework so I don't have to copy-paste 
    labs of interest in to the same functions. This script also determines if lab values
    are abnormal (outside listed normal range) or low, normal, high.
    
    3. `ibd_flare.categorical_labs_wide` </br>
    This script pivots categorical_labs long to wide for each patient and date to join 
    with visits.
    
- ***05_create_analysis_tables_query.py  (numeric labs)*** </br>
General purpose of this script is to join the visits with flare (ibd_flare.flare_vists) 
table with any prescription of immuosuppresive medications at or before visit temp 
table, demographics table, and baseline and longitudinal labs summary together. It 
then subsets only to patient visits with at least one lab measurement. The final step
is to save a permanent table and csv file in Ryan's home directory on AWS to run analyses.

    1. `immuno_med_date_window` </br>
    Finds immunomodulator therapies related to IBD for each patient at a given visit.
    
    2. `flare_predictors` </br>
    Joins immunosuppresive meds, demographcis, and labs to visits with flare table.
    
    3. `ibd_flare.analysis` </br>
    Creates csv file saved on Ryan's directory for use in analytic models.
    
- ***05a_create_categorical_labs_analysis_tables_query.py (binary/categorical labs)*** </br>
General purpose of this script is to join the visits with flare (ibd_flare.flare_vists) 
table with any prescription of immuosuppresive medications at or before visit temp 
table, demographics table, and categorical labs together. It then subsets only to patient 
visits with at least one lab measurement. The final step is to save a permanent table and 
csv file in Ryan's home directory on AWS to run analyses. In the continous labs script,
I also ran some summary metrics and demographics. That is not done in this script as it's the same.

    1. `immuno_med_date_window` </br>
    Finds immunomodulator therapies related to IBD for each patient at a given visit.
    
    2. `flare_predictors_cat` </br>
    Joins immunosuppresive meds, demographcis, and categorical labs to visits with 
    flare table.
    
    3. `ibd_flare.analysis_cat_labs` </br>
    Creates csv file of binary/categorical labs saved on Ryan's directory for use 
    in analytic models.

### Miscellaneous Queries

- ***06_cdiff_query.py*** </br>
General purpose of this script is to create a table to identify outpatient corticosteroid 
events with a clostridium difficile (c-diff) to get a proportion missing to account for these
visits. This script uses the permanent table created in Teradata to calculate some metrics
on outpatient corticosteroid prescriptions that also have a c-diff Dx +/- 7 days of the
prescription.

    1. `ibd_flare.cdiff` </br>
    Finds all c-diff diagnoses on a given date for the IBD cohort.
    
- ***07_fecal_cal_query.py*** </br>
Script that identifies and saves fecal cal protectin lab data. The lab data were too messy
and not captured frequently enough for use in the analysis.

    1. `ibd_flare.fecal_cal` </br>
    Script to find all fecal calprotectin labs for IBD flare cohort.