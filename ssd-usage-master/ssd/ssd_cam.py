#!/usr/bin/env python

import os
import math
import random
import pandas as pd
import numpy as np
import tensorflow as tf
import cv2
from cv_bridge import CvBridge, CvBridgeError
import rospy
from sensor_msgs.msg import Image
from sensor_msgs.msg import CompressedImage

slim = tf.contrib.slim

#matplotlib inline
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

import sys
from pathlib import Path
# sys.path.append('../')
# sys.path.insert(0, '/home/lab/Downloads/ssd-usage-master/ssd')
#from ssd 
import ssd_wrapper
path_to_model = str(Path(__file__).parent.parent)
labels = pd.read_csv(path_to_model+'/model/labels.txt')

# TensorFlow session: grow memory when needed. TF, DO NOT USE ALL MY GPU MEMORY!!!
gpu_options = tf.GPUOptions(allow_growth=True)
config = tf.ConfigProto(log_device_placement=False, gpu_options=gpu_options)

ssd = ssd_wrapper.ssdWrapper(config = config)

colors = dict()
for cls_id in range(len(np.array(labels))):
    colors[cls_id] = (int(random.random()*255), int(random.random()*255), int(random.random()*255))

cam = cv2.VideoCapture(0)
#ret = cam.set(3,320)
#ret = cam.set(4,240)
#ret = cam.set(5,10)

cv_img = 0

def img_callback (ros_img):
    #print ('got an image')
    global bridge, cv_img
    try: 
        cv_img = bridge.imgmsg_to_cv2(ros_img,"bgr8")
    except CvBridgeError as e:
        print (e)

bridge = CvBridge()

rospy.init_node('img', anonymous = True)
pub_detections = rospy.Publisher('/ssd/results/compressed/', CompressedImage, queue_size=2)
img_sub = rospy.Subscriber('/kinect2/qhd/image_color_rect', Image, img_callback)
ros_img = rospy.wait_for_message('/kinect2/qhd/image_color_rect', Image)
print ('got an image')
while not rospy.is_shutdown():
    #ret_val, img = cam.read()
    global cv_img
    img = cv_img
    img = cv2.resize(img, (300, 300),interpolation = cv2.INTER_AREA)
    rclasses, rscores, rbboxes =  ssd.process_image(img)
    height = img.shape[0]
    width = img.shape[1]
   
    for i in range(len(rclasses)):
        cls_id = int(rclasses[i])
        if cls_id >= 0:          
            ymin = int(rbboxes[i, 0] * height)
            xmin = int(rbboxes[i, 1] * width)
            ymax = int(rbboxes[i, 2] * height)
            xmax = int(rbboxes[i, 3] * width)
        
            img = cv2.rectangle(img,(xmin,ymin),(xmax,ymax),colors[cls_id],2)
            font                   = cv2.FONT_HERSHEY_SIMPLEX
            bottomLeftCornerOfText = (xmin,ymin + 20)
            fontScale              = 1
            fontColor              =colors[cls_id]
            lineType               = 2
            
            img = cv2.putText(img,str(labels.iloc[cls_id][0]), 
                    bottomLeftCornerOfText, 
                    font, 
                    fontScale,
                    fontColor,
                    lineType)
    
    msg = CompressedImage()
    msg.header.stamp = rospy.Time.now()
    msg.format = "jpeg"
    msg.data = np.array(cv2.imencode('.jpg', img)[1]).tostring()
    pub_detections.publish(msg)        
    # cv2.imshow('ssd300', img)

    
    # if cv2.waitKey(1) == 27: 
    #     cam.release()
    #     cv2.destroyAllWindows()
    #     break  # esc to quit
