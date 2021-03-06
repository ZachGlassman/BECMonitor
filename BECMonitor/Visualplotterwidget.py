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
from matplotlib.figure import Figure
from lmfit import Parameters, fit_report
import numpy as np
import copy
#here we import models for fits
try:
    from BECMonitor.Fitmodels import sinMod, gaussMod, expMod, lorentzMod, sincMod
    from BECMonitor.Auxwidgets import TextBox
except:
    from Fitmodels import sinMod, gaussMod, expMod, lorentzMod, sincMod
    from Auxwidgets import TextBox


import seaborn #for nice plots
seaborn.set_style('whitegrid')
#need to add them to dict of models

class VisualPlotter(QtGui.QWidget):
    """Class to choose plotting visually so it is easy.  Will also
    automatically update plots for every shot.  Can automatically fit on a
    single shot or updating shot basis.

    :var message: pyqtSignal which can be transmitted to main message box
    :var plots: Dictionary to hold all the plots
    :var data: local copy of entire pandas dataframe
    :var index: index of shot
    :var start: start of plot region
    :var end: end of plot region
    :var ignore_list: list of shots to ignore
    :fit_models: different models to fit too needs to be updated when models added

    """

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

         #fitting models dict
         self.fit_models = {"Sin":sinMod,
                            "Gaussian":gaussMod,
                            "Exponential":expMod,
                            "Lorentzian":lorentzMod,
                            "Sinc":sincMod
                            }

         self.labelx = QtGui.QLabel(self)
         self.labelx.setText('X variable')
         self.labely = QtGui.QLabel(self)
         self.labely.setText('Y variable')
         self.label_list = []


         self.entrystart = QtGui.QSpinBox()
         self.entryend = QtGui.QSpinBox()
         self.entrystart.setMinimum(0)
         self.entryend.setMinimum(0)

         self.checkstart = QtGui.QCheckBox('Set Start Index')
         self.checkend = QtGui.QCheckBox('Set End Index')
         self.ignore_b = QtGui.QPushButton('Ignore Indices')

         self.ignore_b.setToolTip('Enter Indices to ignore separated by ;, can use list slicing')
         self.ignore =  TextBox()



         #fitting check box
         self.fitting_check = QtGui.QCheckBox('Do Fitting')
         self.fitting_select = QtGui.QComboBox()

         for i in sorted(list(self.fit_models.keys())):
             self.fitting_select.addItem(i)

         #variable combo boxes
         self.xvars = QtGui.QComboBox()
         self.yvars = QtGui.QComboBox()
         self.var_push(['Shot'])


         self.fitting_stack = QtGui.QStackedWidget()
         #param dictionary of dictionary to hold parameter values
         self.fit_param_dict = {}
         self.params_objects = {} #dictionary of parameters objects
         self.add_fitting_widgets()



         #set up matplotlib figure
         self.preview = Figure(figsize=(3,4))
         self.canvas = FigureCanvas(self.preview)
         self.ax = self.preview.add_subplot(111)


         #buttons
         self.plot_b = QtGui.QPushButton('Updating Plot')
         self.static_plot_b = QtGui.QPushButton('Static Plot')
         self.try_fit_b = QtGui.QPushButton('Try Fit')
         self.do_fit_b = QtGui.QPushButton('Do Fit')



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

         row3c3 = QtGui.QVBoxLayout()
         row3c3.addWidget(self.fitting_check)
         row3c3.addWidget(self.fitting_select)
         row3c3.addWidget(self.fitting_stack)
         row3c3.addWidget(self.try_fit_b)
         row3c3.addWidget(self.do_fit_b)


         row3.addLayout(row3c2)
         row3.addLayout(row3c3)

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
         QtCore.QObject.connect(self.try_fit_b,
                                QtCore.SIGNAL('clicked()'), self.test_fit)
         QtCore.QObject.connect(self.do_fit_b,
                                QtCore.SIGNAL('clicked()'), self.do_fit)


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
         QtCore.QObject.connect(self.fitting_select,
                                QtCore.SIGNAL('activated(int)'),
                                self.fitting_stack.setCurrentIndex)


    def add_fitting_widgets(self):
        """function populates stacked box for each type of fit"""
        fits = sorted(list(self.fit_models.keys()))
        #loop through fits
        fit_widget = {}
        for i in fits:
            self.fit_param_dict[i] = {}
            #initiate widget of parameter entry
            fit_widget[i]= ParamEntry()
            self.params_objects[i] = Parameters()
            for j in self.fit_models[i].param_names:
                self.params_objects[i].add(j)
                lay = QtGui.QHBoxLayout()
                self.fit_param_dict[i][j] = QtGui.QDoubleSpinBox()
                self.fit_param_dict[i][j].setMaximum(1e17)
                lay.addWidget(QtGui.QLabel(j))
                lay.addWidget(self.fit_param_dict[i][j])
                fit_widget[i].layout.addLayout(lay)
            self.fitting_stack.addWidget(fit_widget[i])






    def update_plots(self ,df, index):
        """Update the updating plots whose references are stored in self.plots

        :params df: pandas dataframe holding data
        :type df: pandas.DataFrame
        :params index: index of shot
        """

        self.index = index
        self.data = df
        #push variables that are not there
        new_names = [i for i in df.columns.values.tolist() if i not in self.label_list]
        self.var_push(new_names)
        self.label_list = self.label_list + new_names
        self.test_plot()

        #filter for plots that are gone
        remove = [k for k in self.plots.keys() if self.plots[k].isHidden()]
        for k in remove: self.plots.pop(k)
        #update remaining plots
        for i in self.plots.keys():
            x_data = self.filter_ignore(
                self.data[self.plots[i].xl]).get_values()
            y_data = self.filter_ignore(
                self.data[self.plots[i].yl]).get_values()

            xx,yy,std = self.verbose_avg(x_data,y_data)
            self.plots[i].update(xx,yy,std)




    def var_push(self,var_list):
        """add a list of variables to options"""
        self.xvars.addItems(var_list)
        self.yvars.addItems(var_list)

    def plot_clicked(self):
        """function called when any plot option is called, sets the start and
        end values
        """
        self.x = str(self.xvars.currentText())
        self.y = str(self.yvars.currentText())
        if self.checkstart.isChecked():
            self.start = self.entrystart.value()
        else:
            self.start = 0
        if self.checkend.isChecked():
            self.end = self.entryend.value()
        else:
            self.end = list(self.data.index)[-1]

    def updating_plot(self):
        """create an updating plot and fill it with parameters
        gathered from current state of widgets
        """
        self.plot_clicked()
        #create new plot
        fit_type = self.fitting_select.currentText()
        mod = self.fit_models[fit_type]
            #update paramter values
        for i in mod.param_names:
            self.params_objects[fit_type][i].value = self.fit_param_dict[fit_type][i].value()

        title = self.make_updating_title_string()

        if title not in self.plots.keys() or self.plots[title] == None:
            self.plots[title] = PopPlot(mod = mod,
                                        params = self.params_objects[fit_type],
                                        do_fit = self.fitting_check.isChecked())

        self.plots[title].update_init(self.x,self.y,
                                        title,
                                        self.ignore_list,
                                        self.start)

        self.message.emit('Plotted updating: ' + title)
        x_data = self.filter_ignore(self.data[self.plots[title].xl]).get_values()
        y_data = self.filter_ignore(self.data[self.plots[title].yl]).get_values()
        xx,yy,std = self.verbose_avg(x_data,y_data)
        self.plots[title].update(xx,yy,std)
        self.plots[title].show()


    def static_plot(self):
        """create new modal popup static plot"""
        self.plot_clicked()
        x_data = self.filter_ignore(self.data[self.x]).get_values()
        y_data = self.filter_ignore(self.data[self.y]).get_values()

        std = self.avg_data()


        fit_type = self.fitting_select.currentText()
        mod = self.fit_models[fit_type]
            #update paramter values
        for i in mod.param_names:
            self.params_objects[fit_type][i].value = self.fit_param_dict[fit_type][i].value()
        staticplot = PopPlot(mod = mod,
                             params = self.params_objects[fit_type],
                             do_fit = self.fitting_check.isChecked())
        title = self.make_title_string()
        staticplot.plot(x_data,y_data,self.x,self.y,title,std)
        self.message.emit('Plotted: ' + title)
        staticplot.show()

    def test_plot(self):
        """update the test plot"""
        self.plot_clicked()
        self.ax.hold(False)
        #get the variables
        self.x_data = self.filter_ignore(self.data[self.x]).get_values()
        self.y_data = self.filter_ignore(self.data[self.y]).get_values()
        #now we need to averaging if it is on:::

        std = self.avg_data()
        self.ax.errorbar(self.x_data,self.y_data,yerr= std,
                     marker='o', linestyle='--', color='r')

        self.ax.set_xlabel(self.x)
        self.ax.set_ylabel(self.y)
        self.ax.set_title(self.make_title_string())
        #if fit is clicked also update that data
        if self.fitting_check.isChecked():
            self.test_fit() #eventually make this a line for now, okay
        self.canvas.draw()

    def test_fit(self):
        """do a fit on the test plto"""
        self.ax.hold(True)
        self.plot_clicked()
        #get the variables
        self.x_data = self.filter_ignore(self.data[self.x]).get_values()
        fit_type = self.fitting_select.currentText()
        mod = self.fit_models[fit_type]
            #update paramter values
        for i in mod.param_names:
            self.params_objects[fit_type][i].value = self.fit_param_dict[fit_type][i].value()
        #make a smooth interpolation of data
        x = np.linspace(self.x_data[0],self.x_data[-1],1000)
        self.ax.plot(x,mod.eval(params=self.params_objects[fit_type],x = x),
                                linestyle = '--')

        self.canvas.draw()


    def do_fit(self):
        """ do a fit"""
        self.ax.hold(True)
        self.plot_clicked()
        self.x_data = self.filter_ignore(self.data[self.x]).get_values()
        self.y_data = self.filter_ignore(self.data[self.y]).get_values()
        self.avg_data()
        fit_type = self.fitting_select.currentText()
        mod = self.fit_models[fit_type]
            #update paramter values
        for i in mod.param_names:
            self.params_objects[fit_type][i].value = self.fit_param_dict[fit_type][i].value()

        result = mod.fit(self.y_data,x = self.x_data, params=self.params_objects[fit_type])

        self.ax.plot(self.x_data,result.best_fit, color = 'c')
        self.canvas.draw()
        self.message.emit(fit_report(result))

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
        ind = [i for i in range(self.start,self.end) if i not in self.ignore_list]
        return data[ind]

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

    def avg_data(self):
        """average data and transform self.x_data and self.y_data
        this is a really crappy algorithm, but it does the trick"""
        x = self.x_data
        y = self.y_data
        ans = []

        distinct = set(list(x))
        for i in distinct:
            tempans = []
            for j in range(len(x)):
                if x[j] == i:
                    tempans.append(y[j])
            ans.append([i,tempans])
        self.x_data = [i[0] for i in ans]
        self.y_data = [np.mean(i[1]) for i in ans]
        std = [np.std(i[1]) for i in ans]
        return std

    def verbose_avg(self,x,y):
        """average data and transform self.x_data and self.y_data
        this is a really crappy algorithm, but it does the trick"""
        ans = []
        distinct = set(list(x))
        for i in distinct:
            tempans = []
            for j in range(len(x)):
                if x[j] == i:
                    tempans.append(y[j])
            ans.append([i,tempans])
        xx = [i[0] for i in ans]
        yy = [np.mean(i[1]) for i in ans]
        std = [np.std(i[1]) for i in ans]
        return xx,yy,std



class PopPlot(QtGui.QDialog):
    """popup class for plots both static and updating

    :var ax: matplotlib axis
    :var figure: matplotlib figure
    :var canvas: matplotlib canvas
    :var toolbar: matplotlib navigation toolbar
    :param mod: lmfit Model object for fitting
    :type mod: lmfit.Model
    :param do_fit: Boolean if fitting should occur
    :type do_fit: Boolean
    :param params: fit parameters
    :type params: lmfit.Parameters
    """
    def __init__(self,mod = None, params = None,do_fit = False, parent = None):
        QtGui.QDialog.__init__(self)
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.ax = self.figure.add_subplot(111)
        self.ax.hold(False)
        self.to_fit = do_fit
        self.mod = mod
        self.params = copy.deepcopy(params)
        layout = QtGui.QHBoxLayout()
        layout1 = QtGui.QVBoxLayout()
        layout1.addWidget(self.canvas)
        layout1.addWidget(self.toolbar)
        layout.addLayout(layout1)
        #add fit section if need to fit
        if self.to_fit:
            self.fit_res = TextBox()
            layout.addWidget(self.fit_res)
        self.setLayout(layout)


    def update_init(self,xl,yl,title,ignore,start):
        """update the parameters to start

        :param title: title of plot
        :type title: string
        :param xl: x label
        :type xl: string
        :param yl: y label
        :type yl: string
        :param start: starting index
        :type start: int
        """
        self.xl = xl
        self.yl = yl
        self.start = start
        self.title = title
        self.ignore = ignore

    def plot(self,x,y,xl,yl,title,std):
        """plot the data with a new fit if do_fit == True

        :params x: x vector of points
        :type x: list,numpy.array
        :params y: y vector of points
        :type y: y list,numpy.array
        :params xl: x label
        :type xl: string
        :params yl: y label
        :type yl: string
        :params title: title of plot
        :type title: string
        :params std: standard devation of points
        :type std: numpy.array
        """
        self.ax.hold(True)
        self.ax.errorbar(x,y, marker='o',yerr = std, linestyle='--', color='r')
        self.ax.set_xlabel(xl)
        self.ax.set_ylabel(yl)
        self.ax.set_title(title)
        if self.to_fit:
            try:
                self.fit_line.pop(0).remove()
            except:
                pass
            fitted = self.mod.fit(y, x=x,params = self.params)
            self.fit_line = self.ax.plot(x,fitted.best_fit, color = 'b')
            self.fit_res.insertPlainText(fitted.fit_report())
            self.fit_res.insertPlainText('\n'+''.join('#' for i in range(10))+'\n')
        self.canvas.draw()

    def update(self,x,y,std = None):
        """update the plots call the plot function

        :params x: x vector of points
        :type x: list,numpy.array
        :params y: y vector of points
        :type y: y list,numpy.array
        :params std: standard devation of points
        :type std: numpy.array
        """
        self.plot(x,y,self.xl,self.yl,self.title,std)




class ParamEntry(QtGui.QWidget):
    """convenience container widget to hold parameters"""
    def __init__(self, parent = None):
        """convenience container widget"""
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
