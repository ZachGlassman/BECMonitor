# -*- coding: utf-8 -*-
"""
Created on Thu May 28 19:13:32 2015
Data Table class to record information on each shot
@author: zag
"""
from pyqtgraph.Qt import QtGui

class DataTable(QtGui.QWidget):
    """tabbed tables to show system parameters and fitted parameters"""
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self)

        self.pandas_table = QtGui.QTableWidget()

        self.pandas_table.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
    
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.pandas_table)
        self.setLayout(layout)

        self.pandas_table_H_Labels = []


    def update_pandas_table(self, df):
        """update tables, check if cols are different"""
        new_cols = [i for i in df.columns.values.tolist() if i not in self.pandas_table_H_Labels]
        #now add new cols
        for i in range(len(new_cols)):
            """if 0 no loop will occur"""
            col = self.pandas_table.columnCount()
            self.pandas_table.insertColumn(col)
            self.pandas_table_H_Labels.append(new_cols[i])
            #might want to make this more veristile with not numbers
            for row in range(self.pandas_table.rowCount()):
                self.pandas_table.setItem(row, col,
                                          QtGui.QTableWidgetItem(
                                              str(df.iloc[row,i])))
        #now add new row and fill data
        num_rows = self.pandas_table.rowCount()
        self.pandas_table.insertRow(num_rows)
        col = 0
        for i in self.pandas_table_H_Labels:
            self.pandas_table.setItem(num_rows, col,
                                          QtGui.QTableWidgetItem(
                                              str(df[i][num_rows])))
            col = col + 1


        self.pandas_table.setHorizontalHeaderLabels(self.pandas_table_H_Labels)

#main routine for testing purposes

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    win = DataTable()
    win.show()
    #run this baby
    #now add fake data
    import pandas as pd
    import numpy as np
    df = pd.DataFrame(np.random.rand(10))
    print(df)
    win.update_pandas_table(df)
    sys.exit(app.exec_())
