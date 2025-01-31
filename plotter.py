import warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import pickle
import copy
from support import path_here, results_cf_obj_method_dir, results_cf_plots_dir
import matplotlib
matplotlib.rcParams['mathtext.fontset'] = 'stix'
matplotlib.rcParams['font.family'] = 'STIXGeneral'
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 8})
from matplotlib.lines import Line2D
from matplotlib import colors
from matplotlib import cm
from matplotlib.ticker import FormatStrFormatter
from matplotlib.path import Path
import matplotlib.patches as patches
from support import load_obj
from evaluator_constructor import distance_calculation
matplotlib.rc('ytick', labelsize=9)
matplotlib.rc('xtick', labelsize=9)
from main import datasets, methods_to_run, lagranges, likelihood_factors
from data_constructor import load_dataset
import seaborn as sns
# import plotly.express as px
import matplotlib.ticker as ticker
# sns.set_style("whitegrid")

def extract_number_idx_instances_feat_val(original_x_df, feat_name, feat_unique_val):
    """
    DESCRIPTION:        Extracts the number of instances per value of a feature of interest

    INPUT:
    original_x_df:      DataFrame containing all the instances of interest in the original format and corresponding accuracy (validity) information
    feat_name:          Name of the feature of interest
    feat_unique_val:    List of unique values of the feature of interest

    OUTPUT:
    len_feat_values:    Number of instances belonging to each feature value
    idx_feat_values:    List of indices of the instances belonging to each feature value
    """
    len_feat_values, idx_feat_values = [], []
    for i in range(len(feat_unique_val)):
        feat_values = original_x_df[original_x_df[feat_name] == feat_unique_val[i]]
        feat_values_idx = feat_values.index.tolist()
        len_feat_values.append(len(feat_values))
        idx_feat_values.append(feat_values_idx)
    return len_feat_values, idx_feat_values

def create_boxplot_handles(protected_feat, original_x_df, color_list):
    """
    DESCRIPTION:                Creates the legend handles for the boxplot subplots for datasets and method calculating the number of examples per sensitive group

    INPUT:
    protected_feat:             Protected features names
    original_x_df:              DataFrame containing the instances of interest
    color_list:                 List of colors to use

    OUTPUT:
    list_handles:               Handles for use on the boxplot subplots
    """
    list_handles = []
    checked_colors = 0
    for feat in protected_feat:
        unique_feat_val = original_x_df[feat].unique()
        for i in range(len(unique_feat_val)):
            feat_val_i = unique_feat_val[i]
            len_feat_val_i = len(original_x_df[original_x_df[feat] == feat_val_i])
            total_instances = len(original_x_df)
            handle = Line2D([0], [0], color=color_list[checked_colors + i], lw=2, label=f'{protected_feat[feat][np.round(feat_val_i, 2)]}: {len_feat_val_i} ({np.round(len_feat_val_i*100/total_instances, 1)}%)')
            list_handles.extend([handle])
        checked_colors += len(unique_feat_val)
    return list_handles

def create_handles_awb(colors_dict, used_features=None):
    """
    DESCRIPTION:            Obtains the accuracy weighted burden for each method and each dataset

    INPUT:
    colors_dict:            Dictionary of colors

    OUTPUT:
    list_handles:           List of handles
    """
    list_handles = []
    for i in range(len(colors_dict.keys())):
        if used_features is None:
            key = list(colors_dict.keys())[i]
            color = colors_dict[key]
            handle = Line2D([0], [0], color=color, lw=2, label=f'{key}')
            list_handles.extend([handle])
        else:
            key = list(colors_dict.keys())[i]
            if key in used_features:
                color = colors_dict[key]
                handle = Line2D([0], [0], color=color, lw=2, label=f'{key} CF')
                list_handles.extend([handle])
            else:
                continue
    return list_handles

def get_data_names(datasets):
    """
    DESCRIPTION:            Gets the names of the datasets for plotting

    INPUT:
    datasets:               List of datasets names

    OUTPUT:
    data_dict:              Dataset dictionary
    """
    data_dict = {}
    for i in datasets:
        if i == 'adult':
            data_dict[i] = 'Adult'
        elif i == 'kdd_census':
            data_dict[i] = 'KDD Census'
        elif i == 'german':
            data_dict[i] = 'German'
        elif i == 'dutch':
            data_dict[i] = 'Dutch'
        elif i == 'bank':
            data_dict[i] = 'Bank'
        elif i == 'credit':
            data_dict[i] = 'Credit'
        elif i == 'compass':
            data_dict[i] = 'Compas'
        elif i == 'diabetes':
            data_dict[i] = 'Diabetes'
        elif i == 'student':
            data_dict[i] = 'Student'
        elif i == 'oulad':
            data_dict[i] = 'Oulad'
        elif i == 'law':
            data_dict[i] = 'Law'
        elif i == 'synthetic_athlete':
            data_dict[i] = 'Athlete'
        elif i == 'synthetic_disease':
            data_dict[i] = 'Disease'
    return data_dict

def get_metric_names(metrics):
    """
    DESCRIPTION:            Gets the names of the performance metrics for plotting

    INPUT:
    metrics:                List of performance metrics to use

    OUTPUT:
    metric_dict:            Performance metrics dictionary
    """
    metric_dict = {}
    for i in metrics:
        # if i == 'proximity':
        #     metric_dict[i] = 'Burden (Lower is better)'
        # elif i == 'sparsity':
        #     metric_dict[i] = 'Sparsity (Higher is better)'
        if i == 'proximity':
            metric_dict[i] = 'Distance'
        elif i == 'likelihood':
            metric_dict[i] = 'Likelihood'
        elif i == 'deviation':
            metric_dict[i] = 'Fairness'
        elif i == 'effectiveness':
            metric_dict[i] = 'Effectiveness'
    return metric_dict

def get_methods_names(methods):
    """
    DESCRIPTION:            Gets the names of the methods for plotting

    INPUT:
    metrics:                List of methods to use

    OUTPUT:
    method_dict:            Methods dictionary
    """
    method_dict = {}
    for i in methods:
        if i == 'nn':
            method_dict[i] = 'NN'
        elif i == 'mutable-nn':
            method_dict[i] = 'Mutable NN'
        elif i == 'mo':
            method_dict[i] = 'MO'
        elif i == 'mutable-mo':
            method_dict[i] = 'Mutable MO'
        elif i == 'ft':
            method_dict[i] = 'FT'
        elif i == 'rt':
            method_dict[i] = 'RT'
        elif i == 'mutable-rt':
            method_dict[i] = 'Mutable RT'
        elif i == 'gs':
            method_dict[i] = 'GS'
        elif i == 'dice':
            method_dict[i] = 'DiCE'
        elif i == 'face':
            method_dict[i] = 'FACE'
        elif i == 'dice':
            method_dict[i] = 'DiCE'
        elif i == 'mace':
            method_dict[i] = 'MACE'
        elif i == 'cchvae':
            method_dict[i] = 'CCHVAE'
        elif i == 'juice':
            method_dict[i] = 'JUICEP'
        elif i == 'mutable-juice':
            method_dict[i] = 'Mutable JUICEP'
        elif i == 'jce_spar':
            method_dict[i] = 'JUICES'
        elif i == 'mutable-jce_spar':
            method_dict[i] = 'Mutable JUICES'
        elif i == 'BIGRACE_dist':
            method_dict[i] = 'CounterFair'
        elif i == 'BIGRACE_l':
            method_dict[i] = r'$BR_{like}$'
        elif i == 'BIGRACE_e':
            method_dict[i] = 'CounterFair'
        elif i == 'BIGRACE_dev_dist':
            method_dict[i] = r'CounterFair$_{dev}$'
        elif i == 'BIGRACE_dev_like':
            method_dict[i] = r'$BR_{s-like}$'
        elif i == 'BIGRACE_dev_eff':
            method_dict[i] = r'$BR_{s-eff}$'
        elif i == 'ARES':
            method_dict[i] = 'AReS'
        elif i == 'FACTS':
            method_dict[i] = 'FACTS'
    return method_dict

def attainable_cf_plot(datasets, methods_to_run):
    """
    DESCRIPTION:        Plots the percentage of attainable CFs given feasibility constraints and whether or not to consider feature mutability

    INPUT:
    datasets:           Datasets names
    methods_to_run:     Methods names

    OUTPUT: (None: plot stored)
    """
    methods_names = get_methods_names(methods_to_run)
    dataset_names = get_data_names(datasets)

def feature_ratio_change_cf_plot(datasets, methods_to_run):
    """
    DESCRIPTION:            Plots the percentage of attainable CFs given feasibility constraints and whether or not to consider feature mutability
    """
    methods_names = get_methods_names(methods_to_run)
    dataset_names = get_data_names(datasets)

def accuracy_burden_plot(datasets, method, metric, colors):
    """
    DESCRIPTION:            Plots the accuracy versus burden for different sensitive groups
    """
    methods_names = get_methods_names([method])
    dataset_names = get_data_names(datasets)

def statistical_parity_burden_plot(datasets, method, metric, colors):
    """
    DESCRIPTION:            Plots the statistical parity versus burden for different sensitive groups
    """
    methods_names = get_methods_names([method])
    dataset_names = get_data_names(datasets)

def equalized_odds_burden_plot(datasets, method, metric, colors):
    """
    DESCRIPTION:            Plots the equalized odds versus burden for different sensitive groups
    """
    methods_names = get_methods_names([method])
    dataset_names = get_data_names(datasets)

def method_box_plot(datasets, methods, metric, colors):
    """
    DESCRIPTION:        Plots the differences w.r.t. the metric of interest among sensitive groups, for all datasets and methods

    INPUT:
    datasets:           Names of the datasets
    methods:            Names of the methods
    metric:             Name of the metric
    colors:             List of colors to be used

    OUTPUT: (None: plot stored)
    """
    methods_names = get_methods_names(methods)
    dataset_names = get_data_names(datasets)
    metric_names = get_metric_names([metric])
    fig, ax = plt.subplots(nrows=len(datasets), ncols=len(methods), sharex=False, sharey=False, figsize=(8,13))
    for dataset_idx in range(len(datasets)):
        data_str = datasets[dataset_idx]
        for method_idx in range(len(methods)):
            method_str = methods[method_idx]
            eval_obj = load_obj(f'{data_str}_{method_str}_eval.pkl')
            protected_feat = eval_obj.feat_protected
            protected_feat_keys = list(protected_feat.keys())
            original_x_df = pd.concat(eval_obj.original_x.values(), axis=0)
            metrics_cf_df = pd.concat((pd.DataFrame.from_dict(eval_obj.cf_proximity, orient='index', columns=['proximity']),
                                      pd.DataFrame.from_dict(eval_obj.cf_sparsity, orient='index', columns=['sparsity']),
                                      pd.DataFrame.from_dict(eval_obj.cf_feasibility, orient='index', columns=['feasibility']),
                                      pd.DataFrame.from_dict(eval_obj.cf_time, orient='index', columns=['time'])), axis=1)
            sum_feat_unique_val = 0
            feat_val_labels = []
            for feat in protected_feat_keys:
                feat_unique_val = original_x_df[feat].unique()
                len_feat_values, idx_feat_values = extract_number_idx_instances_feat_val(original_x_df, feat, feat_unique_val)
                xaxis_pos_box = np.arange(sum_feat_unique_val+len(feat_unique_val))
                for feat_val_idx in range(len(feat_unique_val)):
                    feat_val_instances_idx = idx_feat_values[feat_val_idx]
                    box_feat_val_pos = xaxis_pos_box[sum_feat_unique_val+feat_val_idx]
                    feat_method_data_values = metrics_cf_df.loc[feat_val_instances_idx, metric].values
                    c = colors[sum_feat_unique_val+feat_val_idx]
                    ax[dataset_idx, method_idx].boxplot(x=feat_method_data_values, positions=[box_feat_val_pos], boxprops=dict(color=c),
                            capprops=dict(color=c), showfliers=False, whiskerprops=dict(color=c),
                            medianprops=dict(color=c), widths=0.9, showmeans=True,
                            meanprops=dict(markerfacecolor=c, markeredgecolor=c, marker='D'), flierprops=dict(markeredgecolor=c), notch=False)
                sum_feat_unique_val += len(feat_unique_val)
                feat_val_labels.append(feat_unique_val)
            if method_idx == 0:
                legend_elements = create_boxplot_handles(protected_feat, original_x_df, colors_list)
                ax[dataset_idx, method_idx].legend(handles=legend_elements)
            ax[dataset_idx, method_idx].axes.xaxis.set_visible(False)
    fig.subplots_adjust(wspace=0.1, hspace=0.1)
    for i in range(len(datasets)):
        ax[i,0].set_ylabel(dataset_names[datasets[i]])
    for j in range(len(methods)):
        ax[0,j].set_title(methods_names[methods[j]])
    fig.suptitle(metric_names[metric])
    fig.legend(handles=legend_elements) #loc=(-0.1,-0.1*len(legend_elements))
    plt.tight_layout()
    plt.savefig(results_cf_plots_dir+f'{metric}_comparison_across_dataset_method.pdf')

def fnr_plot(datasets, colors_dict):
    """
    DESCRIPTION:        Obtains the false negative rate plots for each sensitive feature

    INPUT:
    datasets:           Names of the datasets
    colors_dict:        Dictionary of colors to be used per feature

    OUTPUT: (None: plot stored)
    """
    dataset_names = get_data_names(datasets)
    fig, ax = plt.subplots(nrows=3,ncols=4,sharex=False,sharey=False,figsize=(8,5.5))
    flat_ax = ax.flatten()
    for dataset_idx in range(len(datasets)):
        data_str = datasets[dataset_idx]
        eval_obj = load_obj(f'{data_str}_nn_eval.pkl')
        protected_feat = eval_obj.feat_protected
        protected_feat_keys = list(protected_feat.keys())
        fnr_list = []
        feat_list = []
        colors_list = []
        for feat_idx in range(len(protected_feat_keys)):
            feat = protected_feat_keys[feat_idx]
            feat_unique_val = eval_obj.desired_ground_truth_test_df[feat].unique()
            for feat_val_idx in range(len(feat_unique_val)):
                feat_val_name = protected_feat[feat][np.round(feat_unique_val[feat_val_idx],2)]
                total_ground_truth_feat_val = np.sum(eval_obj.desired_ground_truth_test_df[feat] == feat_unique_val[feat_val_idx])
                total_false_undesired_feat_val = np.sum(eval_obj.false_undesired_test_df[feat] == feat_unique_val[feat_val_idx])
                fnr = total_false_undesired_feat_val/total_ground_truth_feat_val
                if feat in ['isMale','isMarried']:
                    feat_val_name = feat+': '+feat_val_name
                fnr_list.append(fnr)
                feat_list.append(feat_val_name)
                colors_list.append(colors_dict[feat_val_name])
        flat_ax[dataset_idx].bar(x=feat_list, height=fnr_list, color=colors_list)
        flat_ax[dataset_idx].set_xticklabels(feat_list, rotation = 30, ha='right')
        flat_ax[dataset_idx].axes.xaxis.set_visible(False)
        flat_ax[dataset_idx].yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
        flat_ax[dataset_idx].set_title(dataset_names[datasets[dataset_idx]])
    legend_handles = create_handles_awb(colors_dict)
    fig.subplots_adjust(wspace=0.1, hspace=0.1)
    fig.suptitle('False Negative Rate per Sensitive Group ($FNR_s$)')
    fig.legend(loc='lower center', bbox_to_anchor=(0.5,0.00), ncol=6, fancybox=True, shadow=True, handles=legend_handles, prop={'size': 10})
    plt.subplots_adjust(left=0.05,
                    bottom=0.2,
                    right=0.975,
                    top=0.91,
                    wspace=0.25,
                    hspace=0.22)
    flat_ax[-1].axis('off')
    plt.savefig(results_cf_plots_dir+'fnr.pdf',format='pdf',dpi=400)

def burden_plot(datasets, methods, colors_dict):
    """
    DESCRIPTION:        Obtains the burden for each method and each dataset

    INPUT:
    datasets:           Names of the datasets
    methods:            Names of the methods
    colors_dict:        Dictionary of colors to be used per feature

    OUTPUT: (None: plot stored)
    """
    methods_names = get_methods_names(methods)
    dataset_names = get_data_names(datasets)
    fig, ax = plt.subplots(nrows=len(datasets), ncols=len(methods), sharex=False, sharey=False, figsize=(8,13))
    for dataset_idx in range(len(datasets)):
        data_str = datasets[dataset_idx]
        for method_idx in range(len(methods)):
            method_str = methods[method_idx]
            eval_obj = load_obj(f'{data_str}_{method_str}_eval.pkl')
            protected_feat = eval_obj.feat_protected
            protected_feat_keys = list(protected_feat.keys())
            original_x_df = pd.concat(eval_obj.original_x.values(), axis=0)
            proximity_df = pd.DataFrame.from_dict(eval_obj.cf_proximity, orient='index', columns=['proximity'])
            awb_list = []
            feat_list = []
            colors_list = []
            for feat_idx in range(len(protected_feat_keys)):
                feat = protected_feat_keys[feat_idx]
                feat_unique_val = eval_obj.desired_ground_truth_test_df[feat].unique()
                len_feat_values, idx_feat_values = extract_number_idx_instances_feat_val(original_x_df, feat, feat_unique_val)
                for feat_val_idx in range(len(feat_unique_val)):
                    feat_val_instances_idx = idx_feat_values[feat_val_idx]
                    feat_val_name = protected_feat[feat][np.round(feat_unique_val[feat_val_idx],2)]
                    feat_method_data = proximity_df.loc[feat_val_instances_idx, 'proximity'].values
                    burden = np.mean(feat_method_data)
                    if feat in ['isMale','isMarried']:
                        feat_val_name = feat+': '+feat_val_name
                    awb_list.append(burden)
                    feat_list.append(feat_val_name)
                    colors_list.append(colors_dict[feat_val_name])
            ax[dataset_idx, method_idx].bar(x=feat_list,height=awb_list,color=colors_list)
            ax[dataset_idx, method_idx].set_xticklabels(feat_list, rotation = 30, ha='right')
            ax[dataset_idx, method_idx].axes.xaxis.set_visible(False)
            ax[dataset_idx, method_idx].yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
    legend_handles = create_handles_awb(colors_dict)
    fig.subplots_adjust(wspace=0.1, hspace=0.1)
    for i in range(len(datasets)):
        ax[i,0].set_ylabel(dataset_names[datasets[i]])
    for j in range(len(methods)):
        ax[0,j].set_title(methods_names[methods[j]])
    fig.suptitle('$Burden_s$')
    fig.legend(loc='lower center', bbox_to_anchor=(0.5,0.00), ncol=6, fancybox=True, shadow=True, handles=legend_handles, prop={'size': 10})
    plt.subplots_adjust(left=0.075,
                    bottom=0.08,
                    right=0.975,
                    top=0.94,
                    wspace=0.25,
                    hspace=0.05)
    plt.savefig(results_cf_plots_dir+'burden.pdf',format='pdf')

def fnr_burden_plot(datasets, methods, colors):
    """
    DESCRIPTION:        Obtains false negative rate plots for each sensitive feature and compares it with the burden of each sensitive group

    INPUT:
    datasets:           Names of the datasets
    methods:            Names of the methods
    colors_dict:        Dictionary of colors to be used per feature

    OUTPUT: (None: plot stored)
    """
    methods_names = get_methods_names(methods)
    dataset_names = get_data_names(datasets)
    fig, ax = plt.subplots(nrows=len(datasets), ncols=len(methods), sharex=False, sharey=False, figsize=(8,4.5))
    fig.supxlabel('$FNR_s$')
    fig.supylabel('$Burden_s$ (Lower is Better)')
    for dataset_idx in range(len(datasets)):
        data_str = datasets[dataset_idx]
        for method_idx in range(len(methods)):
            method_str = methods[method_idx]
            eval_obj = load_obj(f'{data_str}_{method_str}_eval.pkl')
            protected_feat = eval_obj.feat_protected
            protected_feat_keys = list(protected_feat.keys())
            original_x_df = pd.concat(eval_obj.original_x.values(), axis=0)
            proximity_df = pd.DataFrame.from_dict(eval_obj.cf_proximity, orient='index', columns=['proximity'])
            for feat_idx in range(len(protected_feat_keys)):
                feat = protected_feat_keys[feat_idx]
                feat_unique_val = eval_obj.desired_ground_truth_test_df[feat].unique()
                len_feat_values, idx_feat_values = extract_number_idx_instances_feat_val(original_x_df, feat, feat_unique_val)
                x_pos_list = []
                mean_data_val_list = []
                for feat_val_idx in range(len(feat_unique_val)):
                    feat_val_instances_idx = idx_feat_values[feat_val_idx]
                    feat_val_name = protected_feat[feat][np.round(feat_unique_val[feat_val_idx],2)]
                    total_ground_truth_feat_val = np.sum(eval_obj.desired_ground_truth_test_df[feat] == feat_unique_val[feat_val_idx])
                    total_false_undesired_feat_val = np.sum(eval_obj.false_undesired_test_df[feat] == feat_unique_val[feat_val_idx])
                    fnr_feat_val = total_false_undesired_feat_val/total_ground_truth_feat_val
                    x_pos_list.append(fnr_feat_val)
                    feat_method_data_values = proximity_df.loc[feat_val_instances_idx, 'proximity'].values
                    mean_data_val_list.append(np.mean(feat_method_data_values))
                    if feat_val_name == 'African-American':
                        feat_val_name = 'Afric.'
                    if feat_val_name == 'Non-white':
                        feat_val_name = 'Non-w.'
                    ax[dataset_idx, method_idx].text(x=fnr_feat_val, y=np.mean(feat_method_data_values), #bbox=dict(ec=c,fc='none'),
                                s=feat_val_name, fontstyle='italic', color=colors[feat_idx], size=9)
                    ax[dataset_idx, method_idx].scatter(x=x_pos_list, y=mean_data_val_list, color=colors[feat_idx], s=10)
                ax[dataset_idx, method_idx].yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
                ax[dataset_idx, method_idx].xaxis.set_major_formatter(FormatStrFormatter('%.1f'))
    for i in range(len(datasets)):
        ax[i,0].set_ylabel(dataset_names[datasets[i]])
    for j in range(len(methods)):
        ax[0,j].set_title(methods_names[methods[j]])
        ax[-1,j].axes.xaxis.set_visible(True)
    fig.suptitle('$Burden_s$ vs. $FNR_s$')
    plt.subplots_adjust(left=0.11,
                    bottom=0.1,
                    right=0.95,
                    top=0.88,
                    wspace=0.24,
                    hspace=0.27)
    plt.savefig(results_cf_plots_dir+'fnr_burden.pdf',format='pdf',dpi=400)

def nawb_plot(datasets, methods, colors_dict):
    """
    DESCRIPTION:        Obtains the accuracy weighted burden for each method and each dataset

    INPUT:
    datasets:           Names of the datasets
    methods:            Names of the methods
    colors_dict:        Dictionary of colors to be used per feature

    OUTPUT: (None: plot stored)
    """
    methods_names = get_methods_names(methods)
    dataset_names = get_data_names(datasets)
    fig, ax = plt.subplots(nrows=len(datasets), ncols=len(methods), sharex=False, sharey=False, figsize=(8,13))
    for dataset_idx in range(len(datasets)):
        data_str = datasets[dataset_idx]
        for method_idx in range(len(methods)):
            method_str = methods[method_idx]
            eval_obj = load_obj(f'{data_str}_{method_str}_eval.pkl')
            protected_feat = eval_obj.feat_protected
            protected_feat_keys = list(protected_feat.keys())
            original_x_df = pd.concat(eval_obj.original_x.values(), axis=0)
            proximity_df = pd.DataFrame.from_dict(eval_obj.cf_proximity, orient='index', columns=['proximity'])
            nawb_list = []
            feat_list = []
            colors_list = []
            for feat_idx in range(len(protected_feat_keys)):
                feat = protected_feat_keys[feat_idx]
                feat_unique_val = eval_obj.desired_ground_truth_test_df[feat].unique()
                len_feat_values, idx_feat_values = extract_number_idx_instances_feat_val(original_x_df, feat, feat_unique_val)
                for feat_val_idx in range(len(feat_unique_val)):
                    feat_val_instances_idx = idx_feat_values[feat_val_idx]
                    feat_val_name = protected_feat[feat][np.round(feat_unique_val[feat_val_idx],2)]
                    total_ground_truth_feat_val = np.sum(eval_obj.desired_ground_truth_test_df[feat] == feat_unique_val[feat_val_idx])
                    total_false_undesired_feat_val = np.sum(eval_obj.false_undesired_test_df[feat] == feat_unique_val[feat_val_idx])
                    fnr = total_false_undesired_feat_val/total_ground_truth_feat_val
                    feat_method_data_values = proximity_df.loc[feat_val_instances_idx, 'proximity'].values
                    mean_burden = np.mean(feat_method_data_values)
                    nawb = fnr*mean_burden*100/len(eval_obj.data_cols)
                    if feat in ['isMale','isMarried']:
                        feat_val_name = feat+': '+feat_val_name
                    nawb_list.append(nawb)
                    feat_list.append(feat_val_name)
                    colors_list.append(colors_dict[feat_val_name])
            ax[dataset_idx, method_idx].bar(x=feat_list,height=nawb_list,color=colors_list)
            ax[dataset_idx, method_idx].set_xticklabels(feat_list, rotation = 30, ha='right')
            ax[dataset_idx, method_idx].axes.xaxis.set_visible(False)
            ax[dataset_idx, method_idx].yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
    legend_handles = create_handles_awb(colors_dict)
    fig.subplots_adjust(wspace=0.1, hspace=0.1)
    for i in range(len(datasets)):
        ax[i,0].set_ylabel(dataset_names[datasets[i]])
    for j in range(len(methods)):
        ax[0,j].set_title(methods_names[methods[j]])
    fig.suptitle('Normalized Accuracy Weighted Burden ($NAWB_s$) (%)')
    fig.legend(loc='lower center', bbox_to_anchor=(0.5,0.00), ncol=6, fancybox=True, shadow=True, handles=legend_handles, prop={'size': 10})
    plt.subplots_adjust(left=0.09,
                    bottom=0.08,
                    right=0.975,
                    top=0.94,
                    wspace=0.25,
                    hspace=0.1)
    plt.savefig(results_cf_plots_dir+'normal_awb.pdf',format='pdf',dpi=400)

def validity_groups_cf(datasets, methods):
    """
    DESCRIPTION:        Obtains the validity percentage of all groups counterfactuals

    INPUT:
    datasets:           Names of the datasets
    methods:            Names of the methods

    OUTPUT: (None: plot stored)
    """
    dataset_names = get_data_names(datasets)
    methods_names = get_methods_names(methods)
    fig, ax = plt.subplots(nrows=len(datasets), ncols=1, sharex=False, sharey=False, figsize=(4,10))
    for dataset_idx in range(len(datasets)):
        data_str = datasets[dataset_idx]
        for method_idx in range(len(methods)):
            method_str = methods[method_idx]
            method_name = methods_names[methods[method_idx]]
            eval_obj = load_obj(f'{data_str}_{method_str}_eval.pkl')
            group_cf_validity_df = pd.DataFrame.from_dict(eval_obj.group_cf_validity, orient='index', columns=[method_name])
            if method_idx == 0:
                validity_df = group_cf_validity_df
            else:
                validity_df = pd.concat((validity_df, group_cf_validity_df), axis=1)
        sns.heatmap(validity_df, cbar=True, annot=True, ax=ax[dataset_idx])
    for i in range(len(datasets)):
        ax[i].set_ylabel(dataset_names[datasets[i]])
    fig.suptitle('Group Counterfactual Validity')
    plt.subplots_adjust(left=0.3,
                    bottom=0.05,
                    right=0.8,
                    top=0.95,
                    wspace=0.1,
                    hspace=0.2)
    plt.savefig(results_cf_plots_dir+'group_cf_validity.pdf',format='pdf')

def validity_clusters(datasets, methods):
    """
    DESCRIPTION:        Obtains the validity percentage of all clusters

    INPUT:
    datasets:           Names of the datasets
    methods:            Names of the methods

    OUTPUT: (None: plot stored)
    """
    dataset_names = get_data_names(datasets)
    methods_names = get_methods_names(methods)
    fig, ax = plt.subplots(nrows=len(datasets), ncols=1, sharex=False, sharey=False, figsize=(4,11))
    for dataset_idx in range(len(datasets)):
        data_str = datasets[dataset_idx]
        for method_idx in range(len(methods)):
            method_str = methods[method_idx]
            method_name = methods_names[methods[method_idx]]
            eval_obj = load_obj(f'{data_str}_{method_str}_eval.pkl')
            cluster_validity_df = pd.DataFrame.from_dict(eval_obj.cluster_validity, orient='index', columns=[method_name])
            if method_idx == 0:
                validity_df = cluster_validity_df
            else:
                validity_df = pd.concat((validity_df, cluster_validity_df), axis=1)
        sns.heatmap(validity_df, cbar=True, annot=True, ax=ax[dataset_idx])
    for i in range(len(datasets)):
        ax[i].set_ylabel(dataset_names[datasets[i]])
    fig.suptitle('Cluster Validity')
    plt.subplots_adjust(left=0.3,
                    bottom=0.05,
                    right=0.8,
                    top=0.95,
                    wspace=0.1,
                    hspace=0.2)
    plt.savefig(results_cf_plots_dir+'cluster_validity.pdf',format='pdf')

def burden_groups_cf(datasets, methods):
        """
        DESCRIPTION:        Obtains the burden for each sensitive group w.r.t. each of the group counterfactuals

        INPUT:
        datasets:           Names of the datasets
        methods:            Names of the methods

        OUTPUT: (None: plot stored)
        """
        methods_names = get_methods_names(methods)
        dataset_names = get_data_names(datasets)
        fig, ax = plt.subplots(nrows=len(datasets), ncols=len(methods), sharex=False, sharey=False, figsize=(8,13))
        for dataset_idx in range(len(datasets)):
            data_str = datasets[dataset_idx]
            for method_idx in range(len(methods)):
                method_str = methods[method_idx]
                eval_obj = load_obj(f'{data_str}_{method_str}_eval.pkl')
                protected_feat = eval_obj.feat_protected
                protected_feat_keys = list(protected_feat.keys())
                original_x_df = pd.concat(eval_obj.original_x.values(), axis=0)
                group_cf_proximity = eval_obj.group_cf_proximity
                groups_names = group_cf_proximity.columns
                burden = pd.DataFrame(index=groups_names, columns=groups_names)
                feat_list = []
                for feat_idx in range(len(protected_feat_keys)):
                    feat = protected_feat_keys[feat_idx]
                    feat_unique_val = original_x_df[feat].unique()
                    len_feat_values, idx_feat_values = extract_number_idx_instances_feat_val(original_x_df, feat, feat_unique_val)
                    for feat_val_idx in range(len(feat_unique_val)):
                        feat_val_instances_idx = idx_feat_values[feat_val_idx]
                        feat_val_name = protected_feat[feat][np.round(feat_unique_val[feat_val_idx],2)]
                        for group in groups_names:
                            feat_method_data = group_cf_proximity.loc[feat_val_instances_idx, group].values
                            burden.loc[feat_val_name, group] = np.mean(feat_method_data)
                        if feat in ['isMale','isMarried']:
                            feat_val_name = feat+': '+feat_val_name
                        feat_list.append(feat_val_name)
                for group in groups_names:
                    burden.loc['all', group] = np.mean(group_cf_proximity.loc[:, group].values)
                burden = burden.apply(pd.to_numeric)
                sns.heatmap(burden, cbar=True, annot=True, fmt='.3f', ax=ax[dataset_idx, method_idx])
        fig.subplots_adjust(wspace=0.1, hspace=0.1)
        for i in range(len(datasets)):
            ax[i,0].set_ylabel(dataset_names[datasets[i]])
        for j in range(len(methods)):
            ax[0,j].set_title(methods_names[methods[j]])
        fig.suptitle('$Burden_{s}$ for Group Counterfactuals')
        plt.subplots_adjust(left=0.075,
                        bottom=0.08,
                        right=0.975,
                        top=0.94,
                        wspace=0.2,
                        hspace=0.2)
        plt.savefig(results_cf_plots_dir+'group_cf_burden_instances.pdf',format='pdf')

def burden_groups_cf_bar(datasets, method_str):
        """
        DESCRIPTION:        Obtains the burden for each sensitive group w.r.t. each of the group counterfactuals

        INPUT:
        datasets:           Names of the datasets
        methods:            Names of the methods

        OUTPUT: (None: plot stored)
        """
        dataset_names = get_data_names(datasets)
        fig, ax = plt.subplots(nrows=len(datasets), ncols=1, sharex=False, sharey=False, figsize=(7,10))
        used_features = []
        for dataset_idx in range(len(datasets)):
            width = 0.1
            multiplier = 0
            data_str = datasets[dataset_idx]
            eval_obj = load_obj(f'{data_str}_{method_str}_eval.pkl')
            protected_feat = eval_obj.feat_protected
            protected_feat_keys = list(protected_feat.keys())
            original_x_df = pd.concat(eval_obj.original_x.values(), axis=0)
            group_cf_proximity = eval_obj.group_cf_proximity
            groups_names = list(group_cf_proximity.columns)
            burden_mean = pd.DataFrame(index=groups_names, columns=groups_names)
            burden_std = pd.DataFrame(index=groups_names, columns=groups_names)
            feat_list = []
            for feat_idx in range(len(protected_feat_keys)):
                feat = protected_feat_keys[feat_idx]
                feat_unique_val = original_x_df[feat].unique()
                _, idx_feat_values = extract_number_idx_instances_feat_val(original_x_df, feat, feat_unique_val)
                for feat_val_idx in range(len(feat_unique_val)):
                    feat_val_instances_idx = idx_feat_values[feat_val_idx]
                    feat_val_name = protected_feat[feat][np.round(feat_unique_val[feat_val_idx],2)]
                    for group in groups_names:
                        feat_method_data = group_cf_proximity.loc[feat_val_instances_idx, group].values
                        burden_mean.loc[feat_val_name, group] = np.mean(feat_method_data)
                        burden_std.loc[feat_val_name, group] = np.std(feat_method_data, ddof=1)
                    if feat in ['isMale','isMarried']:
                        feat_val_name = feat+': '+feat_val_name
                    feat_list.append(feat_val_name)
            for group in groups_names:
                burden_mean.loc['all', group] = np.mean(group_cf_proximity.loc[:, group].values)
                burden_std.loc['all', group] = np.std(group_cf_proximity.loc[:, group].values, ddof=1)
            burden_mean = burden_mean.apply(pd.to_numeric)
            burden_std = burden_std.apply(pd.to_numeric)
            x = np.arange(len(groups_names))
            for col in burden_mean.columns:
                offset = width*multiplier
                graph = ax[dataset_idx].bar(x + offset, burden_mean.loc[:, col], width, label=col, color=colors_dict[col.capitalize()]) # yerr=burden_std.loc[idx, :]
                # ax[dataset_idx].bar_label(graph, fmt='%.3f', padding=3)
                # ax[dataset_idx].legend(loc='upper left', ncol=len(burden_mean.index))
                ax[dataset_idx].set_xticks(x + width*0.5*(len(x) - 1), [f'{i.capitalize()} inst.' for i in groups_names])
                ax[dataset_idx].set_ylabel(dataset_names[datasets[dataset_idx]])
                multiplier += 1
                used_features.append(col.capitalize())
        legend_handles = create_handles_awb(colors_dict, used_features)
        fig.legend(loc='lower center', bbox_to_anchor=(0.5,0.025), ncol=4, fancybox=True, shadow=True, handles=legend_handles, prop={'size': 10})
        fig.subplots_adjust(wspace=0.1, hspace=0.1)
        fig.suptitle(f'{method_str.upper()} $Burden_s$ for Group Counterfactuals')
        fig.supxlabel(f'Sensitive Group Instances')
        fig.supylabel(f'Avg. Burden')
        plt.subplots_adjust(left=0.125,
                        bottom=0.1,
                        right=0.975,
                        top=0.94,
                        wspace=0.2,
                        hspace=0.2)
        plt.savefig(f'{results_cf_plots_dir}{method_str.upper()}_group_cf_burden_instances_bar.pdf',format='pdf')

def burden_cluster_cf(datasets, methods):
        """
        DESCRIPTION:        Obtains the burden for each sensitive groups cluster w.r.t. each of the cluster counterfactuals

        INPUT:
        datasets:           Names of the datasets
        methods:            Names of the methods

        OUTPUT: (None: plot stored)
        """
        methods_names = get_methods_names(methods)
        dataset_names = get_data_names(datasets)
        fig, ax = plt.subplots(nrows=len(datasets), ncols=len(methods), sharex=False, sharey=False, figsize=(8,13))
        for dataset_idx in range(len(datasets)):
            data_str = datasets[dataset_idx]
            for method_idx in range(len(methods)):
                method_str = methods[method_idx]
                eval_obj = load_obj(f'{data_str}_{method_str}_eval.pkl')
                protected_feat = eval_obj.feat_protected
                protected_feat_keys = list(protected_feat.keys())
                original_x_df = pd.concat(eval_obj.original_x.values(), axis=0)
                cluster_cf_proximity = eval_obj.cluster_cf_proximity
                groups_names = cluster_cf_proximity.columns
                burden = pd.DataFrame(index=groups_names, columns=groups_names)
                feat_list = []
                for feat_idx in range(len(protected_feat_keys)):
                    feat = protected_feat_keys[feat_idx]
                    feat_unique_val = original_x_df[feat].unique()
                    len_feat_values, idx_feat_values = extract_number_idx_instances_feat_val(original_x_df, feat, feat_unique_val)
                    for feat_val_idx in range(len(feat_unique_val)):
                        feat_val_instances_idx = idx_feat_values[feat_val_idx]
                        feat_val_name = protected_feat[feat][np.round(feat_unique_val[feat_val_idx],2)]
                        for group in groups_names:
                            feat_method_data = cluster_cf_proximity.loc[feat_val_instances_idx, group].values
                            burden.loc[feat_val_name, group] = np.mean(feat_method_data)
                        if feat in ['isMale','isMarried']:
                            feat_val_name = feat+': '+feat_val_name
                        feat_list.append(feat_val_name)
                for group in groups_names:
                    burden.loc['all', group] = np.mean(cluster_cf_proximity.loc[:, group].values)
                burden = burden.apply(pd.to_numeric)
                sns.heatmap(burden, cbar=True, annot=True, fmt='.3f', ax=ax[dataset_idx, method_idx])
        fig.subplots_adjust(wspace=0.1, hspace=0.1)
        for i in range(len(datasets)):
            ax[i,0].set_ylabel(dataset_names[datasets[i]])
        for j in range(len(methods)):
            ax[0,j].set_title(methods_names[methods[j]])
        fig.suptitle('$Burden_s$ for Cluster Counterfactuals')
        plt.subplots_adjust(left=0.075,
                        bottom=0.08,
                        right=0.975,
                        top=0.94,
                        wspace=0.2,
                        hspace=0.2)
        plt.savefig(results_cf_plots_dir+'cluster_cf_burden_instances.pdf',format='pdf')

def nawb_groups_cf(datasets, methods):
        """
        DESCRIPTION:        Obtains the NAWB measure for each sensitive group w.r.t. each of the group counterfactuals

        INPUT:
        datasets:           Names of the datasets
        methods:            Names of the methods

        OUTPUT: (None: plot stored)
        """
        methods_names = get_methods_names(methods)
        dataset_names = get_data_names(datasets)
        fig, ax = plt.subplots(nrows=len(datasets), ncols=len(methods), sharex=False, sharey=False, figsize=(8,13))
        for dataset_idx in range(len(datasets)):
            data_str = datasets[dataset_idx]
            for method_idx in range(len(methods)):
                method_str = methods[method_idx]
                eval_obj = load_obj(f'{data_str}_{method_str}_eval.pkl')
                protected_feat = eval_obj.feat_protected
                protected_feat_keys = list(protected_feat.keys())
                original_x_df = pd.concat(eval_obj.original_x.values(), axis=0)
                group_cf_proximity = eval_obj.group_cf_proximity
                groups_names = group_cf_proximity.columns
                nawb = pd.DataFrame(index=groups_names, columns=groups_names)
                feat_list = []
                for feat_idx in range(len(protected_feat_keys)):
                    feat = protected_feat_keys[feat_idx]
                    feat_unique_val = original_x_df[feat].unique()
                    len_feat_values, idx_feat_values = extract_number_idx_instances_feat_val(original_x_df, feat, feat_unique_val)
                    for feat_val_idx in range(len(feat_unique_val)):
                        feat_val_instances_idx = idx_feat_values[feat_val_idx]
                        feat_val_name = protected_feat[feat][np.round(feat_unique_val[feat_val_idx],2)]
                        total_ground_truth_feat_val = np.sum(eval_obj.desired_ground_truth_test_df[feat] == feat_unique_val[feat_val_idx])
                        total_false_undesired_feat_val = np.sum(eval_obj.false_undesired_test_df[feat] == feat_unique_val[feat_val_idx])
                        fnr_group = total_false_undesired_feat_val/total_ground_truth_feat_val
                        for group in groups_names:
                            feat_method_data = group_cf_proximity.loc[feat_val_instances_idx, group].values
                            mean_burden = np.mean(feat_method_data)
                            nawb.loc[feat_val_name, group] = fnr_group*mean_burden*100/len(eval_obj.data_cols)
                        if feat in ['isMale','isMarried']:
                            feat_val_name = feat+': '+feat_val_name
                        feat_list.append(feat_val_name)
                for group in groups_names:
                    nawb.loc['all', group] = np.mean(group_cf_proximity.loc[:, group].values)
                nawb = nawb.apply(pd.to_numeric)
                sns.heatmap(nawb, cbar=True, annot=True, fmt='.3f', ax=ax[dataset_idx, method_idx])
        fig.subplots_adjust(wspace=0.1, hspace=0.1)
        for i in range(len(datasets)):
            ax[i,0].set_ylabel(dataset_names[datasets[i]])
        for j in range(len(methods)):
            ax[0,j].set_title(methods_names[methods[j]])
        fig.suptitle('$NAWB_s$ for Group Counterfactuals')
        plt.subplots_adjust(left=0.075,
                        bottom=0.08,
                        right=0.975,
                        top=0.94,
                        wspace=0.2,
                        hspace=0.2)
        plt.savefig(results_cf_plots_dir+'group_cf_nawb_instances.pdf',format='pdf')

def nawb_cluster_cf(datasets, methods):
        """
        DESCRIPTION:        Obtains the NAWB measure for each sensitive group cluster w.r.t. each of the cluster counterfactuals

        INPUT:
        datasets:           Names of the datasets
        methods:            Names of the methods

        OUTPUT: (None: plot stored)
        """
        methods_names = get_methods_names(methods)
        dataset_names = get_data_names(datasets)
        fig, ax = plt.subplots(nrows=len(datasets), ncols=len(methods), sharex=False, sharey=False, figsize=(8,13))
        for dataset_idx in range(len(datasets)):
            data_str = datasets[dataset_idx]
            for method_idx in range(len(methods)):
                method_str = methods[method_idx]
                eval_obj = load_obj(f'{data_str}_{method_str}_eval.pkl')
                protected_feat = eval_obj.feat_protected
                protected_feat_keys = list(protected_feat.keys())
                original_x_df = pd.concat(eval_obj.original_x.values(), axis=0)
                cluster_cf_proximity = eval_obj.cluster_cf_proximity
                groups_names = cluster_cf_proximity.columns
                nawb = pd.DataFrame(index=groups_names, columns=groups_names)
                feat_list = []
                for feat_idx in range(len(protected_feat_keys)):
                    feat = protected_feat_keys[feat_idx]
                    feat_unique_val = original_x_df[feat].unique()
                    len_feat_values, idx_feat_values = extract_number_idx_instances_feat_val(original_x_df, feat, feat_unique_val)
                    for feat_val_idx in range(len(feat_unique_val)):
                        feat_val_instances_idx = idx_feat_values[feat_val_idx]
                        feat_val_name = protected_feat[feat][np.round(feat_unique_val[feat_val_idx],2)]
                        total_ground_truth_feat_val = np.sum(eval_obj.desired_ground_truth_test_df[feat] == feat_unique_val[feat_val_idx])
                        total_false_undesired_feat_val = np.sum(eval_obj.false_undesired_test_df[feat] == feat_unique_val[feat_val_idx])
                        fnr_group = total_false_undesired_feat_val/total_ground_truth_feat_val
                        for group in groups_names:
                            feat_method_data = cluster_cf_proximity.loc[feat_val_instances_idx, group].values
                            mean_burden = np.mean(feat_method_data)
                            nawb.loc[feat_val_name, group] = fnr_group*mean_burden*100/len(eval_obj.data_cols)
                        if feat in ['isMale','isMarried']:
                            feat_val_name = feat+': '+feat_val_name
                        feat_list.append(feat_val_name)
                for group in groups_names:
                    nawb.loc['all', group] = np.mean(cluster_cf_proximity.loc[:, group].values)
                nawb = nawb.apply(pd.to_numeric)
                sns.heatmap(nawb, cbar=True, annot=True, fmt='.3f', ax=ax[dataset_idx, method_idx])
        fig.subplots_adjust(wspace=0.1, hspace=0.1)
        for i in range(len(datasets)):
            ax[i,0].set_ylabel(dataset_names[datasets[i]])
        for j in range(len(methods)):
            ax[0,j].set_title(methods_names[methods[j]])
        fig.suptitle('$NAWB_s$ for Cluster Counterfactuals')
        plt.subplots_adjust(left=0.075,
                        bottom=0.08,
                        right=0.975,
                        top=0.94,
                        wspace=0.2,
                        hspace=0.2)
        plt.savefig(results_cf_plots_dir+'cluster_cf_nawb_instances.pdf',format='pdf')

def inverse_transform_only(bin_enc, cat_enc, bin_enc_cols, cat_enc_cols, binary, categorical, numerical, instance):
    """
    DESCRIPTION:            Transforms an instance to the original features

    INPUT:
    instance:               Instance of interest

    OUTPUT:
    original_instance_df:   Instance of interest in the original feature format
    """
    instance_index = instance.index
    original_instance_df = pd.DataFrame(index=instance_index)
    if len(bin_enc_cols) > 0:
        instance_bin = bin_enc.inverse_transform(instance[bin_enc_cols])
        instance_bin_pd = pd.DataFrame(data=instance_bin, index=instance_index, columns=binary)
        original_instance_df = pd.concat((original_instance_df, instance_bin_pd), axis=1)
    if len(cat_enc_cols) > 0:
        instance_cat = cat_enc.inverse_transform(instance[cat_enc_cols])
        instance_cat_pd = pd.DataFrame(data=instance_cat, index=instance_index, columns=categorical)
        original_instance_df = pd.concat((original_instance_df, instance_cat_pd), axis=1)
    if len(numerical) > 0:
        instance_num = instance[numerical]
        instance_num_pd = pd.DataFrame(data=instance_num, index=instance_index, columns=numerical)
        original_instance_df = pd.concat((original_instance_df, instance_num_pd), axis=1)
    return original_instance_df

def plot_centroids():
    """
    Plot all centroids of clusters found for each feature and feature_value
    """
    method_str = 'fijuice'
    for data_str in datasets:
        eval_obj = load_obj(f'{data_str}_{method_str}_cluster_eval.pkl')
        clusters = eval_obj.cluster_obj
        cluster_centroid_dict = clusters.centroids
        cluster_instance_dict = clusters.clusters
        cluster_centroid_feat_list = list(cluster_centroid_dict.keys())
        for feat in cluster_centroid_feat_list:
            feat_val_list = list(cluster_centroid_dict[feat].keys())
            for feat_val_idx in range(len(feat_val_list)):
                feat_val = feat_val_list[feat_val_idx]
                centroid_list = cluster_centroid_dict[feat][feat_val]
                instance_list = cluster_instance_dict[feat][feat_val]
                fig, ax = plt.subplots(figsize=(4, 4))
                cluster_number_series_all = pd.Series()
                instances_all_df = pd.DataFrame()
                for idx in range(len(instance_list)):
                    instances_df = clusters.false_undesired_test_df.loc[instance_list[idx]]
                    instances_df['Clusters'] = [idx]*len(instances_df)
                    cluster_number_series = instances_df.pop('Clusters')
                    instances_all_df = pd.concat((instances_all_df, instances_df))
                    cluster_number_series_all = pd.concat((cluster_number_series_all, cluster_number_series), axis=0)
                cluster_number_series_all.name = 'Clusters'
                len_clusters = len(cluster_number_series_all.unique())
                map_var = dict(zip(cluster_number_series_all.unique(), cm.rainbow(np.linspace(0, 1, len_clusters))))
                cluster_colors = cluster_number_series_all.map(map_var)
                ax = sns.clustermap(instances_all_df, row_colors=cluster_colors, row_cluster=False, col_cluster=False, cbar_pos=(0.05, .4, .01, .2), figsize=(4, 4), standard_scale=1)
                ax.fig.suptitle(f'{data_str.capitalize()} ({feat}: {feat_val})')
                plt.savefig(f'{results_cf_plots_dir}{data_str}_{feat}_{feat_val}_instances.pdf', format='pdf')

def estimate_difference(eval_obj, centroid, instances, feat_type):
    """
    Obtains the differences among the centroid and the instances
    """
    difference = copy.deepcopy(instances)
    cat_bin_features = eval_obj.categorical + eval_obj.binary
    num_features = eval_obj.numerical
    for idx in range(len(instances)):
        inst_idx = instances.iloc[idx].name
        for feat in cat_bin_features:
            difference.loc[inst_idx, feat] = 1 if difference.loc[inst_idx, feat] != centroid[feat].values[0] else 0
        for feat in num_features:
            difference.loc[inst_idx, feat] = np.abs(centroid[feat].values[0] - difference.loc[inst_idx, feat])
    return difference

def plot_centroids_diff():
    """
    Plots the differences of the centroids with their corresponding cluster instances
    """
    for data_str in datasets:
        for method_idx in range(len(methods_to_run)):
            method_str = methods_to_run[method_idx]
            eval_obj = load_obj(f'{data_str}_{method_str}_cluster_eval.pkl')
            clusters = eval_obj.cluster_obj
            cluster_centroid_dict = clusters.centroids_dict
            cluster_instance_dict = clusters.clusters
            cluster_centroid_feat_list = list(cluster_centroid_dict.keys())
            for feat in cluster_centroid_feat_list:
                feat_val_list = list(cluster_centroid_dict[feat].keys())
                for feat_val_idx in range(len(feat_val_list)):
                    feat_val = feat_val_list[feat_val_idx]
                    centroid_list = cluster_centroid_dict[feat][feat_val]
                    instance_list = cluster_instance_dict[feat][feat_val]
                    fig, ax = plt.subplots(figsize=(4*len(feat_val_list), 4), nrows=1, ncols=len(feat_val_list))
                    cluster_number_series_all = pd.Series()
                    difference_all_df = pd.DataFrame()
                    for idx in range(len(instance_list)):
                        instances_df = clusters.false_undesired_test_df.loc[instance_list[idx]]
                        instances_df['Clusters'] = [idx]*len(instances_df)
                        cluster_number_series = instances_df.pop('Clusters')
                        centroid_original = eval_obj.inverse_transform_original(centroid_list[idx])
                        difference_df = estimate_difference(eval_obj, centroid_original, instances_df, eval_obj.feat_type)
                        difference_all_df = pd.concat((difference_all_df, difference_df))
                        cluster_number_series_all = pd.concat((cluster_number_series_all, cluster_number_series), axis=0)
                    cluster_number_series_all.name = 'Clusters'
                    len_clusters = len(cluster_number_series_all.unique())
                    map_var = dict(zip(cluster_number_series_all.unique(), cm.rainbow(np.linspace(0, 1, len_clusters))))
                    cluster_colors = cluster_number_series_all.map(map_var)
                    ax[feat_val_idx] = sns.clustermap(difference_all_df, row_colors=cluster_colors, row_cluster=False, col_cluster=False, cbar_pos=(0.05, .4, .01, .2), figsize=(4, 4), standard_scale=1)
                    ax[feat_val_idx].fig.suptitle(f'{data_str.capitalize()} ({feat}: {feat_val}) Centroid difference')
                    plt.savefig(f'{results_cf_plots_dir}{data_str}_{method_str}_{feat}_{feat_val}_instances_diff_centroid.pdf', format='pdf')

def plot_centroids_cf_proximity():
    """
    Plots the proximity for each of the features and feature value clusters towards their corresponding cluster counterfactual
    """
    method_str = 'fijuice'
    lagranges = [0.0, 1.0]
    # lagrange = 1.0 # May be changed together with ncols to draw several plots, one for each lagrange
    dataset_names = get_data_names(datasets)
    for lagrange in lagranges:
        fig, ax = plt.subplots(nrows=len(datasets), ncols=1, sharex=False, sharey=False, figsize=(6, 8))
        for data_idx in range(len(datasets)):
            data_str = datasets[data_idx]
            dataset = dataset_names[data_str]
            eval_obj = load_obj(f'{data_str}_{method_str}_cluster_eval.pkl')
            cf_df = eval_obj.cf_df
            cf_df_lagrange = cf_df.loc[cf_df['lagrange'] == lagrange]
            cluster_centroid_dict = eval_obj.cluster_obj.centroids_dict
            cluster_centroid_feat_list = list(cluster_centroid_dict.keys())
            all_proximity_list = []
            x_axis_labels = []
            for feat in cluster_centroid_feat_list:
                feat_val_list = list(cluster_centroid_dict[feat].keys())
                for feat_val_idx in range(len(feat_val_list)):
                    feat_val = feat_val_list[feat_val_idx]
                    cf_feat_val_df = cf_df_lagrange.loc[(cf_df_lagrange['feature'] == feat) & (cf_df_lagrange['feat_value'] == feat_val)]
                    cf_feat_val_proximity_list = list(cf_feat_val_df['cf_proximity'].values)
                    all_proximity_list.append(cf_feat_val_proximity_list)
                    x_axis_labels.extend([f'{feat.capitalize()}: {eval_obj.feat_protected[feat.capitalize()][feat_val]}'])
            ax[data_idx].boxplot(all_proximity_list, showmeans=True, meanprops=mean_prop, showfliers=False)
            ax[data_idx].set_xticklabels([x_axis_labels[i] for i in range(len(x_axis_labels))], rotation=0)
            ax[data_idx].set_ylabel(dataset.capitalize())
            ax[data_idx].grid(axis='y', linestyle='--', alpha=0.4)
        fig.suptitle(f'Distance to CFs')
        fig.subplots_adjust(left=0.15, bottom=0.1, right=0.9, top=0.9, wspace=0.475, hspace=0.25)
        plt.savefig(f'{results_cf_plots_dir}all_datasets_{method_str}_{lagrange}_proximity.pdf', format='pdf')

def plot_centroids_cfs_ablation():
    """
    Plots the ablation with respect to the lagrange factor
    """
    fig, ax = plt.subplots(nrows=1, ncols=len(datasets), sharex=True, sharey=True, figsize=(8, 5))
    method_str = 'fijuice_like_constraint'
    start, end = 0, 1.1
    for data_idx in range(len(datasets)):
        data_str = datasets[data_idx]
        dataset = get_data_names(datasets)[data_str]
        mean_proximity = []
        all_cf_differences = []
        for lagrange in lagranges:
            eval_obj = load_obj(f'{data_str}_{method_str}_cluster_eval.pkl')
            cf_df = eval_obj.cf_df
            cf_df_lagrange = cf_df.loc[cf_df['lagrange'] == lagrange]
            len_cf_df_lagrange = len(cf_df_lagrange)
            cf_df_mean_all = np.mean(cf_df_lagrange['cf_proximity'].values)
            unique_centroids_idx = np.unique(cf_df_lagrange['centroid_idx'].values)
            cf_difference_proximity = 0
            cf_mean_proximity = 0
            for c_idx in range(len(unique_centroids_idx)):
                centroid_idx = unique_centroids_idx[c_idx]
                centroid_cf_df = cf_df_lagrange.loc[cf_df_lagrange['centroid_idx'] == centroid_idx]
                len_centroid_cf_df = len(centroid_cf_df)
                weight_centroid = len_centroid_cf_df/len_cf_df_lagrange
                mean_proximity_centroid_cf_df = np.mean(centroid_cf_df['cf_proximity'].values)
                weighted_mean_proximity_centroid_cf_df = mean_proximity_centroid_cf_df*weight_centroid
                cf_mean_proximity += weighted_mean_proximity_centroid_cf_df
                cf_difference_proximity += weight_centroid*(mean_proximity_centroid_cf_df - cf_df_mean_all)**2
            mean_proximity.append(cf_df_mean_all)
            all_cf_differences.append(cf_difference_proximity)
        ax[data_idx].plot(lagranges, all_cf_differences, color='#5E81AC', label='Variance of Distance')
        ax[data_idx].grid(axis='both', linestyle='--', alpha=0.4)
        ax[data_idx].yaxis.set_tick_params(labelcolor='#5E81AC')
        ax[data_idx].xaxis.set_ticks(ticks=np.arange(start, end, 0.1), labels=['0.0','','','','','0.5','','','','','1.0'])
        ax[data_idx].set_title(f'{dataset.capitalize()}')
        secax = ax[data_idx].twinx()
        secax.plot(lagranges, mean_proximity, color='#BF616A', label='Mean Distance')
        secax.yaxis.set_tick_params(labelcolor='#BF616A')
        ax[data_idx].yaxis.set_major_formatter(FormatStrFormatter('%.4f'))
        secax.yaxis.set_major_formatter(FormatStrFormatter('%.3f'))
    fig.supxlabel('$\lambda$ Weight Parameter')
    fig.supylabel('Variance of Distance', color='#5E81AC')
    fig.suptitle(f'Mean Distance and Variance of Distance vs. $\lambda$')
    fig.text(0.965, 0.5, 'Mean Distance', color='#BF616A', va='center', rotation='vertical')
    fig.subplots_adjust(left=0.1, bottom=0.1, right=0.925, top=0.9, wspace=0.4, hspace=0.2)
    plt.savefig(f'{results_cf_plots_dir}{method_str}_lagrange_ablation.pdf', format='pdf')

def get_all_mean_variance_values(data_str):
    method_str = 'fijuice_like_constraint'
    dataset_mean_proximity = []
    dataset_all_cf_differences = []
    for likelihood_idx in range(len(likelihood_factors)):
        likelihood_factor = likelihood_factors[likelihood_idx]
        mean_proximity = []
        all_cf_differences = []
        for lagrange in lagranges:
            eval_obj = load_obj(f'{data_str}_{method_str}_cluster_eval.pkl')
            cf_df_lagrange_likelihood = eval_obj.cf_df.loc[(eval_obj.cf_df['lagrange'] == lagrange) & (eval_obj.cf_df['likelihood'] == likelihood_factor)]
            len_cf_df_lagrange = len(cf_df_lagrange_likelihood)
            cf_df_mean_all = np.mean(cf_df_lagrange_likelihood['cf_proximity'].values)
            unique_centroids_idx = np.unique(cf_df_lagrange_likelihood['centroid_idx'].values)
            cf_difference_proximity = 0
            cf_mean_proximity = 0
            for c_idx in range(len(unique_centroids_idx)):
                centroid_idx = unique_centroids_idx[c_idx]
                centroid_cf_df = cf_df_lagrange_likelihood.loc[cf_df_lagrange_likelihood['centroid_idx'] == centroid_idx]
                weight_centroid = len(centroid_cf_df)/len_cf_df_lagrange
                mean_proximity_centroid_cf_df = np.mean(centroid_cf_df['cf_proximity'].values)
                weighted_mean_proximity_centroid_cf_df = mean_proximity_centroid_cf_df*weight_centroid
                cf_mean_proximity += weighted_mean_proximity_centroid_cf_df
                cf_difference_proximity += weight_centroid*(mean_proximity_centroid_cf_df - cf_df_mean_all)**2
            mean_proximity.append(cf_df_mean_all)
            all_cf_differences.append(cf_difference_proximity)
        dataset_mean_proximity.extend(mean_proximity)
        dataset_all_cf_differences.extend(all_cf_differences)
    min_dataset_mean_proximity, max_dataset_mean_proximity = min(dataset_mean_proximity)-0.01, max(dataset_mean_proximity)+0.01
    min_dataset_cf_differences, max_dataset_cf_differences = min(dataset_all_cf_differences)-0.01, max(dataset_all_cf_differences)+0.01
    return min_dataset_mean_proximity, max_dataset_mean_proximity, min_dataset_cf_differences, max_dataset_cf_differences

def plot_centroids_cfs_ablation_lagrange_likelihood():
    """
    Plots the ablation with respect to the lagrange factor
    """
    fig, ax = plt.subplots(nrows=len(datasets), ncols=len(likelihood_factors), sharex=True, sharey=False, figsize=(8, 11))
    method_str = 'fijuice_like_constraint'
    start, end = 0, 1.1
    for data_idx in range(len(datasets)):
        data_str = datasets[data_idx]
        dataset = get_data_names(datasets)[data_str]
        min_mean, max_mean, min_var, max_var = get_all_mean_variance_values(data_str)
        for likelihood_idx in range(len(likelihood_factors)):
            likelihood_factor = likelihood_factors[likelihood_idx]
            mean_proximity = []
            all_cf_differences = []
            all_Z = []
            for lagrange in lagranges:
                eval_obj = load_obj(f'{data_str}_{method_str}_cluster_eval.pkl')
                cf_df_lagrange_likelihood = eval_obj.cf_df.loc[(eval_obj.cf_df['lagrange'] == lagrange) & (eval_obj.cf_df['likelihood'] == likelihood_factor)]
                len_cf_df_lagrange = len(cf_df_lagrange_likelihood)
                cf_df_mean_all = np.mean(cf_df_lagrange_likelihood['cf_proximity'].values)
                unique_centroids_idx = np.unique(cf_df_lagrange_likelihood['centroid_idx'].values)
                cf_difference_proximity = 0
                cf_mean_proximity = 0
                Z_list = list(cf_df_lagrange_likelihood['obj_val'].values)
                all_Z.append(Z_list)
                for c_idx in range(len(unique_centroids_idx)):
                    centroid_idx = unique_centroids_idx[c_idx]
                    centroid_cf_df = cf_df_lagrange_likelihood.loc[cf_df_lagrange_likelihood['centroid_idx'] == centroid_idx]
                    weight_centroid = len(centroid_cf_df)/len_cf_df_lagrange
                    mean_proximity_centroid_cf_df = np.mean(centroid_cf_df['cf_proximity'].values)
                    weighted_mean_proximity_centroid_cf_df = mean_proximity_centroid_cf_df*weight_centroid
                    cf_mean_proximity += weighted_mean_proximity_centroid_cf_df
                    cf_difference_proximity += weight_centroid*(mean_proximity_centroid_cf_df - cf_df_mean_all)**2
                mean_proximity.append(cf_df_mean_all)
                all_cf_differences.append(cf_difference_proximity)
                if 3 in list(cf_df_lagrange_likelihood['model_status'].values):
                    ax[data_idx, likelihood_idx].text(x=0.05, y=max_var-0.005, s='*', fontsize=12)
            if 3 not in list(cf_df_lagrange_likelihood['model_status'].values):
                ax[data_idx, likelihood_idx].text(x=0.05, y=max_var-0.005, s=r'$\hat{Z}$'+f': {np.round_(np.mean(all_Z),3)}', fontsize=10)
            ax[data_idx, likelihood_idx].plot(lagranges, all_cf_differences, color='#5E81AC', label='Distance Variance')
            ax[data_idx, likelihood_idx].grid(axis='x', linestyle='--', alpha=0.4)
            ax[data_idx, likelihood_idx].yaxis.set_tick_params(labelcolor='#5E81AC')
            if likelihood_idx > 0:
                ax[data_idx, likelihood_idx].yaxis.set_visible(False)
            ax[data_idx, likelihood_idx].xaxis.set_ticks(ticks=np.arange(start, end, 0.1), labels=['0.0','','','','','0.5','','','','','1.0'])
            if data_idx == 0:
                ax[data_idx, likelihood_idx].set_title(r'$\rho_{min}=$'+str(likelihood_factor), fontsize=10)
            secax = ax[data_idx, likelihood_idx].twinx()
            secax.plot(lagranges, mean_proximity, color='#BF616A', label='Mean Distance')
            secax.yaxis.set_tick_params(labelcolor='#BF616A')
            if likelihood_idx < len(likelihood_factors) - 1:
                secax.yaxis.set_visible(False)
            ax[data_idx, likelihood_idx].set_ylim(min_var, max_var)
            secax.set_ylim(min_mean, max_mean)
            ax[data_idx, likelihood_idx].yaxis.set_major_formatter(FormatStrFormatter('%.3f'))
            secax.yaxis.set_major_formatter(FormatStrFormatter('%.3f'))
    for data_idx in range(len(datasets)):
        data_str = datasets[data_idx]
        dataset = get_data_names(datasets)[data_str]
        ax[data_idx, 0].set_ylabel(f'{dataset.capitalize()}')
    fig.supxlabel('$\lambda$ Weight Parameter')
    fig.supylabel('Distance Variance', color='#5E81AC')
    fig.suptitle(f'Mean Distance and Variance of Distance vs. $\lambda$ and '+r'$\rho$')
    fig.text(0.965, 0.5, 'Mean Distance', color='#BF616A', va='center', rotation='vertical')
    fig.subplots_adjust(left=0.125, bottom=0.1, right=0.9, top=0.9, wspace=0.25, hspace=0.1)
    plt.savefig(f'{results_cf_plots_dir}{method_str}_lagrange_likelihood_ablation.pdf', format='pdf')

def proximity_all_datasets_all_methods_plot(datasets, methods):
    """
    DESCRIPTION:        Obtains the accuracy weighted burden for each method and each dataset

    INPUT:
    datasets:           Names of the datasets
    methods:            Names of the methods

    OUTPUT: (None: plot stored)
    """

    methods_names = get_methods_names(methods)
    dataset_names = get_data_names(datasets)
    fig, axes = plt.subplots(nrows=len(datasets), ncols=3)
    for dataset_idx in range(len(datasets)):
        data_str = datasets[dataset_idx]
        data_name = dataset_names[data_str]
        eval_alpha_10 = load_obj(f'{data_str}_BIGRACE_dist_alpha_1.0_eval.pkl').cf_df
        eval_alpha_05 = load_obj(f'{data_str}_BIGRACE_dist_alpha_0.5_eval.pkl').cf_df
        eval_alpha_01 = load_obj(f'{data_str}_BIGRACE_dist_alpha_0.1_eval.pkl').cf_df
        eval_ares_df = load_obj(f'{data_str}_ARES_alpha_0.0_eval.pkl').cf_df
        eval_facts_df = load_obj(f'{data_str}_FACTS_alpha_0.0_eval.pkl').cf_df
        all_alpha_10 = pd.concat((eval_alpha_10, eval_ares_df, eval_facts_df), axis=0)
        all_alpha_05 = pd.concat((eval_alpha_05, eval_ares_df, eval_facts_df), axis=0)
        all_alpha_01 = pd.concat((eval_alpha_01, eval_ares_df, eval_facts_df), axis=0)
        b0 = sns.barplot(x=all_alpha_10['Method'], y=all_alpha_10['Distance'], hue=all_alpha_10['Sensitive group'], ax=axes[dataset_idx, 0], errwidth=0.5, capsize=0.1, estimator=sum)
        b1 = sns.barplot(x=all_alpha_05['Method'], y=all_alpha_05['Distance'], hue=all_alpha_05['Sensitive group'], ax=axes[dataset_idx, 1], errwidth=0.5, capsize=0.1, estimator=sum)
        b2 = sns.barplot(x=all_alpha_01['Method'], y=all_alpha_01['Distance'], hue=all_alpha_01['Sensitive group'], ax=axes[dataset_idx, 2], errwidth=0.5, capsize=0.1, estimator=sum)
        b0.legend([], [], frameon=False)
        b1.legend([], [], frameon=False)
        b2.legend(bbox_to_anchor=(1.01,1), frameon=False, prop={'size': 6}) #
        b0.set(xlabel=None)
        b1.set(xlabel=None)
        b2.set(xlabel=None)
        b0.set(ylabel=data_name)
        b1.set(ylabel=None)
        b2.set(ylabel=None)
        if dataset_idx == 0:
            b0.set_title(f'$\\alpha = 1.0$')
            b1.set_title(f'$\\alpha = 0.5$')
            b2.set_title(f'$\\alpha = 0.1$')
        if dataset_idx < len(datasets) - 1:
            b0.set_xticklabels([])
            b1.set_xticklabels([])
            b2.set_xticklabels([])
        if dataset_idx == len(datasets) - 1:
            xticklabels_dist = [methods_names['BIGRACE_dist'], methods_names['ARES'], methods_names['FACTS']]
            xticklabels_like = [methods_names['BIGRACE_dist'], methods_names['ARES'], methods_names['FACTS']]
            xticklabels_eff = [methods_names['BIGRACE_dist'], methods_names['ARES'], methods_names['FACTS']]
            b0.set_xticklabels(xticklabels_dist, rotation = 45)
            b1.set_xticklabels(xticklabels_like, rotation = 45)
            b2.set_xticklabels(xticklabels_eff, rotation = 45)
    fig.subplots_adjust(left=0.075,
                    bottom=0.10,
                    right=0.8,
                    top=0.9,
                    wspace=0.3,
                    hspace=0.1)
    fig.suptitle('Proximity performance of CounterFair', fontsize=20)
    plt.savefig(results_cf_plots_dir+'proximity_performance2.pdf',format='pdf',dpi=400)

def proximity_across_alpha_counterfair(datasets):
    """
    DESCRIPTION:        Obtains the accuracy weighted burden for each method and each dataset

    INPUT:
    datasets:           Names of the datasets

    OUTPUT: (None: plot stored)
    """
    dataset_names = get_data_names(datasets)
    fig, axes = plt.subplots(nrows=len(datasets), ncols=2, figsize=(8, 9.5), gridspec_kw={'width_ratios': [7, 3], 'height_ratios': [1.5, 1.5, 1.5, 1.5, 1.5, 2]})
    for dataset_idx in range(len(datasets)):
        data_str = datasets[dataset_idx]
        data_name = dataset_names[data_str]
        eval_alpha_10 = load_obj(f'{data_str}_BIGRACE_dist_alpha_1.0_eval.pkl')
        eval_alpha_05 = load_obj(f'{data_str}_BIGRACE_dist_alpha_0.5_eval.pkl')
        eval_alpha_01 = load_obj(f'{data_str}_BIGRACE_dist_alpha_0.1_eval.pkl')
        eval_alpha_10_df = eval_alpha_10.cf_df
        eval_alpha_05_df = eval_alpha_05.cf_df
        eval_alpha_01_df = eval_alpha_01.cf_df
        all_alphas = pd.concat((eval_alpha_10_df, eval_alpha_05_df, eval_alpha_01_df), axis=0)
        b0 = sns.barplot(x=all_alphas['alpha'], y=all_alphas['Distance'], hue=all_alphas['Sensitive group'], ax=axes[dataset_idx, 0], estimator=sum, ci=None)
        h, l = b0.get_legend_handles_labels()
        bar_colors_dict = {}
        for idx, sensitive_group in enumerate(l):
            bar_colors_dict[sensitive_group] = h[idx][0].get_facecolor()

        x_alphas = np.array([0.1, 0.5, 1.0]).astype(float)
        max_y = -100

        labels = []
        for sensitive_group in bar_colors_dict.keys():
            eval_alpha_10_df_sensitive_group = eval_alpha_10_df[eval_alpha_10_df['Sensitive group'] == sensitive_group]
            eval_alpha_05_df_sensitive_group = eval_alpha_05_df[eval_alpha_05_df['Sensitive group'] == sensitive_group]
            eval_alpha_01_df_sensitive_group = eval_alpha_01_df[eval_alpha_01_df['Sensitive group'] == sensitive_group]
            n_different_cfs_alpha_10 = len(np.unique(np.concatenate((eval_alpha_10_df_sensitive_group['cf'].values), axis=0), axis=0))
            n_different_cfs_alpha_05 = len(np.unique(np.concatenate((eval_alpha_05_df_sensitive_group['cf'].values), axis=0), axis=0))
            n_different_cfs_alpha_01 = len(np.unique(np.concatenate((eval_alpha_01_df_sensitive_group['cf'].values), axis=0), axis=0))
            y_n_different_cfs = np.array([n_different_cfs_alpha_01, n_different_cfs_alpha_05, n_different_cfs_alpha_10]).astype(int)
            number_instances_group = len(eval_alpha_10_df[eval_alpha_10_df['Sensitive group'] == sensitive_group])
            axes[dataset_idx, 1].plot(x_alphas, y_n_different_cfs, marker='d', markersize=4, linestyle='--', color=bar_colors_dict[sensitive_group])
            if np.max(y_n_different_cfs) > max_y:
                max_y = np.max(y_n_different_cfs)
            labels.append(f'{sensitive_group} ({number_instances_group} FNs)')
        axes[dataset_idx, 1].set_xlim(np.min(x_alphas)-0.2, np.max(x_alphas)+0.2)
        axes[dataset_idx, 1].set_ylim(-1, max_y+7)
        ticks = x_alphas
        xticklabels_alpha = x_alphas
        axes[dataset_idx, 1].set_xticks(ticks)
        axes[dataset_idx, 1].set_xticklabels(x_alphas)

        b0.legend([], [], frameon=False)
        if data_str == 'adult':
            b0.legend(h, labels, frameon=False, prop={'size': 7.5}, ncol=1, loc='upper left', bbox_to_anchor=(0.55,1.04))
        else:
            b0.legend(h, labels, frameon=False, prop={'size': 8})
        axes[dataset_idx, 1].set_ylabel(f'Subgroups'+r' ($L^{s_k}$)', fontsize=12)
        b0.set_xlabel(None)
        b0.set_ylabel(f'{data_name}\nBurden'+r' ($AWB^{s_k}$)', fontsize=12)
        # if dataset_idx == 0:
            # b0.set_title(f'Burden vs. $\\alpha$', fontsize=12)
            # axes[dataset_idx, 1].set_title('Number of different groups vs. $\\alpha$', fontsize=12)
        # if dataset_idx < len(datasets) - 1:
            # b0.set_xticklabels([])
            # axes[dataset_idx, 1].set_xticklabels([])
            # axes[dataset_idx, 1].axes.get_xaxis().set_visible(False)
        if dataset_idx == len(datasets) - 1:
            b0.set_xlabel(f'$\\alpha$', fontsize=10)
            axes[dataset_idx, 1].set_xlabel(f'$\\alpha$', fontsize=10)
            b0.set_xticklabels(xticklabels_alpha)
    fig.subplots_adjust(left=0.1,
                    bottom=0.05,
                    right=0.98,
                    top=0.99,
                    wspace=0.175,
                    hspace=0.175)
    # fig.suptitle('CounterFair burden and number of subgroups identified', fontsize=15)
    plt.savefig(results_cf_plots_dir+'burden_subgroups_counterfair.pdf',format='pdf',dpi=400)

def proximity_fairness_across_alpha_counterfair(datasets):
    """
    DESCRIPTION:        Obtains the accuracy weighted burden for each method and each dataset

    INPUT:
    datasets:           Names of the datasets

    OUTPUT: (None: plot stored)
    """
    dataset_names = get_data_names(datasets)
    for dataset_idx in range(len(datasets)):
        data_str = datasets[dataset_idx]
        data_name = dataset_names[data_str]
        eval_alpha_10_df = load_obj(f'{data_str}_BIGRACE_dist_alpha_1.0_eval.pkl').cf_df
        eval_alpha_05_df = load_obj(f'{data_str}_BIGRACE_dist_alpha_0.5_eval.pkl').cf_df
        eval_alpha_01_df = load_obj(f'{data_str}_BIGRACE_dist_alpha_0.1_eval.pkl').cf_df
        eval_dev_df = load_obj(f'{data_str}_BIGRACE_dev_dist_dev_eval.pkl').cf_df
        eval_alpha_10_df['alpha'] = [f'$\\alpha=1.0$']*len(eval_alpha_10_df)
        eval_alpha_05_df['alpha'] = [f'$\\alpha=0.5$']*len(eval_alpha_05_df)
        eval_alpha_01_df['alpha'] = [f'$\\alpha=0.1$']*len(eval_alpha_01_df)
        eval_dev_df['alpha'] = ['Fair']*len(eval_dev_df)
        all_alphas = pd.concat((eval_alpha_01_df, eval_alpha_05_df, eval_alpha_10_df, eval_dev_df), axis=0)
        unique_sensitive_features = np.unique(all_alphas['feature'].values)
        size = (len(unique_sensitive_features)*2.6, 2)
        fig, axes = plt.subplots(figsize=size, nrows=1, ncols=len(unique_sensitive_features), sharey=True)
        max_y = -100
        min_y = 100
        for sensitive_feature_idx in range(len(unique_sensitive_features)):
            sensitive_feature = unique_sensitive_features[sensitive_feature_idx]
            all_alphas_feat = all_alphas[all_alphas['feature'] == sensitive_feature]
            if len(unique_sensitive_features) == 1:
                b0 = sns.barplot(x=all_alphas_feat['alpha'], y=all_alphas_feat['Distance'], hue=all_alphas_feat['Sensitive group'], ax=axes, estimator=sum, ci=None)
            else:
                b0 = sns.barplot(x=all_alphas_feat['alpha'], y=all_alphas_feat['Distance'], hue=all_alphas_feat['Sensitive group'], ax=axes[sensitive_feature_idx], estimator=sum, ci=None)
            h, l = b0.get_legend_handles_labels()
            bar_colors_dict = {}
            for idx, sensitive_group in enumerate(l):
                bar_colors_dict[sensitive_group] = h[idx][0].get_facecolor()
            x_positions = np.array([0, 1, 2, 3])
            b0_twin = b0.twinx()
            b0_twin.set_xticks([])
            b0_twin.set_xticks(x_positions)
            b0_twin.set_xticklabels(b0.get_xticklabels())
            labels = []
            for sensitive_group in l:
                eval_alpha_01_df_sensitive_group = eval_alpha_01_df[eval_alpha_01_df['Sensitive group'] == sensitive_group]
                eval_alpha_05_df_sensitive_group = eval_alpha_05_df[eval_alpha_05_df['Sensitive group'] == sensitive_group]
                eval_alpha_10_df_sensitive_group = eval_alpha_10_df[eval_alpha_10_df['Sensitive group'] == sensitive_group]
                eval_dev_df_sensitive_group = eval_dev_df[eval_dev_df['Sensitive group'] == sensitive_group]
                n_different_cfs_alpha_01 = len(np.unique(np.concatenate((eval_alpha_01_df_sensitive_group['cf'].values), axis=0), axis=0))
                n_different_cfs_alpha_05 = len(np.unique(np.concatenate((eval_alpha_05_df_sensitive_group['cf'].values), axis=0), axis=0))
                n_different_cfs_alpha_10 = len(np.unique(np.concatenate((eval_alpha_10_df_sensitive_group['cf'].values), axis=0), axis=0))
                n_different_cfs_eval = len(np.unique(np.concatenate((eval_dev_df_sensitive_group['cf'].values), axis=0), axis=0))
                y_n_different_cfs = np.array([n_different_cfs_alpha_01, n_different_cfs_alpha_05, n_different_cfs_alpha_10, n_different_cfs_eval]).astype(int)
                number_instances_group = len(eval_alpha_10_df[eval_alpha_10_df['Sensitive group'] == sensitive_group])
                b0_twin.plot(x_positions, y_n_different_cfs, marker='d', markersize=6, markeredgecolor='black', markerfacecolor=bar_colors_dict[sensitive_group], linestyle=':', linewidth=0.05, color='black')
                if np.max(y_n_different_cfs) > max_y:
                    max_y = np.max(y_n_different_cfs)
                if np.min(y_n_different_cfs) < min_y:
                    min_y = np.min(y_n_different_cfs)
                sensitive_group_name = sensitive_group.replace(f'{sensitive_feature}: ','')
                labels.append(f'{sensitive_group_name} ({number_instances_group})')
            b0_twin.set_ylim(min_y-int((max_y - min_y)*0.1), max_y+int((max_y - min_y)*0.1))
            b0.legend([], [], frameon=False)
            b0.legend(h, labels, frameon=False, prop={'size': 8}, ncols=len(l), handletextpad=0.2, handlelength=0.5, loc='upper center', bbox_to_anchor=(0.5, -0.15))
            b0.set_title(sensitive_feature, fontsize=9)
            if sensitive_feature_idx == len(unique_sensitive_features) - 1:
                b0_twin.set_ylabel(f'Subgroups'+r' ($L^{s_k}$)', fontsize=9)
            # if sensitive_feature_idx < len(unique_sensitive_features) - 1:
            #     b0_twin.set_yticklabels('')
            b0.set_xlabel(None)
            if sensitive_feature_idx == 0:
                b0.set_ylabel(f'Burden'+r' ($AWB^{s_k}$)', fontsize=9)
            else:
                b0.set_ylabel('')
        # fig.supxlabel(f'$\\alpha$', fontsize=9)
        if len(unique_sensitive_features) == 3:
            left_m = 0.075
            bottom_m = 0.2
            right_m = 0.925
            top_m = 0.9
            wspace_m = 0.2
            hspace_m = 0.175
        elif len(unique_sensitive_features) == 2:
            left_m = 0.11
            bottom_m = 0.225
            right_m = 0.92
            top_m = 0.9
            wspace_m = 0.25
            hspace_m = 0.175
        elif len(unique_sensitive_features) == 1:
            left_m = 0.2
            bottom_m = 0.2
            right_m = 0.8
            top_m = 0.9
            wspace_m = 0.15
            hspace_m = 0.175
        fig.subplots_adjust(left=left_m,
                    bottom=bottom_m,
                    right=right_m,
                    top=top_m,
                    wspace=wspace_m,
                    hspace=hspace_m)
        plt.savefig(results_cf_plots_dir+f'{data_str}_burden_subgroups_fairness_counterfair.pdf',format='pdf',dpi=400)

def distance_calculation_correction(x, y, **kwargs):
    if 'kwargs' in kwargs.keys():
        data = kwargs['kwargs']['dat']
        type = kwargs['kwargs']['type']
    else:
        data = kwargs['dat']
        type = kwargs['type']
    """
    Method that calculates the distance between two points. Default is 'euclidean'. Other types are 'L1', 'mixed_L1' and 'mixed_L1_Linf'
    """
    def euclid(x, y):
        """
        Calculates the euclidean distance between the instances (inputs must be Numpy arrays)
        """
        return np.sqrt(np.sum((x - y)**2))

    def L1(x, y):
        """
        Calculates the L1-Norm distance between the instances (inputs must be Numpy arrays)
        """
        return np.sum(np.abs(x - y))

    def L0(x, y, data):
        """
        Calculates a simple matching distance between the features of the instances (pass only categortical features, inputs must be Numpy arrays)
        """
        not_match = 0
        for binary_categorical_feature in data.binary+data.categorical:
            binary_categorical_idx = data.processed_features_dict_idx[binary_categorical_feature]
            x_categorical_np = x[binary_categorical_idx]
            y_categorical_np = y[binary_categorical_idx]
            if not np.array_equal(x_categorical_np, y_categorical_np):
                not_match += 1
        return not_match

    def Linf(x, y):
        """
        Calculates the Linf distance
        """
        return np.max(np.abs(x - y))

    def L1_L0(x, y, data):
        """
        Calculates the distance components according to Sharma et al.: Please see: https://arxiv.org/pdf/1905.07857.pdf
        """
        x_continuous_np = x[data.processed_ordinal_continuous_idx_list]
        y_continuous_np = y[data.processed_ordinal_continuous_idx_list]
        L1_distance = L1(x_continuous_np, y_continuous_np)
        L0_distance = L0(x, y, data)
        return L1_distance, L0_distance

    if type == 'euclidean':
        distance = euclid(x, y)
    elif type == 'L1':
        distance = L1(x, y)
    elif type == 'L_inf':
        distance = Linf(x, y)
    elif type == 'L1_L0':
        n_con, n_cat = len(data.numerical), len(data.binary + data.categorical)
        n = n_con + n_cat
        L1_distance, L0_distance = L1_L0(x, y, data)
        """
        Equation from Sharma et al.: Please see: https://arxiv.org/pdf/1905.07857.pdf
        """
        distance = (n_con/n)*L1_distance + (n_cat/n)*L0_distance
    return distance

def correct_eval_distance_df(eval_df, data_str):
    """
    Corrects the distance in eval_facts
    """
    train_fraction = 0.7
    seed_int = 54321
    step = 0.01 
    data = load_dataset(data_str, train_fraction, seed_int, step)
    type = 'L1_L0'
    arg_dict = {'dat': data, 'type':type}
    for idx in range(len(eval_df)):
        x = eval_df['normal_centroid'][idx]
        y = eval_df['normal_cf'][idx]
        feat = eval_df['feature'][idx]
        feat_val = eval_df['feat_value'][idx]
        feat_num_val = [feat_num_value for feat_num_value in data.feat_protected[feat].keys() if data.feat_protected[feat][feat_num_value] == feat_val][0]
        len_sensitive_group_df = len(data.test_df.loc[(data.test_df[feat] == feat_num_val) & (data.test_target == data.desired_class)])
        dist = distance_calculation_correction(x, y, kwargs=arg_dict)
        eval_df.loc[idx, 'Distance'] = dist/len_sensitive_group_df
    return eval_df

def burden_effectiveness_benchmark(datasets):
    """
    DESCRIPTION:        Obtains the accuracy weighted burden for each method and each dataset

    INPUT:
    datasets:           Names of the datasets

    OUTPUT: (None: plot stored)
    """
    dataset_names = get_data_names(datasets)
    methods_names = get_methods_names(methods_to_run)
    for dataset_idx in range(len(datasets)):
        data_str = datasets[dataset_idx]
        data_name = dataset_names[data_str]
        eval_alpha_10_df = load_obj(f'{data_str}_BIGRACE_dist_alpha_1.0_eval.pkl').cf_df
        eval_eff_df = load_obj(f'{data_str}_BIGRACE_e_eff_eval.pkl').cf_df
        if data_str == 'student':
            eval_ares_df = load_obj(f'{data_str}_ARES_alpha_0.0_support_0.1_eval.pkl').cf_df
            eval_facts_df = load_obj(f'{data_str}_FACTS_cluster_eval.pkl').cf_df
            eval_facts_df = correct_eval_distance_df(eval_facts_df, data_str)
        elif data_str == 'adult':
            eval_ares_df = load_obj(f'{data_str}_ARES_alpha_0.0_support_0.05_eval.pkl').cf_df
            eval_facts_df = load_obj(f'{data_str}_FACTS_alpha_0.0_support_0.05_eval.pkl').cf_df
        elif data_str == 'dutch':
            eval_facts_df = load_obj(f'{data_str}_FACTS_alpha_0.0_support_0.1_eval.pkl').cf_df
            eval_ares_df = load_obj(f'{data_str}_ARES_alpha_0.0_support_0.01_eval.pkl').cf_df
        else:
            eval_ares_df = load_obj(f'{data_str}_ARES_alpha_0.0_support_0.01_eval.pkl').cf_df
            eval_facts_df = load_obj(f'{data_str}_FACTS_alpha_0.0_support_0.01_eval.pkl').cf_df
        burden_df = pd.concat((eval_alpha_10_df, eval_ares_df, eval_facts_df), axis=0)
        eff_df = pd.concat((eval_eff_df, eval_ares_df, eval_facts_df), axis=0)
        unique_sensitive_features = np.unique(burden_df['feature'].values)
        size = (len(unique_sensitive_features)*2.5, 1.6)
        fig, axes = plt.subplots(figsize=size, nrows=1, ncols=int(2*len(unique_sensitive_features)))
        max_y = -100
        min_y = 100
        x_burden = [methods_names['BIGRACE_dist'], methods_names['ARES'], methods_names['FACTS']]
        x_eff = [methods_names['BIGRACE_e'], methods_names['ARES'], methods_names['FACTS']]
        color_palette = ['C0','C1','C2','C3','C4','C5','C6','C7','C8','C9','C10','C11']
        count_sensitive_groups = 0
        for sensitive_feature_idx in range(len(unique_sensitive_features)):
            sensitive_feature = unique_sensitive_features[sensitive_feature_idx]
            burden_df_feat = burden_df[burden_df['feature'] == sensitive_feature]
            eff_df_feat = eff_df[eff_df['feature'] == sensitive_feature]
            b0 = sns.barplot(x=burden_df_feat['Method'], y=burden_df_feat['Distance'], hue=burden_df_feat['Sensitive group'], ax=axes[sensitive_feature_idx*2], estimator=sum, ci=None, palette=color_palette[count_sensitive_groups:count_sensitive_groups+len(np.unique(burden_df_feat['Sensitive group'].values))])
            b0.set_title(f'Burden'+r' ($AWB^{s_k}$)', fontsize=9)
            b0.set_ylabel('')
            b0.set_xlabel('')
            b0.set_xticklabels(x_burden, fontsize=6, rotation=22, va='top', ha='center')
            # text_kwargs = dict(ha='center', va='center', fontsize=10, transform=axes[sensitive_feature_idx*2].transAxes)
            # b0.text(x=1.125, y=1.25, s=sensitive_feature, **text_kwargs)
            # b0.yaxis.get_label().set_fontsize(8)
            b0.tick_params(axis='y', labelsize=8)
            b1 = sns.barplot(x=eff_df_feat['Method'], y=eff_df_feat['Effectiveness'], hue=eff_df_feat['Sensitive group'], ax=axes[sensitive_feature_idx*2 + 1], ci=None, palette=color_palette[count_sensitive_groups:count_sensitive_groups+len(np.unique(burden_df_feat['Sensitive group'].values))])
            count_sensitive_groups += len(np.unique(burden_df_feat['Sensitive group'].values))
            b1.set_title('Effectiveness'+r' ($E^{s_k}$)', fontsize=9)
            b1.set_ylabel('')
            b1.set_xlabel('')
            b1.set_xticklabels(x_eff, fontsize=7, rotation=25, va='top', ha='center')
            # b1.yaxis.get_label().set_fontsize(8)
            b1.tick_params(axis='y', labelsize=8)
            h, l = b0.get_legend_handles_labels()
            labels = []
            for sensitive_group in l:
                number_instances_group = len(eval_alpha_10_df[eval_alpha_10_df['Sensitive group'] == sensitive_group])
                sensitive_group_name = sensitive_group.replace(f'{sensitive_feature}: ','')
                labels.append(f'{sensitive_group_name} ({number_instances_group})')
            b0.legend([], [], frameon=False)
            b0.legend(h, labels, frameon=False, prop={'size': 8}, ncols=len(l), handletextpad=0.2, handlelength=0.5, loc='upper center', bbox_to_anchor=(1.13, -0.29))
            b1.legend([], [], frameon=False)
            # b1.legend(h, labels, frameon=False, prop={'size': 8}, ncols=len(l), handletextpad=0.2, handlelength=0.5, loc='upper center', bbox_to_anchor=(0.5, -0.15))
        # fig.supxlabel(f'CF generation model', fontsize=9)
        if len(unique_sensitive_features) == 3:
            left_m = 0.06
            bottom_m = 0.3
            right_m = 0.975
            top_m = 0.85
            wspace_m = 0.35
            hspace_m = 0.175
        elif len(unique_sensitive_features) == 2:
            left_m = 0.07
            bottom_m = 0.3
            right_m = 0.975
            top_m = 0.85
            wspace_m = 0.35
            hspace_m = 0.175
        elif len(unique_sensitive_features) == 1:
            left_m = 0.12
            bottom_m = 0.3
            right_m = 0.975
            top_m = 0.85
            wspace_m = 0.35
            hspace_m = 0.175
        fig.subplots_adjust(left=left_m,
                    bottom=bottom_m,
                    right=right_m,
                    top=top_m,
                    wspace=wspace_m,
                    hspace=hspace_m)
        plt.savefig(results_cf_plots_dir+f'{data_str}_burden_effectiveness_benchmark.pdf',format='pdf',dpi=400)

def time_benchmark(datasets):
    """
    DESCRIPTION:        Obtains the accuracy weighted burden for each method and each dataset

    INPUT:
    datasets:           Names of the datasets

    OUTPUT: (None: plot stored)
    """
    dataset_names = get_data_names(datasets)
    methods_names = get_methods_names(methods_to_run)
    fig, axes = plt.subplots(figsize=(5.5, 1.5), nrows=1, ncols=len(datasets), sharey=True)
    for dataset_idx in range(len(datasets)):
        data_str = datasets[dataset_idx]
        data_name = dataset_names[data_str]
        eval_alpha_10_df = load_obj(f'{data_str}_BIGRACE_dist_alpha_1.0_eval.pkl').cf_df
        if data_str == 'student':
            eval_ares_df = load_obj(f'{data_str}_ARES_alpha_0.0_support_0.1_eval.pkl').cf_df
            eval_facts_df = load_obj(f'{data_str}_FACTS_cluster_eval.pkl').cf_df
            eval_facts_df = correct_eval_distance_df(eval_facts_df, data_str)
        elif data_str == 'adult':
            eval_ares_df = load_obj(f'{data_str}_ARES_alpha_0.0_support_0.05_eval.pkl').cf_df
            eval_facts_df = load_obj(f'{data_str}_FACTS_alpha_0.0_support_0.05_eval.pkl').cf_df
        elif data_str == 'dutch':
            eval_facts_df = load_obj(f'{data_str}_FACTS_alpha_0.0_support_0.1_eval.pkl').cf_df
            eval_ares_df = load_obj(f'{data_str}_ARES_alpha_0.0_support_0.01_eval.pkl').cf_df
        else:
            eval_ares_df = load_obj(f'{data_str}_ARES_alpha_0.0_support_0.01_eval.pkl').cf_df
            eval_facts_df = load_obj(f'{data_str}_FACTS_alpha_0.0_support_0.01_eval.pkl').cf_df
        burden_df = pd.concat((eval_alpha_10_df, eval_ares_df, eval_facts_df), axis=0)
        x_burden = [methods_names['BIGRACE_dist'], methods_names['ARES'], methods_names['FACTS']]
        b0 = sns.barplot(x=burden_df['Method'], y=burden_df['Time'], ax=axes[dataset_idx], ci=None)
        b0.set_yscale("log")
        b0.set_title(f'{data_name}', fontsize=9)
        if dataset_idx == 0:
            b0.set_ylabel('Time (log) [s]')
        else:
            b0.set_ylabel('')
        b0.set_xlabel('')
        b0.set_xticklabels(x_burden, fontsize=7, va='top', ha='center')
        b0.tick_params(axis='y', labelsize=9)
        left_m = 0.09
        bottom_m = 0.25
        right_m = 0.99
        top_m = 0.87
        wspace_m = 0.125
        hspace_m = 0.175
        fig.supxlabel('Method')
        fig.subplots_adjust(left=left_m,
                    bottom=bottom_m,
                    right=right_m,
                    top=top_m,
                    wspace=wspace_m,
                    hspace=hspace_m)
    plt.savefig(results_cf_plots_dir+f'time_benchmark.pdf',format='pdf',dpi=400)

def actionability_oriented_fairness_plot(datasets, methods):
    """
    DESCRIPTION:        Obtains the plots of burden for the actionability-oriented CF obtained by CounterFair

    INPUT:
    datasets:           Names of the datasets

    OUTPUT: (None: plot stored)
    """
    methods_names = get_methods_names(methods)
    dataset_names = get_data_names(datasets)
    fig, axes = plt.subplots(nrows=len(datasets), ncols=1, figsize=(7, 8), gridspec_kw={'height_ratios': [1.5, 1.5, 1.5, 1.5, 1.5, 2]})
    x_alphas = ['$\\alpha=0.1$', '$\\alpha=0.5$', '$\\alpha=1.0$', 'Fair Recourse']
    for dataset_idx in range(len(datasets)):
        data_str = datasets[dataset_idx]
        data_name = dataset_names[data_str]
        eval_dev = load_obj(f'{data_str}_BIGRACE_dev_dist_dev_eval.pkl')
        eval_alpha_01 = load_obj(f'{data_str}_BIGRACE_dist_alpha_0.1_eval.pkl')
        eval_alpha_05 = load_obj(f'{data_str}_BIGRACE_dist_alpha_0.5_eval.pkl')
        eval_alpha_10 = load_obj(f'{data_str}_BIGRACE_dist_alpha_1.0_eval.pkl')
        eval_alpha_10_df = eval_alpha_10.cf_df
        eval_alpha_05_df = eval_alpha_05.cf_df
        eval_alpha_01_df = eval_alpha_01.cf_df
        eval_dev_df = eval_dev.cf_df
        eval_dev_df['alpha'] = ['dev']*len(eval_dev_df)
        all_df = pd.concat((eval_alpha_01_df, eval_alpha_05_df, eval_alpha_10_df, eval_dev_df), axis=0)
        sns.barplot(x=all_df['alpha'], y=all_df['Distance'], hue=all_df['Sensitive group'], ax=axes[dataset_idx], estimator=sum, ci=None)
        xticklabels_dist = [methods_names['BIGRACE_dist'], methods_names['BIGRACE_dev_dist']]
        axes[dataset_idx].set_xticklabels(x_alphas)
        if data_str == 'adult':
            axes[dataset_idx].legend(frameon=False, prop={'size': 7.5}, ncol=1, loc='upper left', bbox_to_anchor=(0.44,1.05))
        else:
            axes[dataset_idx].legend(frameon=False, prop={'size': 8})
        axes[dataset_idx].set_xlabel(None)
        axes[dataset_idx].set_ylabel(f'{data_name}\nBurden'+r' ($AWB^{s_k}$)', fontsize=12)
    fig.subplots_adjust(left=0.11,
                    bottom=0.03,
                    right=0.99,
                    top=0.99,
                    wspace=0.15,
                    hspace=0.175)
    plt.savefig(results_cf_plots_dir+'actionability_oriented_counterfair.pdf',format='pdf',dpi=400)

def parallel_coordinates(data_name, data, data_mode, features, mean_minus_std_list, mean_plus_std_list, min_all, max_all):

    bin_cat_feat = {}
    if data_name == 'Dutch':
        bin_cat_feat['Sex'] = ['Male','Female']
        bin_cat_feat['HouseholdPosition'] = ['Spouse1','Partner','Married','Reference1','Reference2','Spouse2','Parent','Spouse3']
        bin_cat_feat['HouseholdSize'] = ['1p','2p','3p','4p','5p','6p']
        bin_cat_feat['Country'] = ['NL','EU','World']
        bin_cat_feat['EconomicStatus'] = ['WorkStudent','WorkNotCurrently','WorkHouse']
        bin_cat_feat['CurEcoActivity'] = ['Retail','RealState','Health','Industry','Education',
                                          'Public','Transport','Community','Tourism','Finance',
                                          'Agriculture','Construction']
        bin_cat_feat['MaritalStatus'] = ['Single','Married','Widowed','Divorced']
    elif data_name == 'German':
        bin_cat_feat['Sex'] = ['Male','Female']
        bin_cat_feat['Single'] = ['No','Yes']
        bin_cat_feat['Unemployed'] = ['No','Yes']
        bin_cat_feat['PurposeOfLoan'] = ['Business','Education','Electronics','Furniture','HomeAppliances',
                                         'NewCar','Other','Repairs','Retraining','UsedCar']
        bin_cat_feat['InstallmentRate'] = ['1%','2%','3%','4%']
        bin_cat_feat['Housing'] = ['Owns','Rents','Other']
    elif data_name == 'Athlete':
        bin_cat_feat['Sex'] = ['Male','Female']
        bin_cat_feat['Diet'] = ['Vegan','Vegetarian','Pescetarian','Omnivore']
        bin_cat_feat['Sport'] = ['Football','Running','Swimming','Shooting']
        bin_cat_feat['TrainingTime'] = ['3/week','4/week','5/week','6/week']
    elif data_name == 'Student':
        bin_cat_feat['School'] = ['GP','MS']
        bin_cat_feat['Sex'] = ['Male','Female']
        bin_cat_feat['AgeGroup'] = ['<18','>=18']
        bin_cat_feat['FamilySize'] = ['LE3','GE3']
        bin_cat_feat['ParentStatus'] = ['A','T']
        bin_cat_feat['SchoolSupport'] = ['No','Yes']
        bin_cat_feat['FamilySupport'] = ['No','Yes']
        bin_cat_feat['ExtraPaid'] = ['No','Yes']
        bin_cat_feat['ExtraActivities'] = ['No','Yes']
        bin_cat_feat['Nursery'] = ['No','Yes']
        bin_cat_feat['HigherEdu'] = ['No','Yes']
        bin_cat_feat['Internet'] = ['No','Yes']
        bin_cat_feat['Romantic'] = ['No','Yes']
        bin_cat_feat['MotherJob'] = ['AtHome','Health','Other','Services','Teacher']
        bin_cat_feat['FatherJob'] = ['AtHome','Health','Other','Services','Teacher']
        bin_cat_feat['SchoolReason'] = ['Course','Home','Other','Reputation']
    elif data_name == 'Compas':
        bin_cat_feat['Race'] = ['Caucasian','African-American']
        bin_cat_feat['Sex'] = ['Male','Female']
        bin_cat_feat['ChargeDegree'] = ['Misdemeanor','Felony']
        bin_cat_feat['AgeGroup'] = ['Less than 25','25 - 45','Greater than 45']
    elif data_name == 'Adult':
        bin_cat_feat['Sex'] = ['Male','Female']
        bin_cat_feat['NativeCountry'] = ['US','Non-US']
        bin_cat_feat['Race'] = ['White','Non-white']
        bin_cat_feat['AgeGroup'] = ['Less than 25','25 - 60','Greater than 60']
        bin_cat_feat['WorkClass'] = ['Federal-gov','Local-gov','Private','Self-emp-inc','Self-emp-not-inc','State-gov','Without-pay']
        bin_cat_feat['MaritalStatus'] = ['Divorced','Married-AF-spouse','Married-civ-spouse','Married-spouse-absent','Never-married','Separated','Widowed']
        bin_cat_feat['Occupation'] = ['Adm-clerical','Armed-Forces','Craft-repair','Exec-managerial','Farming-fishing','Handlers-cleaners','Machine-op-inspct',
                                      'Other-service','Priv-house-serv','Prof-specialty','Protective-serv','Sales','Tech-support','Transport-moving']
        bin_cat_feat['Relationship'] = ['Husband','Not-in-family','Other-relative','Own-child','Unmarried','Wife']
        
    data_new_mean = data[:,:-1]
    data_new_mode = data_mode[:,:-1]
    fig, host = plt.subplots(figsize=(7, 3))

    N = len(data_new_mean)
    category_list = []
    group_values = np.unique(data[:,-1])
    for group_value in group_values:
        N_group = np.sum(data[:,-1] == group_value)
        category_list.append(np.full(N_group, int(group_value)))
    category = np.concatenate(category_list)

    # data_new_min = min_all[:-1]
    # data_new_max = max_all[:-1]
    # data_new_range = data_new_max - data_new_min
    # for feature_idx in range(len(data_new_range)):
    #     if np.isclose(data_new_range[feature_idx], 0.0):
    #         data_new_min[feature_idx] = 0.0
    #         data_new_max[feature_idx] = 1.0
    #         data_new_range[feature_idx] = 1.0
    # data_new_min -= data_new_range * 0.05
    # data_new_max += data_new_range * 0.05
    # data_new_range = data_new_max - data_new_min

    data_new_min = np.array([0]*data_new_mean.shape[1])
    data_new_max = np.array([1]*data_new_mean.shape[1])
    data_new_range = data_new_max - data_new_min
    for feature_idx in range(len(data_new_range)):
        feat_i = features[feature_idx]
        if feat_i in bin_cat_feat.keys():
            list_feat_val = bin_cat_feat[feat_i]
            data_new_min[feature_idx] = min_all[feature_idx]
            data_new_max[feature_idx] = 1 if ((data_name == 'Athlete') & (feature_idx == 0)) or ((data_name == 'German') & (feature_idx == 1)) else len(list_feat_val)
        else:
            data_new_min[feature_idx] = min_all[feature_idx]
            data_new_max[feature_idx] = max_all[feature_idx]
        if np.isclose(data_new_range[feature_idx], 0.0):
            data_new_min[feature_idx] = 0.0
            data_new_max[feature_idx] = 1.0
    # data_new_min -= data_new_range * 0.01
    # data_new_max += data_new_range * 0.01
    data_new_range = data_new_max - data_new_min

    norm_data = np.zeros_like(data_new_mean)
    norm_data_mean = np.zeros_like(data_new_mean)
    norm_data_mode = np.zeros_like(data_new_mode)
    # norm_data_mean[:, 0] = data_new_mean[:, 0]
    # norm_data_mode[:, 0] = data_new_mode[:, 0]

    # norm_data[:, 1:] = (data_new[:, 1:] - data_new_min[1:]) / data_new_range[1:] * data_new_range[0] + data_new_min[0]

    for feat_idx in range(len(features)):
        norm_data_mean[:, feat_idx] = (data_new_mean[:, feat_idx] - data_new_min[feat_idx]) / data_new_range[feat_idx]
        norm_data_mode[:, feat_idx] = (data_new_mode[:, feat_idx] - data_new_min[feat_idx]) / data_new_range[feat_idx]
    
    for feat_idx in range(len(features)):
        feat_i = features[feat_idx]
        if feat_i in bin_cat_feat.keys():
            norm_data[:, feat_idx] = norm_data_mode[:, feat_idx]
        else:
            norm_data[:, feat_idx] = norm_data_mean[:, feat_idx]            
    
    norm_mean_minus_std_list, norm_mean_plus_std_list = [], []
    for group_idx, group in enumerate(mean_minus_std_list):
        # group = (group[:-1] - data_new_min) / data_new_range * data_new_range[0] + data_new_min[0]
        group = group[:-1]
        for feat_idx in range(len(features)):
            feat_i = features[feat_idx]
            if feat_i in bin_cat_feat.keys():
                group[feat_idx] = norm_data[group_idx, feat_idx]
            else:
                group[feat_idx] = (group[feat_idx] - data_new_min[feat_idx]) / data_new_range[feat_idx]
        group[group < 0.0] = 0.0
        norm_mean_minus_std_list.append(group)
    for group_idx, group in enumerate(mean_plus_std_list):
        # group = (group[:-1] - data_new_min) / data_new_range * data_new_range[0] + data_new_min[0]
        group = group[:-1]
        for feat_idx in range(len(features)):
            feat_i = features[feat_idx]
            if feat_i in bin_cat_feat.keys():
                group[feat_idx] = norm_data[group_idx, feat_idx]
            else:
                group[feat_idx] = (group[feat_idx] - data_new_min[feat_idx]) / data_new_range[feat_idx]
        group[group < 0.0] = 0.0
        norm_mean_plus_std_list.append(group)
    norm_mean_minus_std_np = np.concatenate([norm_mean_minus_std_list]).astype(float)
    norm_mean_plus_std_np = np.concatenate([norm_mean_plus_std_list]).astype(float)

    axes = [host] + [host.twinx() for i in range(data_new_mean.shape[1] - 1)]
    for i, ax in enumerate(axes):
        ax.set_ylim(data_new_min[i], data_new_max[i])
        ax.spines['top'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        if ax != axes:
            ax.yaxis.set_ticks_position('right')
            ax.spines["right"].set_position(("axes", i / (data_new_mean.shape[1] - 1)))

    host.set_xlim(0, data_new_mean.shape[1] - 1)
    host.set_xticks(range(data_new_mean.shape[1]))
    host.set_xticklabels(features, fontsize=12, rotation=20, va='bottom')
    host.tick_params(axis='x', which='major', pad=35)
    host.spines['right'].set_visible(False)
    host.xaxis.tick_bottom()
    # host.set_title(f'{data_name}: CounterFair subgroups with $\\alpha = 0.1$', fontsize=16)

    colors = colors_list
    used_colors = []
    for j in range(N):
        color_to_use = colors[(category[j] - 1) % len(colors)]
        if color_to_use not in used_colors:
            used_colors.append(color_to_use)
        host.plot(range(data_new_mean.shape[1]), norm_data[j,:], c=color_to_use, linestyle=':', marker='o')
    for i in range(len(used_colors)):
        host.fill_between(range(data_new_mean.shape[1]), norm_mean_minus_std_np[i], norm_mean_plus_std_np[i], color=used_colors[i], alpha=0.2)
    
    for feat_idx in range(len(features)):
        feat_i = features[feat_idx]
        if feat_i in bin_cat_feat.keys():
            list_feat_val = bin_cat_feat[feat_i]
        else:
            list_feat_val = axes[feat_idx].get_yticklabels()
        feat_val_positions = np.linspace(0, 1, len(list_feat_val))
        axes[feat_idx].set_yticks([])
        axes[feat_idx].set_yticks(feat_val_positions)
        axes[feat_idx].set_yticklabels(list_feat_val, fontsize=10)
        axes[feat_idx].set_ylim(min(feat_val_positions)-0.05, max(feat_val_positions)+0.05)

    handle_list = []
    # for i in range(len(used_colors)):
    #     handle = Line2D([0], [0], color=used_colors[i], lw=2, label=f'Subgroup {int(i+1)}')
    #     handle_list.append(handle)
    # host.legend(handles=handle_list)
    # legend_elements = create_boxplot_handles(protected_feat, original_x_df, colors_list)
    # ax[dataset_idx, method_idx].legend(handles=legend_elements)
    fig.subplots_adjust(left=0.025,
                    bottom=0.2,
                    right=0.85,
                    top=0.95,
                    wspace=0.2,
                    hspace=0.2)
    return plt

def parallel_plots_alpha_01(datasets):
    """
    Plots parallel coordinates for each of the groups found
    """
    def get_original_instances_for_cf(cf, eval_df, group_idx):
        """
        Gets the unique original instances for the CFs given
        """
        indices = []
        eval_cfs = np.concatenate((eval_df['cf'].values), axis=0)
        for i, cf_in_eval in enumerate(eval_cfs):
            if np.array_equal(cf_in_eval, cf):
                indices.append(i)
        original_instances_with_cf = eval_df.iloc[indices]['centroid']
        sensitive_group = group_idx
        original_instances_with_cf = [i[:-1] for i in original_instances_with_cf]
        original_instances_with_cf_with_sensitive_group = [np.concatenate([i,[sensitive_group]]) for i in original_instances_with_cf]
        original_instances_with_cf_with_sensitive_group = np.concatenate([original_instances_with_cf_with_sensitive_group], axis=0)
        return original_instances_with_cf_with_sensitive_group

    dataset_names = get_data_names(datasets)
    for dataset_idx in range(len(datasets)):
        data_str = datasets[dataset_idx]
        data_name = dataset_names[data_str]
        eval_alpha_01 = load_obj(f'{data_str}_CounterFair_dist_alpha_0.0_support_0.01_eval.pkl')
        eval_alpha_01_df = eval_alpha_01.cf_df
        original_features = list(eval_alpha_01.raw_data_cols)
        labels_dict = {}
        for feature in original_features:
            labels_dict.update({feature:feature})
        labels_dict.update({'sensitive_group':'Subgroup'})
        features_with_sensitive_group = list(eval_alpha_01.raw_data_cols)
        unique_cfs_np_array = np.unique(np.concatenate((eval_alpha_01_df['cf'].values), axis=0), axis=0)
        group_idx = 1
        colors_dict = {}
        features_with_sensitive_group.extend(['sensitive_group'])
        compilation_mean_np_list, compilation_mode_np_list, mean_minus_std_list, mean_plus_std_list = [], [], [], []
        compilation_all_df = pd.DataFrame(columns=original_features)
        len_unique_groups = len(unique_cfs_np_array) if len(unique_cfs_np_array) <= 25 else 25
        if data_name == 'Adult':
            half_len_unique_groups = int(0.5*(len_unique_groups))
            for unique_cf_idx in list(range(0,half_len_unique_groups)) + list(range(len(unique_cfs_np_array)-half_len_unique_groups,len(unique_cfs_np_array))):
                unique_cf = unique_cfs_np_array[unique_cf_idx]
                original_instances_with_cf_with_sensitive_group = get_original_instances_for_cf(unique_cf, eval_alpha_01_df, group_idx)
                original_instances_with_cf_with_sensitive_group_df = pd.DataFrame(data=original_instances_with_cf_with_sensitive_group, columns=features_with_sensitive_group)
                original_instances_with_cf_with_sensitive_group_df[original_features] = original_instances_with_cf_with_sensitive_group_df[original_features].apply(pd.to_numeric)
                mean_feature_value_per_group = np.mean(original_instances_with_cf_with_sensitive_group_df.values, axis=0)
                mode_feature_value_per_group = original_instances_with_cf_with_sensitive_group_df.mode(axis=0).values[0]
                std_feature_value_per_group = np.std(original_instances_with_cf_with_sensitive_group_df.values, axis=0)
                mean_minus_std_feature_value_per_group = mean_feature_value_per_group - 0.5*std_feature_value_per_group
                mean_plus_std_feature_value_per_group = mean_feature_value_per_group + 0.5*std_feature_value_per_group
                compilation_mean_np_list.append(mean_feature_value_per_group)
                compilation_mode_np_list.append(mode_feature_value_per_group)
                mean_minus_std_list.append(mean_minus_std_feature_value_per_group)
                mean_plus_std_list.append(mean_plus_std_feature_value_per_group)
                colors_dict.update({group_idx:colors_list[group_idx - 1]})
                compilation_all_df = pd.concat([compilation_all_df, original_instances_with_cf_with_sensitive_group_df], axis=0)
                group_idx += 1
            min_all = np.min(compilation_all_df, axis=0).values
            max_all = np.max(compilation_all_df, axis=0).values
            compilation_mean_np = np.concatenate([compilation_mean_np_list])
            compilation_mode_np = np.concatenate([compilation_mode_np_list])
        else:
            for unique_cf_idx in range(len_unique_groups):
                unique_cf = unique_cfs_np_array[unique_cf_idx]
                original_instances_with_cf_with_sensitive_group = get_original_instances_for_cf(unique_cf, eval_alpha_01_df, group_idx)
                original_instances_with_cf_with_sensitive_group_df = pd.DataFrame(data=original_instances_with_cf_with_sensitive_group, columns=features_with_sensitive_group)
                original_instances_with_cf_with_sensitive_group_df[original_features] = original_instances_with_cf_with_sensitive_group_df[original_features].apply(pd.to_numeric)
                mean_feature_value_per_group = np.mean(original_instances_with_cf_with_sensitive_group_df.values, axis=0)
                mode_feature_value_per_group = original_instances_with_cf_with_sensitive_group_df.mode(axis=0).values[0]
                std_feature_value_per_group = np.std(original_instances_with_cf_with_sensitive_group_df.values, axis=0)
                mean_minus_std_feature_value_per_group = mean_feature_value_per_group - 0.5*std_feature_value_per_group
                mean_plus_std_feature_value_per_group = mean_feature_value_per_group + 0.5*std_feature_value_per_group
                compilation_mean_np_list.append(mean_feature_value_per_group)
                compilation_mode_np_list.append(mode_feature_value_per_group)
                mean_minus_std_list.append(mean_minus_std_feature_value_per_group)
                mean_plus_std_list.append(mean_plus_std_feature_value_per_group)
                colors_dict.update({group_idx:colors_list[group_idx - 1]})
                compilation_all_df = pd.concat([compilation_all_df, original_instances_with_cf_with_sensitive_group_df], axis=0)
                group_idx += 1
            min_all = np.min(compilation_all_df, axis=0).values
            max_all = np.max(compilation_all_df, axis=0).values
            compilation_mean_np = np.concatenate([compilation_mean_np_list])
            compilation_mode_np = np.concatenate([compilation_mode_np_list])
        parallel_coordinates(data_name, compilation_mean_np, compilation_mode_np, original_features, mean_minus_std_list, mean_plus_std_list, min_all, max_all).savefig(results_cf_plots_dir+str(data_str)+'_subgroups_details_counterfair.pdf', format='pdf', dpi=400)

def get_subgroup_name(feat_protected, subgroup_instance):
    """
    Method to obtain the name string for a given subgroup
    """
    feat_protected_list = list(feat_protected.keys())
    string_group = ""
    for feat_key in feat_protected_list:
        feat_value = subgroup_instance[feat_key]
        feat_value_name = feat_protected[feat_key][feat_value]
        string_to_add = f'{feat_key}: {feat_value_name}'
        if string_group == "":
            string_group = string_group + string_to_add
        else:
            string_group = string_group + ' | ' + string_to_add
    return string_group

def get_unique_cfs_instance_dict(graph_nodes, eval_alpha_df, original_features):
    """
    Method that obtains the unique CFs and a dictionary of instances per CF
    """
    unique_cf_list, instance_dict = [], {}
    for n in range(len(graph_nodes)):
        unique_cf_list.append(eval_alpha_df[eval_alpha_df['graph_node'] == graph_nodes[n]]['cf'].iloc[0][0])
        original_instance_array = np.array(list(eval_alpha_df[eval_alpha_df['graph_node'] == graph_nodes[n]]['centroid']))[:,:-1]
        instance_dict[n] = pd.DataFrame(data=original_instance_array, columns=original_features)
    return instance_dict

def get_test_data(data_str):
    """
    Method to estimate the number of total test instances
    """
    seed_int = 54321           # Seed integer value
    np.random.seed(seed_int)
    train_fraction = 0.7
    step = 0.01
    data = load_dataset(data_str, train_fraction, seed_int, step)
    return data.test_df

def modify_graph_nodes(original_cfs, eval_alpha_01_df):
    """
    Method that updates the graph node in the evaluator pandas DF
    """
    count=0
    eval_alpha_01_df['graph_node'] = 0
    for row_index_original in range(len(original_cfs)):
        original_cf_instance = original_cfs[row_index_original]
        for row_index in eval_alpha_01_df.index:
            row = eval_alpha_01_df.loc[row_index,:]
            cf_row = row['cf'][0]
            if np.array_equal(original_cf_instance, cf_row):
                eval_alpha_01_df.loc[row_index,'graph_node'] = count
        count+=1
    return eval_alpha_01_df

def pie_chart_subgroup_relevance(datasets):
    """
    Plots parallel coordinates for each of the groups found
    """
    dataset_names = get_data_names(datasets)
    for dataset_idx in range(len(datasets)):
        data_str = datasets[dataset_idx]
        data_name = dataset_names[data_str]
        eval_alpha_01 = load_obj(f'{data_str}_CounterFair_dist_alpha_0.1_support_0.01_eval.pkl')
        original_features = eval_alpha_01.raw_data_cols
        eval_alpha_01_df = eval_alpha_01.cf_df
        if 'adult' in data_str or 'dutch' in data_str:
            test_df = get_test_data(data_str)
            test_number_instances = len(test_df)
        else:
            test_number_instances = eval_alpha_01.test_number_instances
        feat_protected = eval_alpha_01.feat_protected
        total_false_negatives = len(eval_alpha_01_df)
        sensitive_groups = list(np.unique(eval_alpha_01_df['Sensitive group']))
        original_cfs = np.unique(list(eval_alpha_01_df['cf'].values), axis=0)[:,0,:]
        graph_nodes = list(range(len(original_cfs)))
        eval_alpha_01_df = modify_graph_nodes(original_cfs, eval_alpha_01_df)
        instance_dict = get_unique_cfs_instance_dict(graph_nodes, eval_alpha_01_df, original_features)
        subgroup_lengths = {}
        string_groups_save = []
        # test_minus_false_negatives = test_number_instances - total_false_negatives
        # subgroup_lengths['Remaining Test Instances'] = test_minus_false_negatives
        if original_cfs.shape[0] == len(sensitive_groups):
            print('Subgroups equal the sensitive feature groups!')
            for sensitive_group in sensitive_groups:
                subgroup_lengths[sensitive_group] = len(eval_alpha_01_df[eval_alpha_01_df['Sensitive group'] == sensitive_group])
        else:
            print('Subgroups NOT equal to the sensitive feature groups')
            if data_str == 'adult':
                graph_nodes = [2, 8, 10, 14, 19, 21, 24, 29, 52, 60]
            elif data_str == 'student':
                graph_nodes = [0, 1, 2, 4]
            for n in graph_nodes:
                a = n
                subgroup_df = instance_dict[n]
                len_subgroup = len(subgroup_df)
                feat_protected_list = list(feat_protected.keys())
                subgroup_instance = subgroup_df.loc[0, feat_protected_list]
                if data_str == 'student' and n == 4:
                    a = 3
                elif data_str == 'adult' and n > 8:
                    a = n-1
                aux_string = r'$G_{%s} $ ' %a
                string_group = aux_string + f' ({len_subgroup})'
                string_group_save = aux_string + get_subgroup_name(feat_protected, subgroup_instance) + f' ({len_subgroup})'
                subgroup_lengths[string_group] = len(eval_alpha_01_df[eval_alpha_01_df['graph_node'] == n])
                string_groups_save.append(string_group_save)
        with open(results_cf_plots_dir+f'pie_chart_subgroup_relevance_{data_name}_subgroup_data.txt', mode='a', encoding='utf-8') as myfile:
            myfile.write('\n'.join(str(line) for line in string_groups_save))
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(subgroup_lengths.values(), labels=subgroup_lengths.keys(), autopct='%1.1f%%', pctdistance=0.9, labeldistance=1.1)
        ax.set_title(data_name)
        # fig.subplots_adjust(left=0.1,
        #             bottom=0.03,
        #             right=0.99,
        #             top=0.99,
        #             wspace=0.1,
        #             hspace=0.1)
        plt.tight_layout()
        plt.savefig(results_cf_plots_dir+f'pie_chart_subgroup_relevance_{data_name}.pdf',format='pdf',dpi=400)

def fnr_per_subgroup():
    """
    Method to bar plot the FNR per sensitive subgroup
    """
    def count_instances_subgroup(subgroup_instance, test_df, feat_protected):
        """
        Gets the amount of instances from the subgroup
        """
        feat_protected_list = list(feat_protected.keys())
        instance_feat_value = subgroup_instance[feat_protected_list].values
        test_df_feat_protected = test_df[feat_protected_list].values
        count = 0
        for row in test_df_feat_protected:
            if all(row == instance_feat_value):
                count+=1
        return count

    dataset_names = get_data_names(datasets)
    for dataset_idx in range(len(datasets)):
        data_str = datasets[dataset_idx]
        data_name = dataset_names[data_str]
        eval_alpha_01 = load_obj(f'{data_str}_CounterFair_dist_alpha_0.1_support_0.01_eval.pkl')
        original_features = eval_alpha_01.raw_data_cols
        eval_alpha_01_df = eval_alpha_01.cf_df
        feat_protected = eval_alpha_01.feat_protected
        sensitive_groups = list(np.unique(eval_alpha_01_df['Sensitive group']))
        original_cfs = np.unique(list(eval_alpha_01_df['cf'].values), axis=0)[:,0,:]
        graph_nodes = list(range(len(original_cfs)))
        eval_alpha_01_df = modify_graph_nodes(original_cfs, eval_alpha_01_df)
        instance_dict = get_unique_cfs_instance_dict(graph_nodes, eval_alpha_01_df, original_features)
        if original_cfs.shape[0] == len(sensitive_groups):
            print('Subgroups equal the sensitive feature groups!')
        else:
            print('Subgroups NOT equal to the sensitive feature groups')
        subgroup_data = {}
        if 'adult' in data_str or 'dutch' in data_str:
            test_df = get_test_data(data_str)
        else:
            test_df = eval_alpha_01.test_df
        for n in range(len(graph_nodes)):
            subgroup_df = instance_dict[n]
            feat_protected_list = list(feat_protected.keys())
            subgroup_instance = subgroup_df.loc[0, feat_protected_list]
            count_subgroup_total_instances = count_instances_subgroup(subgroup_instance, test_df, feat_protected)
            subgroup_len = len(subgroup_df)
            aux_string = r'$G_{%s} $ ' %n
            string_group = aux_string + get_subgroup_name(feat_protected, subgroup_instance) + f' ({subgroup_len})'
            string_group = aux_string + get_subgroup_name(feat_protected, subgroup_instance) + f' ({subgroup_len})'
            subgroup_data[string_group] = subgroup_len/count_subgroup_total_instances
        fig, ax = plt.subplots()
        ax.bar(subgroup_data.keys(), height=subgroup_data.values())
        ax.set_title(data_name)
        ax.set_ylabel(r'FNR per Subgroup $G_n$')
        ax.set_xlabel(r'Subgroup $G_n$')
        ax.set_xticklabels(subgroup_data.keys(), rotation = 15, ha='center')
        # fig.subplots_adjust(left=0.1,
        #             bottom=0.03,
        #             right=0.99,
        #             top=0.99,
        #             wspace=0.1,
        #             hspace=0.1)
        plt.tight_layout()
        plt.savefig(results_cf_plots_dir+f'FNR_per_subgroup_{data_name}.pdf',format='pdf',dpi=400)

def fnr_per_subgroup_vs_group():
    """
    Method to bar plot the FNR per sensitive subgroup
    """
    def count_instances_group(subgroup_instance, test_df, feat):
        """
        Method to count the instances in the group
        """
        subgroup_feat = subgroup_instance[feat]
        test_df_feat = test_df[feat].values
        count = 0
        for row in test_df_feat:
            if row == subgroup_feat:
                count+=1
        return count
    
    def count_instances_subgroup(subgroup_instance, test_df, feat_protected):
        """
        Gets the amount of instances from the subgroup
        """
        feat_protected_list = list(feat_protected.keys())
        instance_feat_value = subgroup_instance[feat_protected_list].values
        test_df_feat_protected = test_df[feat_protected_list].values
        count = 0
        for row in test_df_feat_protected:
            if all(row == instance_feat_value):
                count+=1
        return count
    
    def count_instances_subgroup_feat(subgroup_instance, original_instances_df, feat):
        """
        Gets the amount of false instances in the feature group of the instances
        """
        subgroup_feat = subgroup_instance[feat]
        original_instances_feat_df = original_instances_df[feat].values
        count = 0
        for row in original_instances_feat_df:
            if row == subgroup_feat:
                count+=1
        return count

    dataset_names = get_data_names(datasets)
    for dataset_idx in range(len(datasets)):
        data_str = datasets[dataset_idx]
        data_name = dataset_names[data_str]
        eval_alpha_01 = load_obj(f'{data_str}_CounterFair_dist_alpha_0.1_support_0.01_eval.pkl')
        original_features = eval_alpha_01.raw_data_cols
        eval_alpha_01_df = eval_alpha_01.cf_df
        feat_protected = eval_alpha_01.feat_protected
        sensitive_groups = list(np.unique(eval_alpha_01_df['Sensitive group']))
        original_cfs = np.unique(list(eval_alpha_01_df['cf'].values), axis=0)[:,0,:]
        graph_nodes = list(range(len(original_cfs)))
        eval_alpha_01_df = modify_graph_nodes(original_cfs, eval_alpha_01_df)
        instance_dict = get_unique_cfs_instance_dict(graph_nodes, eval_alpha_01_df, original_features)
        original_instance_array = np.array(list(eval_alpha_01_df['centroid']))[:,:-1]
        original_instance_df = pd.DataFrame(data=original_instance_array, columns=original_features)
        if original_cfs.shape[0] == len(sensitive_groups):
            print('Subgroups equal the sensitive feature groups!')
        else:
            print('Subgroups NOT equal to the sensitive feature groups')
        if 'adult' in data_str or 'dutch' in data_str:
            test_df = get_test_data(data_str)
        else:
            test_df = eval_alpha_01.test_df
        for n in range(len(graph_nodes)):
            subgroup_data = {}
            subgroup_df = instance_dict[n]
            if data_str == 'student' and n == 4:
                subgroup_df = subgroup_df.iloc[:9]
            feat_protected_list = list(feat_protected.keys())
            subgroup_instance = subgroup_df.loc[0, feat_protected_list]
            count_subgroup_total_instances = count_instances_subgroup(subgroup_instance, test_df, feat_protected)
            subgroup_len = len(subgroup_df)
            aux_string = r'$G_{%s} $ ' %n
            string_subgroup = aux_string + get_subgroup_name(feat_protected, subgroup_instance) + f' ({subgroup_len})'
            subgroup_data[string_subgroup] = subgroup_len/count_subgroup_total_instances
            for feat in feat_protected_list:
                feat_count_false_neg_group = count_instances_subgroup_feat(subgroup_instance, original_instance_df, feat)
                feat_count_group_total_instances = count_instances_group(subgroup_instance, test_df, feat)
                feat_value = subgroup_instance[feat]
                feat_value_name = feat_protected[feat][feat_value]
                string_to_add = f'{feat}: {feat_value_name}'
                subgroup_data[string_to_add] = feat_count_false_neg_group/feat_count_group_total_instances
            fig, ax = plt.subplots()
            ax.bar(subgroup_data.keys(), height=subgroup_data.values())
            ax.set_title(data_name)
            ax.set_ylabel(r'FNR')
            ax.set_xlabel(r'Subgroups $G_n$ and Sensitive Groups $s_k$')
            ax.set_xticklabels(subgroup_data.keys(), rotation = 15, ha='center')
            # fig.subplots_adjust(left=0.1,
            #             bottom=0.03,
            #             right=0.99,
            #             top=0.99,
            #             wspace=0.1,
            #             hspace=0.1)
            plt.tight_layout()
            plt.savefig(results_cf_plots_dir+f'FNR_per_subgroup_{n}_vs_group_{data_name}.pdf',format='pdf',dpi=400)


def get_subgroup_name(feat_protected, subgroup_instance):
    """
    Method to obtain the name string for a given subgroup
    """
    feat_protected_list = list(feat_protected.keys())
    string_group = ""
    for feat_key in feat_protected_list:
        feat_value = subgroup_instance[feat_key]
        feat_value_name = feat_protected[feat_key][feat_value]
        string_to_add = f'{feat_key}: {feat_value_name}'
        if string_group == "":
            string_group = string_group + string_to_add
        else:
            string_group = string_group + ' | ' + string_to_add
    return string_group

def get_unique_cfs_instance_dict(graph_nodes, eval_alpha_df, original_features):
    """
    Method that obtains the unique CFs and a dictionary of instances per CF
    """
    unique_cf_list, instance_dict = [], {}
    for n in range(len(graph_nodes)):
        unique_cf_list.append(eval_alpha_df[eval_alpha_df['graph_node'] == graph_nodes[n]]['cf'].iloc[0][0])
        original_instance_array = np.array(list(eval_alpha_df[eval_alpha_df['graph_node'] == graph_nodes[n]]['centroid']))[:,:-1]
        instance_dict[n] = pd.DataFrame(data=original_instance_array, columns=original_features)
    return instance_dict

def get_test_data(data_str):
    """
    Method to estimate the number of total test instances
    """
    seed_int = 54321           # Seed integer value
    np.random.seed(seed_int)
    train_fraction = 0.7
    step = 0.01
    data = load_dataset(data_str, train_fraction, seed_int, step)
    return data.test_df

def get_data(data_str):
    """
    Method to estimate the number of total test instances
    """
    seed_int = 54321           # Seed integer value
    np.random.seed(seed_int)
    train_fraction = 0.7
    step = 0.01
    return load_dataset(data_str, train_fraction, seed_int, step)

def modify_graph_nodes(original_cfs, eval_alpha_01_df):
    """
    Method that updates the graph node in the evaluator pandas DF
    """
    count=0
    eval_alpha_01_df['graph_node'] = 0
    for row_index_original in range(len(original_cfs)):
        original_cf_instance = original_cfs[row_index_original]
        for row_index in eval_alpha_01_df.index:
            row = eval_alpha_01_df.loc[row_index,:]
            cf_row = row['cf'][0]
            if np.array_equal(original_cf_instance, cf_row):
                eval_alpha_01_df.loc[row_index,'graph_node'] = count
        count+=1
    return eval_alpha_01_df

def get_unique_cfs_instance_burden_dict(graph_nodes, eval_alpha_df, features, normal_features):
    """
    Method that obtains the CFs and Instances per subgroup
    """
    unique_cf_dict, unique_normal_cf_dict, instance_dict, normal_instance_dict = {}, {}, {}, {}
    for n in range(len(graph_nodes)):
        unique_cf_dict[n] = eval_alpha_df[eval_alpha_df['graph_node'] == graph_nodes[n]]['cf'].iloc[0][0]
        unique_normal_cf_dict[n] = eval_alpha_df[eval_alpha_df['graph_node'] == graph_nodes[n]]['normal_cf'].iloc[0]
        instance_array = np.array(list(eval_alpha_df[eval_alpha_df['graph_node'] == graph_nodes[n]]['centroid']))[:,:-1]
        normal_instance_array = np.array(list(eval_alpha_df[eval_alpha_df['graph_node'] == graph_nodes[n]]['normal_centroid']))
        instance_dict[n] = pd.DataFrame(data=instance_array, columns=features)
        normal_instance_dict[n] = pd.DataFrame(data=normal_instance_array, columns=normal_features)
    return unique_cf_dict, unique_normal_cf_dict, instance_dict, normal_instance_dict

def calculate_subgroup_burden(data, normal_subgroup_df, normal_cf, type='L1_L0'):
    """
    Calculate the average subgroup burden
    """
    type = 'L1_L0'
    arg_dict = {'dat': data, 'type':type}
    distances = []
    for idx in normal_subgroup_df.index:
        normal_instance = normal_subgroup_df.loc[idx].values
        dist = distance_calculation_correction(normal_instance, normal_cf, kwargs=arg_dict)
        distances.append(dist)
    return np.mean(distances)

def calculate_group_burden(data, subgroup_instance, instances_df, normal_instances_df, normal_cfs_df, feat):
    """
    Calculates the average group burden
    """
    type = 'L1_L0'
    arg_dict = {'dat': data, 'type':type}
    feat_value = subgroup_instance[feat]
    group_fn_instances_idx = instances_df[instances_df[feat] == feat_value].index
    group_normal_fn_instances = normal_instances_df.loc[group_fn_instances_idx,:]
    group_normal_cfs = normal_cfs_df.loc[group_fn_instances_idx,:]
    group_burden_list = []
    for idx in group_fn_instances_idx:
        normal_fn_instance = group_normal_fn_instances.loc[idx].values
        normal_cf = group_normal_cfs.loc[idx].values
        dist = distance_calculation_correction(normal_fn_instance, normal_cf, kwargs=arg_dict)
        group_burden_list.append(dist)
    return np.mean(group_burden_list)

def burden_per_subgroup():
    """
    Method to bar plot the burden per sensitive subgroup
    """
    dataset_names = get_data_names(datasets)
    for dataset_idx in range(len(datasets)):
        data_str = datasets[dataset_idx]
        data_name = dataset_names[data_str]
        eval_alpha_01 = load_obj(f'{data_str}_CounterFair_dist_alpha_0.1_support_0.01_eval.pkl')
        original_features = eval_alpha_01.raw_data_cols
        normal_features = eval_alpha_01.data_cols
        eval_alpha_01_df = eval_alpha_01.cf_df
        feat_protected = eval_alpha_01.feat_protected
        sensitive_groups = list(np.unique(eval_alpha_01_df['Sensitive group']))
        original_cfs = np.unique(list(eval_alpha_01_df['cf'].values), axis=0)[:,0,:]
        graph_nodes = list(range(len(original_cfs)))
        eval_alpha_01_df = modify_graph_nodes(original_cfs, eval_alpha_01_df)
        cf_dict, normal_cf_dict, instance_dict, normal_instance_dict = get_unique_cfs_instance_burden_dict(graph_nodes, eval_alpha_01_df, original_features, normal_features)
        data = get_data(data_str)
        if original_cfs.shape[0] == len(sensitive_groups):
            print('Subgroups equal the sensitive feature groups!')
        else:
            print('Subgroups NOT equal to the sensitive feature groups')
        subgroup_data = {}
        if 'adult' in data_str or 'dutch' in data_str:
            test_df = data.test_df
        else:
            test_df = eval_alpha_01.test_df
        if data_str == 'adult':
            graph_nodes = [2, 8, 10, 14, 19, 21, 24, 29, 52, 60]
        elif data_str == 'student':
            graph_nodes = [0, 1, 2, 4]
        for n in graph_nodes:
            a = n
            subgroup_df = instance_dict[n]
            normal_subgroup_df = normal_instance_dict[n]
            normal_cf_df = normal_cf_dict[n]
            feat_protected_list = list(feat_protected.keys())
            subgroup_instance = subgroup_df.loc[0, feat_protected_list]
            mean_subgroup_burden = calculate_subgroup_burden(data, normal_subgroup_df, normal_cf_df)
            subgroup_len = len(subgroup_df)
            if data_str == 'student' and n == 4:
                a = 3
            elif data_str == 'adult' and n > 8:
                a = n-1
            aux_string = r'$G_{%s} $ ' %a
            string_group = aux_string + get_subgroup_name(feat_protected, subgroup_instance) + f' ({subgroup_len})'
            subgroup_data[string_group] = mean_subgroup_burden
        fig, ax = plt.subplots()
        ax.barh(subgroup_data.keys(), width=subgroup_data.values())
        ax.set_title(data_name)
        ax.set_xlabel(r'Distance $d(X_{i},X´_{i})$ [L1 & L0]')
        ax.set_ylabel(r'Subgroup $G_n$')
        # ax.set_xticklabels(subgroup_data.keys(), rotation = 15, ha='center')
        # fig.subplots_adjust(left=0.1,
        #             bottom=0.03,
        #             right=0.99,
        #             top=0.99,
        #             wspace=0.1,
        #             hspace=0.1)
        plt.tight_layout()
        plt.savefig(results_cf_plots_dir+f'Burden_per_subgroup_{data_name}.pdf',format='pdf',dpi=400)

def burden_per_subgroup_vs_group():
    """
    Method to bar plot the burden per subgroup and compare to the burden of each group
    """

    dataset_names = get_data_names(datasets)
    for dataset_idx in range(len(datasets)):
        data_str = datasets[dataset_idx]
        data_name = dataset_names[data_str]
        eval_alpha_01 = load_obj(f'{data_str}_CounterFair_dist_alpha_0.1_support_0.01_eval.pkl')
        original_features = eval_alpha_01.raw_data_cols
        normal_features = eval_alpha_01.data_cols
        eval_alpha_01_df = eval_alpha_01.cf_df
        feat_protected = eval_alpha_01.feat_protected
        sensitive_groups = list(np.unique(eval_alpha_01_df['Sensitive group']))
        original_cfs = np.unique(list(eval_alpha_01_df['cf'].values), axis=0)[:,0,:]
        graph_nodes = list(range(len(original_cfs)))
        eval_alpha_01_df = modify_graph_nodes(original_cfs, eval_alpha_01_df)
        cf_dict, normal_cf_dict, instance_dict, normal_instance_dict = get_unique_cfs_instance_burden_dict(graph_nodes, eval_alpha_01_df, original_features, normal_features)
        instances_array = np.array(list(eval_alpha_01_df['centroid']))[:,:-1]
        instances_df = pd.DataFrame(data=instances_array, columns=original_features)
        normal_instances_array = np.array(list(eval_alpha_01_df['normal_centroid']))
        normal_instances_df = pd.DataFrame(data=normal_instances_array, columns=normal_features)
        normal_cfs_array = np.array(list(eval_alpha_01_df['normal_cf']))
        normal_cfs_df = pd.DataFrame(data=normal_cfs_array, columns=normal_features)
        data = get_data(data_str)
        if original_cfs.shape[0] == len(sensitive_groups):
            print('Subgroups equal the sensitive feature groups!')
        else:
            print('Subgroups NOT equal to the sensitive feature groups')
        if 'adult' in data_str or 'dutch' in data_str:
            test_df = data.test_df
        else:
            test_df = eval_alpha_01.test_df
        if data_str == 'adult':
            graph_nodes = [2, 8, 10, 14, 19, 21, 24, 29, 52, 60]
        elif data_str == 'student':
            graph_nodes = [0, 1, 2, 4]
        for n in graph_nodes:
            a = n
            subgroup_df = instance_dict[n]
            normal_subgroup_df = normal_instance_dict[n]
            normal_cf_df = normal_cf_dict[n]
            subgroup_len = len(subgroup_df)
            subgroup_data = {}
            feat_protected_list = list(feat_protected.keys())
            subgroup_instance = subgroup_df.loc[0, feat_protected_list]
            mean_subgroup_burden = calculate_subgroup_burden(data, normal_subgroup_df, normal_cf_df)
            if data_str == 'student' and n == 4:
                a = 3
            elif data_str == 'adult' and n > 8:
                a = n-1
            aux_string = r'$G_{%s} $ ' %a
            string_subgroup = aux_string + get_subgroup_name(feat_protected, subgroup_instance) + f' ({subgroup_len})'
            subgroup_data[string_subgroup] = mean_subgroup_burden
            for feat in feat_protected_list:             
                mean_group_burden = calculate_group_burden(data, subgroup_instance, instances_df, normal_instances_df, normal_cfs_df, feat)
                feat_value = subgroup_instance[feat]
                feat_value_name = feat_protected[feat][feat_value]
                string_to_add = f'{feat}: {feat_value_name}'
                subgroup_data[string_to_add] = mean_group_burden
            fig, ax = plt.subplots()
            ax.barh(subgroup_data.keys(), width=subgroup_data.values())
            ax.set_title(data_name)
            ax.set_xlabel(r'Distance $d(X_{i},X´_{i})$ [L1 & L0]')
            ax.set_ylabel(r'Subgroups $G_n$ and Sensitive Groups $s_k$')
            # fig.subplots_adjust(left=0.1,
            #             bottom=0.03,
            #             right=0.99,
            #             top=0.99,
            #             wspace=0.1,
            #             hspace=0.1)
            plt.tight_layout()
            plt.savefig(results_cf_plots_dir+f'Burden_per_subgroup_{a}_vs_group_{data_name}.pdf',format='pdf',dpi=400)

def effectiveness_fix_ares_facts(df, len_instances):
    """
    Method that normalizes the effectiveness calculated for ARES and FACTS
    """
    df['Effectiveness'] = df['Effectiveness']*len(df)
    df['Effectiveness'] = df['Effectiveness']/len_instances
    unique_sensitive_groups = np.unique(df['Sensitive group'])
    for sensitive_group in unique_sensitive_groups:
        sensitive_group_instances = df[df['Sensitive group'] == sensitive_group]
        effectiveness_sensitive_group_instances = df[df['Sensitive group'] == sensitive_group]['Effectiveness']/len(sensitive_group_instances)
        effectiveness_sensitive_group_instances_values = effectiveness_sensitive_group_instances.values
        df.loc[df['Sensitive group'] == sensitive_group, 'Effectiveness'] = effectiveness_sensitive_group_instances_values
    return df

def effectiveness_across_methods(datasets, methods):
    """
    DESCRIPTION:        Obtains the accuracy weighted burden for each method and each dataset

    INPUT:
    datasets:           Names of the datasets

    OUTPUT: (None: plot stored)
    """
    dataset_names = get_data_names(datasets)
    methods_names = get_methods_names(methods)
    fig, axes = plt.subplots(nrows=int(np.ceil((len(datasets)/2))), ncols=2, figsize=(7, 4))
    flatten_ax = axes.flatten()
    for dataset_idx in range(len(datasets)):
        data_str = datasets[dataset_idx]
        data_name = dataset_names[data_str]
        eval_counterfair = load_obj(f'{data_str}_BIGRACE_e_eff_eval.pkl')
        if data_str == 'student':
            eval_ares = load_obj(f'{data_str}_ARES_alpha_0.0_support_0.3_eval.pkl')
            eval_facts = load_obj(f'{data_str}_FACTS_alpha_0.0_support_0.3_eval.pkl')
        elif data_str == 'adult':
            eval_ares = load_obj(f'{data_str}_ARES_alpha_0.0_support_0.05_eval.pkl')
            eval_facts = load_obj(f'{data_str}_FACTS_alpha_0.0_support_0.05_eval.pkl')
        elif data_str == 'dutch':
            eval_facts = load_obj(f'{data_str}_FACTS_alpha_0.0_support_0.1_eval.pkl')
            eval_ares = load_obj(f'{data_str}_ARES_alpha_0.0_eval.pkl')
        else:
            eval_ares = load_obj(f'{data_str}_ARES_alpha_0.0_support_0.01_eval.pkl')
            eval_facts = load_obj(f'{data_str}_FACTS_alpha_0.0_support_0.01_eval.pkl')
        eval_counterfair_df = eval_counterfair.cf_df
        eval_ares_df = eval_ares.cf_df
        eval_facts_df = eval_facts.cf_df
        all_eval = pd.concat((eval_counterfair_df, eval_ares_df, eval_facts_df), axis=0)
        b0 = sns.barplot(x=all_eval['Method'], y=all_eval['Effectiveness'], hue=all_eval['Sensitive group'], ax=flatten_ax[dataset_idx], errwidth=0.5, capsize=0.1)
        h, l = b0.get_legend_handles_labels()
        bar_colors_dict = {}
        for idx, sensitive_group in enumerate(l):
            bar_colors_dict[sensitive_group] = h[idx][0].get_facecolor()
        xs = [methods_names['BIGRACE_e'], methods_names['ARES'], methods_names['FACTS']]
        b0.set_xticklabels(xs)
        b0.legend([], [], frameon=False)
        b0.legend(frameon=False, prop={'size': 8})
        b0.set_xlabel(None)
        b0.set_ylabel('Effectiveness'+r' ($E^{s_k}$)', fontsize=12)
        b0.set_title(f'{data_name}', fontsize=12)
    fig.subplots_adjust(left=0.01,
                    bottom=0.02,
                    right=0.99,
                    top=0.99,
                    wspace=0.2,
                    hspace=0.2)
    plt.savefig(results_cf_plots_dir+'effectiveness_all.pdf',format='pdf',dpi=400)

colors_list = ['blue', 'orange', 'green', 'red', 'purple', 'lightgreen', 'tab:brown', 'cyan', 'pink', 'black',
               'dimgray','thistle','violet','yellow','peachpuff','peru','darkcyan','lightcoral','firebrick','lightgreen',
               'limegreen','darkgreen','orangered','coral','saddlebrown']
colors_dict = {'All':'black','Male':'red','Female':'blue','White':'gainsboro','Non-white':'dimgray',
               '<25':'thistle','25-60':'violet','>60':'purple','<18':'green','>=18':'yellow','Single':'peachpuff',
               'Married':'peru','Divorced':'saddlebrown','isMarried: True':'cyan','isMarried: False':'darkcyan',
               'isMale: True':'lightcoral','isMale: False':'firebrick','Other':'lightgreen','HS':'limegreen',
               'University':'green','Graduate':'darkgreen','African-American':'orangered','Caucasian':'coral'}
mean_prop = dict(marker='D', markeredgecolor='firebrick', markerfacecolor='firebrick', markersize=2)
metric = 'proximity'

# method_box_plot(datasets, methods_to_run, 'proximity', colors_list)
# fnr_plot(datasets, colors_dict)
# burden_plot(datasets, methods_to_run, colors_dict)
# fnr_burden_plot(datasets, methods_to_run, 'proximity', colors_list)
# nawb_plot(datasets, methods_to_run, colors_dict)
# validity_groups_cf(datasets, methods_to_run)
# validity_clusters(datasets, methods_to_run)
# burden_groups_cf(datasets, methods_to_run)
# burden_cluster_cf(datasets, methods_to_run)
# nawb_groups_cf(datasets, methods_to_run)
# nawb_cluster_cf(datasets, methods_to_run)
# burden_groups_cf_bar(datasets, 'NN')
# plot_centroids_cf_proximity()
# plot_centroids_cfs_ablation_lagrange_likelihood()
# plot_centroids_cfs_ablation_alpha_beta_gamma('oulad')
# proximity_all_datasets_all_methods_plot(datasets, methods_to_run)
# proximity_across_alpha_counterfair(datasets)
# proximity_fairness_across_alpha_counterfair(datasets)
# burden_effectiveness_benchmark(datasets)
# parallel_plots_alpha_01(datasets)
pie_chart_subgroup_relevance(datasets)
# fnr_per_subgroup()
# fnr_per_subgroup_vs_group()
burden_per_subgroup()
burden_per_subgroup_vs_group()
# actionability_oriented_fairness_plot(datasets, methods_to_run)
# effectiveness_across_methods(datasets, methods_to_run)
# time_benchmark(datasets)