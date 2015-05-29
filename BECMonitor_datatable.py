# -*- coding: utf-8 -*-
"""
Created on Thu May 28 19:13:32 2015
Data Table class to record information on each shot
@author: zag
"""
from pyqtgraph.Qt import QtCore, QtGui
import copy

class DataTable(QtGui.QWidget):
    """tabbed tables to show system parameters and fitted parameters"""
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self)
        
      
        self.fit_table = QtGui.QTableWidget()
        self.exp_table = QtGui.QTableWidget()
        self.fit_table.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.exp_table.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.tabs = QtGui.QTabWidget()
        
        self.tabs.addTab(self.fit_table,'Fitted Paramters')
        self.tabs.addTab(self.exp_table,'Experimental Parameters')
        
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        
        #now for labels as lists!!! (dicts not ordered)
        self.fit_table_H_Labels = []
        self.exp_table_H_Labels = []
     
        
    def update_exp_table(self,params_dict,names):
        """function to update exp params table"""
        num_rows = self.fit_table.rowCount()
        self.exp_table.insertRow(num_rows) 
        #check if names is the same as in memory, same order always
        diff = len(names) - len(self.exp_table_H_Labels) 
        if diff > 0:
            """this mean there has been a new experimental parameter report
                need to add columns with that name"""
            for i in range(diff):
                new_column_pos = self.exp_table.columnCount()
                self.exp_table.insertColumn(new_column_pos)
            #now set names of all columns
            self.exp_table.setHorizontalHeaderLabels(names)
        #now update names
        self.exp_table_H_Labels = names
        # now insert data into rows
        col = 0
        for i in names:
            self.exp_table.setItem(num_rows, col,
                            QtGui.QTableWidgetItem(str(params_dict[i])))
            col = col + 1
        
        self.exp_table.setVerticalHeaderLabels(
                [str(k) for k in range(num_rows+1)])
                
      
      
    def update_fit_table(self, params):
        temp = copy.deepcopy(params['spinorvars']) #deep copy necessary
        num_rows = self.fit_table.rowCount()
        self.fit_table.insertRow(num_rows) 
        col = 0
        #position of value is last in list of temp
        for i in self.fit_table_H_Labels:
           self.fit_table.setItem(num_rows, col,
                     QtGui.QTableWidgetItem(str(temp[i][-1])))

           col = col + 1
        #update labels which are just the index list
        self.fit_table.setVerticalHeaderLabels([str(i) for i in temp['Index']])
                            
                
                
    def init_fit_params(self, params_list):
        """since we know fit parameter's won't change shot to shot
           we can set table colums upon initiation"""
        self.fit_table.setColumnCount(len(params_list)-1)
        self.fit_table_H_Labels = [i for i in params_list if i != 'Index']
        self.fit_table.setHorizontalHeaderLabels(self.fit_table_H_Labels)
      
        
    
    
