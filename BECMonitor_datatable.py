# -*- coding: utf-8 -*-
"""
Created on Thu May 28 19:13:32 2015
Data Table class to record information on each shot
@author: zag
"""
from pyqtgraph.Qt import QtCore, QtGui

class DataTable(QtGui.QWidget):
    """tabbed tables to show system parameters and fitted parameters"""
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self)
        
        self.fit_table = QtGui.QTableWidget()
        self.exp_table = QtGui.QTableWidget()
        
        self.tabs = QtGui.QTabWidget()
        
        self.tabs.addTab(self.fit_table,'Fitted Paramters')
        self.tabs.addTab(self.exp_table,'Experimental Parameters')
        
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)
