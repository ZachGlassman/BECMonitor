# -*- coding: utf-8 -*-
"""
Created on Fri Mar 13 16:54:53 2015
This Contains Routines called by BECMonitor
@author: zachglassman
"""
import numpy as np
from lmfit import minimize, Parameters, Parameter, report_fit

"""
For all routines involved with fitting, we will use a global parameters object
with the following attributes
    ABEC    - amplitude of Thomas-Fermi profile - linked to NBEC atoms
    ATherm  - amplitude of Gaussian profile - linked to NTherm
    dxBEC   - x width of Thomas-Fermi
    dyBEC   - y width of Thomas-Fermi
    dxTherm - x width of Gaussian (or enhanced Gaussian) profile
    dyTherm - y width of Gaussian (or enhanced Gaussian) profile
    x0BEC   - x center of Thomas-Fermi profile
    y0BEC   - y center of Thomas-Fermi profile
    x0Therm - x center of Gaussian profile
    offset  - offset to fits
    theta   - rotation of x-y plane

These routines  are mostly used with the BECMonitor program, however they are
also proper for themselves.  They will be implemented within a fit object which
contains the data and fitted routines.
"""
            
class fit_object(object):
    """fit object holds all the information for a single fit
        initiated with a name and a params_dict which contains:
            file location of image
            inital guesses for parameters
            restrictions on parameters
            fit type
            region of interest
    """
    
    def __init__(self, index, params, roi, data):
        """initalize with name and params_dict and global object variables
          variables:
          image_raw - image to analyze
          image_corrected - image with background corrections applied
          image_fitted - image once its been fitted
          fit_results_raw - dictionary raw results of fit
          fit_results - dictionary of final results of fit
          
        """
        self.name = index
        self.image = data[roi[0]:roi[1],roi[2]:roi[3]]
        self.image_fitted = None
        self.fit_results = None
        self.pad = [roi[0],data.shape[0]-roi[1],roi[2],data.shape[1]-roi[3]]
        self.x, self.y = self.create_vecs(roi)
        self.params = params
        #create lmfit parameters object
        #self.params = Parameters()
        #for i in params_dict.keys():
            #self.params.add(i, value = params_dict[i], min = 0)
            
    def create_vecs(self,roi):
        """create vectors scaled by pixel size"""
        y = np.arange(roi[0],roi[1],1)
        x = np.arange(roi[2],roi[3], 1)
        X,Y = np.meshgrid(x,y)
        return X,Y
        
    def gauss_2D(self):
        """two dimensional Gaussian which is not normalized of the form
         G = A * exp(-1/2 *(x-x0)^2/dx^2-1/2 * (y-y0)^2/dy^2)
        """
        #read out
        x0 = self.params['x0Therm'].value
        y0 = self.params['y0Therm'].value
        theta = self.params['theta'].value
        A = self.params['ATherm'].value
        dx = self.params['dxTherm'].value
        dy = self.params['dyTherm'].value
        off = self.params['offset'].value
        xc = (self.x-x0)*np.cos(theta) - (self.y-y0)*np.sin(theta)
        yc = (self.x-x0)*np.sin(theta) - (self.y-y0)*np.cos(theta)
        a = np.divide(np.power(xc,2), (2 * dx**2))
        b = np.divide(np.power(yc,2), (2 * dy**2))
        return off + A * np.exp(-a-b)
      
    def TF_2D(self):
        #need to enter actual profile
        """two dimensional Thomas Fermi which is not normalized of the form
        TF =
        """
        x0 = self.params['x0BEC'].value
        y0 = self.params['y0BEC'].value
        theta = self.params['theta'].value
        A = self.params['ABEC'].value
        dx = self.params['dxBEC'].value
        dy = self.params['dyBEC'].value
        off = self.params['offset'].value
        xc = (self.x-x0)*np.cos(theta) - (self.y-y0)*np.sin(theta)
        yc = (self.x-x0)*np.sin(theta) - (self.y-y0)*np.cos(theta)
        a = (np.divide((xc),dx))**2
        aa = (np.divide((yc),dy))**2
        bb = np.subtract(np.subtract(1, a), aa)
        c = np.zeros(bb.shape)
        b = np.power(np.maximum(bb,c),3/2)
        return off + np.multiply(A,b) 
        
    def bimod2min(self,params):
        """function to minimize, need to subtract offset since included
            in both terms"""
        a = self.TF_2D() + self.gauss_2D() - self.params['offset'].value 
        b = a - self.image
        return b.ravel()
        
    def subtract_background(self):
        """Subtract background from image
        @params
          none
        @returns
          null, but modifies image_corrected
        """
        #subtract the background
        pass
      
      
    #need to add functionality for other stuff
    def fit_image(self):
        """fit corrected image with parameters from params"""
        self.fit_results = minimize(self.bimod2min, self.params, 
                                    args = ())
        #report_fit(self.fit_results)
        
    def process_results(self, scalex,scaley):
        """process results of fit and allow output return dictonary
           scale with the appropriate pixel values after fit"""
        results = {}
        #need to write actual function for amplitudes, but whatever
        #dictionary binding results to graph names
        results = {"N_BEC_Atoms":self.BEC_num(scalex,scaley),
               "N_Therm_Atoms":self.Therm_num(scalex,scaley),
               "X_Width":self.params['dxBEC'].value * scalex,
               "Y_Width":self.params['dyBEC'].value * scaley,
               "Temperature":self.params['dxTherm'].value * scalex,
               "All":1}
        results['index'] = self.name
        results['fitted'] = self.line_profile()
        
        return results
        
    def BEC_num(self, scalex,scaley):
        A = self.params['ABEC']
        Rx = self.params['dxBEC'].value * scalex
        Ry = self.params['dyBEC'].value * scaley
        sigma =  3 * (0.5891583264**2)/(2 * np.pi)
        V = 2*np.pi/5 * A* Rx * Ry
        return V/sigma
    
    def Therm_num(self, scalex,scaley):
        A = self.params['ATherm']
        Rx = self.params['dxTherm'].value * scalex
        Ry = self.params['dyTherm'].value* scaley
        sigma =  3 * (0.5891583264**2)/(2 * np.pi)
        V = 2*np.pi* A* Rx * Ry
        return V/sigma
        
    def line_profile(self):
        """calculate line profile, with zeroes to make full image"""
        calc = self.TF_2D() + self.gauss_2D() - self.params['offset'].value
        a = np.pad(calc, ((self.pad[0],self.pad[1]), (self.pad[2],self.pad[3])), 
                   mode='constant', constant_values=0)
        return a