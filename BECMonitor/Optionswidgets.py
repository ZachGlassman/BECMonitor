# -*- coding: utf-8 -*-
"""
Created on Thu May 28 11:07:37 2015
Options classes for spinor monitor
@author: zag
"""
from pyqtgraph.Qt import QtCore, QtGui
from lmfit import Parameters

class ParameterEntry(QtGui.QWidget):
    """popup box to select parameters"""
    def __init__(self, params ,first, parent = None):
        QtGui.QWidget.__init__(self,parent)
        self.setWindowTitle('Spinor Parameters')
        layout = QtGui.QGridLayout()
        layout.setSpacing(10)
        self.params = params
        self.first = first #check if lock to previous value
        #create a dict of QLineEdit Objects and another dict of labels
        self.edits = {}
        self.mins = {}
        self.maxs = {}
        self.labels = {}
        self.top = {}
        self.free = {}
        kk = 0
        for i in ['Parameters','Value','Minimum','Maximum','Fixed']:
            self.top[i] = QtGui.QLabel(self)
            self.top[i].setText(i)
            layout.addWidget(self.top[i],0,kk,1,1)
            kk = kk + 1
        k = 1
        for key in self.params.keys():
            self.edits[key] = QtGui.QLineEdit(self)
            self.mins[key] = QtGui.QLineEdit(self)
            self.maxs[key] = QtGui.QLineEdit(self)
            self.labels[key] = QtGui.QLabel(self)
            self.free[key] = QtGui.QCheckBox(self)
            if self.first:
                self.edits[key].setText(str(self.params[key].value))
            else:
                self.edits[key].setText('N/A')
            self.mins[key].setText(str(self.params[key].min))
            self.maxs[key].setText(str(self.params[key].max))
            self.labels[key].setText(key)

            layout.addWidget(self.labels[key],k,0,1,1)
            layout.addWidget(self.edits[key],k,1,1,1)
            layout.addWidget(self.mins[key],k,2,1,1)
            layout.addWidget(self.maxs[key],k,3,1,1)
            layout.addWidget(self.free[key],k,4,1,1)
            k = k + 1



        self.setLayout(layout)

    def readout(self):
        """function to return updated Parameters object"""
        try:
            """try to readout, return 0 if no error, 1 if error"""
            for key in self.params.keys():
                if self.first:
                    self.params[key].value = float(self.edits[key].text())

                if self.maxs[key].text() == 'None':
                    toMax = None
                else:
                    toMax = float(self.maxs[key].text())

                self.params[key].min = float(self.mins[key].text())
                self.params[key].max = toMax
                self.params[key].vary = not self.free[key].isChecked()
            return 0

        except:
            return 1



class Options(QtGui.QWidget):
    """Panel which defines options for fitting and analyzing images"""
    message = QtCore.pyqtSignal(str, name = 'message')
    fit_name = QtCore.pyqtSignal(str, name = 'fit_name')
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)

        #4 different parameter objects for multiple fits!!!!
        self.params = {}
        self.num_fits = {}
        #num_fits to keep track of number of fits (really number of extra fits)
        self.types = ['Mixture', 'Stern-Gerlach']
        self.params_choose = {}
        self.fit_type_l = QtGui.QLabel()
        self.fit_type_l.setText('Fit Type')
        self.fit_type_chooser = QtGui.QComboBox()
        self.fit_type_chooser.addItems(self.types)


        self.stacked_params = QtGui.QStackedLayout()
        self.tabs = {}
        self.scroll = {}
        for i in self.types:
            self.type_of_fit = i
            self.num_fits[i] = 0
            self.params[i] = {}
            self.params_choose[i] = {}
            self.tabs[i] = QtGui.QTabWidget()
            self.create_fit_panel()
            self.scroll[i] = QtGui.QScrollArea()
            self.scroll[i].setWidget(self.tabs[i])
            self.stacked_params.addWidget(self.scroll[i])


        #buttons
        self.add_fit_b = QtGui.QPushButton('Add Fit')
        self.remove_fit_b = QtGui.QPushButton('Remove Fit')
        self.save_params_b = QtGui.QPushButton('Save')
        self.get_fit_info_b = QtGui.QPushButton('Current Fit Info')
        self.get_fit_info_b.setToolTip('Current Saved Fit')
        #connect buttons
        QtCore.QObject.connect(self.save_params_b,
                               QtCore.SIGNAL('clicked()'),
                               self.save_params)
        QtCore.QObject.connect(self.add_fit_b,
                               QtCore.SIGNAL('clicked()'),
                               self.create_fit_panel)
        QtCore.QObject.connect(self.remove_fit_b,
                               QtCore.SIGNAL('clicked()'),
                               self.remove_fit_panel)
        QtCore.QObject.connect(self.get_fit_info_b,
                               QtCore.SIGNAL('clicked()'),
                               self.get_fit_info)
        QtCore.QObject.connect(self.fit_type_chooser,
                               QtCore.SIGNAL('activated(int)'),
                               self.stacked_params.setCurrentIndex)
        QtCore.QObject.connect(self.fit_type_chooser,
                               QtCore.SIGNAL('activated(QString)'),
                               self.set_current_fit)

        buttons = QtGui.QHBoxLayout()

        buttons.addWidget(self.add_fit_b)
        buttons.addWidget(self.remove_fit_b)
        buttons.addWidget(self.get_fit_info_b)
        buttons.addWidget(self.save_params_b)

        top_layout = QtGui.QHBoxLayout()
        top_layout.addWidget(self.fit_type_l)
        top_layout.addWidget(self.fit_type_chooser)

        layout = QtGui.QVBoxLayout()
        layout.setSpacing(10)
        layout.addLayout(top_layout)
        layout.addLayout(self.stacked_params)
        layout.addLayout(buttons)
        self.setLayout(layout)
        self.type_of_fit = self.fit_type_chooser.currentText()

    def set_current_fit(self,fit_name):
        self.type_of_fit = fit_name


    def save_params(self):
        """update params"""
        for key in self.params[self.type_of_fit].keys():
            err = self.params_choose[self.type_of_fit][key].readout()
            if err == 1:
                print('Error')
        self.message.emit('Updated Parameters')
        self.fit_name.emit(self.fit_type_chooser.currentText())


    def make_key(self,index):
        return 'Fit {0}'.format(index)

    def create_fit_panel(self):
        """create a fit panel"""
        key = self.make_key(self.num_fits[self.type_of_fit])
        if self.num_fits[self.type_of_fit] == 0:
            first = True
        else:
            first = False
        self.num_fits[self.type_of_fit] = self.num_fits[self.type_of_fit] + 1
        self.params[self.type_of_fit][key] = Parameters()


        #name, Value, Vary,Min,Max, Expr
        if self.type_of_fit == 'Mixture':
            self.params[self.type_of_fit][key].add_many(
                    ('ABEC',1,True,0,None,None),
                    ('ATherm',.2,True,.01,None,None),
                    ('dxBEC',10,True,0,None,None),
                    ('dyBEC',10,True,0,None,None),
                    ('dxTherm',30,True,25,None,None),
                    ('dyTherm',30,True,25,None,None),
                    ('x0BEC',120,True,0,None,None),
                    ('y0BEC',120,True,0,None,None),
                    ('x0Therm',120,True,0,None,None),
                    ('y0Therm',120,True,0,None,None),
                    ('offset',0,True,0,None,None),
                    ('theta',0,True,0,None,None))

        elif self.type_of_fit == 'Stern-Gerlach':
            self.params[self.type_of_fit][key].add_many(
                    ('ABECp1',1,True,0,None,None),
                    ('ABEC0',1,True,0,None,None),
                    ('ABECm1',1,True,0,None,None),
                    ('dxBECp1',10,True,0,None,None),
                    ('dxBEC0',10,True,0,None,None),
                    ('dxBECm1',10,True,0,None,None),
                    ('dyBECp1',10,True,0,None,None),
                    ('dyBEC0',10,True,0,None,None),
                    ('dyBECm1',10,True,0,None,None),
                    ('x0BECp1',65,True,0,None,None),
                    ('x0BEC0',120,True,0,None,None),
                    ('x0BECm1',180,True,0,None,None),
                    ('y0BECp1',120,True,0,None,None),
                    ('y0BEC0',120,True,0,None,None),
                    ('y0BECm1',120,True,0,None,None),
                    ('offset',0,True,0,None,None),
                    ('theta',0,True,0,None,None))

        #spawn parameter chooser
        self.params_choose[self.type_of_fit][key] = ParameterEntry(
            self.params[self.type_of_fit][key],
            first = first)
        self.tabs[self.type_of_fit].addTab(self.params_choose[self.type_of_fit][key],key)
        self.message.emit('Inialized Fit {0}'.format(self.num_fits[self.type_of_fit]-1))

    def remove_fit_panel(self):
        """remove fit panel"""
        if self.num_fits[self.type_of_fit] > 1:
            self.num_fits[self.type_of_fit] = self.num_fits[self.type_of_fit] -1
            key = self.make_key(self.num_fits[self.type_of_fit])
            self.tabs.removeTab(self.num_fits[self.type_of_fit])
            self.params[self.type_of_fit].pop(key)
            self.params_choose[self.type_of_fit].pop(key)
            self.message.emit('Removed Fit {0}'.format(self.num_fits[self.type_of_fit]))
        else:
            self.message.emit('Cannot remove all fits')


    def get_fit_info(self):
         """popup window which has info of all fits"""
         dialog = FitInfo(self.params[self.type_of_fit])
         if dialog.exec_():
             pass



class FitInfo(QtGui.QDialog):
    """custom dialog for fit information"""
    def __init__(self, params, parent = None):
        QtGui.QDialog.__init__(self,parent)
        self.resize(1300,500)
        self.setWindowTitle('Fit Information')
        self.params = params
        self.exit_b = QtGui.QPushButton("Close", self)
        self.num_fits = len(self.params)

        QtCore.QObject.connect(self.exit_b,
                               QtCore.SIGNAL('clicked()'),
                               self.close)

        #make a bunch of tables, number of columns is N_params
        #number of rows is num_fits
        self.tabs = QtGui.QTabWidget()
        table_names = ['Value', 'Min', 'Max', 'Fix']
        self.tables = {}
        for i in table_names:
            self.tables[i] = QtGui.QTableWidget(self)
            self.tables[i].setRowCount(self.num_fits)
            self.tables[i].setColumnCount(len(self.params['Fit 0']))
            self.tables[i].setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        #labels
            self.tables[i].setHorizontalHeaderLabels(list(self.params['Fit 0'].keys()))
            self.tables[i].setVerticalHeaderLabels(
                ['Fit {0}'.format(i) for i in range(self.num_fits)])
            self.tabs.addTab(self.tables[i], i)


        self.parse_params(table_names)


        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.tabs)
        layout.addWidget(self.exit_b)
        self.setLayout(layout)

    def parse_params(self,tabs):
        """populates the tables, row and column determined by run and
        parameter, so same for all table"""

        row = 0
        for key in ['Fit {0}'.format(i) for i in range(self.num_fits)]:
            """loop through rows"""
            col = 0
            for param in self.params[key].keys():
                p = self.params[key][param]
                if row == 0:
                    val = str(p.value)
                else:
                    val = 'N/A'
                self.tables['Value'].setItem(row, col,
                     QtGui.QTableWidgetItem(val))
                self.tables['Min'].setItem(row, col,
                     QtGui.QTableWidgetItem(str(p.min)))
                self.tables['Max'].setItem(row, col,
                     QtGui.QTableWidgetItem(str(p.max)))
                self.tables['Fix'].setItem(row, col,
                     QtGui.QTableWidgetItem(str(not p.vary)))
                col = col + 1
            row = row + 1
    
    def close(self):
        self.accept()

class PlotOptions(QtGui.QWidget):
    """Widget for Region of Interest Information and other plot options"""
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        #get region of interest button
        self.get_roi = QtGui.QPushButton("Get ROI",self)

        info = QtGui.QLabel()
        info.setText('Select ROI on top screen and click')

        self.labels_list = ['x<sub>0','x<sub>1','y<sub>0','y<sub>1',u"\u03F4"]
        self.aux_list = ['x Pixel size', 'y Pixel size']
        self.pixels = {}
        self.labels = {}
        self.roi = {}


        layout = QtGui.QHBoxLayout()
        layout1 = QtGui.QVBoxLayout()
        layout2 = QtGui.QVBoxLayout()
        layout.addLayout(layout1)
        layout.addLayout(layout2)


        layout1.addWidget(info)
        row = QtGui.QHBoxLayout()

        row.addWidget(self.get_roi)
        layout1.addLayout(row)

        for i in self.labels_list:
            self.labels[i] = QtGui.QLabel(self)
            self.labels[i].setText(i)
            self.roi[i] = QtGui.QLineEdit(self)
            self.roi[i].setReadOnly(True)
            row = QtGui.QHBoxLayout()
            row.addWidget(self.labels[i])
            row.addWidget(self.roi[i])
            layout1.addLayout(row)

        for i in ['x Pixel size', 'y Pixel size']:
            lab = QtGui.QLabel(self)
            lab.setText(i)
            self.pixels[i] = QtGui.QDoubleSpinBox()
            self.pixels[i].setValue(3.52)
            row = QtGui.QHBoxLayout()
            row.addWidget(lab)
            row.addWidget(self.pixels[i])
            layout2.addLayout(row)

        self.setLayout(layout)

    def set_roi(self,vec):
        """Generate roi strings and print coords"""
        k = 0
        for i in self.labels_list:
            self.roi[i].setText("{:>.2f}".format(vec[k]))
            k = k + 1
