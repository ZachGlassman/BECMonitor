# -*- coding: utf-8 -*-
"""
Created on Thu May 28 19:13:32 2015
Data Table class to record information on each shot
@author: zag
"""
from pyqtgraph.Qt import QtGui,QtCore

class DataTableModel(QtCore.QAbstractTableModel):
    """Abstract model for datatable
    need to imlement several functions"""
    def __init__(self, data_in, header_data, parent=None):
        QtCore.QAbstractTableModel.__init__(self)
        self.data = data_in
        self.h_data = header_data

    def rowCount(self, parent):
        """count rows in padnas DataFrame"""
        return len(self.data.index)

    def columnCount(self, parent):
        """count columns in pandas DataFrame"""
        return len(self.data.columns)

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self.h_data)

    def data(self,):
        pass

    def insertRows(self):
        self.beginInsertRows()
        #do stuff
        self.endInsertRows()

    def insertColumns(self):
        self.beginInsertColumns()
        #do stuff
        self.endInsertColumns()

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


    def bulk_update_pandas_table(self, df):
        """update tables with more than one element"""
        for _ in range(len(df)):
            self.update_pandas_table(df)



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
    num_rows = 5000
    num_columns = 10
    df = pd.DataFrame(np.random.rand(num_rows,num_columns))
    df.columns = ['a'*i for i in range(num_columns)]
    print(df)
    for _ in range(len(df.index)):
        win.update_pandas_table(df)
    sys.exit(app.exec_())
