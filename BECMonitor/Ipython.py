# -*- coding: utf-8 -*-
"""
Created on Wed Apr  8 16:33:29 2015
BECMonitor IPYTHON routines
@author: zag
"""
import inspect
import matplotlib.pyplot as plt
import numpy as np
from qtconsole.rich_ipython_widget import RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager
from IPython.lib import guisupport
from pyqtgraph import QtCore

class QIPythonWidgetContainer(QtCore.QObject):
    """Ipython container class for multi-threading"""
    def __init__(self, parent = None):
        """initialize fit_object"""
        QtCore.QObject.__init__(self)
        self.ipy = QIPythonWidget()

class QIPythonWidget(RichJupyterWidget):
    """ Convenience class for a live IPython console widget.
    This widget lives within the main GUI
    """
    def __init__(self,customBanner=None,*args,**kwargs):
    
        super(QIPythonWidget, self).__init__(*args,**kwargs)
        self.kernel_manager = kernel_manager = QtInProcessKernelManager()
        kernel_manager.start_kernel()
        kernel_manager.kernel.gui = 'qt4'
        self.kernel_client = kernel_client = self._kernel_manager.client()
        kernel_client.start_channels()
        

        def stop():
            kernel_client.stop_channels()
            kernel_manager.shutdown_kernel()
            guisupport.get_app_qt4().exit()
        self.exit_requested.connect(stop)

    def pushVariables(self,variableDict):
        """ Given a dictionary containing name / value pairs,
        push those variables to the IPython console widget """
        self.kernel_manager.kernel.shell.push(variableDict)
     
        
    def clearTerminal(self):
        """ Clears the terminal """
        self._control.clear()
      
        
    def printText(self,text):
        """ Prints some plain text to the console """
        self._append_plain_text(text)
        
    def executeCommand(self,command):
        """ Execute a command in the frame of the console widget """
        self._execute(command,False)
     
    

class PlotObj(object):
    """class to hold  SpinorPlot objects"""
    def __init__(self):
        self.plots = {}
        
    def add_plot(self,plot,name):
        """Add plot to dictionary of plots to update"""
        if name in self.plots.keys():
            print('Need unique plot name')
        else:
            self.plots[name] = plot

            
    def update(self,var_dict):
        """update all plots in dictionary"""
        for i in self.plots.keys():
            self.plots[i].update_plot(var_dict)
            
class SpinorPlot(object):
    """class to plot with updating stuff"""
    def __init__(self, func, name = None, xaxis = None, yaxis = None):
        """initalize function with arguments in databinds
        only arguments which match pushed variables
        this is because pushed variables are in a dictionary
        so the keys will match"""
        self.data_binds = inspect.getargspec(func).args
        self.func = func
        self.f, self.ax = plt.subplots()
        self.name = name
        self.xaxis = xaxis
        self.yaxis = yaxis
        self.set_axis()
        plt.show()
        
    def update_plot(self, var_dict):
        self.ax.clear()
        toplot = self.func(*self.get_vars(var_dict))
        x = range(len(toplot))
        self.ax.scatter(x,toplot)
        self.set_axis()
        self.f.canvas.draw()
     
        
    def set_axis(self):
        if self.name != None:
            self.ax.set_title(self.name)
        if self.xaxis != None:
            self.ax.set_xlabel(self.xaxis)
        if self.yaxis != None:
            self.ax.set_ylabel(self.yaxis)
        
        
    def get_vars(self,var_dict):
        return tuple(np.asarray(var_dict[i]) for i in self.data_binds)

def uplot(func,name = None, xaxis = None, yaxis = None):
    """function assumes PlotObj has been initialized as Plot_obj"""
    Plot_obj.add_plot(SpinorPlot(func,name = name,xaxis = xaxis, yaxis =yaxis)
        ,name)
 

Plot_obj = PlotObj()
