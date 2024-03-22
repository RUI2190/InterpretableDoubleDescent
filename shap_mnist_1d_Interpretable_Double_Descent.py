# -*- coding: utf-8 -*-
"""FINAL: MNIST-1D: Double descent: Changing number of parameters in hidden layer

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ZRcyp03QQU3EUZHsjRcuzk7sSLEdCQBJ

# **MNIST-1D**: Observing deep double descent

This notebook investigates double descent as described in section 8.4 of the ["Understanding Deep Learning"](https://udlbook.github.io/udlbook/) textbook.

The deep double descent phenomenon was [originally described here](https://arxiv.org/abs/1812.11118) and later extended to modern architectures and large datasets in an [OpenAI research project](https://openai.com/blog/deep-double-descent/).

This case study is meant to show the convenience and computational savings of working with the low-dimensional MNIST-1D dataset. You can find more details at https://github.com/greydanus/mnist1d.
"""

from google.colab import drive
drive.mount('/content/drive')

# Run this if you're in a Colab to make a local copy of the MNIST 1D repository
!git clone https://github.com/greydanus/mnist1d

!pip install shap

import torch, torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from torch.optim.lr_scheduler import StepLR
import numpy as np
import matplotlib.pyplot as plt
import mnist1d
import random
random.seed(0)

# Try attaching to GPU -- Use "Change Runtime Type to change to GPUT"
DEVICE = str(torch.device('cuda' if torch.cuda.is_available() else 'cpu'))
print('Using:', DEVICE)

import torch
import matplotlib.pyplot as plt

from mnist1d.data import get_templates, get_dataset_args, get_dataset
from mnist1d.train import get_model_args, train_model
from mnist1d.models import ConvBase, GRUBase, MLPBase, LinearBase
from mnist1d.utils import set_seed, plot_signals, ObjectView, from_pickle

import seaborn as sns
import shap
shap.initjs()

args = mnist1d.data.get_dataset_args()
args.num_samples = 8000 # try after changing this
args.train_split = 0.5 # try after changing this
args.corr_noise_scale = 0.25 # try after changing this
args.iid_noise_scale = 2e-2 # try after changing this
data = mnist1d.data.get_dataset(args, path='./mnist1d_data.pkl', download=False, regenerate=True)

# Add 15% noise to training labels
for c_y in range(len(data['y'])):
    random_number = random.random()
    if random_number < 0.15 :
        random_int = int(random.random() * 10)
        data['y'][c_y] = random_int

# The training and test input and outputs are in
# data['x'], data['y'], data['x_test'], and data['y_test']
print("Examples in training set: {}".format(len(data['y'])))
print("Examples in test set: {}".format(len(data['y_test'])))
print("Length of each example: {}".format(data['x'].shape[-1]))

data['t']

data['x'][0]

data.keys()

for k in range(1,5):
    i = np.randint(0,101)
    samp_x = data['x'][i]
    t = data['t'].reshape((40,1))
    y = data['y']
    plt.plot(samp_x, t, 'k-', linewidth=2)
    print(y[i])
    plt.show()
    #fig = plot_signals(data['x'], t, labels = y, ratio=3, dark_mode=False)

# Initialize the parameters with He initialization
def weights_init(layer_in):
  if isinstance(layer_in, nn.Linear):
    nn.init.kaiming_uniform_(layer_in.weight)
    layer_in.bias.data.fill_(0.0)

# Return an initialized model with two hidden layers and n_hidden hidden units at each
def get_model(n_hidden):

  D_i = 40    # Input dimensions
  D_k = n_hidden   # Hidden dimensions
  D_o = 10    # Output dimensions

  # Define a model with two hidden layers of size 100
  # And ReLU activations between them
  model = nn.Sequential(
  nn.Linear(D_i, D_k),
  nn.ReLU(),
  nn.Linear(D_k, D_k),
  nn.ReLU(),
  nn.Linear(D_k, D_o))

  # Call the function you just defined
  model.apply(weights_init)

  # Return the model
  return model ;

def fit_model(model, data):

  # choose cross entropy loss function (equation 5.24)
  loss_function = torch.nn.CrossEntropyLoss()
  # construct SGD optimizer and initialize learning rate and momentum
  # optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
  optimizer = torch.optim.SGD(model.parameters(), lr = 0.01, momentum=0.9)


  # create 100 dummy data points and store in data loader class
  x_train = torch.tensor(data['x'].astype('float32'))
  y_train = torch.tensor(data['y'].transpose().astype('long'))
  x_test= torch.tensor(data['x_test'].astype('float32'))
  y_test = torch.tensor(data['y_test'].astype('long'))

  # load the data into a class that creates the batches
  data_loader = DataLoader(TensorDataset(x_train,y_train), batch_size=100, shuffle=True, worker_init_fn=np.random.seed(1))

  # loop over the dataset n_epoch times
  n_epoch = 1000

  for epoch in range(n_epoch):
    # loop over batches
    for i, batch in enumerate(data_loader):
      # retrieve inputs and labels for this batch
      x_batch, y_batch = batch
      # zero the parameter gradients
      optimizer.zero_grad()
      # forward pass -- calculate model output
      pred = model(x_batch)
      # compute the loss
      loss = loss_function(pred, y_batch)
      # backward pass
      loss.backward()
      # SGD update
      optimizer.step()

    # Run whole dataset to get statistics -- normally wouldn't do this
    pred_train = model(x_train)
    pred_test = model(x_test)
    _, predicted_train_class = torch.max(pred_train.data, 1)
    _, predicted_test_class = torch.max(pred_test.data, 1)
    errors_train = 100 - 100 * (predicted_train_class == y_train).float().sum() / len(y_train)
    errors_test= 100 - 100 * (predicted_test_class == y_test).float().sum() / len(y_test)
    losses_train = loss_function(pred_train, y_train).item()
    losses_test= loss_function(pred_test, y_test).item()
    if epoch%100 ==0 :
      print(f'Epoch {epoch:5d}, train loss {losses_train:.6f}, train error {errors_train:3.2f},  test loss {losses_test:.6f}, test error {errors_test:3.2f}')

  return errors_train, errors_test, predicted_train_class, predicted_test_class

"""#Final Code"""

#import numpy as np
#hidden_variables = np.array([2,4,6,8,10,14,18,22,26,30,35,40,45,50,55,60,70,80,90,100,120,140,160,180,200,250,300,400, 500, 600, 700, 800, 900]);
#for c_hidden in range(25,len(hidden_variables)):
#    print(hidden_variables[c_hidden])

for c_hidden in range(28,len(hidden_variables)):
    print(hidden_variables[c_hidden])

len([2,4,6,8,10,14,18,22,26,30,35,40,45,50,55,60,70,80,90,100,120,140,160,180,200,250,300,400, 500, 600, 700, 800, 900])

# Commented out IPython magic to ensure Python compatibility.
# %%time
# hidden_variables = np.array([2,4,6,8,10,14,18,22,26,30,35,40,45,50,55,60,70,80,90,100,120,140,160,180,200,250,300,400, 500, 600, 700, 800, 900]);
# errors_train_all = np.zeros_like(hidden_variables)
# errors_test_all = np.zeros_like(hidden_variables)
# 
# # For each hidden variable size
# for c_hidden in range(28,len(hidden_variables)):
#     print("#"*100)
#     print(f'Training model with {hidden_variables[c_hidden]:3d} hidden variables')
#     # Get a model
#     model = get_model(hidden_variables[c_hidden]) ;
#     # Train the model
#     errors_train, errors_test, pred_train, pred_test = fit_model(model, data)
#     # Store the results
#     errors_train_all[c_hidden] = errors_train
#     errors_test_all[c_hidden]= errors_test
# 
#     x_train = torch.tensor(data['x'].astype('float32'))
#     y_train = torch.tensor(data['y'].transpose().astype('long'))
#     x_test= torch.tensor(data['x_test'].astype('float32'))
#     y_test = torch.tensor(data['y_test'].astype('long'))
# 
#     #data_loader = DataLoader(TensorDataset(x_train,y_train), batch_size=100, shuffle=True, worker_init_fn=np.random.seed(1))
#     test_data_loader = DataLoader(TensorDataset(x_test,y_test), batch_size=12, shuffle=False, worker_init_fn=np.random.seed(1))#batch_size = 100
# 
#     #explainer = shap.DeepExplainer(model, x_test)
#     explainer = shap.DeepExplainer(model, x_train) #should this be train or test
# 
#     test_set_num = 1
#     for i, batch in enumerate(test_data_loader):
#       # retrieve inputs and labels for this batch
#       if(i == test_set_num):
#         sample_data, y_d = batch #sample_data, y_d = next(iter(test_data_loader))# Get a sample of data for explanation
#         shap_values = explainer.shap_values(sample_data) # Compute SHAP values for a specific instance
#         break
# 
# 
#     #Explanation of one correct and one wrong prediction
#     for j in range(len(sample_data)):
#         val = []
#         k_val = pred_test[j + test_set_num*12] #jth data point, k_val is the prediction of the jth data point
#         for i in range(40):
#             val.append(shap_values[j][i][k_val])
#         val = np.array(val)
# 
#         samp_x = sample_data[j]
#         y = t.reshape((40,1))
#         colors = (val/max(val))*256
#         cmap = plt.get_cmap('bwr')  # You can choose any other colormap
#         plt.plot(samp_x, t, 'k-', linewidth=2)
#         plt.scatter(samp_x, y, c=colors, cmap=cmap, s=100, alpha=0.7)  # Use the specified colormap
#         print("True Label:", int(y_d[j]))
#         print("Model Prediction:", int(k_val))
#         plt.colorbar(label='Color intensity')  # Add colorbar to show mapping
#         plt.title('Scatter Plot with Float Colors')
#         plt.xlabel('X Axis')
#         plt.ylabel('Y Axis')
#         plt.grid(True)
# 
#         pre_t_val = str(int(y_d[j])) + str(int(k_val))
#         path = "/content/drive/MyDrive/MNIST_results_v2/"
#         if int(y_d[j]) == int(k_val):
#             plt.savefig(path+"CP/"+str(j+(test_set_num*12))+"th_smpl_"+pre_t_val+"_"+str(hidden_variables[c_hidden])+'_nn.jpg', format='jpg', dpi=300)
#         else:
#             plt.savefig(path+"WP/"+str(j+(test_set_num*12))+"th_smpl_"+pre_t_val+"_"+str(hidden_variables[c_hidden])+'_nn.jpg', format='jpg', dpi=300)
# 
#         plt.savefig(path+"ALL/"+str(j+(test_set_num*12))+"th_smpl_"+pre_t_val+"_"+str(hidden_variables[c_hidden])+'_nn.jpg', format='jpg', dpi=300)
# 
#         plt.show()

plt.figure(dpi=250, figsize=[4,2.5])
plt.plot(hidden_variables, errors_train_all,'r.-', label='train', alpha=0.33, linewidth=2.5)
plt.plot(hidden_variables, errors_test_all,'b.-', label='test', linewidth=2.5)
plt.ylim(-5,80);
plt.xlabel('Size of hidden layer'); plt.ylabel('Test error')
plt.legend(ncols=2)
plt.show()

plt.figure(dpi=250, figsize=[4,2.5])
val1 = 25
plt.plot(hidden_variables[:val1], errors_train_all[:val1],'r.-', label='train', alpha=0.33, linewidth=2.5)
plt.plot(hidden_variables[:val1], errors_test_all[:val1],'b.-', label='test', linewidth=2.5)
plt.ylim(-5,80);
plt.xlabel('Size of hidden layer'); plt.ylabel('Test error')
plt.legend(ncols=2)
plt.show()

from google.colab import drive
drive.mount('/content/drive')

import os
import re
# Path to your directory

directory_path1 = '/content/drive/MyDrive/MNIST_results_v2/CP'
directory_path2 = '/content/drive/MyDrive/MNIST_results_v2/WP'

CP_2_22 = []
WP_26_69 = []
CP_70_900 = []


# flexible_before_nn_pattern = r'(.+)_\d+nn'
flexible_before_nn_pattern = r'(.+?)_\d+_\d+_nn'

for filename in os.listdir(directory_path1):
    if os.path.isfile(os.path.join(directory_path1, filename)):
      match1 = re.search(r'_(\d+)_nn\.jpg', filename)
      hidden_var = int(match1.group(1))
      if hidden_var in list(range(2, 23)):
        flexible_before_nn_match = re.search(flexible_before_nn_pattern, filename)
        flexible_before_nn_string = flexible_before_nn_match.group(1)

        CP_2_22.append(flexible_before_nn_string)
      elif hidden_var in list(range(70, 901)):
        flexible_before_nn_match = re.search(flexible_before_nn_pattern, filename)
        flexible_before_nn_string = flexible_before_nn_match.group(1)

        CP_70_900.append(flexible_before_nn_string)

for filename in os.listdir(directory_path2):
    if os.path.isfile(os.path.join(directory_path2, filename)):
      match1 = re.search(r'_(\d+)_nn\.jpg', filename)
      hidden_var = int(match1.group(1))
      if hidden_var in list(range(26, 70)):
        flexible_before_nn_match = re.search(flexible_before_nn_pattern, filename)
        flexible_before_nn_string = flexible_before_nn_match.group(1)

        WP_26_69.append(flexible_before_nn_string)

set(CP_2_22) & set(WP_26_69) & set(CP_70_900)

smpl_num_req = 0

flexible_before_nn_pattern = r'(.+?)_\d+_\d+_nn'
nth_number_pattern = r'(\d+)th_smpl'

for filename in os.listdir(directory_path1):
    if os.path.isfile(os.path.join(directory_path1, filename)):
      match1 = re.search(r'_(\d+)_nn\.jpg', filename)
      hidden_var = int(match1.group(1))
      # Search for the adjusted pattern
      nth_number_match = re.search(nth_number_pattern, filename)
      nth_number_string = int(nth_number_match.group(1))

      if (hidden_var in list(range(2, 23)) or hidden_var in list(range(70, 901))) and nth_number_string == smpl_num_req:
       print(filename)

# flexible_before_nn_pattern = r'(.+)_\d+nn'
flexible_before_nn_pattern = r'(.+?)_\d+_\d+_nn'
nth_number_pattern = r'(\d+)th_smpl'

for filename in os.listdir(directory_path2):
    if os.path.isfile(os.path.join(directory_path2, filename)):
      match1 = re.search(r'_(\d+)_nn\.jpg', filename)
      hidden_var = int(match1.group(1))
      # Search for the adjusted pattern
      nth_number_match = re.search(nth_number_pattern, filename)
      nth_number_string = int(nth_number_match.group(1))

      if hidden_var in list(range(26, 70)) and nth_number_string == smpl_num_req:
       print(filename)

WP_2_22 = []
WP_26_69 = []
CP_70_900 = []

# flexible_before_nn_pattern = r'(.+)_\d+nn'
flexible_before_nn_pattern = r'(.+?)_\d+_\d+_nn'

for filename in os.listdir(directory_path1):
    if os.path.isfile(os.path.join(directory_path1, filename)):
      match1 = re.search(r'_(\d+)_nn\.jpg', filename)
      hidden_var = int(match1.group(1))
      if hidden_var in list(range(70, 901)):
        flexible_before_nn_match = re.search(flexible_before_nn_pattern, filename)
        flexible_before_nn_string = flexible_before_nn_match.group(1)
        CP_70_900.append(flexible_before_nn_string)

for filename in os.listdir(directory_path2):
    if os.path.isfile(os.path.join(directory_path2, filename)):
      match1 = re.search(r'_(\d+)_nn\.jpg', filename)
      hidden_var = int(match1.group(1))
      if hidden_var in list(range(26, 70)):
        flexible_before_nn_match = re.search(flexible_before_nn_pattern, filename)
        flexible_before_nn_string = flexible_before_nn_match.group(1)
        WP_26_69.append(flexible_before_nn_string)

for filename in os.listdir(directory_path2):
    if os.path.isfile(os.path.join(directory_path2, filename)):
      match1 = re.search(r'_(\d+)_nn\.jpg', filename)
      hidden_var = int(match1.group(1))
      if hidden_var in list(range(2, 23)):
        flexible_before_nn_match = re.search(flexible_before_nn_pattern, filename)
        flexible_before_nn_string = flexible_before_nn_match.group(1)
        WP_2_22.append(flexible_before_nn_string)

set(WP_2_22) & set(WP_26_69) & set(CP_70_900)

# pre_t_val = str(int(y_d[j])) + str(int(k_val))
# path = '/content/drive/MyDrive/lime/'
# if int(y_d[j]) == int(k_val):
#     plt.savefig(path+"CP/"+str(j)+"th_smpl_"+pre_t_val+"_"+str(hidden_variables[c_hidden])+'nn.jpg', format='jpg', dpi=300)
# else:
#     plt.savefig(path+"WP/"+str(j)+"th_smpl_"+pre_t_val+"_"+str(hidden_variables[c_hidden])+'nn.jpg', format='jpg', dpi=300)

# plt.savefig(path+"ALL/"+str(j)+"th_smpl_"+pre_t_val+"_"+str(hidden_variables[c_hidden])+'nn.jpg', format='jpg', dpi=300)

"""# Misc"""

# This code will take a while (~30 mins on GPU) to run!  Go and make a cup of coffee!

hidden_variables = np.array([2,4,6,8,10,14,18,22,26,30,35,40,45,50,55,60,70,80,90,100,120,140,160,180,200,250,300,400]) ;
errors_train_all = np.zeros_like(hidden_variables)
errors_test_all = np.zeros_like(hidden_variables)

# For each hidden variable size
for c_hidden in range(len(hidden_variables)):
    print(f'Training model with {hidden_variables[c_hidden]:3d} hidden variables')
    # Get a model
    model = get_model(hidden_variables[c_hidden]) ;
    # Train the model
    errors_train, errors_test = fit_model(model, data)
    # Store the results
    errors_train_all[c_hidden] = errors_train
    errors_test_all[c_hidden]= errors_test

sample_data.shape, shap_values.shape

y_d

pred_test

for j in range(len(sample_data)):
    val = []
    k_val = pred_test[j] #jth data point, k_val is the prediction of the jth data point
    for i in range(40):
        val.append(shap_values[j][i][k_val])
    val = np.array(val)

    for k in range(1,2):
        samp_x = sample_data[j]
        y = t.reshape((40,1))
        colors = (val/max(val))*256
        cmap = plt.get_cmap('bwr')  # You can choose any other colormap
        plt.plot(samp_x, t, 'k-', linewidth=2)
        plt.scatter(samp_x, y, c=colors, cmap=cmap, s=100, alpha=0.7)  # Use the specified colormap
        print("True Label:", int(y_d[j]))
        print("Model Prediction:", int(k_val))
        plt.colorbar(label='Color intensity')  # Add colorbar to show mapping
        plt.title('Scatter Plot with Float Colors')
        plt.xlabel('X Axis')
        plt.ylabel('Y Axis')
        plt.grid(True)
        plt.close()

        #fig = plot_signals(data['x'], t, labels = y, ratio=3, dark_mode=False)

k_val = pred_test[0]
shap.waterfall_plot(shap.Explanation(values=val,
                                            base_values=explainer.expected_value[k_val],
                                            data= sample_data[0].reshape((40,1))), max_display = 10)

k_val = pred_test[0]
shap.waterfall_plot(shap.Explanation(values=shap_values[k_val][0],
                                            base_values=explainer.expected_value[k_val],
                                            data= sample_data[0].reshape((40,1))), max_display = 5)
it = 0
for i in range(len(pred_test)):
    if pred_test[i] == y_test[i]: #correct prediction
        k_val = pred_test[i]
        print(i, k_val)
        shap.waterfall_plot(shap.Explanation(values=shap_values[k_val][i],
                                            base_values=explainer.expected_value[k_val],
                                            data= sample_data[i].reshape((40,1))), max_display = 5)
    break

it = 0
for i in range(len(pred_test)):
    if pred_test[i] != y_test[i]: #wrong prediction
        k_val = pred_test[i]
        print(i, k_val)
        shap.waterfall_plot(shap.Explanation(values=shap_values[k_val][i],
                                            base_values=explainer.expected_value[k_val],
                                            data= sample_data[i].reshape((40,1))), max_display = 5)
    break

shap_values

explainer.expected_value

y_d, y_test[0:len(y_d)], pred_test[0:len(y_d)]

if len(y_d) == len(sample_data):
    pass
else:
    print("Error")

it = 0
for i in range(1,len(pred_test)):
    k_val = pred_test[i]
    shap.waterfall_plot(shap.Explanation(values=shap_values[k_val][i],
                                            base_values=explainer.expected_value[k_val],
                                            data= sample_data[i].reshape((40,1))), max_display = 5)
    print("*"*100)
    for j in range(10):
        shap.waterfall_plot(shap.Explanation(values=shap_values[j][i],
                                            base_values=explainer.expected_value[j],
                                            data= sample_data[i].reshape((40,1))), max_display = 5)

y_test[:5], pred_test[:5]

it = 0
for i in range(1,len(pred_test)):
    if pred_test[i] == y_test[i]: #correct prediction
        k_val = pred_test[i]
        print(i, k_val)
        shap.waterfall_plot(shap.Explanation(values=shap_values[k_val][i],
                                             base_values=explainer.expected_value[k_val],
                                             data= sample_data[i].reshape((40,1))), max_display = 5)
    it+=1
    if it == 5:
        break

explainer.expected_value

y_test, pred_test

it = 0
for i in range(len(pred_test)):
    if pred_test[i] != y_test[i]: #wrong prediction
        print(i)
        k_val = pred_test[i]
        shap.waterfall_plot(shap.Explanation(values=shap_values[k_val][i],
                                             base_values=explainer.expected_value[k_val],
                                             data= sample_data[i].reshape((40,1))), max_display = 5)
    it+=1
    if it == 5:
        break
