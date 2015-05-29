# -*- coding: utf-8 -*-
"""
Created on Fri May 29 13:55:04 2015
Fit Models used for 1d Data
@author: zag
"""
import numpy as np
from lmfit import Model

#first a sin function

def sin_func(x, amplitude, frequency, phi, offset):
    """1d sin wave amplitude, frequency, phi"""
    return amplitude * np.sin(2*np.pi*frequency*x + phi) + offset
 

   
sinMod = Model(sin_func)