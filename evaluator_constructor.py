"""
Imports
"""
import numpy as np
import pandas as pd
from support import euclidean, sort_data_distance
from support import verify_feasibility
from scipy.spatial import distance_matrix
import copy

def distance_calculation(x, y, **kwargs):
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

class Evaluator():
    """
    DESCRIPTION:        Evaluator Class
    
    INPUT:
    data_obj:           Dataset object
    n_feat:             Number of examples to generate synthetically per feature
    method_str:         Name of the method to use to obtain counterfactuals
    """
    def __init__(self, data_obj, n_feat, method_str, cluster_obj):
        self.data_name = data_obj.name
        self.method_name = method_str
        self.feat_type = data_obj.feat_type
        self.feat_mutable = data_obj.feat_mutable
        self.feat_step = data_obj.feat_step
        self.feat_dir = data_obj.feat_dir
        self.feat_protected = data_obj.feat_protected
        self.binary = data_obj.binary
        self.categorical = data_obj.categorical
        self.numerical = data_obj.numerical
        self.bin_enc, self.bin_enc_cols  = data_obj.bin_enc, data_obj.bin_enc_cols
        self.cat_enc, self.cat_enc_cols  = data_obj.cat_enc, data_obj.cat_enc_cols
        self.scaler = data_obj.scaler
        self.data_cols = data_obj.processed_features
        self.raw_data_cols = data_obj.train_df.columns
        self.undesired_class = data_obj.undesired_class
        self.desired_class = 1 - self.undesired_class
        self.n_feat = n_feat
        self.cf_df = pd.DataFrame()
        self.cluster = cluster_obj
        self.test_df = data_obj.test_df
        self.epsilon = self.calculate_epsilon(data_obj)

    def search_desired_class_penalize(self, x, data):
        """
        DESCRIPTION:        Obtains the penalization for the method if no instance of the desired class is obtained as CF

        INPUT:
        x:                  Instance of interest in the correct (CARLA or normal) framework format
        data:               Dataset object

        OUTPUT:
        penalize_instance:  The furthest training instance available
        """
        data_np = data.transformed_train_np
        train_desired_class = data_np[data.train_target != self.undesired_class]
        sorted_train_x = sort_data_distance(x, train_desired_class, data.train_target[data.train_target != self.undesired_class])
        penalize_instance = sorted_train_x[-1][0]
        return penalize_instance

    def statistical_parity_eval(self, prob, length):
        """
        DESCRIPTION:        Calculates the Statistical Parity measure for each of the protected feature groups given a model

        INPUT:
        prob:               Probability dictionary
        length:             Number of instances belonging to each feature value or group

        OUTPUT:
        stat_parity:        Statistical parity measure
        """
        stat_parity = {}
        for i in self.feat_protected.keys():
            feat_names = prob[i].keys()
            feat_parity = {}
            for j in feat_names:
                j_probability = prob[i][j]
                total_others_length = np.sum([length[i][x] for x in feat_names if x != j])
                others_probability = np.sum([prob[i][x]*length[i][x] for x in feat_names if x != j]) / total_others_length
                feat_parity[j] = j_probability - others_probability
            stat_parity[i] = feat_parity
        return stat_parity

    def statistical_parity_proba(self, data_obj, model_obj):
        """
        DESCRIPTION:        Calculates the probabilities used by the Statistical Parity method

        INPUT:
        data_obj:           Dataset object
        model_obj:          Model object

        OUTPUT:
        prob_dict:          Probability dictionary
        length_dict:        Dictionary with the number of instances belonging to each feature value or group
        """
        prob_dict = {}
        length_dict = {}
        test_data = data_obj.test_df
        test_data_transformed = data_obj.transformed_test_df
        test_data_transformed_index = test_data_transformed.index
        pred = model_obj.model.predict(test_data_transformed)
        pred_df = pd.DataFrame(data=pred, index=test_data_transformed_index, columns=['prediction'])
        test_data_with_pred = pd.concat((test_data, pred_df),axis=1)
        for i in self.feat_protected.keys():
            feat_i_values = test_data_with_pred[i].unique()
            val_dict = {}
            length_val_dict = {}
            for j in feat_i_values:
                val_name = self.feat_protected[i][np.round(j,2)]
                total_feat_i_val_j = len(test_data_with_pred[test_data_with_pred[i] == j])
                total_feat_i_val_j_desired_pred = len(test_data_with_pred[(test_data_with_pred[i] == j) & (test_data_with_pred['prediction'] == self.desired_class)])
                stat_parity_feat_val = total_feat_i_val_j_desired_pred / total_feat_i_val_j
                val_dict[val_name] = stat_parity_feat_val
                length_val_dict[val_name] = total_feat_i_val_j
            prob_dict[i] = val_dict
            length_dict[i] = length_val_dict
        return prob_dict, length_dict

    def equalized_odds_eval(self, prob, length):
        """
        DESCRIPTION:        Calculates the Equalized Odds measure for each of the protected feature groups given a model

        INPUT:
        prob:               Probability dictionary
        length:             Number of instances belonging to each feature value or group

        OUTPUT:
        eq_odds:            Equalized odds measure
        """
        eq_odds = {}
        for i in self.feat_protected.keys():
            feat_val_names = prob[i].keys()
            feat_odds = {}
            for j in feat_val_names:
                j_probability_target_0, j_probability_target_1 = prob[i][j][0], prob[i][j][1]
                total_others_target_0_length = np.sum([length[i][x][0] for x in feat_val_names if x != j])
                total_others_target_1_length = np.sum([length[i][x][1] for x in feat_val_names if x != j])
                others_probability_target_0 = np.sum([prob[i][x][0]*length[i][x][0] for x in feat_val_names if x != j]) / total_others_target_0_length
                others_probability_target_1 = np.sum([prob[i][x][1]*length[i][x][1] for x in feat_val_names if x != j]) / total_others_target_1_length
                feat_odds[j] = np.abs(j_probability_target_0 - others_probability_target_0) + np.abs(j_probability_target_1 - others_probability_target_1)
            eq_odds[i] = feat_odds
        return eq_odds

    def equalized_odds_proba(self, data_obj, model_obj):
        """
        DESCRIPTION:        Calculates the probabilities used by the Equalized Odds method

        INPUT:
        data_obj:           Dataset object
        model_obj:          Model object

        OUTPUT:
        prob_dict:          Probability dictionary
        length_dict:        Dictionary with the number of instances belonging to each feature value or group
        """
        prob_dict = {}
        length_dict = {}
        test_data = data_obj.test_df
        test_data_transformed = data_obj.transformed_test_df
        test_data_transformed_index = test_data_transformed.index
        test_target = data_obj.test_target
        pred = model_obj.model.predict(test_data_transformed)
        pred_df = pd.DataFrame(data=pred, index=test_data_transformed_index, columns=['prediction'])
        target_df = pd.DataFrame(data=test_target, index=test_data_transformed_index, columns=['target'])
        test_data_with_pred_target = pd.concat((test_data, pred_df, target_df),axis=1)
        for i in self.feat_protected.keys():
            feat_i_values = test_data_with_pred_target[i].unique()
            feat_dict = {}
            length_val_dict = {}
            for j in feat_i_values:
                val_name = self.feat_protected[i][np.round(j,2)]
                target_dict = {}
                length_target_dict = {}
                for k in [0,1]:
                    data_feat_i_val_j_ground_k = test_data_with_pred_target[(test_data_with_pred_target[i] == j) & (test_data_with_pred_target['target'] == k)]
                    data_feat_i_val_j_ground_k_desired_pred = data_feat_i_val_j_ground_k[data_feat_i_val_j_ground_k['prediction'] == self.desired_class]
                    total_feat_i_val_j_ground_k = len(data_feat_i_val_j_ground_k)
                    total_feat_i_val_j_ground_k_desired_pred = len(data_feat_i_val_j_ground_k_desired_pred)
                    prob_val = total_feat_i_val_j_ground_k_desired_pred / total_feat_i_val_j_ground_k
                    target_dict[k] = prob_val
                    length_target_dict[k] = total_feat_i_val_j_ground_k
                feat_dict[val_name] = target_dict
                length_val_dict[val_name] = length_target_dict
            prob_dict[i] = feat_dict
            length_dict[i] = length_val_dict
        return prob_dict, length_dict

    def add_fairness_measures(self, data_obj, model_obj):
        """
        DESCRIPTION:        Adds the fairness metrics Statistical Parity and Equalized Odds

        INPUT:
        data_obj:           Dataset object
        model_obj:          Model object

        OUTPUT: (None: stored as class attributes)
        prob_dict:          Probability dictionary
        length_dict:        Dictionary with the number of instances belonging to each feature value or group
        """
        stat_proba, stat_length = self.statistical_parity_proba(data_obj, model_obj)
        odds_proba, odds_length = self.equalized_odds_proba(data_obj, model_obj)
        self.stat_parity = self.statistical_parity_eval(stat_proba, stat_length)
        self.eq_odds = self.equalized_odds_eval(odds_proba, odds_length)

    def add_fnr_data(self, data):
        """
        DESCRIPTION:                            Adds the desired ground truth test DataFrame and the false negative test DataFrame
        
        INPUT:
        desired_ground_truth_test_df:           Desired ground truth DataFrame
        false_undesired_test_df:                False negative test DataFrame
        transformed_false_undesired_test_df:    Transformed false negative test DataFrame

        OUTPUT: (None: stored as class attributes)
        """
        self.desired_ground_truth_test_df = data.desired_ground_truth_test_df
        self.false_undesired_test_df = data.false_undesired_test_df
        self.transformed_false_undesired_test_df = data.transformed_false_undesired_test_df

    def add_specific_x_data(self, ioi):
        """
        DESCRIPTION:        Calculates and stores x data found in the Evaluator

        INPUT:
        ioi:                Instance of interest object
        x:                  Instance of interest in Numpy array
        original_x:         Instance of interest in original format (before normalization and encoding) in DataFrame
        x_pred:             Predicted label of the instance of interest
        x_target:           Ground truth label of the instance of interest

        OUTPUT: (None: stored as class attributes)
        """
        self.x[ioi.idx] = pd.DataFrame(data=ioi.normal_x.reshape(1, -1), index=[ioi.idx], columns=self.data_cols)
        self.original_x[ioi.idx] = ioi.x
        self.x_pred[ioi.idx] = ioi.x_label
        self.x_target[ioi.idx] = ioi.x_target
        self.x_accuracy[ioi.idx] = self.accuracy(ioi.idx)

    def transform_instance(self, instance):
        """
        DESCRIPTION:            Transforms an instance to the preprocessed features

        INPUT:
        instance:               Instance of interest

        OUTPUT:
        transformed_instance:   Transformed instance of interest
        """
        instance_bin, instance_cat, instance_num = instance[self.binary], instance[self.categorical], instance[self.numerical]
        enc_instance_bin = self.bin_enc.transform(instance_bin).toarray()
        enc_instance_cat = self.cat_enc.transform(instance_cat).toarray()
        scaled_instance_num = self.scaler.transform(instance_num)
        scaled_instance_num_df = pd.DataFrame(scaled_instance_num, index=instance_num.index, columns=self.numerical)
        enc_instance_bin_df = pd.DataFrame(enc_instance_bin, index=instance_bin.index, columns=self.bin_enc_cols)
        enc_instance_cat_df = pd.DataFrame(enc_instance_cat, index=instance_cat.index, columns=self.cat_enc_cols)
        transformed_instance_df = pd.concat((enc_instance_bin_df, enc_instance_cat_df, scaled_instance_num_df), axis=1)
        return transformed_instance_df

    def inverse_transform_original(self, instance):
        """
        DESCRIPTION:            Transforms an instance to the original features
        
        INPUT:
        instance:               Instance of interest

        OUTPUT:
        original_instance_df:   Instance of interest in the original feature format
        """
        instance_index = instance.index
        original_instance_df = pd.DataFrame(index=instance_index)
        if len(self.bin_enc_cols) > 0:
            instance_bin = self.bin_enc.inverse_transform(instance[self.bin_enc_cols])
            instance_bin_pd = pd.DataFrame(data=instance_bin, index=instance_index, columns=self.binary)
            original_instance_df = pd.concat((original_instance_df, instance_bin_pd), axis=1)
        if len(self.cat_enc_cols) > 0:
            instance_cat = self.cat_enc.inverse_transform(instance[self.cat_enc_cols])
            instance_cat_pd = pd.DataFrame(data=instance_cat, index=instance_index, columns=self.categorical)
            original_instance_df = pd.concat((original_instance_df, instance_cat_pd), axis=1)
        if len(self.numerical) > 0:
            instance_num = self.scaler.inverse_transform(instance[self.numerical])
            instance_num_pd = pd.DataFrame(data=instance_num, index=instance_index, columns=self.numerical)
            original_instance_df = pd.concat((original_instance_df, instance_num_pd), axis=1)
        return original_instance_df

    def add_specific_cf_data(self, counterfactual, centroid):
        """
        DESCRIPTION:        Calculates and stores a cf method result and performance metrics into the Pandas DataFrame found in the Evaluator

        INPUT:
        counterfactual:     Counterfactual object
        """
        idx = counterfactual.ioi.idx
        cols = counterfactual.data.processed_features
        x = centroid.x
        cf, cf_time = counterfactual.cf_method.normal_x_cf, counterfactual.cf_method.run_time
        if cf is not None and not np.isnan(np.sum(cf)):
            if isinstance(cf, pd.DataFrame):
                self.cf[idx] = cf
            elif isinstance(cf, pd.Series):
                cf_np = cf.to_numpy()
                self.cf[idx] = pd.DataFrame(data=cf_np, index=[idx], columns=cols) 
            else:
                self.cf[idx] = pd.DataFrame(data=cf.reshape(1, -1), index=[idx], columns=cols)
        else:
            penalize_instance = self.search_desired_class_penalize(x, counterfactual.data)
            self.cf[idx] = pd.DataFrame(data=[penalize_instance], index=[idx], columns=cols)
        self.cf_validity[idx] = True
        self.original_cf[idx] = self.inverse_transform_original(self.cf[idx])
        self.proximity(idx)
        self.feasibility(idx)
        self.sparsity(counterfactual.data, idx)
        self.cf_time[idx] = cf_time

    def accuracy(self, idx):
        """
        DESCRIPTION:        Estimates accuracy between the target and the predicted label of x

        INPUT:
        idx:                Index of the instance of interest

        OUTPUT:
        acc:                Accuracy (agreement) between the predicted and ground truth labels 
        """
        acc = self.x_target[idx] == self.x_pred[idx]
        return acc

    def proximity(self, idx, group=None, cluster_str=None):
        """
        DESCRIPTION:        Calculates the distance between the instance of interest and the counterfactual given

        INPUT:
        idx:                Index of the instance of interest
        group:              Whether to calculate proximity w.r.t. individual counterfactual or the group counterfactual
        cluster_str:        Cluster counterfactual name

        OUTPUT: (None: stored as class attributes)
        """
        x = self.x[idx]
        if group is not None and cluster_str is None:
            cf = self.groups_cf[group]
        elif group is None and cluster_str is not None:
            cf = self.x_clusters_cf[cluster_str] 
        else:
            cf = self.cf[idx]
        if (x.columns == cf.columns).all():
            distance = np.round_(euclidean(x.to_numpy(), cf.to_numpy()), 3)
        else:
            x_copy = copy.deepcopy(x)
            x_copy = x_copy[cf.columns]
            distance = np.round_(euclidean(x_copy.to_numpy(), cf.to_numpy()), 3)
        if group is not None and cluster_str is None:
            self.group_cf_proximity.loc[idx, group] = distance
        elif group is None and cluster_str is not None:
            self.cluster_cf_proximity.loc[idx, cluster_str] = distance
        else:
            self.cf_proximity[idx] = distance

    def feasibility(self, idx, group=None, cluster_str=None):
        """
        DESCRIPTION:        Indicates whether cf is a feasible counterfactual with respect to x and the feature mutability

        INPUT:
        idx:                Index of the instance of interest
        group:              Whether to calculate feasibility w.r.t. individual counterfactual or the group counterfactual
        cluster_str:        Cluster counterfactual name

        OUTPUT: (None: stored as class attributes)
        """
        x_idx = self.x[idx]
        step = self.feat_step
        types = self.feat_type
        direc = self.feat_dir
        
        toler = 0.000001
        feasibility = True
        if group is not None and cluster_str is None:
            cf = self.groups_cf[group]
        elif group is None and cluster_str is not None:
            cf = self.x_clusters_cf[cluster_str] 
        else:
            cf = self.cf[idx]
        cf_np = cf.to_numpy()[0]
        x_np = x_idx.to_numpy()[0]
        vector = cf_np - x_np
        for i in range(len(types)):
            if types[i] == 'bin':
                if not np.isclose(cf.iloc[0,i], [0,1], atol=toler).any():
                    feasibility = False
                    break
            elif types[i] == 'num-ord':
                possible_val = np.linspace(0, 1, int(1/step[i]+1), endpoint=True)
                if not np.isclose(cf.iloc[0,i], possible_val, atol=toler).any():
                    feasibility = False
                    break
            else:
                if cf.iloc[0,i] < 0-toler or cf.iloc[0,i] > 1+toler:
                    feasibility = False
                    break
            if direc[i] == 0 and vector[i] != 0:
                feasibility = False
                break
            elif direc[i] == 'pos' and vector[i] < 0:
                feasibility = False
                break
            elif direc[i] == 'neg' and vector[i] > 0:
                feasibility = False
                break
        transformed_protected_cols = [col for col in x_idx.columns if any(feat in col for feat in self.feat_protected.keys())]
        if not np.array_equal(x_idx[transformed_protected_cols], cf[transformed_protected_cols]):
            feasibility = False
        if group is not None and cluster_str is None:
            self.group_cf_feasibility.loc[idx, group] = feasibility
        elif group is None and cluster_str is not None:
            self.cluster_cf_feasibility.loc[idx, cluster_str] = feasibility
        else:
            self.cf_feasibility[idx] = feasibility

    def sparsity(self, data_obj, idx, group=None, cluster_str=None):
        """
        DESCRIPTION:        Calculates sparsity for a given counterfactual according to x. Sparsity is 1 - the fraction of features changed in the cf. Takes the value of 1 if the number of changed features is 1

        INPUT:
        data_obj:           Dataset object
        idx:                Index of the instance of interest
        group:              Whether to calculate sparsity w.r.t. individual counterfactual or the group counterfactual
        cluster_str:        Cluster counterfactual name

        OUTPUT: (None: stored as class attributes)
        """
        x = self.x[idx]
        cat = data_obj.feat_cat
        if group is not None and cluster_str is None:
            cf = self.groups_cf[group]
        elif group is None and cluster_str is not None:
            cf = self.x_clusters_cf[cluster_str] 
        else:
            cf = self.cf[idx]
        cf_idx = cf.to_numpy()[0]
        x_idx = x.to_numpy()[0]
        unchanged_features = np.sum(np.equal(x_idx, cf_idx))
        categories_feat_changed = np.unique([cat[col] for col in x.columns if not x[col].equals(cf[col])])
        len_categories_feat_changed_unique = len([i for i in categories_feat_changed if 'cat' in i])
        unchanged_features += len_categories_feat_changed_unique
        n_changed = len(x_idx) - unchanged_features
        if n_changed == 1:
            sparsity = 1.000
        else:
            sparsity = np.round_(1 - n_changed/len(x_idx), 3)
        if group is not None and cluster_str is None:
            self.group_cf_sparsity.loc[idx, group] = sparsity
        elif group is None and cluster_str is not None:
            self.cluster_cf_sparsity.loc[idx, cluster_str] = sparsity
        else:
            self.cf_sparsity[idx] = sparsity

    def validity(self, model_obj, group):
        """
        DESCRIPTION:            Calculates the validity of the group counterfactual

        INPUT:
        model_obj:              Model object
        group:                  Sensitive groups name

        OUTPUT: (None: stored as class attributes)
        """
        pred = model_obj.model.predict(self.groups_cf[group])
        self.group_cf_validity[group] = pred != self.undesired_class

    def calculate_epsilon(self, data):
        """
        Obtains the epsilon value for the estimation of the likelihood of all the CFs obtained by the ARES method
        """
        distance = distance_matrix(data.transformed_train_np, data.transformed_train_np, p=1)
        upper_tri_distance = distance[np.triu_indices(len(data.transformed_train_np), k = 1)]
        return np.std(upper_tri_distance, ddof=1) 

    def get_likelihood(self, data, cfs):
        """
        Extracts the likelihood of all the nodes obtained
        """
        rho = {}
        cfs_keys = list(cfs.keys())
        cfs_np = np.array([cfs[i].values[0] for i in cfs.keys()])
        print(cfs_np.shape, data.transformed_train_np.shape)
        distance = distance_matrix(cfs_np, data.transformed_train_np, p=1)
        gaussian_kernel = np.exp(-(distance/self.epsilon)**2)
        sum_gaussian_kernel_col = np.sum(gaussian_kernel, axis=1)
        max_sum_gaussian_kernel_col = np.max(sum_gaussian_kernel_col)
        min_sum_gaussian_kernel_col = np.min(sum_gaussian_kernel_col)
        for cf_key_idx in range(len(cfs_keys)):
            cf_key = cfs_keys[cf_key_idx]
            rho[cf_key] = (sum_gaussian_kernel_col[cf_key_idx] - min_sum_gaussian_kernel_col)/(max_sum_gaussian_kernel_col - min_sum_gaussian_kernel_col)
        return rho
    
    # def get_effectiveness(self, data, cfs):
    #     """
    #     Extracts the effectiveness of all the nodes obtained
    #     """
    #     eta = {}
    #     len_cluster_instances = 0
    #     for c_idx in range(1, len(self.cluster.filtered_clusters_list) + 1):
    #         cluster_instances_list = self.cluster.filtered_clusters_list[c_idx - 1]
    #         len_cluster_instances += len(cluster_instances_list)
    #     for cf_key in list(cfs.keys()):
    #         sum_eta = 0
    #         cf_k = cfs[cf_key]
    #         cf_k = cf_k.values[0]
    #         for c_idx in range(1, len(self.cluster.filtered_clusters_list) + 1):
    #             cluster_instances_list = self.cluster.filtered_clusters_list[c_idx - 1]
    #             for instance_idx in cluster_instances_list:
    #                 instance = self.cluster.transformed_false_undesired_test_df.loc[instance_idx].values
    #                 sum_eta += verify_feasibility(instance, cf_k, data)
    #         eta[cf_key] = sum_eta/len_cluster_instances
    #         print(f'Highest eta value: {np.max(list(eta.values()))}')
    #     return eta

    def get_effectiveness(self, data, model, cfs):
        """
        Extracts the effectiveness of all the nodes obtained
        """
        eta = {}
        feat_val_instance_idx = self.cluster.sensitive_feat_idx_dict
        for feat in list(feat_val_instance_idx.keys()):
            for feat_value in feat_val_instance_idx[feat]:
                feat_val_instance_idx_list = feat_val_instance_idx[feat][feat_value]
                for instance_idx, cf in cfs.items():
                    cumulative_eta = 0
                    cf_normal = cf.values[0]
                    if model.model.predict(cf_normal.reshape(1, -1)) == 1 - self.undesired_class:
                        if instance_idx in feat_val_instance_idx_list:
                            instances_feat_value = data.transformed_false_undesired_test_df.loc[feat_val_instance_idx_list].values
                            len_sensitive_group = len(instances_feat_value)
                            for instance in instances_feat_value:
                                cumulative_eta += verify_feasibility(instance, cf_normal, data)/len_sensitive_group
                        else:
                            continue
                    eta[instance_idx] = cumulative_eta
        return eta

    def prepare_groups_clusters_analysis(self):
        """
        DESCRIPTION:            Preallocates the required dictionaries and DataFrames for the analysis of groups and clusters

        INPUT: (None)

        OUTPUT: (None: stored as class attributes)
        """
        self.groups_cf, self.original_groups_cf = {}, {}
        self.group_cf_proximity = pd.DataFrame(index=self.x.keys(), columns=self.x_clusters.keys())
        self.group_cf_feasibility = pd.DataFrame(index=self.x.keys(), columns=self.x_clusters.keys())
        self.group_cf_sparsity = pd.DataFrame(index=self.x.keys(), columns=self.x_clusters.keys())
        self.group_cf_validity = {}
        self.cluster_cf_proximity = pd.DataFrame(index=self.x.keys(), columns=self.x_clusters.keys())
        self.cluster_cf_feasibility = pd.DataFrame(index=self.x.keys(), columns=self.x_clusters.keys())
        self.cluster_cf_sparsity = pd.DataFrame(index=self.x.keys(), columns=self.x_clusters.keys())
        self.cluster_validity = {}
        self.cluster_cf_time = {}

    def add_groups_cf(self, data_obj, model_obj):
        """
        DESCRIPTION:            Adds the group counterfactual by finding the mean point of all counterfactuals for the false negative group of test instances and obtains the performance measures of each

        INPUT:
        data_obj:               Dataset object
        model_obj:              Model object

        OUTPUT: (None: stored as class attributes)
        """
        original_x_df = pd.concat(self.original_x.values(), axis=0)
        cf_df = pd.concat(self.cf.values(), axis=0)
        self.groups_cf['all'] = cf_df.mean(axis=0).to_frame().T
        original_all_cf = self.inverse_transform_original(self.groups_cf['all'])
        self.original_groups_cf['all'] = original_all_cf
        for idx in self.original_x.keys():
            self.proximity(idx, group='all')
            self.feasibility(idx, group='all')
            self.sparsity(data_obj, idx, group='all')
            self.validity(model_obj, group='all')
        for feat in self.feat_protected:
            feat_unique_val = original_x_df[feat].unique()
            for feat_val in feat_unique_val:
                original_x_df_feat_val = original_x_df[original_x_df[feat] == feat_val]
                feat_val_name = self.feat_protected[feat][np.round(feat_val, 2)]
                feat_values_idx = original_x_df_feat_val.index.tolist()
                cf_df_feat_val = cf_df.loc[feat_values_idx,:]
                self.groups_cf[feat_val_name] = cf_df_feat_val.mean(axis=0).to_frame().T
                original_feat_val_cf = self.inverse_transform_original(self.groups_cf[feat_val_name])
                self.original_groups_cf[feat_val_name] = original_feat_val_cf
                for idx in self.original_x.keys():
                    self.proximity(idx, group=feat_val_name)
                    self.feasibility(idx, group=feat_val_name)
                    self.sparsity(data_obj, idx, group=feat_val_name)
                    self.validity(model_obj, group=feat_val_name)
    
    def add_clusters(self):
        """
        DESCRIPTION:            Adds the clusters for all instances of interest and per sensitive group

        INPUT: (None)

        OUTPUT: (None: stored as class attributes)      
        """
        self.x_clusters, self.original_x_clusters = {}, {}
        self.x_clusters_cf, self.original_x_clusters_cf = {}, {}
        x_df = pd.concat(self.x.values(), axis=0)
        original_x_df = pd.concat(self.original_x.values(), axis=0)
        x_cluster_all = x_df.mean(axis=0).to_frame().T
        self.original_x_clusters['all'] = self.inverse_transform_original(x_cluster_all)
        self.x_clusters['all'] = self.transform_instance(self.original_x_clusters['all'])
        for feat in self.feat_protected:
            feat_unique_val = original_x_df[feat].unique()
            for feat_val in feat_unique_val:
                original_x_df_feat_val = original_x_df[original_x_df[feat] == feat_val]
                feat_val_name = self.feat_protected[feat][np.round(feat_val, 2)]
                feat_values_idx = original_x_df_feat_val.index.tolist()
                x_df_feat_val = x_df.loc[feat_values_idx,:]
                x_cluster_feat_val = x_df_feat_val.mean(axis=0).to_frame().T
                self.original_x_clusters[feat_val_name] = self.inverse_transform_original(x_cluster_feat_val)
                self.x_clusters[feat_val_name] = self.transform_instance(self.original_x_clusters[feat_val_name])
    
    def cluster_search_desired_class_penalize(self, x_cluster, data):
        """
        DESCRIPTION:        Obtains the penalization for the method if no instance of the desired class is obtained as CF

        INPUT:
        x_cluster:          Cluster of the group of interest in the correct (CARLA or normal) framework format
        data:               Dataset object

        OUTPUT:
        penalize_instance:  The furthest training instance available
        """
        data_np = data.transformed_train_np
        train_desired_class = data_np[data.train_target != self.undesired_class]
        sorted_train_x = sort_data_distance(x_cluster, train_desired_class, data.train_target[data.train_target != self.undesired_class])
        penalize_instance = sorted_train_x[-1][0]
        return penalize_instance

    def add_cf_data(self, counterfactual):
        """
        DESCRIPTION:            Stores the cluster CF and obtains all the performance measures for the cluster counterfactual 
        OUTPUT: (None: stored as class attributes)
        """
        cols = ['Method','alpha','feature','feat_value','Sensitive group','instance_idx','centroid_idx','normal_centroid','centroid', 'graph_node',
                'normal_cf','cf','Distance','Feasibility','Likelihood','Effectiveness','Time','model_status','obj_val']
        data = counterfactual.data
        self.test_number_instances = len(data.test_df)
        cf_dict = counterfactual.cf_method.normal_x_cf
        graph_nodes_dict = counterfactual.cf_method.graph_nodes
        likelihood_dict = counterfactual.cf_method.likelihood_dict
        effectiveness_dict = counterfactual.cf_method.effectiveness_dict
        sensitive_group_idx_feat_value_dict = counterfactual.cf_method.sensitive_group_idx_feat_value_dict
        for feature in self.feat_protected.keys():
            cf_feature = cf_dict[feature]
            graph_nodes_feature = graph_nodes_dict[feature]
            likelihood_feature = likelihood_dict[feature]
            effectiveness_feature = effectiveness_dict[feature]
            idx_feature = sensitive_group_idx_feat_value_dict[feature]
            for idx in cf_feature.keys():
                normal_cf = cf_feature[idx]
                graph_node = graph_nodes_feature[idx]
                likelihood = likelihood_feature[graph_node]
                effectiveness = effectiveness_feature[graph_node]
                feat_value = idx_feature[idx]
                len_positives_sensitive_group = len(data.test_df.loc[(data.test_df[feature] == feat_value) & (data.test_target == data.desired_class)])
                instance = data.transformed_false_undesired_test_df.loc[idx].values
                original_instance = data.test_df.loc[idx].values
                normal_x_cf_df = pd.DataFrame(data=normal_cf.reshape(1,-1), index=[0], columns=data.processed_features)
                original_cf = self.inverse_transform_original(normal_x_cf_df)
                original_cf = original_cf.values
                feat_val_name = data.feat_protected[feature][np.round(float(feat_value),2)] 
                sensitive_group = f'{feature}: {feat_val_name}'
                cf_proximity = distance_calculation(instance, normal_cf, kwargs={'dat':data, 'type':counterfactual.type})
                cf_feasibility = verify_feasibility(instance, normal_cf, data)
                data_list = [counterfactual.method, counterfactual.alpha, feature, feat_val_name, sensitive_group, 
                            idx, idx, instance, original_instance, graph_node, normal_cf, 
                            original_cf, cf_proximity/len_positives_sensitive_group, cf_feasibility, likelihood, effectiveness, 
                            counterfactual.cf_method.run_time, counterfactual.cf_method.model_status, counterfactual.cf_method.obj_val]
                data_df = pd.DataFrame(data=[data_list], index=[len(self.cf_df)], columns=cols)
                self.cf_df = pd.concat((self.cf_df, data_df),axis=0)
        print('Printed counterfactual data')

    def find_centroid_for_ares(self, counterfactual, feat, feat_val):
        """
        Finds the centroid corresponding to the feat and feat_val to enable the ground truth positive estimate
        """
        for centroid in counterfactual.cluster.filtered_centroids_list:
            if centroid.feat == feat and centroid.feat_val == feat_val:
                positives_sensitive_group = centroid.positives_sensitive_group
        return positives_sensitive_group

    def add_cf_data_ares(self, counterfactual):
        """
        DESCRIPTION: Stores the results for the ARES method in the evaluation object
        OUTPUT: (None: stored as class attributes)
        """ 
        cols = ['Method','alpha','beta','gamma','delta1','delta2','delta3','feature','feat_value','Sensitive group','q_c_c_prime','instance_idx','centroid_idx','normal_centroid','centroid',
                'normal_cf','cf','Distance','Feasibility','Likelihood','Effectiveness','Time','model_status','obj_val']
        data = counterfactual.data
        model = counterfactual.model
        cfs = counterfactual.cf_method.normal_x_cf
        run_time = counterfactual.cf_method.run_time
        rho = self.get_likelihood(data, cfs)
        eta = self.get_effectiveness(data, model, cfs)
        for idx in range(len(counterfactual.cf_method.best_recourse_df)):
            instance = counterfactual.cf_method.best_recourse_df.iloc[idx]
            instance_idx = instance['x_idx']
            if isinstance(instance_idx,str):
                continue
            else:
                x = data.test_df.loc[instance_idx].values[:-1]
            normal_x = data.transformed_test_df.loc[instance_idx].values
            q_c_c_prime = instance['best_q_c_c_prime']
            q, c, c_prime = q_c_c_prime[0], q_c_c_prime[1], q_c_c_prime[2]
            feat, feat_val = q.split('_')[0], int(float(q.split('_')[1]))
            len_positives_sensitive_group = self.find_centroid_for_ares(counterfactual, feat, feat_val)
            feat_val_name = counterfactual.data.feat_protected[feat][np.round(float(feat_val),2)] 
            normal_cf_df = cfs[instance_idx]
            normal_cf = normal_cf_df.values[0]
            original_cf = self.inverse_transform_original(normal_cf_df).values
            cf_proximity = distance_calculation(normal_x, normal_cf, kwargs={'dat':data, 'type':counterfactual.type})
            cf_feasibility = verify_feasibility(normal_x, normal_cf, data)
            sensitive_group = f'{feat}: {feat_val_name}'
            data_list = ['ARES', counterfactual.alpha, 0, 0, 0, 0, 0, feat, feat_val_name, sensitive_group, q_c_c_prime, instance_idx, instance_idx, normal_x, x, normal_cf, 
                         original_cf, cf_proximity/len_positives_sensitive_group, cf_feasibility, rho[instance_idx], eta[instance_idx], run_time, 2, 'NA']
            data_df = pd.DataFrame(data=[data_list], index=[len(self.cf_df)], columns=cols)
            self.cf_df = pd.concat((self.cf_df, data_df),axis=0)

    def add_cf_data_facts(self, counterfactual):
        """
        DESCRIPTION: Stores the results for the FACTS method in the evaluation object
        OUTPUT: (None: stored as class attributes)
        """ 
        cols = ['Method','alpha','beta','gamma','delta1','delta2','delta3','feature','feat_value','Sensitive group','q_c_c_prime','instance_idx','centroid_idx','normal_centroid','centroid',
                'normal_cf','cf','Distance','Feasibility','Likelihood','Effectiveness','Time','model_status','obj_val']
        data = counterfactual.data
        model = counterfactual.model
        cfs = counterfactual.cf_method.normal_x_cf
        actions = counterfactual.cf_method.actions_x
        run_time = counterfactual.cf_method.run_time
        effectiveness_df = counterfactual.cf_method.best_effectiveness_df
        rho = self.get_likelihood(data, cfs)
        eta = self.get_effectiveness(data, model, cfs)
        for c_idx in range(len(counterfactual.cluster.filtered_centroids_list)):
            centroid = counterfactual.cluster.filtered_centroids_list[c_idx]
            len_positives_sensitive_group = centroid.positives_sensitive_group
            cluster_instances_list = counterfactual.cluster.filtered_clusters_list[c_idx]
            feat_val_name = counterfactual.data.feat_protected[centroid.feat][np.round(float(centroid.feat_val),2)] 
            sensitive_group = f'{centroid.feat}: {feat_val_name}'
            for idx in cluster_instances_list:
                normal_x = data.transformed_test_df.loc[idx].values
                normal_cf_df = cfs[idx]
                action = actions[idx]
                normal_cf = normal_cf_df.values[0]
                original_cf = self.inverse_transform_original(normal_cf_df).values
                cf_proximity = distance_calculation(normal_x, normal_cf, kwargs={'dat':data, 'type':counterfactual.type})
                cf_feasibility = verify_feasibility(normal_x, normal_cf, data)
                sensitive_group = f'{centroid.feat}: {feat_val_name}'
                data_list = ['FACTS', counterfactual.alpha, 0, 0, 0, 0, 0, centroid.feat, feat_val_name, sensitive_group, action, idx, idx, normal_x, centroid.x, normal_cf, 
                            original_cf, cf_proximity/len_positives_sensitive_group, cf_feasibility, rho[idx], eta[idx], run_time, 2, 'NA']
                data_df = pd.DataFrame(data=[data_list], index=[len(self.cf_df)], columns=cols)
                self.cf_df = pd.concat((self.cf_df, data_df),axis=0)