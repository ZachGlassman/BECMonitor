# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 13:30:44 2015
This will make a new image every few seconds
@author: zag
"""
import numpy as np
import time

data = np.loadtxt('319bec_avg.txt')
def add_noise(data):
    x,y = data.shape
    add = np.random.randn(x,y)/20
    return data + add
    
while(1 > 0):
    time.sleep(10)
    np.savetxt('newimage.txt',add_noise(data))