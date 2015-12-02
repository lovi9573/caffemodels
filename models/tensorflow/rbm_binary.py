"""Simple, end-to-end, LeNet-5-like convolutional MNIST model example.

This should achieve a test error of 0.8%. Please keep this model as simple and
linear as possible, it is meant as a tutorial for simple convolutional models.
Run with --self_test on the command line to exectute a short self-test.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import gzip
import os
import sys

import tensorflow.python.platform

import numpy
from six.moves import urllib
from six.moves import xrange  # pylint: disable=redefined-builtin
import tensorflow as tf

SOURCE_URL = 'http://yann.lecun.com/exdb/mnist/'
WORK_DIRECTORY = '/home/user/storage/mnist'
IMAGE_SIZE = 28
NUM_CHANNELS = 1
PIXEL_DEPTH = 255
NUM_LABELS = 10
VALIDATION_SIZE = 5000  # Size of the validation set.
SEED = 66478  # Set to None for random seed.
BATCH_SIZE = 64
NUM_EPOCHS = 10
NUM_HIDDEN = 32
V_DIM = IMAGE_SIZE*IMAGE_SIZE*NUM_CHANNELS
SAMPLE_HIDDEN = True
SAMPLE_VISIBLE = True


tf.app.flags.DEFINE_boolean("self_test", False, "True if running a self test.")
FLAGS = tf.app.flags.FLAGS


def maybe_download(filename):
  """Download the data from Yann's website, unless it's already here."""
  if not os.path.exists(WORK_DIRECTORY):
    os.mkdir(WORK_DIRECTORY)
  filepath = os.path.join(WORK_DIRECTORY, filename)
  if not os.path.exists(filepath):
    filepath, _ = urllib.request.urlretrieve(SOURCE_URL + filename, filepath)
    statinfo = os.stat(filepath)
    print('Succesfully downloaded', filename, statinfo.st_size, 'bytes.')
  return filepath


def extract_data(filename, num_images):
  """Extract the images into a 4D tensor [image index, y, x, channels].

  Values are rescaled from [0, 255] down to [0, 1.0].
  """
  print('Extracting', filename)
  with gzip.open(filename) as bytestream:
    bytestream.read(16)
    buf = bytestream.read(IMAGE_SIZE * IMAGE_SIZE * num_images)
    data = numpy.frombuffer(buf, dtype=numpy.uint8).astype(numpy.float32)
    data = data / PIXEL_DEPTH
    data = data.reshape(num_images, IMAGE_SIZE*IMAGE_SIZE)
    return data


def extract_labels(filename, num_images):
  """Extract the labels into a 1-hot matrix [image index, label index]."""
  print('Extracting', filename)
  with gzip.open(filename) as bytestream:
    bytestream.read(8)
    buf = bytestream.read(1 * num_images)
    labels = numpy.frombuffer(buf, dtype=numpy.uint8)
  # Convert to dense 1-hot representation.
  return (numpy.arange(NUM_LABELS) == labels[:, None]).astype(numpy.float32)


def fake_data(num_images):
  """Generate a fake dataset that matches the dimensions of MNIST."""
  data = numpy.ndarray(
      shape=(num_images, IMAGE_SIZE*IMAGE_SIZE*NUM_CHANNELS),
      dtype=numpy.float32)
  labels = numpy.zeros(shape=(num_images, NUM_LABELS), dtype=numpy.float32)
  for image in xrange(num_images):
    label = image % 2
    data[image, :, :, 0] = label - 0.5
    labels[image, label] = 1.0
  return data, labels


def error_rate(predictions, labels):
  """Return the error rate based on dense predictions and 1-hot labels."""
  return 100.0 - (
      100.0 * 
      numpy.sum(numpy.argmax(predictions, 1) == numpy.argmax(labels, 1)) / 
      predictions.shape[0])


def main(argv=None):  # pylint: disable=unused-argument
  if FLAGS.self_test:
    print('Running self-test.')
    train_data, train_labels = fake_data(256)
    validation_data, validation_labels = fake_data(16)
    test_data, test_labels = fake_data(256)
    num_epochs = 1
  else:
    # Get the data.
    train_data_filename = maybe_download('train-images-idx3-ubyte.gz')
    test_data_filename = maybe_download('t10k-images-idx3-ubyte.gz')

    # Extract it into numpy arrays.
    train_data = extract_data(train_data_filename, 60000)
    test_data = extract_data(test_data_filename, 10000)

    # Generate a validation set.
    train_data = train_data[:VALIDATION_SIZE, :]
    validation_data = train_data[VALIDATION_SIZE:, :]
    num_epochs = NUM_EPOCHS
  train_size = train_data.shape[0]

  # This is where training samples and labels are fed to the graph.
  # These placeholder nodes will be fed a batch of training data at each
  # training step using the {feed_dict} argument to the Run() call below.
  # TODO(jesse lovitt): Can I modify this in place?
  visible = tf.placeholder(
      tf.float32,
      shape=(BATCH_SIZE,V_DIM))
  
  # For the validation and test data, we'll just hold the entire dataset in
  # one constant node.
  validation_data_node = tf.constant(validation_data)
  test_data_node = tf.constant(test_data)

  # The variables below hold all the trainable weights. They are passed an
  # initial value which will be assigned when when we call:
  # {tf.initialize_all_variables().run()}
  weights = tf.Variable(
      tf.truncated_normal([NUM_HIDDEN, V_DIM],
                          stddev=0.1,
                          seed=SEED))
  bias_h = tf.Variable(tf.zeros([NUM_HIDDEN]))
  bias_v = tf.Variable(tf.constant(0.1, shape=[V_DIM]))


  recon = tf.Variable(tf.zeros([BATCH_SIZE, V_DIM]))
  hidden = tf.Variable(tf.zeros([BATCH_SIZE, NUM_HIDDEN],dtype=tf.float32))
  
  E_p = tf.Variable(tf.zeros([NUM_HIDDEN,V_DIM]))

  def v_h(v, sample=True):
    hidden = tf.matmul(v,weights,transpose_b=True)+bias_h
    if sample:
      thresh = tf.random_uniform([BATCH_SIZE, NUM_HIDDEN])
      hidden = hidden > thresh
    return hidden
  
  def h_v(h, sample=True):
    recon = h*weights + bias_v
    if sample:
      thresh = tf.random_uniform([BATCH_SIZE, V_DIM])
      recon = recon > thresh
    return recon

  # We will replicate the model structure for the training subgraph, as well
  # as the evaluation subgraphs, while sharing the trainable parameters.
  def model(data, train=False):
    """The Model definition."""
    # Positive Phase
    hidden = v_h(data, SAMPLE_HIDDEN)
    
    # Get positive phase energy
    E_p = tf.matmul(hidden, data, transpose_a=True)
    
    # Gibbs chain  
    recon = h_v(hidden,SAMPLE_VISIBLE)
    hidden = v_h(recon, SAMPLE_HIDDEN)
    
    # Get positive phase energy
    E_n = tf.transpose(hidden)*recon
    
    return E_p - E_n

  # Training computation: logits + cross-entropy loss.
  E = model(visible, True)
  loss = tf.reduce_mean(E)

  
  # Optimizer: set up a variable that's incremented once per batch and
  # controls the learning rate decay.
  batch = tf.Variable(0)
  # Decay once per epoch, using an exponential schedule starting at 0.01.
  learning_rate = tf.train.exponential_decay(
      0.01,  # Base learning rate.
      batch * BATCH_SIZE,  # Current index into the dataset.
      train_size,  # Decay step.
      0.95,  # Decay rate.
      staircase=True)
  # Use simple momentum for the optimization.
  optimizer = tf.train.MomentumOptimizer(learning_rate,
                                         0.9).minimize(loss,
                                                       global_step=batch)


  # Create a local session to run this computation.
  with tf.Session() as s:
    # Run all the initializers to prepare the trainable parameters.
    tf.initialize_all_variables().run()
    print('Initialized!')
    # Loop through training steps.
    for step in xrange(num_epochs * train_size // BATCH_SIZE):
      # Compute the offset of the current minibatch in the data.
      # Note that we could use better randomization across epochs.
      offset = (step * BATCH_SIZE) % (train_size - BATCH_SIZE)
      batch_data = train_data[offset:(offset + BATCH_SIZE), :, :, :]
      batch_labels = train_labels[offset:(offset + BATCH_SIZE)]
      # This dictionary maps the batch data (as a numpy array) to the
      # node in the graph is should be fed to.
      feed_dict = {visible: batch_data}
      # Run the graph and fetch some of the nodes.
      _, l, lr = s.run(
          [optimizer, loss, learning_rate],
          feed_dict=feed_dict)
      if step % 100 == 0:
        print('Epoch %.2f' % (float(step) * BATCH_SIZE / train_size))
        print('Minibatch loss: %.3f, learning rate: %.6f' % (l, lr))
        sys.stdout.flush()
    # Finally print the result!


if __name__ == '__main__':
  tf.app.run()
