"""
Title: Table one script
Author: Ryan Gan
Date Created: 2019-06-28

This script will calculate table one statistics of interest
"""
# load teradatasql to establish connection to teradata
import teradatasql
# load pandas
import pandas as pd
# os 
# import os functions
import os
import timeit

# read hidden login info; not the best way to do this but it works
login = [line.rstrip('\n') for line in open('../sql_query/login.txt')]

# new connection info for teradatasql client
usertd = login[2]
passwordtd = login[3]
host = login[4]

# create connection to teradata
con = teradatasql.connect('{"host": "' + host + '",' + \
                          '"user": "' + usertd + '",' + \
                          '"password": "' + passwordtd + '",' + \
                          '"logmech":"LDAP"}')

# create cursor to submit scripts
cur = con.cursor()

"""
Load IBD cohort
"""
# join flare events with ibd cohort demographics and load cohort dataset
ibd_cohort = pd.read_sql_query(
"""
SELECT b.ptid, b.birth_yr, b.gender, b.race, 
    b.region, b.deceased_indicator, b.first_month_active,
    b.last_month_active, b.uc_count, b.cd_count,
    b.first_ibd_date, b.index_year, b.last_ibd_date, b.age_at_index,
    a.n_flares, a.n_vis, 
    (b.last_month_active - b.first_ibd_date)/30 AS follow_up_month,
    CASE WHEN a.n_flares > 0
        THEN 'Yes'
        ELSE 'No'
        END flare,
    CASE WHEN a.n_flares IS NULL
        THEN a.n_vis
        ELSE (a.n_vis - a.n_flares)
        END nonflare_vis,
    CASE WHEN b.deceased_indicator = 1
        THEN 'Deceased Yes'
        ELSE 'Deceased No'
        END deceased,
    CASE WHEN (b.uc_count > 0 AND b.cd_count = 0)
            THEN 'Ulceartive colitis'
        WHEN (b.uc_count = 0 AND b.cd_count > 0)
            THEN 'Crohns disease'
            ELSE 'Indeterminate disease'
        END disease,
    CASE WHEN a.n_immuno_med > 0
        THEN 'Immuno Med Yes'
        ELSE 'Immuno Med No'
        END immuno_med
FROM
    (
    SELECT 
        ptid, 
        -- count up visits; new, need to check
        COUNT(*) AS n_vis,
        SUM(immuno_med) AS n_immuno_med,
        SUM(flare_v1) AS n_flares
    FROM ibd_flare.analysis
    GROUP BY ptid
    ) AS a
    INNER JOIN ibd_flare.ibd_cohort AS b
    ON a.ptid = b.ptid;
""", con)

# lowercase all variables
ibd_cohort.columns = map(str.lower, ibd_cohort.columns)


"""
Custom function to create table one summary statistics
"""

def tableone(df, name = 'All_Patients'):
    # empty dictionary
    dict = {}
    # count of patients
    dict.update({'Number of Patients': str(df['ptid'].nunique())})
    
    # continous variables
    """Continous variables"""
    cont_list = ['age_at_index', 'follow_up_month', 'nonflare_vis']
    
    for var in cont_list:
        # update dictionary name
        dict.update({var.capitalize(): '--------------'})
        # summary statistics 
        cont_df = df[var] \
            .astype('int') \
            .agg({'mean': 'mean', 
                  'std' : 'std'}).round(1) 
        # update dictionary
        dict.update({var.capitalize() + ', mean (std)': 
                     (str(cont_df[0]) + ' (' + str(cont_df[1]) + ')')})
        
        # quantiles
        cont_df = df[var].astype('int').quantile([0.5,0.25,0.75])
        # update dictionary
        dict.update({var.capitalize() + ', median (IQR)': \
                     (str(cont_df.values[0]) + \
                      ' (' + str(cont_df.values[1]) + ', ' +
                      str(cont_df.values[2]) + ')')})

    """Catgorical variables"""
    cat_list = ['gender', 'race', 'region', 
                'deceased', 'disease', 
                'immuno_med']
    
    for var in cat_list:        
        n_df = df[[var, 'ptid']] \
            .groupby(var).agg({'ptid': 'count'})
        # percent
        n_df['pct'] = (n_df['ptid']/df['ptid'].count()*100.0) \
            .round(decimals = 1)
        
        # update dictionary name
        dict.update({var.capitalize() + ', n (%)': '--------------'})
        # add index as new key and new values to dictionary
        for index, row in n_df.iterrows():
            dict.update({index: (str(int(row[0])) + ' (' + str(row[1]) + ')')})
    
    # create final dataframe
    final_df = pd.DataFrame.from_dict(dict, orient='index', columns = [name])
    # name index
    final_df.rename_axis('Characteristic').reset_index()
    # return final_df
    return final_df

"""
Apply function to calculate all patients and strata specific
"""

# strata to loop through
strata = ['All_Patients', 'No', 'Yes']

df_list = []
for s in strata:
    if s == 'All_Patients':
        tab = tableone(ibd_cohort)
    else:
        # subset
        df = ibd_cohort.query("flare == '" + s + "'")
        # table
        tab = tableone(df, name = s)
    
    # add tab to list
    df_list.append(tab)
    
# final dataframe
table_one_df = pd.concat(df_list, axis = 1)

# write dataframe
table_one_df.to_csv('../../results/table_one.csv')

