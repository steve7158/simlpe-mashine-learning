import time
import os
import math
import copy
import numpy as np
import pandas as pd
from collections import Counter
import collections
import random
import sklearn.metrics as sk_m
import scipy.sparse as sc
from scipy.stats import mstats as sc_st_mst

start = time.localtime(time.time())

class my_data():
	def __init__(self):
		
		
		self.variables_all = []
		self.variables = []
		self.class_variable = None
		self.classes = []
		self.p_initial = None
		self.test_all = None
		self.train_all = None
		self.calibration_all = None
		self.train = None
		self.test = None
		self.calibration = None
		



	def read_data(self, directory, file1, file2, file3):
		os.chdir(directory)

		self.train_all = pd.read_csv(file1, sep = ',', header = 0, dtype = 'float', na_values = '?')
		self.test_all = pd.read_csv(file2, sep = ',', header = 0, dtype = 'float', na_values = '?')
		self.calibration_all = pd.read_csv(file3, sep = ',', header = 0, dtype = 'float', na_values = '?')

		self.train_all = self.train_all.drop(self.train_all.columns[0],1)
		self.test_all = self.test_all.drop(self.test_all.columns[0],1)
		self.calibration_all = self.calibration_all.drop(self.calibration_all.columns[0],1)
		variables = list(self.train_all.columns)
 
		self.variables_all = copy.copy(variables)
		self.variables_all.remove('churn')
	
		self.class_variable = 'churn'
		
		self.classes = list(np.unique(self.train_all[self.class_variable]))

		
		self.p_initial = (self.train_all[self.train_all[self.class_variable]==self.classes[0]].shape[0]/
			float(self.train_all.shape[0]))
		

	def fill_missing_values(self):
		for variable in self.variables_all:
			if 	len(self.defined[self.defined[variable].isna()].index) > 0:
				p_na = (len(self.defined[(self.defined[variable].isna()) & (self.defined[self.class_variable]==self.classes[1])].index)/
					float(len(self.defined[self.defined[variable].isna()].index)))
				self.defined[variable] = self.defined[variable].fillna(p_na*np.mean(self.defined[variable]))		

	def train_test_split(self, size):
		self.train['split'] = np.random.rand(len(self.train.index))
		self.calibration = self.train[self.train['split']<=size]
		self.train = self.train.drop('split',1)
		self.calibration = self.calibration.drop('split',1)

	def cleaning_data(self):
		variables = copy.copy(self.variables)
		variables.append(self.class_variable)
		variables = list(variables)
		self.train = self.train_all[variables]
		self.test = self.test_all[variables]
		self.calibration = self.calibration_all[variables]



data = my_data()
data.read_data('\Python27\Binary_classifiers\my\KDD\data','traindata.csv', 'testdata.csv','calibration.csv')




def loglikehood(actual,predicted,classes):
	likehood = 0
	length = len(actual)
	if isinstance(predicted, collections.Iterable):
		for i in range(length):
			if actual[i]==classes[1]:
				likehood+=np.log(predicted[i]+0.0001)
			else:
				likehood+=np.log(1-predicted[i]+0.0001)
			
	else:
		for i in range(length):
			if actual[i]==classes[1]:
				likehood+=np.log(predicted+0.0001)
			else:
				likehood+=np.log(1-predicted+0.0001)
	return likehood		

def calibration(data,variables,class_variable,classes):
	bestVars = []
	baselikehood = (loglikehood(list(data[class_variable]),len(data[data[class_variable]==classes[1]].index)/
		float(len(data.index)),classes))
	for variable in variables:
		if 2*(loglikehood(list(data[class_variable]),list(data[variable]),classes) - baselikehood)>6:
			bestVars.append(variable)
	
	return bestVars		 



data.variables = calibration(data.calibration_all,data.variables_all,data.class_variable,data.classes)
data.cleaning_data()
data.variables.append(data.class_variable)


train = data.train[data.variables]
test = data.test[data.variables]


class Binary_Decision_Tree_Classifier():
	def __init__(self, max_height, min_samples_split = 1, min_samples_leaf = 1, n_quantiles=10):
		self.max_height = max_height
		self.min_samples_split = min_samples_split 
		self.min_samples_leaf  = min_samples_leaf 
		self.n_quantiles = n_quantiles
		self.tree = None
		self.variables = None
		self.classes = None
		self.p_initial = None
		self.class_variable= None

		

	def fit(self, data, class_variable):
		print class_variable
		self.class_variable = class_variable
		if len(np.unique(data[class_variable])) != 2:
			print 'Data have more than 2 classes in output'
		else:
			self.classes = np.unique(data[self.class_variable])
			self.variables = list(data.drop(self.class_variable,1).columns)
			self.p_initial = len(data[data[self.class_variable]==self.classes[0]].index)/float(len(data.index))
			self.tree = compute_tree(data, self.variables, self.class_variable, self.classes, self.p_initial, self.max_height,
									 min_samples_split = self.min_samples_split, min_samples_leaf = self.min_samples_leaf, n_quantiles = self.n_quantiles)
	def predict_proba(self, data):
		return predictions(data, self.tree, self.variables, self.class_variable)	


def get_entropy(p, p_initial):
	if p <= p_initial:
		p_current = p/(2*p_initial)
	else:
		p_current = (p+1-2*p_initial)/(2*(1-p_initial))
		
	return  -(p_current*math.log(p_current+0.0001,2)+(1-p_current)*math.log(1-p_current+0.0001,2))


def get_split(data, variables, class_variable, classes, p_initial, min_samples_leaf, n_quantiles):

	entropy = 1
	split_variable = None
	split_value = None
	ones_r = None
	ones_l = None


	for variable in variables:
		value_list = data[variable]

		if len(np.unique(value_list))>n_quantiles:
			
			probs = [j/float(n_quantiles) for j in range(1,n_quantiles+1)]
			values = sc_st_mst.mquantiles(value_list,probs)
		else:
			if len(np.unique(value_list))==1:
				continue
			values = np.unique(value_list)	
			
		for value in values[:-1]:

			data_with_value = data[data[variable] <= value]
			data_without_value =  data[data[variable] > value]
			without_len = len(data_without_value.index)
			with_len = len(data_with_value.index)
			if (with_len < min_samples_leaf) or (without_len < min_samples_leaf):
				continue	
	
			### Ratios of each value of specified variable
			p_value = with_len/float(len(data.index))

			ones_with = len(data_with_value[data_with_value[class_variable]==classes[0]].index)
			ones_without = len(data_without_value[data_without_value[class_variable]==classes[0]].index)

			p_with = ones_with/float(with_len)
			p_without = ones_without/float(without_len)
			### split_entropy shows how good split seperates class_values in generaly 
			split_entropy = p_value*get_entropy(p_with, p_initial) + (1-p_value)*get_entropy(p_without, p_initial)
			
			
			if split_entropy < entropy :
				p_right = p_with
				p_left = p_without
				entropy = split_entropy
				split_variable = variable
				split_value = value

	if split_variable == None:
		return None		
				
	

	return split_variable, split_value, entropy, p_right, p_left

####	
		
class Node():
	def __init__(self, parent, length, is_right):
		
		self.variable = None
		self.value = None
		self.parent = parent
		self.entropy = None
		self.is_leaf = False
		self.height = None
		self.class_value = None
		self.left_child = None
		self.right_child = None
		self.length = length
		self.is_right = is_right
	
		
		
def compute_tree(data, variables, class_variable, classes, p_initial, max_height,
				 min_samples_split = 1, min_samples_leaf = 1, n_quantiles=10, parent=None, length = None,
				  p_current = None, is_right = False):
	
	print '111'
	node = Node(parent, length, is_right)

	if node.parent == None:
		node.height = 0
		p_current = p_initial
	else:
		node.height = node.parent.height + 1
	
	if (node.length != None) and (node.length < min_samples_split):
		print 'Node_split ; complex_node'
		node.is_leaf = True
		node.class_value = (1-p_current)
		return node
																							

	if p_current == 1:
		print 'Zeros'
		node.is_leaf = True
		node.class_value = 0
		return node

	elif p_current == 0:
		print 'Ones'
		node.is_leaf = True
		node.class_value = 1
		return node	

	if node.height == max_height:
		print 'Height ; complex_node'
		node.is_leaf = True
		node.class_value = 1-p_current
		return node
		

	parameters = get_split(data, variables, class_variable, classes, p_initial, min_samples_leaf, n_quantiles)

	if parameters == None:
		node.is_leaf= True
		node.class_value = 1-p_current
		return node

	node.variable = parameters[0]
	node.value = parameters[1]
	node.entropy = parameters[2]

	
	entropy = get_entropy(p_current, p_initial)
	print entropy
	

	if node.entropy > entropy:
		print 'Entropy ; complex_node'
		node.is_leaf = True
		node.class_value = 1-p_current
		return node
		

	data_for_right_branch = data[data[node.variable] <= node.value]
	data_for_left_branch = data[data[node.variable] > node.value]
	right = len(data_for_right_branch.index) 
	left = len(data_for_left_branch.index)
		

	node.right_child = compute_tree(data_for_right_branch, variables, class_variable, classes, p_initial, max_height,
										min_samples_split = min_samples_split, n_quantiles = n_quantiles, parent = node, length = right, p_current = parameters[3], is_right = True)	
	node.left_child = compute_tree(data_for_left_branch, variables, class_variable, classes, p_initial, max_height,
										min_samples_split = min_samples_split, n_quantiles = n_quantiles, parent = node, length = left, p_current = parameters[4])
	


	return node


def count_nodes(node,i=0):
	i+=1
	if (node.is_leaf) :
		return i
	return count_nodes(node.left_child,i) + count_nodes(node.right_child,i)



def count_leaves(node):
	if (node.is_leaf) :
		return 1
	return count_leaves(node.left_child) + count_leaves(node.right_child)
		 	

def classify(row, node, variables):
	if node.is_leaf:
		return 	node.class_value_	
	if row[variables.index(node.variable)] <= node.value:
		return classify(row,node.right_child, variables)
	else:
		return classify(row,node.left_child, variables)
	
def predictions(data, node, variables, class_variable):
	length = len(data.index)
	data_for_pred = data.drop(class_variable,1)
	data_arr = np.array(data_for_pred)
	return [classify(data_arr[i], node, variables) for i in range(length)] 

	
		
tree = Binary_Decision_Tree_Classifier(50, min_samples_split = 1000, min_samples_leaf = 1000, n_quantiles = 20 )
tree.fit(train,data.class_variable)	

test_data = data.test.copy()		
predicted = tree.predict_proba(test)



tested_arr = np.array(predicted)
test_arr = np.array(test_data[data.class_variable])

print sk_m.roc_auc_score(test_arr, tested_arr)
try:
	print sk_m.accuracy_score(test_arr, tested_arr)
	print sk_m.roc_auc_score(test_arr, tested_arr)
	print sk_m.precision_score(test_arr, tested_arr)
	print sk_m.confusion_matrix(test_arr, tested_arr)
except ValueError:
	print 'I can calculate auc only, beacouse values are continious'	

			

print 'leaves : %s' % (count_leaves(tree))
print 'nodes : %s' % (count_nodes(tree))


end = time.localtime(time.time())
start_in_sec = start[3]*3600 + start[4]*60 + start[5]
end_in_sec = end[3]*3600 + end[4]*60 + end[5]


all_time_min = int((end_in_sec-start_in_sec)/60)
all_time_sec = (end_in_sec-start_in_sec)%60
if all_time_min < 10:
	if all_time_sec < 10:
		print('0%s:0%s' % (all_time_min, all_time_sec ))
	else:
		print('0%s:%s' % (all_time_min, all_time_sec ))	
else:
	if all_time_sec < 10:
		print('%s:0%s' % (all_time_min, all_time_sec ))
	else:
		print('%s:%s' % (all_time_min, all_time_sec ))		

def prune_tree(data, tree, node, variables, class_variable, best_score):
	# if node is a leaf
	if node.is_leaf == True:
		# run validate_tree on a tree with the nodes parent as a leaf with its classification
		node.parent.is_leaf = True
		node.parent.class_value = node.class_value
		new_score = validate_tree(data, tree, variables, class_variable)
		
		# if its better, change it
		if (new_score >= best_score):
			return new_score
		else:
			node.parent.is_leaf = False
			node.parent.class_value = None
			return best_score
	# if its not a leaf
	else: 
		new_score = prune_tree(data, tree, node.right_child, variables, class_variable, best_score)
		if node.is_leaf == True:
			return new_score

		new_score = prune_tree(data, tree, node.left_child, variables, class_variable, best_score)
		if node.is_leaf == True:
			return new_score

		return new_score



def validate_tree(data, tree, variables, class_variable):
	data_for_test = data.copy()
	predicted = predictions(data_for_test, tree, variables)
	return sk_m.accuracy_score(np.array(data[class_variable]), np.array(predicted)) 





		

