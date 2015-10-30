# -*- coding: utf-8 -*-
"""
Created on Fri Oct 30 16:54:53 2015
Generalize Procedure class for doing anything to data
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

    @property
    def operation(self):
        return self.__operation

    @operation.setter
    def operation(self, val):
        """function in case we want to restrict at some point"""
        self.__operation = val
