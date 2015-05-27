# -*- coding: utf-8 -*-
"""
Created on Tue May 26 14:44:12 2015
Class to choose plots
@author: zag
"""
from pyqtgraph.Qt import QtCore, QtGui

#going to use matplotlib here
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt



class VisualPlotter(QtGui.QWidget):
    """Class to choose plotting visually so it is easy.  Will also 
    automatically update plots"""
    
    message = QtCore.pyqtSignal(str, name = 'message')
    def __init__(self, parent = None):
         QtGui.QWidget.__init__(self)
         self.plots = {}
         self.data = None
         self.index = 0
         self.start = 0
         self.end = None
         self.ignore_list = []
         self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
         
         
         self.labelx = QtGui.QLabel(self) 
         self.labelx.setText('X variable')
         self.labely = QtGui.QLabel(self)
         self.labely.setText('Y variable')
         
         
         self.entrystart = QtGui.QSpinBox()
         self.entryend = QtGui.QSpinBox()
         self.entrystart.setMinimum(0)
         self.entryend.setMinimum(0)
         
         self.checkstart = QtGui.QCheckBox('Set Start Index')
         self.checkend = QtGui.QCheckBox('Set End Index')
         self.ignore_b = QtGui.QPushButton('Ignore Indices')
         self.ignore_b.setToolTip('Enter Indices to ignore separated by ;, can use list slicing')
         self.ignore = QtGui.QTextEdit()
         
         
         #variable combo boxes
         self.xvars = QtGui.QComboBox()
         self.yvars = QtGui.QComboBox()
         self.xvars.addItem('Index')
         self.yvars.addItem('Index')
         #type
         #self.type = QtGui.QComboBox()
         #self.type.addItems('Scatter,Plot'.split(','))
         
         #set up matplotlib figure
         self.preview = plt.figure(figsize=(3,4))
         self.canvas = FigureCanvas(self.preview)
         self.ax = self.preview.add_subplot(111)

         
         #buttons

         self.plot_b = QtGui.QPushButton('Updating Plot')
         self.static_plot_b = QtGui.QPushButton('Static Plot')
         
         
         #going to use box layout
         #first row
         row1 = QtGui.QHBoxLayout()
         row1.addWidget(self.labelx)
         row1.addWidget(self.labely)
         #second row
         row2 = QtGui.QHBoxLayout()
         row2.addWidget(self.xvars)
         row2.addWidget(self.yvars)
         #third row
         row3 = QtGui.QHBoxLayout()
         row3.addWidget(self.canvas, stretch = 1)
         #third row column
         row3c2 = QtGui.QVBoxLayout()
         row3c2.addWidget(self.checkstart)
         row3c2.addWidget(self.entrystart)
         row3c2.addWidget(self.checkend)
         row3c2.addWidget(self.entryend) 
         row3c2.addWidget(self.ignore)
         row3c2.addWidget(self.ignore_b)
         row3c2.addStretch(2)
         row3.addLayout(row3c2)
         
         row4 = QtGui.QHBoxLayout()
         
         row4.addWidget(self.plot_b)
         row4.addWidget(self.static_plot_b)
         
         layout = QtGui.QVBoxLayout()
         layout.addLayout(row1)
         layout.addLayout(row2)
         layout.addLayout(row3)
         layout.addLayout(row4)

    
         self.setLayout(layout)
         
         #wire up the buttons        
         QtCore.QObject.connect(self.static_plot_b,
                               QtCore.SIGNAL('clicked()'), self.static_plot)
         QtCore.QObject.connect(self.ignore_b,
                               QtCore.SIGNAL('clicked()'), self.ignore_update) 
                               
         QtCore.QObject.connect(self.plot_b,
                                QtCore.SIGNAL('clicked()'), self.updating_plot)
        
         #connect changes to the test plot so it updates
         QtCore.QObject.connect(self.xvars,
                               QtCore.SIGNAL('activated(QString)'),
                               self.test_plot)
         QtCore.QObject.connect(self.yvars,
                               QtCore.SIGNAL('activated(QString)'),
                               self.test_plot)
         QtCore.QObject.connect(self.checkstart,
                               QtCore.SIGNAL('stateChanged(int)'),
                               self.test_plot)
         QtCore.QObject.connect(self.checkend,
                               QtCore.SIGNAL('stateChanged(int)'),
                               self.test_plot)
         QtCore.QObject.connect(self.entrystart,
                               QtCore.SIGNAL('valueChanged(int)'),
                               self.test_plot)
         QtCore.QObject.connect(self.entryend,
                               QtCore.SIGNAL('valueChanged(int)'),
                               self.test_plot)
                               
         
    
    def add_init_data(self,data):
        self.data = data
        self.plot_clicked()
     
        
    def update_plots(self ,data, index):
        """Update the updating plots whose references are stored in self.plots
        which is a dictionary
        Clean up the plots which are not there, I think if reference is lost
        garbage collection should clean them up? (need to check)"""
        self.data = data
        self.index = index
        self.test_plot()
        for i in self.plots.keys():
            if self.plots[i] == None:
                pass
            elif self.plots[i].isHidden():
               self.plots[i] = None
            else:
                x_data = self.filter_ignore(
                    self.data['spinorvars'][self.plots[i].xl][self.start:])
                y_data = self.filter_ignore(
                    self.data['spinorvars'][self.plots[i].yl][self.start:])
                self.plots[i].update(x_data,y_data)
                
    
        
        
    def var_push(self,var_list):
        """add a list of variables to options"""
        self.xvars.addItems(var_list)
        self.yvars.addItems(var_list)
        
        
    def plot_clicked(self):
        self.x = str(self.xvars.currentText())
        self.y = str(self.yvars.currentText())
        if self.checkstart.isChecked():
            self.start = self.entrystart.value()
        else:
            self.start = 0
        if self.checkend.isChecked():
            self.end = self.entryend.value()
        else:
            self.end = None
            
    def updating_plot(self):
        self.plot_clicked()
        #create new plot
        
        title = self.make_updating_title_string()
        if title not in self.plots.keys() or self.plots[title] == None:
            self.plots[title] = PopPlot()
    
        self.plots[title].update_init(self.x,self.y,
                                        title,
                                        self.ignore_list,
                                        self.start)
        
        self.message.emit('Plotted updating: ' + title)
        x_data = self.filter_ignore(
            self.data['spinorvars'][self.plots[title].xl][self.start:])
        y_data = self.filter_ignore(
            self.data['spinorvars'][self.plots[title].yl][self.start:])
        self.plots[title].update(x_data,y_data)
        self.plots[title].show()
        
        
    def static_plot(self):
        """create new modal popup"""
        self.plot_clicked()
        x_data = self.filter_ignore(
            self.data['spinorvars'][self.x][self.start:self.end])
        y_data = self.filter_ignore(
            self.data['spinorvars'][self.y][self.start:self.end])
                
        staticplot = PopPlot()
        title = self.make_title_string()
        staticplot.plot(x_data,y_data,self.x,self.y,title)
        self.message.emit('Plotted: ' + title)
        staticplot.show()
        
    def test_plot(self):
        self.plot_clicked()
        #get the variables
        self.x_data = self.filter_ignore(
            self.data['spinorvars'][self.x][self.start:self.end])
        self.y_data = self.filter_ignore(
            self.data['spinorvars'][self.y][self.start:self.end])
        self.ax.hold(False)
        self.ax.plot(self.x_data,self.y_data, 'r--')
        #self.ax.scatter(self.x_data,self.y_data)
        self.ax.set_xlabel(self.x)
        self.ax.set_ylabel(self.y)
        self.ax.set_title(self.make_title_string())
        self.canvas.draw()
    
        
        
        
    def make_title_string(self):
        """make a title string"""
        if self.end == None:
            ans = self.index
        else:
            ans = self.end
        
        return '{0} vs. {1} in ({2},{3})'.format(self.x,self.y,self.start,ans)
        
    def make_updating_title_string(self):
        """make a title string"""        
        return '{0} vs. {1} in ({2},\u221E)'.format(self.x,self.y,self.start)
        
    def filter_ignore(self, data):
        """filter data, list of indices to remove
        built list of indices not ignored"""
        ind = [i for i in range(self.index) if i not in self.ignore_list]
        return [data[i] for i in ind]
        
    def ignore_update(self):
        """update the ignore list parse out test"""
        text = self.ignore.toPlainText()
        if not text:
            self.ignore_list = []
        else:
            elements = text.split(';')
            #validate elements, should be int, or list comprehension
            val = [self.validate(i) for i in elements]
            flat_val = [item for sublist in val for item in sublist]
            if False in val:
                self.message.emit('Some Invalid Input')
            #filter elements for false
            self.ignore_list = list(set([i for i in flat_val if i != False]))
        
        self.message.emit(
            'Ignoring'+''.join((str(e)+',') for e in self.ignore_list) -',')
        self.test_plot()

    
    def validate(self,el):
        """valid to make sure is a single integer or list comprehension
        and turn list comprehensions into their equivalent
        definee here since its an object method in QTGUI"""
        def my_int(e):
            if not e:
                return None
            else:
                return int(e)
        
        try:
            return [int(el)]
        
        except:
            try:
                
                left,right = el.lstrip('[').rstrip(']').split(':')
                pos = [i for i in range(my_int(right))]
                return pos[my_int(left):my_int(right)]
            except:
                return False
        
class PopPlot(QtGui.QDialog):
    """popup class for plots"""
    def __init__(self, parent = None):
        QtGui.QDialog.__init__(self)
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self) 
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.toolbar)
        self.setLayout(layout)
        self.ax = self.figure.add_subplot(111)
        
    def update_init(self,xl,yl,title,ignore,start):
        self.xl = xl
        self.yl = yl
        self.start = start
        self.title = title
        self.ignore = ignore
    
    def plot(self,x,y,xl,yl,title):
        self.ax.plot(x,y, 'r--')
        self.ax.set_xlabel(xl)
        self.ax.set_ylabel(yl)
        self.ax.set_title(title)
        self.canvas.draw()
        
    def update(self,x,y):
        self.plot(x,y,self.xl,self.yl,self.title)
        

        
        