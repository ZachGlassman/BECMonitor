# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 18:33:39 2015
Image objects for handling incoming images for SpinorMonitor
@author: zag
"""

from pyqtgraph.Qt import QtCore
import numpy as np
try:
    import BECMonitor.Fitobject as fo
except:
    import Fitobject as fo

import time
import os
from multiprocessing import Queue

class ProcessImage(QtCore.QObject):
    """Processing object for threading purposes
    @parameters
        data: numpy array
        options: list of options for fit parameters
                    [params,
                type_of_fit,
                ROI,
                index"""
    def __init__(self,data,exp_data,options,path,run):
        """initialize fit_object"""
        QtCore.QObject.__init__(self)
        self.q = Queue()
        self.fit = fo.fit_object(self.q,
                                 options[3], #index
                                 options[0], #params
                                 options[1], #type of fit
                                 options[2], #region of interest
                                    data)
        name = 'run_' + str(run) + 'index_' + str(options[3]) + '.txt'
        self.savePath = os.path.join(path,name)
        self.data = data
        self.index = options[3]
        self.exp_data = exp_data

    @QtCore.pyqtSlot()
    def run(self):
        """process results using methods from fit process and emit"""
        #save image
        np.savetxt(self.savePath, self.data)
        #self.fit.fit_image()
        #self.fit.multiple_fits()
        #eventually modify for different pixel sizes
        #results = self.fit.process_results(7.04,7.04)
        self.fit.start()
        results = self.q.get()
        self.fit.join()
        results[0].update(self.exp_data)
        results.append(self.index)
        self.emit(QtCore.SIGNAL('fit_obj'),results)
        time.sleep(2)
        self.emit(QtCore.SIGNAL('finished()'))
        time.sleep(1)
        self.q.close()
        #re assign q to try to get it garbage collected
        self.q = 0



class IncomingImage(QtCore.QThread):
    """check for images, if found obtain image and send back to main GUI"""
    def __init__(self, fname):
        QtCore.QThread.__init__(self)
        self.data = None
        self.exp_params = {'timing':0, 'spin':2}
        self.fname = fname

    def run(self):
        """every second search folder for new images, if found
            get image and emit back to main gui for processing"""
        while(1>0):
            time.sleep(1)
            if self.newImage():
                #emit signal that image is recieved, wait for response
                self.emit(QtCore.SIGNAL('update(QString)'), 'Image Recieved')
                results = {'image':self.data,'exp_params':self.exp_params}
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
            self.data = np.loadtxt(self.fname)
            os.remove(self.fname)
            #for now read in parameters in some useless format
            return True
        except:
            return False
