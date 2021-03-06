#! /usr/bin/python

'''
import user's own dataset using low level API when the original data is float

this demo is modified based on exp11
'''

import tensorflow as tf
import numpy as np
import glob
import cv2
import os
import h5py

os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

def _int64_feature(value):
    return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))

##############################################################################
# this part is changed
def _float_feature(value):
    return tf.train.Feature(float_list=tf.train.FloatList(value=value))
# end change
##############################################################################

##############################################################################
# this part is changed
def read_tfrecord(tf_filename, size):
    queue = tf.train.string_input_producer([tf_filename])
    reader = tf.TFRecordReader()
    __, serialized_example = reader.read(queue)
    feature = {
          'image_raw': tf.FixedLenFeature([size[0]*size[1]*size[2]], tf.float32),
          'height': tf.FixedLenFeature([], tf.int64),
          'width': tf.FixedLenFeature([], tf.int64)
    }
    features = tf.parse_single_example(serialized_example, features=feature)
    image = features['image_raw']
    image = tf.reshape(image, size)
    return image
# end change
##############################################################################

if __name__ == "__main__":
    dataset_name = 'dataset.tfrecords'

    ## save my own images to dataset (100 images of size 180 x 180)
    print("saving data ...\n")
    # build tfrecord file
    writer = tf.python_io.TFRecordWriter(dataset_name)
    # reader for original data
    h5f = h5py.File('my_data.h5', 'r')
    keys = list(h5f.keys())
    # save my images to dataset
    ##############################################################################
    # this part is changed
    for key in keys:
        img = np.array(h5f[key]).astype(dtype=np.float32)
        height = img.shape[0]
        width = img.shape[1]
        feature = {
            'image_raw': _float_feature(img.reshape( (height*width) )),
            'height': _int64_feature(height),
            'width':  _int64_feature(width)
        }
        example = tf.train.Example(features=tf.train.Features(feature=feature))
        writer.write(example.SerializeToString())
    h5f.close()
    writer.close()
    # end change
    ##############################################################################

    ## load the dataset and display them with tensorboard
    print("loading data ...\n")
    # define batch
    batch_size = 10
    Image = read_tfrecord(dataset_name, size=[180,180,1])
    data_batch = tf.train.shuffle_batch([Image],
                batch_size = batch_size,
                capacity = 1000 + 3 * batch_size,
                num_threads = 2,
                min_after_dequeue = 1000)
    ##############################################################################
    # this part is changed
    img_batch = tf.placeholder(tf.float32, [None, 180, 180, 1])
    # end change
    ##############################################################################
    # summary
    tf.summary.image(name='display', tensor=img_batch, max_outputs=4)
    # begin loading
    epoch = 0
    with tf.Session() as sess:
        coord = tf.train.Coordinator()
        threads = tf.train.start_queue_runners(sess=sess, coord=coord)
        summary = tf.summary.merge_all()
        summ_writer = tf.summary.FileWriter('logs', sess.graph)
        while epoch < 10:
            print("epoch %d" % epoch)
            batch = sess.run(data_batch)
            print([np.min(batch), np.max(batch)])
            summ = sess.run(summary, {img_batch: batch})
            summ_writer.add_summary(summ, epoch)
            summ_writer.flush()
            epoch += 1
        coord.request_stop()
        coord.join(threads)
