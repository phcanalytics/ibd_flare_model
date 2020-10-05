"""
Custom fit transformers for sklearn prediction pipeline
Author: Ryan Gan
Date Created: 2019-06-26
"""

from sklearn.base import BaseEstimator, TransformerMixin
import numpy 
import pandas

"""
Custom sklearn class
"""

class FeatureSelector(BaseEstimator, TransformerMixin):
    """Custom category transformer that selects features.
    """    
    # class constructor
    def __init__(self, feature_names):
        self._feature_names = feature_names
        self._variables = []
    # return self
    def fit(self, X, y = None):
        return self
    # method to describe what transformer does
    def transform(self, X, y = None):
        var_subset = []
        for i in X.columns:
            if i in self._feature_names:
                var_subset.append(i)
        # save variables selected
        self._variables = var_subset
        return X.loc[:, var_subset]
    

class CategoricalTransformer(BaseEstimator, TransformerMixin):
    """CategoricalTransformer: Selects catogrical variable and if it's numeric, 
    it turns 0/1 values in to yes or no. If a string, it returns an array that will
    be transformed later on using onehot encoding. 
    """  
    # class constructor with empty list for 0 or 1 binary vars
    def __init__(self, binary_vars=[]):
        self._binary_vars = binary_vars
    # no object fit; fit returns self
    def fit(self, X, y = None):
        return self 
    # create simple transformer of yes or no
    def create_binary(self, obj):
        if obj == 0:
            return 'No'
        else:
            return 'Yes'
    # more complicated codes later
    def transform(self, X, y=None):
        for i in X.columns:
            if i in self._binary_vars:
                X.loc[:, i] = X.loc[:, i].apply(self.create_binary)
        else:
            X.loc[:, i] = X.loc[:, i]
        return X.values
    
    
class OtherTransformer(BaseEstimator, TransformerMixin):
    """OtherTransformer: Selects variables that I don't want to go through 
    the normalization/imputation pipeline or onehot pipeline
    """
    # class constructor
    def __init__(self):
        self
    # no object fit; fit returns self
    def fit(self, X, y = None):
        return self 
    # more complicated codes later
    def transform(self, X, y=None):
        for i in X.columns:
            X.loc[:, i] = X.loc[:, i]
        return X.values


class PastMedianLabs(BaseEstimator, TransformerMixin):
    """PastMedianLabs: Function that imputes missing lab data by
    calculating per patient past median lab values.
    """
    # class constructor with empty list of labs to impute
    def __init__(self, lab_vars=[], variables=[]):
        self._labs = lab_vars 
        self._variables = variables
        self._new_labs = []
    # no object fit; fit returns self
    def fit(self, X, y=None):
        return self
    def transform(self, X, y=None):
        # turn index in to variable
        X.reset_index(inplace = True)
        if 'index' in X.columns:
            print('Index set as column')
            
        print(X.shape)
        print('Sorting dataframe of both x and setting index as variable')
        sorted_X = X.sort_values(by=['id', 'vis_date'])
        print('Starting past median imputation')
        # imputing X based on median of past value if missing
        labs_impute = (sorted_X.loc[:, ['index', 'id', 'vis_date'] + self._labs]
                       .set_index(['vis_date', 'index'])
                       .groupby('id')
                       .rolling(window=20, min_periods=1)
                       .median()
                       .reset_index())
        
        print('Replacing missing values with past median imputation')
        labs_impute.update(sorted_X.reset_index())
        
        print('Past median imputed')
        # find lab completeness after imputation
        lab_completeness = (labs_impute.groupby('id')
                            .count()
                            .apply(lambda x: numpy.where(x > 0, 1, 0))
                            .sum()/labs_impute['id'].nunique())
        
        print('Finding labs greater than 50%')
        # subset lab values
        labs_to_keep = []
        for k in dict(lab_completeness[lambda x: x > 0.50]):
            if k not in ['vis_date', 'index']:
                labs_to_keep.append(k)
        
        print('Assigning labs that were kept as a new object list')
        print(labs_to_keep)
        self._new_labs = labs_to_keep
        
        # keep other labs not in self._labs
        other_vars = []
        for i in self._variables:
            if i not in self._labs:
                other_vars.append(i)
        print("Other vars", other_vars)
        
        print('Joining imputed lab values back in with dataframe')
        # using concat so I don't duplicate rows
        X_impute = pandas.merge(
            X.loc[:, ['index'] + other_vars],
            labs_impute.loc[:, ['index'] + labs_to_keep], 
            how = 'left', on = 'index').set_index('index')
        
        # drop index column from X
        if 'index' in X.columns:
            del(X['index'])
        # return new sorted imputed x and sorted y
        return X_impute
