'''
Created on Jan 13, 2016

@author: jlovitt
'''
import sys
from dataio import LMDBDataProvider, CifarDataProvider, MnistDataProvider
from matplotlib import pyplot as plt
from matplotlib import image as mpimg
from sigmoid_autoencoder import *
import random as rand
import numpy as np
import tensorflow as tf
from weights_to_img import display
from itertools import islice, cycle
from dnf.cli.output import Output
from PIL import Image
import math
import weights_to_img as w2i

class Object:
    pass

N_COLUMNS = 4
N_STEPS = 1
DEFAULT_PATIENCE=5
DEFAULT_PATIENCE_DELTA=0.00001
"""
Cifar Setup
LAYERS = [
          {"Layerdef":CorruptionLayerDef(0.9),
           "Train":False},
          {"Layerdef":ConvLayerDef(2,1,8),
           "Pretrain_epochs":-1,
           "Convergence_threshold":0.0},
          {"Layerdef":ConvLayerDef(3,2,16),
           "Pretrain_epochs":-1,
           "Convergence_threshold":0.0},
          {"Layerdef":ConvLayerDef(3,2,16),
           "Pretrain_epochs":-1,
           "Convergence_threshold":0.0},
          {"Layerdef":ConvLayerDef(3,2,32),
           "Pretrain_epochs":-1,
           "Convergence_threshold":0.0},
          {"Layerdef":ConvLayerDef(3,1,32),
            "Pretrain_epochs":-1,
            "Convergence_threshold":0.0},
#           {"Layerdef":ConvLayerDef(3,1,1),
#            "Pretrain_epochs":10,
#            "Convergence_threshold":0.99}
          ]
"""
"""
LAYERS = [
          {"Layerdef":CorruptionLayerDef(0.15),
           "Train":False},
          {'Layerdef':FCLayerDef(128,lr=0.7),
           "Pretrain_epochs":-1,
           "Patience": 10,
           "Patience_delta": 0.0001,
           "Convergence_threshold":0.0},
          {'Layerdef':FCLayerDef(64,lr=0.9),
           "Pretrain_epochs":-1,
           "Patience": 10,
           "Patience_delta": 0.0001,
           "Convergence_threshold":0.0},
          {'Layerdef':FCLayerDef(32),
           "Pretrain_epochs":-1,
           "Patience": 10,
           "Patience_delta": 0.0001,
           "Convergence_threshold":0.0},
          {'Layerdef':FCLayerDef(16),
           "Pretrain_epochs":-1,
           "Patience": 10,
           "Patience_delta": 0.0001,
           "Convergence_threshold":0.0},
          {'Layerdef':FCLayerDef(10),
           "Pretrain_epochs":-1,
           "Patience": 10,
           "Patience_delta": 0.0001,
           "Convergence_threshold":0.0},
         ]
"""
"""
Mnist setup
"""
LAYERS = [
#           {"Layerdef":CorruptionLayerDef(0.0),
#            "Train":False},
#           {'Layerdef':FCLayerDef(1024),
#            "Pretrain_epochs":-1,
#            "Convergence_threshold":0.0},
#1
          {"Layerdef":ConvLayerDef(5,2,8,padding='SAME',tied_weights=False ),
              "Pretrain_epochs":0,
               "Patience": 5,
               "Patience_delta": DEFAULT_PATIENCE_DELTA,
               "Convergence_threshold":0.0}, #out: 14
#2
          {"Layerdef":ConvLayerDef(5,2,32,padding='SAME',tied_weights=False),
               "Pretrain_epochs":0,
               "Patience": 5,
               "Patience_delta": DEFAULT_PATIENCE_DELTA,
               "Convergence_threshold":0.0}, #out: 7
#3
          {"Layerdef":ConvLayerDef(1,1,24,tied_weights=False),
               "Pretrain_epochs":0,
               "Patience": 5,
               "Patience_delta": DEFAULT_PATIENCE_DELTA,
               "Convergence_threshold":0.0}, #out: 7
#4
          {"Layerdef":ConvLayerDef(3,1,64,tied_weights=False),
               "Pretrain_epochs":0,
               "Patience": 5,
               "Patience_delta": DEFAULT_PATIENCE_DELTA,
               "Convergence_threshold":0.0}, #out:5
#5
          {"Layerdef":ConvLayerDef(1,1,48,tied_weights=False),
               "Pretrain_epochs":0,
               "Patience": 5,
               "Patience_delta": DEFAULT_PATIENCE_DELTA,
               "Convergence_threshold":0.0}, #out: 5
#6
          {"Layerdef":ConvLayerDef(3,1,96,tied_weights=False),
               "Pretrain_epochs":0,
               "Patience": 5,
               "Patience_delta": DEFAULT_PATIENCE_DELTA,
               "Convergence_threshold":0.0}, #out: 3
#7
          {"Layerdef":ConvLayerDef(1,1,48,tied_weights=False),
               "Pretrain_epochs":0,
               "Patience": 5,
               "Patience_delta": DEFAULT_PATIENCE_DELTA,
               "Convergence_threshold":0.0}, #out: 3
#8
          {"Layerdef":ConvLayerDef(3,1,96,tied_weights=False),
               "Pretrain_epochs":0,
               "Patience": 5,
               "Patience_delta": DEFAULT_PATIENCE_DELTA,
               "Convergence_threshold":0.0}, #out: 1
#9
          {'Layerdef':FCLayerDef(16,sparsity_target=0.02, sparsity_lr=0.0 , activation_entropy_lr=0.0),
           "Pretrain_epochs":20,
           "Patience": 5,
           "Patience_delta": DEFAULT_PATIENCE_DELTA,
           "Convergence_threshold":0.99},
#           {"Layerdef":ConvLayerDef(3,1,32,sparsity_target=0.03, sparsity_lr=0.1),
#                "Pretrain_epochs":-1,
#                "Patience": 5,
#                "Patience_delta": 0.001,
#                "Convergence_threshold":0.0},
#           {"Layerdef":ConvLayerDef(3,1,32),
#             "Pretrain_epochs":-1,
#             "Convergence_threshold":0.0},
#           {"Layerdef":ConvLayerDef(3,1,1),
#            "Pretrain_epochs":10,
#            "Convergence_threshold":0.99}
          ]

DATA_PARAM = Object()
DATA_PARAM.batch_size = 256
TRANSFORM_PARAM = Object()
TRANSFORM_PARAM.mean_file = ""
TRANSFORM_PARAM.mean_value = [127,127,127]
TRANSFORM_PARAM.crop_size = 28
TRANSFORM_PARAM.mirror = False
NUM_LABELS = 10
SHOW = False
LOG_DIR = 'log/'
IMG_DIR = 'img/'
CHECKPOINT_DIR = 'check/'

def converged(a, b):
  if a == None or b == None:
    return False
  else:
    return a == b

def stationary(a,b,thresh):
  if thresh*len(a) < 1.0:
    return True
  if a == None or b == None:
    return False
  matches = 0
  for label,column in a.iteritems():
    if b[label] == column:
      matches += 1
  if float(matches)/float(len(a)) > thresh:
    return True
  return False

def map_img_2_col(columns):
  mapping = {}
  rev_mapping = dict([(col,[]) for col in columns.keys()])
  stats = dict([(col,0) for col in columns.keys()])
  outputs = np.zeros([DATA_PARAM.batch_size, len(columns)])
  for mb in dp.get_mb():
    for i,column in columns.iteritems():
       tmp = column.individual_reconstruction_loss(mb[0])
       outputs[:,i] = tmp
      #outputs[:,i] = np.mean(np.max(np.max(act, axis=1), axis=1), axis=1)
    maxvals = np.argmin(outputs,axis=1)
    for key,col in zip(mb[2],maxvals):
      mapping[key] = col
      stats[col] += 1
      rev_mapping[col].append(key)
  #print "Mapping Stats: ",stats
  return {'key2col':mapping, 'stats':stats, "col2key":rev_mapping}

def encode(imap, columns, epochs, epoch_num):
    datas = [np.zeros(dp.shape()) for i in columns]
    indicies = [0 for i in columns]
    max_examples = max(imap['stats'])
    if min(imap['stats']) == 0:
      max_examples = DATA_PARAM.batch_size
    n_updates = max_examples/DATA_PARAM.batch_size
    report = ["\tTraining column {} on {} examples\n".format(col,len(k)) for col,k in imap['col2key'].iteritems()]
    print(''.join(report))
    for e in range(epoch_num,epoch_num+epochs):
        print "Epoch: {}".format(e)
        for mb in dp.get_mb():
            #print len(mb)
            for i in range(len(mb[2])):
                dat,label,tag = (mb[0][i], mb[1][i], mb[2][i])
                colnum = imap['key2col'][tag]
                datas[colnum][indicies[colnum],:] = dat
                indicies[colnum] += 1
                if indicies[colnum] == DATA_PARAM.batch_size:
                    columns[colnum].encode_mb(datas[colnum])
                    indicies[colnum] = 0
                for colnum,stat in imap['stats'].iteritems():
                  if stat == 0:
                    datas[colnum][indicies[colnum],:] = dat
                    indicies[colnum] += 1
                    if indicies[colnum] == DATA_PARAM.batch_size:
                      columns[colnum].encode_mb(datas[colnum])
                      indicies[colnum] = 0
 
def encode_even(imap, columns, keys, epochs, epoch_num):
    indicies = [0 for i in columns]
    max_examples = max(imap['stats'].values())
    if min(imap['stats'].values()) == 0:
      max_examples = len(keys)
      for colnum,n in imap['stats'].iteritems():
        if n == 0:
          imap['col2key'][colnum] = keys
          print("\tColumn {} has no examples mapped to it.  Training it on all data".format(colnum))
    n_updates = max_examples/DATA_PARAM.batch_size
    for e in range(epoch_num,epoch_num+epochs):
        print "Epoch: {}".format(e)
        losses = dict([(col,0) for col in columns.keys()])
        for update in range(n_updates):
          for colnum,col in columns.iteritems():
            batch_keys = list(islice(cycle(imap['col2key'][colnum]),indicies[colnum],indicies[colnum]+DATA_PARAM.batch_size))
            indicies[colnum] += DATA_PARAM.batch_size
            s,l,k = dp.get_mb_by_keys(batch_keys)
            #print("\tTraining column {} on {} keys".format(colnum,len(batch_keys)))
            losses[colnum] += columns[colnum].encode_mb(s)
    return dict([(col, loss/n_updates) for col,loss in losses.iteritems()])
            

def save_recon(dp, columns):
    for n,column in columns.iteritems():
      d,r = column.recon(dp.get_mb().next()[0])
      s = list(d.shape)
      s[0] = s[0]*2
      d_r_array = np.empty(s,dtype=d.dtype)
      d_r_array[0::2,:,:,:] = d
      d_r_array[1::2,:,:,:] = r
      im = w2i.tile_imgs(d_r_array)
      im.save(IMG_DIR+'im_recon_col'+str(n)+'_level'+str(layer_number+1)+'.png')
      top_shape = column.top_shape()
      a = np.zeros(top_shape)
      input_shape = dp.shape()
      imgs = np.zeros([top_shape[-1]] + list(input_shape[1:]))
      for channel in range(top_shape[-1]):
        b = a.copy()
        if len(top_shape) == 4:
          b[0,top_shape[1]/2,top_shape[2]/2,channel] = 1
        elif len(top_shape) == 2:
          b[0,channel] = 1
        c = column.inject(b)
        imgs[channel,:,:,:] = c[0,:,:,:]
      im = w2i.tile_imgs(imgs, normalize=True)
#       im = Image.fromarray(dp.denormalize(c[0,:]).astype(np.uint8).squeeze(),mode='L')
      im.save(IMG_DIR+'col'+str(n)+'_level'+str(layer_number+1)+'.png')    

def save_top(dp, columns):
    for n,column in columns.iteritems():
      t = column.fwd(dp.get_mb().next()[0])
      top_shape = column.top_shape()
      if len(top_shape) == 4:
        im = w2i.tile_imgs(t)
  #       im = Image.fromarray(dp.denormalize(c[0,:]).astype(np.uint8).squeeze(),mode='L')
        im.save(IMG_DIR+'col'+str(n)+'_level'+str(layer_number+1)+'_top.png')   

def save_exemplars(dp, columns):
      for i in range(len(columns)):
        keys = []
        map_iter = immap['key2col'].iterkeys()
        try:
          while len(keys) < 64:
            k = map_iter.next()
            if immap['key2col'][k] == i:
              keys.append(k)
          sample = dp.get_mb_by_keys(keys)
          im = w2i.tile_imgs(sample)
          im.save(IMG_DIR+"col"+str(i)+"_exemplars.png")
        except StopIteration:
          pass
        #display(dp.denormalize(s.run(columns[i].layers[-1].W).transpose([3,0,1,2])))

 
def mapping_stats(mapping):
  counts = {}
  for val in mapping.values():
    while len(counts) <= val:
      counts[len(counts)] = 0
    counts[val] += 1
  return counts


def pretrain_epoch(columns,dp, i):
    print("Pretrain epoch {}".format(i))
    losses = dict([(col,0) for col in columns.keys()])
    n = 0
    for mb in dp.get_mb():
      n += 1
      for colnum,column in columns.iteritems():
        losses[colnum] += column.encode_mb(mb[0])
    losses = dict([(col,v/n) for col,v in losses.iteritems()])
    return losses
      

if __name__ == '__main__':
    if len(sys.argv) < 2:
      print "Usage: python dynamic_columns.py <path to data> [<>]"
      sys.exit(-1)
    DATA_PARAM.source = sys.argv[1:]
    dp = MnistDataProvider(DATA_PARAM,TRANSFORM_PARAM )
    imgkeys = dp.get_keys()
    columns = {}
    with tf.Session() as sess:
      for i in range(N_COLUMNS):
        g = tf.Graph()
        s = tf.Session(graph=g)
        columns[i] = AutoEncoder(s,g,dp,LOG_DIR, CHECKPOINT_DIR)
      print "Columns Initialized"
      
      #Iterate over layer definitions to build a column
      for layer_number,l in enumerate(LAYERS):
        for column in columns.values():
          column.add_layer(l['Layerdef'])
        print "{} added".format(l['Layerdef'])
        
        if l.get('Train',True):
          #Pretrain on all data
          if l.get('Pretrain_epochs',0) > 0:
            for i in range(l['Pretrain_epochs']):
              losses = pretrain_epoch(columns, dp, i)
              print("\tAve loss: {}".format([str(c)+":"+str(los) for c,los in losses.iteritems()]))
          elif l.get('Pretrain_epochs',0) == -1:
            losses = dict([(col,10) for col in columns.keys()])
            best_loss = losses
            patience = 0
            i = 0
            while patience < l.get("Patience",0):
              for col in best_loss.keys():
                best_loss[col] = min(best_loss[col],losses[col])
              losses = pretrain_epoch(columns, dp, i)
              if min([(ln - lo)/abs(lo)  for ln,lo in zip(losses.values(),best_loss.values())]) < -l.get("Patience_delta",0.1):
                patience = 0
                print("\tAve loss: {} ***".format([str(c)+":"+str(los) for c,los in losses.iteritems()]))
              else:
                print("\tAve loss: {}".format([str(c)+":"+str(los) for c,los in losses.iteritems()]))
                patience += 1
              i += 1
          print "All columns trained on all data {} epochs".format(l.get('Pretrain_epochs',0))

          #Visual investigation
          save_recon(dp,columns)   
          save_top(dp,columns)       

          
          immap_old = {'key2col':None}
          immap = map_img_2_col(columns)
          
          #Train current layer depth until convergence.
          epoch_num = 0
          while(not stationary(immap['key2col'], immap_old['key2col'], l['Convergence_threshold'])):
            print("Mapping Distribution " + str(immap['stats']))
            loss = encode_even(immap, columns, imgkeys, N_STEPS, epoch_num)
            print("Encoding loss on mapped examples {}").format(loss)

            epoch_num += N_STEPS
            immap_old = immap
            immap = map_img_2_col(columns)

          
          #Get column entropy
          columnlabels = dict([(col,[0]*NUM_LABELS) for col in columns.keys()])
          for key,col in immap['key2col'].iteritems():
            _,l,_ = dp.get_mb_by_keys([key])
            columnlabels[col][l[0]] += 1
          output = ""
          for col,dat in columnlabels.iteritems():
            output += "==============="+str(col)+"======================\n"
            output += str(dat) + "\n"
            s = reduce(add,dat)
            print dat
            ents = [0]*len(dat)
            print ents
            for i in range(len(ents)):
              v = dat[i]
              if v != 0:
                ents[i] = -float(v)/s*math.log(float(v)/s)
            entropy = reduce(add, ents )
            output += "Entropy: {}\n".format(entropy)
          print(output)
          
          #print column mapping
          with open(IMG_DIR+"col2key",'w') as fout:
            fout.write(output)
            fout.write(str(immap['col2key']))
      
        
          
#     
# #   dat = dp.get_mb()
# #   for d in dat:
# #       i = d[0][0,:]
# #       print i.shape
# #       plt.imshow(i.reshape((225,225*3)),shape=(225,225*3))
# #       plt.show()
#     for i in range(N_COLUMNS):
#       columns[i] = make_column()