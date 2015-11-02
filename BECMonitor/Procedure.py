# -*- coding: utf-8 -*-
"""
Created on Fri Oct 30 16:54:53 2015
Generalize Procedure class for doing anything to data
define both main function for processing and
optionally plotting functions for shot to shot
Two calculated plots and six parameter plots may be designated

Specific procedures will be subclassed.
@author: zachglassman
"""
from collections import OrderedDict

class Procedure(object):
    """Class for defining procedure to operate on data"""
    def __init__(self,name):
        if isinstance(name,str):
            self.name = name
        else:
            print('Need real name for this')

        #input, output, data, names bound to types for specific purpose
        #will be ordered dictionary for consistence
        self.input = OrderedDict()
        self.output = OrderedDict()
        self.data = OrderedDict()
        #define operatation on data, should be function
        #will always be able to
        self.operation = None
        #plotting function
        self.plot_func = None
        #list of plotted variables must be six or less
        self.plot_vars = []


    @property
    def operation(self):
        return self._operation

    @operation.setter
    def operation(self, val):
        """set the function"""
        self._operation = val

    @property
    def plot_vars(self):
        return self._plot_vars

    @plot_vars.setter
    def plot_vars(self, var_list):
        self._plot_vars = var_list[:6]
