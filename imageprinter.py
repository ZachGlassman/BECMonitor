# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 13:30:44 2015
This will make a new image every few seconds
@author: zag
"""
import numpy as np
import time

data = np.loadtxt('319bec_avg.txt')
#data = np.loadtxt('sgimage.txt')
def add_noise(data):
    x,y = data.shape
    add = np.random.randn(x,y)/20
    return data + add

#k = 1
for k in range(2000):
    time.sleep(5)
    np.savetxt('newimage.txt',add_noise(data))
    print('Printed image {0}'.format(k))
    #k +=1

def make_name(k):
    """note k start at 313"""
    return 'C:\\Users\\zag\\Documents\\BECMonitor\\testData\\' + str(k)+'bec_avg.txt'
'''
for k in range(313,659):
    time.sleep(5)
    data = np.loadtxt(make_name(k))
    np.savetxt('newimage.txt',data)
    print('Printed image {0}'.format(k))

'''
