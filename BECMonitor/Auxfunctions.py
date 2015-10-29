# -*- coding: utf-8 -*-
"""
Created on Wed Jun  3 11:03:42 2015
File for auxillary functions, every function in this file will
be parsed and added to SpinorMonitor.

Please add a documentation string in quotes underneath the function
@author: zag
"""
import numpy as np

def calculateQ(Rf_resonance_frequency,microwave_power,microwave_detuning):
    """calculate Q
    parameters:
        Rf resonance frequency (Hz)
        microwave power (dB(m))
        microwave detuning (hz)

    returns:
        q in Hz
    """
    fRabi = 22000 #measure on resonance microwave Rabi frequency (Hz)
    Pcalib = 44 #microwave power used when measureing Rabi frequency (dBm)
    qz = 277 #spinor quadratic Zeeman (Hz/G^2)
    qm = (Rf_resonance_frequency/700000)**2*qz
    qu = 10**((microwave_power-Pcalib)/10)*fRabi**2/(4 * microwave_detuning)
    return qm-qu
