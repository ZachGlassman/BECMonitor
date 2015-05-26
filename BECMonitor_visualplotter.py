# -*- coding: utf-8 -*-
"""
Created on Tue May 26 14:44:12 2015
Class to choose plots
@author: zag
"""
from pyqtgraph.Qt import QtCore, QtGui
from BECMonitor_ipython import SpinorPlot, PlotObj

class VisualPlotter(QtGui.QWidget):
    """Class to choose plotting visually so it is easy.  Will also 
    automatically update plots"""
    def __init__(self, parent = None):
         QtGui.QWidget.__init__(self)
         self.plots = PlotObj()
         self.data = None
         
         self.labelx = QtGui.QLabel(self) 
         self.labelx.setText('X variable')
         self.labely = QtGui.QLabel(self)
         self.labely.setText('Y variable')
         
         layout = QtGui.QGridLayout()
         layout.setSpacing(10)
         layout.addWidget(self.labelx,0,0)
         layout.addWidget(self.labelx,0,1)
         
         self.setLayout(layout)
         
    def update_plots(self ,data):
        self.data = data
        self.plots.update(self.data)
