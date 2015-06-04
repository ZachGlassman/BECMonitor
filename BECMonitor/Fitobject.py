# -*- coding: utf-8 -*-
"""
Created on Fri Mar 13 16:54:53 2015
This Contains Routines called by BECMonitor
@author: zachglassman
"""
import numpy as np
from lmfit import minimize, Parameters, Parameter, report_fit
import copy

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
    
    def __init__(self, index, params, type_of_fit, roi, data):
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
        self.num_fits = len(params[type_of_fit])
        self.fit_names =  ['Fit {0}'.format(i) for i in range(self.num_fits)]
        self.all_params = copy.deepcopy(params[type_of_fit])#deep copy just to make sure
        self.fit_type = type_of_fit
        
        #dictionary binding type of fits to functions        
        self.fit_dict = {
            'Mixture':self.bimod2min,
            'Stern-Gerlach': self.sg2min
        }

            
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
        
    def stern_gerlach_2D(self):
        """2 dimensional three thomas fermi distributions"""
        Ap1 = self.params['ABECp1'].value
        A0 = self.params['ABEC0'].value
        Am1 = self.params['ABECm1'].value
        dxp1 = self.params['dxBECp1'].value
        dx0 = self.params['dxBEC0'].value
        dxm1 = self.params['dxBECm1'].value
        dyp1 = self.params['dyBECp1'].value
        dy0 = self.params['dyBEC0'].value
        dym1 = self.params['dyBECm1'].value
        x0p1 = self.params['x0BECp1'].value
        x00 = self.params['x0BEC0'].value
        x0m1 = self.params['x0BECm1'].value
        y0p1 = self.params['y0BECp1'].value
        y00 = self.params['y0BEC0'].value
        y0m1 = self.params['y0BECm1'].value
        offset = self.params['offset'].value
        theta = self.params['theta'].value
        xcp1, ycp1 = self.get_angled_line(x0p1,y0p1,theta)
        xc0, yc0 = self.get_angled_line(x00,y00,theta)
        xcm1, ycm1 = self.get_angled_line(x0m1,y0m1,theta)
        TFp1 = self.partial_TF_2D(xcp1,ycp1,Ap1,dxp1,dyp1,theta)
        TF0 = self.partial_TF_2D(xc0,yc0,A0,dx0,dy0,theta)
        TFm1 = self.partial_TF_2D(xcm1,ycm1,Am1,dxm1,dym1,theta)
        return TFp1 + TF0 + TFm1 + offset
    
    def partial_TF_2D(self,xc,yc,A,dx,dy,theta):
        a = (np.divide((xc),dx))**2
        aa = (np.divide((yc),dy))**2
        bb = np.subtract(np.subtract(1, a), aa)
        c = np.zeros(bb.shape)
        b = np.power(np.maximum(bb,c),3/2)
        return np.multiply(A,b) 
        
    def get_angled_line(self,x0,y0,theta):
        xc = (self.x-x0)*np.cos(theta) - (self.y-y0)*np.sin(theta)
        yc = (self.x-x0)*np.sin(theta) - (self.y-y0)*np.cos(theta)
        return xc, yc
        
    def bimod2min(self,params):
        """function to minimize, need to subtract offset since included
            in both terms"""
        a = self.TF_2D() + self.gauss_2D() - self.params['offset'].value 
        b = a - self.image
        return b.ravel()
       
    def sg2min(self, params):
        a = self.stern_gerlach_2D() - self.image     
        return a.ravel()
        
        
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
        self.params = self.all_params['Fit 0']
        self.fit_results = minimize(self.fit_dict[self.fit_type], self.params, 
                                    args = ())
        #report_fit(self.fit_results)
                                    
    def multiple_fits(self):
        """function to fit sequentially with input defined from SpinorMonitor
        we may need to take parameters of previous fit!!
        do fit, update values, do next fit"""
        k = 1
        for key in self.fit_names:
            #get params for this fit
            self.params = copy.deepcopy(self.all_params[key])
            
            results = minimize(self.fit_dict[self.fit_type], self.params, 
                                    args = ())
                                   
            #then if k > num_fits copy result values to params dictionary and fit
            if k < self.num_fits:
                #update parameters
                next_key = self.fit_names[k]
                for i in self.all_params[next_key].keys():
                    self.all_params[next_key][i].value = self.params[i].value
                   
                #move to next iteration
                k = k + 1
            
        self.fit_results = results
        
                                    
                                    
                                    
    def process_results(self, scalex,scaley):
        """process results of fit and allow output return dictonary
           scale with the appropriate pixel values after fit"""
        results = {}
        #need to write actual function for amplitudes, but whatever
        #dictionary binding results to graph names
        if self.fit_type == 'Mixture':
            results = {"N_BEC_Atoms":self.BEC_num(scalex,scaley),
                       "N_Therm_Atoms":self.Therm_num(scalex,scaley),
                       "X_Width":self.params['dxBEC'].value * scalex,
                       "Y_Width":self.params['dyBEC'].value * scaley,
                       "Temperature":self.params['dxTherm'].value * scalex,
                       "All":1}
            results['Index'] = self.name
        elif self.fit_type == 'Stern-Gerlach':
            Ap1 = self.params['ABECp1'].value
            A0 = self.params['ABEC0'].value
            Am1 = self.params['ABECm1'].value
            dxp1 = self.params['dxBECp1'].value 
            dx0 = self.params['dxBEC0'].value 
            dxm1 = self.params['dxBECm1'].value 
            dyp1 = self.params['dyBECp1'].value
            dy0 = self.params['dyBEC0'].value
            dym1 = self.params['dyBECm1'].value
            Np1 = self.BEC_num_1(scalex,scaley,Ap1,dxp1,dyp1)
            N0 = self.BEC_num_1(scalex,scaley,A0,dx0,dy0)
            Nm1 = self.BEC_num_1(scalex,scaley,Am1,dxm1,dym1)
            results = {"N_BEC_Atoms1":Np1,
                       "N_BEC_Atoms0":N0,
                       "N_BEC_Atoms-1":Nm1,
                       "X_Width1":dxp1*scalex,
                       "X_Width0":dx0*scalex,
                       "X_Width-1":dxm1*scalex,
                       "Magnetization":Np1-Nm1/(Np1+N0+Nm1),
                       }
            results['Index'] = self.name
        
        return [results, self.line_profile()]
        
    def BEC_num(self, scalex,scaley):
        A = self.params['ABEC']
        Rx = self.params['dxBEC'].value * scalex
        Ry = self.params['dyBEC'].value * scaley
        sigma =  3 * (0.5891583264**2)/(2 * np.pi)
        V = 2*np.pi/5 * A* Rx * Ry
        return V/sigma
        
    def BEC_num_1(self, scalex,scaley,A,dx,dy):
        """helper function for BEC num"""
        Rx = dx * scalex
        Ry = dy * scaley
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
        if self.fit_type == 'Mixture':
            calc = self.TF_2D() + self.gauss_2D() - self.params['offset'].value
        else:
            calc = self.stern_gerlach_2D()
        a = np.pad(calc, ((self.pad[0],self.pad[1]), (self.pad[2],self.pad[3])), 
                   mode='constant', constant_values=0)
        return a