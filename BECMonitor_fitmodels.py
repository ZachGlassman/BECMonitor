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

def gauss_func(x, amplitude, center, std):
    """1d gaussian function"""
    return amplitude * np.exp(-(x-center)**2/(2*std*std))
    
def exp_func(x, initial, lifetime):
    """1d expoential with 1/e liftime, lifetime"""
    return initial * np.exp(-x/lifetime)
    
def lorentz_func(x, center, width):
    """1d lorentzian with width width"""
    return 1/np.pi*width/2 *1/((x-center)**2+(x/width)**2)
    
def sinc_func(x, center, amplitude):
    """sinc function with center and amplitude"""
    return amplitude * np.sinc(x-center)

gaussMod = Model(gauss_func)
expMod = Model(exp_func)
lorentzMod = Model(lorentz_func)
sinMod = Model(sin_func)
sincMod = Model(sinc_func)