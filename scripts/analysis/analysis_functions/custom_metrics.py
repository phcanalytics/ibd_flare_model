"""
Custom functions for metrics
"""

import numpy 
import pandas 
from sklearn.metrics import confusion_matrix
from sklearn.metrics import roc_curve, auc
import matplotlib.pyplot as plt
import seaborn as sns; sns.set_style('whitegrid')

def dx_accuracy(cm):
    """dx_accuracy return model performance metrics in a Pandas dataframe
    
    cm: sklearn confusion matrix object  
    """
    # turn this in to a function that takes the confusion matrix based 
    FP = numpy.sum(cm, axis=0) - numpy.diag(cm)
    FN = numpy.sum(cm, axis=1) - numpy.diag(cm)
    TP = numpy.diag(cm)
    TN = numpy.sum(cm) - (FP + FN + TP)
    # Sensitivity, hit rate, recall, or true positive rate
    TPR = TP/(TP+FN)
    # Specificity or true negative rate
    TNR = TN/(TN+FP) 
    # Precision or positive predictive value
    PPV = TP/(TP+FP)
    # Negative predictive value
    NPV = TN/(TN+FN)
    # Fall out or false positive rate
    FPR = FP/(FP+TN)
    # False negative rate
    FNR = FN/(TP+FN)
    # False discovery rate
    FDR = FP/(TP+FP)
    # Overall accuracy
    ACC = (TP+TN)/(TP+FP+FN+TN)
    # list of statistics
    stats = ['Sensitivity', 'Specificity', 'Positive Predictive Value',
             'Negative Predictive Value', 'False Positive Rate', 
             'False Negative Rate', 'False Discovery Rate', 'Accuracy']
    
    # list of values for y=1
    vals = [TPR[1].round(3), TNR[1].round(3), 
            PPV[1].round(3), NPV[1].round(3),
            FPR[1].round(3), FNR[1].round(3), 
            FDR[1].round(3), ACC[1].round(3)]
    # pd dataframe
    return pandas.DataFrame({'DxStatistic': stats, 'Value': vals})


# use boostrap function defined in custom metrics module to find percentil 95%ci
def model_metrics_boot(model, x_test, y_test, boot_iteration):
    """model_metrics_boot: Takes a sklearn model, x_test and y_test 
    data, and number of iterations and returns a list of values. 
    This is meant to be used with the Joblib parallel function.
    
    model: sklearn model
    x_test: Pandas dataframe of features of test set
    y_test: Pandas series of outcome
    boot_iteration: number of times to repeat process. Must be number.
    """
    print('Iteration: ', boot_iteration)
    sample_index = numpy.random.choice(
        range(0, len(y_test)), len(y_test), 
        replace = True)

    x_samples = x_test.iloc[sample_index, :]
    y_samples = y_test.iloc[sample_index] 
    # predicted probability of y
    y_pred = model.predict_proba(x_samples)
    y_pred_class = numpy.where(y_pred[:, 1] > 0.5, 1, 0)

    """
    Accuracy metrics saved to lists
    """
    # define confusion matrix based on booted sample
    cm = confusion_matrix(y_samples, y_pred_class)

    # run accuracy summary on confuxion matrix
    dx_summary = dx_accuracy(cm)

    # append values to lists
    sn = dx_summary.iloc[0,1]
    sp = dx_summary.iloc[1,1]
    ppv = dx_summary.iloc[2,1]
    npv = dx_summary.iloc[3,1]
    acc = dx_summary.iloc[7,1]
    
    """
    Calculate ROC
    """
    # roc for prediction of y=1 (2nd part of 2d array)
    fpr, tpr, thresholds = roc_curve(y_samples, y_pred[:,1])
    # auc
    roc_auc = auc(fpr, tpr).round(3) 
    
    """
    Return list of metrics
    """
    return [sn, sp, ppv, npv, acc, roc_auc]


def boot_95(boot_list):
    """boot_95: Calculating median and 95% confidence interval
    of bootstraped estimates
    
    boot_list: Bootstrapped list created using model_metric_boot
    function. 
    """
    # empty sensitivity list to bind stuff to
    sn_list = []
    sp_list = []
    ppv_list = []
    npv_list = []
    acc_list = []
    roc_auc_list = []

    for i in range(len(boot_list)):
        sn_list.append(boot_list[i][0])
        sp_list.append(boot_list[i][1])
        ppv_list.append(boot_list[i][2])
        npv_list.append(boot_list[i][3])
        acc_list.append(boot_list[i][4])
        roc_auc_list.append(boot_list[i][5])
    
    # create list of lists
    dx_list = [sn_list, sp_list, ppv_list, 
               npv_list, acc_list, roc_auc_list]

    name_list = ['sensitivity', 'specificity', 'ppv', 
                 'npv', 'accuracy', 'roc_auc']
    # create empty dictionary
    dx_95ci_dict = {}

    # bind results list
    for i in range(0, len(dx_list)):
        median = numpy.quantile(dx_list[i], q=0.5).round(3) 
        lower95 = numpy.quantile(dx_list[i], q=0.025).round(3) 
        upper95 = numpy.quantile(dx_list[i], q=0.975).round(3) 

        dx_95ci_dict.update({name_list[i]: [median, lower95, upper95]})

    # create dataframe of accuracy 95% CIs
    dx_intervals = pandas.DataFrame.from_dict(
        dx_95ci_dict, 
        orient='index',
        columns=['median', 'lower95', 'upper95'])
    # return dx intervals dataframe
    return dx_intervals 

"""
Plot functions

Note, I may want to pass an args function to allow user defined
size, scale, etc. This works for now.
"""
def roc_plot(fpr, tpr, roc_auc, model_name):
    """roc_plot: Creates matplotlib ROC curve plot.
    
    fpr, tpr, roc_auc: Comes from sklearn roc_curve function
    and auc function.
    
    model_name: string of the name you want to give to the legend
    and title.
    """
    # ROC plot
    plt.figure(figsize=(10,10))
    lw = 2
    plt.plot(fpr, tpr, color='darkblue',
             lw=lw, label= (model_name + ' (area = %0.2f)' % roc_auc))
    plt.plot([0, 1], [0, 1], color='grey', lw=lw, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('1-Specificity')
    plt.ylabel('Sensitivity')
    plt.title(model_name + ' ROC')
    plt.legend(loc="lower right")
    
def odds_ratio_plot(or_data):
    """odds_ratio_plot: Takes a Pandas dataframe of odds ratios
    and returns a matplot/seaborn plot.
    """
    plt.subplots(figsize=(10,15))
    sns.set_color_codes('muted')
    sns.pointplot(x='Odds_Ratios', y='Features', data = or_data,
               color='b', join=False)
    plt.axvline(1.0, color='red', label = 'No Association')
    plt.title('Feature Odds Ratios to Predict Flare')
    plt.xlabel('Odds Ratios')
    plt.ylabel('Features')
    plt.legend(loc="lower right")
    plt.xlim(0.7,1.4)
    plt.tight_layout(pad=2, w_pad=2, h_pad=2)
    
def readable_variables(feature_list):
    """readable_variables: Takes list of feature names and strips
    out units and underscores as well as capitalizes names to make
    them easier to read on plots
    """

    # make readable variable names from feature list
    # list of words to strip from variable names
    word_exclude = ['mgdl', 'mmoll', 'mgdl', 'fl', 'count', 
                    'x103ul', 'total', 'random', 'base'] 

    # split out units
    readable_vars = [" ".join(
        [w.title() for w in t.split('_') if not w in word_exclude]
    ) for t in feature_list]

    # manually replace V with vs. and Prev Flare V1 Sum with Previous Flares Sum
    readable_vars = ['Male vs. Female' if w == 'Male V Female' 
                      else w for w in readable_vars]
    # replace immuno med
    readable_vars = ['Immunosuppressive Use' if w == 'Immuno Med' 
                      else w for w in readable_vars]

    # replace prev flare
    readable_vars = ['Number of Previous Flares' if w == 'Prev Flare V1 Sum' 
                      else w for w in readable_vars]
    # returns list of readable names
    return(readable_vars)

"""Decision curve net benefit analysis function (DCA)

    Equation:
    
    odds_pt = ( prob thresh / (1 - prob thresh) )
    
    Net benefit = (true positive / n) - ((false negative / n) * odds_pt)

"""
    
def dca(true_class, model_pred_prob, n_thresholds = 100):
    """dca: Decision curve net benefit analysis function (DCA)

    Equation:
    
        odds_pt = ( probability threshold / (1 - probability threshold) )
    
        Net benefit = (true positive / n) - ((false negative / n) * odds_pt)

    true_class: Takes a 1d array/vector of the true 1 or 0 values.
    
    model_pred_prob: Takes the predicted probabilities from the trained 
        model.
        
    n_thresholds: Number of thresholds to create from 0.01 to 0.99.
    """
    
    # probability thresholds to calculate
    # (note goes from 0.01 to 0.99 to avoid division by 0)
    pt_vals = numpy.linspace(0.01, 0.99, n_thresholds)
    
    # lists to append values to for a given threshold
    net_benefit = []
    sensitivity = []
    specificity = []
    
    for pt in pt_vals:
        pred_class = numpy.where(model_pred_prob >= pt, 1, 0 )

        # crosstabulation / confusion matrix 
        cm = confusion_matrix(true_class, pred_class)
        
        # sensitivity value for a given threshold
        sn = cm[1][1] / cm[1].sum()
        # specificity value for a given threshold
        sp = cm[0][0] / cm[0].sum()

        # true positives number from confusion matrix
        true_pos = cm[1][1]
        # false positives number from confusion matrix
        false_pos = cm[0][1]

        # sample size number
        samp_n = cm.sum()

        # threshold ratio
        thresh_odds = ( pt / (1 - pt) )

        # net benefit formula
        net_ben = ( true_pos / samp_n ) - ( ( false_pos / samp_n ) * thresh_odds )
        
        # append to list
        net_benefit.append(net_ben)
        sensitivity.append(sn)
        specificity.append(sp)
    
    # create dataframe of threshold values and net benefit
    df = pandas.DataFrame(
        {
            'prob_thresh': pt_vals , 
            'net_benefit': net_benefit , 
            'sensitivity': sensitivity , 
            'specificity': specificity
        }
    )
    
    # return pandas dataframe
    return( df )