# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 18:33:39 2015
Image objects for handling incoming images for SpinorMonitor
@author: zag
"""

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
import numpy as np
import BECMonitor_fitobject as fo
import time
import os

class ProcessImage(QtCore.QObject):
    """Processing object for threading purposes
    @parameters
        data: numpy array
        options: list of options for fit parameters"""
    def __init__(self,data,options,path,run):
        """initialize fit_object"""
        QtCore.QObject.__init__(self)
        self.fit = fo.fit_object(options[2], options[0],options[1], data)
        name = 'run_' + str(run) + 'index_' + str(options[2]) + '.txt'
        self.savePath = os.path.join(path,name)
        self.data = data
           
    @QtCore.pyqtSlot()
    def run(self):
        """process results using methods from fit process and emit"""
        #save image
        np.savetxt(self.savePath, self.data)
        self.fit.fit_image()
        #eventually modify for different pixel sizes
        results = self.fit.process_results(7.04,7.04)
        self.emit(QtCore.SIGNAL('fit_obj'),results)
        self.emit(QtCore.SIGNAL('finished()'))
        
        

class IncomingImage(QtCore.QThread):
    """check for images, if found obtain image and send back to main GUI"""
    def __init__(self):
        QtCore.QThread.__init__(self)
        self.data = None
        
    def run(self):
        """every second search folder for new images, if found
            get image and emit back to main gui for processing"""
        while(1>0):
            time.sleep(1)
            if self.newImage():
                #emit signal that image is recieved, wait for response
                self.emit(QtCore.SIGNAL('update(QString)'), 'Image Recieved')
                results = self.get_image()
                self.emit(QtCore.SIGNAL('packetReceived(PyQt_PyObject)'),
                          results)
                self.data = None
                
    def __del__(self):
        self.wait()
        
    def newImage(self):
        """This function checks in directory for new image with proper name
            if found, it reads it in and then deletes it"""
        #in future go to custom directory for now, just work
        try:
            self.data = np.loadtxt('newimage.txt')
            os.remove('newimage.txt')    
            return True
        except:
            return False
            
    def get_image(self):
        return self.data
        
    
