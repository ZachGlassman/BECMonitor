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
import inspect
import numpy as np

class Procedure(object):
    """Class for defining procedure to operate on data
     input will be separated into data from the experiment (images for us),
     parameter input which can be changed by the user live (such as fitting parameters)
     and other input which comes from the controlling program, but will not be part
     of the fitting widget such as a region of interest set in a different part.

     The function being wrapped must return a dictionary (or OrderedDict)

    :param name: Name of Procedure object
    :param func: Function defining operatoion of Procedure
    :param data: name of variable to be passed into function as data
    :param other: list of other variable which are not in control widget
    :param plot_vars: list of variables which should be live plotted when primary procedure
    """
    def __init__(self,name,func = None, data = None, other =[],plot_vars=[], *args, **kwargs):
        """Create Procedure object (can also subclass)
        """
        self.name = name
        self.other = other
        self.input = OrderedDict()
        self.data = data

        if data == None:
            print('No data entered, make sure you know what you are doing')
        #define operatation on data, should be function
        #will always be able to
        self.operation = None
        #plotting function
        self.plot_func = None
        #list of plotted variables must be six or less
        self.plot_vars = plot_vars
        if func:
            self._create_from_function(func,data,other)

    def _create_from_function(self,func,data=None,other=[]):
        """
        populate fields from function.  Test somewhat to make sure it has
        some of the relevent features.  It will infer parameters needed
        for gui entry from function signature.

        :param func: procedure function
        :param data: name of data
        :param other: other parameters
        """
        self.operation = func
        func_sig = inspect.signature(func)
        for param in func_sig.parameters.values():
            if param.name != data and param.name not in other:
                if param.default is param.empty:
                    self.input[param.name] = {'value':0,'min':None,'max':None}
                else:
                    try:
                        self.input[param.name] = param.default
                    except ValueError:
                        print('Parameter', param.name, 'does not have proper form')

        ans = self._test_function()
        if self.plot_vars == []:
            self.plot_vars = [i for i in ans.keys()]

    def get_plot_vars(self):
        """get the first six plot variables for plotting"""
        return self.plot_vars[:6]

    def _test_function(self):
        """tests function to ensure return values are dictionaries"""
        data=np.random.rand(100,100)
        test_params = {i:self.input[i]['value'] for i in self.input}
        test_params[self.data] = data
        for i in self.other:
            self
        return_ans = self.operation(**test_params)
        if isinstance(return_ans, dict):
            return return_ans
        else:
            raise ValueError


    def run(self, data, var_dict, other_dict):
        """run with a particular set of data and parameters"""
        pass

if __name__ == '__main__':
    """for testing purposes a main function"""
    def test_proc_one_func(data,x,y={'value':10,'max':100}):
        return {'val':x * y}
    test_proc_one = Procedure('test_proc_one',test_proc_one_func,data='data')
    print(test_proc_one.test_function())
