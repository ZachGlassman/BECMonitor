# -*- coding: utf-8 -*-
"""
Created on Sun Mar 15 20:12:32 2015
Spinor Monitor
This is the data aquisition software for Paul Lett's sodium spinor experiment.
It collects images, processes them, saves them, and provides
convenient information storage for determined paramters
It is written in pure python 3
@dependencies: pyqtgraph, ipython, matplotlib, lmfit,numpy
@author: zachglassman
"""
import sys
import os
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import matplotlib.pyplot as plt
import BECMonitor_subroutines as bs
from lmfit import Parameters
# Import the console machinery from ipython
from BECMonitor_ipython import  QIPythonWidget
from BECMonitor_image import ProcessImage, IncomingImage
from BECMonitor_visualplotter import VisualPlotter


#Set main options
#pg.setConfigOption('background', 'b')
#pg.setConfigOption('foreground', 'k')



class PopupParameter(QtGui.QDialog):
    """popup box to select parameters"""
    def __init__(self, params, parent = None):
        QtGui.QDialog.__init__(self,parent)
        self.setWindowTitle('Spinor Parameters')
        layout = QtGui.QGridLayout()
        layout.setSpacing(10)
        self.params = params
        #create a dict of QLineEdit Objects and another dict of labels
        self.edits = {}
        self.mins = {}
        self.maxs = {}
        self.labels = {}
        self.top = {}
        kk = 0
        for i in ['Parameters','Value','Minimum','Maximum']:
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
            self.edits[key].setText(str(self.params[key].value))
            self.mins[key].setText(str(self.params[key].min))
            self.maxs[key].setText(str(self.params[key].max))
            self.labels[key].setText(key)
            layout.addWidget(self.labels[key],k,0,1,1)
            layout.addWidget(self.edits[key],k,1,1,1)
            layout.addWidget(self.mins[key],k,2,1,1)
            layout.addWidget(self.maxs[key],k,3,1,1)
            k = k + 1
            

        self.exit = QtGui.QPushButton("Save", self)
        layout.addWidget(self.exit,len(params) + 1,0,1,2)
        QtCore.QObject.connect(self.exit, QtCore.SIGNAL('clicked()'), self.save)
        self.setLayout(layout)
        
    def save(self):
        """closes and windows and return updated parameter object"""
        for key in self.params.keys():
            self.params[key].value = float(self.edits[key].text())
            self.params[key].min = float(self.mins[key].text())
            self.params[key].max = float(self.maxs[key].text())
            self.accept()
        return self.params
                
        
        
class Options(QtGui.QWidget):
    """Panel which defines options for fitting and analyzing images"""
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        
        #Parameters object for guesses
        self.params = Parameters()
        #name, Value, Vary,Min,Max, Expr
        self.params.add_many(
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
            ('theta',10,True,0,None,None))
  
        #fit types
        self.fit_types = QtGui.QComboBox()
        self.fit_types.addItems('Gaussian,Thomas-Fermi,Bimodal'.split(','))
     
      
        #parameters
        self.param_select = QtGui.QPushButton("Parameter Entry",self)
        QtCore.QObject.connect(self.param_select, QtCore.SIGNAL('clicked()'), self.popup)
       
     
        layout = QtGui.QGridLayout()
        layout.setSpacing(10)
    
        layout.addWidget(self.fit_types,   0,0,1,1)
        layout.addWidget(self.param_select,0,2,1,1)
        
        self.setLayout(layout)
        
   
       
    
    def popup(self):
        """function to start parameter window object"""
        param_window = PopupParameter(self.params)
        if param_window.exec_():
            self.params = param_window.save()
            
class RoiOptions(QtGui.QWidget):
    """Widget for Region of Interest Information"""
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        #get region of interest button
        self.get_roi = QtGui.QPushButton("Get ROI",self)
        
        info = QtGui.QLabel()
        info.setText('Select ROI on top screen and click')
        lbroi = QtGui.QLabel(self)
        lbroi.setText('ROI')
        self.labels_list = ['x<sub>0','x<sub>1','y<sub>0','y<sub>1',u"\u03F4"]
        self.labels = {}
        self.roi = {}
        for i in self.labels_list:
            self.labels[i] = QtGui.QLabel(self) 
            self.labels[i].setText(i)
            self.roi[i] = QtGui.QLineEdit(self)
            self.roi[i].setReadOnly(True)
       
     
        layout = QtGui.QGridLayout()
        layout.setSpacing(10)
        layout.addWidget(info,0,0)
        layout.addWidget(lbroi,1,0)
        layout.addWidget(self.get_roi,1,2)
        k = 2
        for i in self.labels_list:
            layout.addWidget(self.labels[i],k,0)
            layout.addWidget(self.roi[i],k,2)
            k = k + 1
 
        self.setLayout(layout)
        
    def set_roi(self,vec):
        """Generate roi strings and print coords"""
        k = 0
        for i in self.labels_list:
            self.roi[i].setText("{:>.2f}".format(vec[k]))
            k = k + 1
        
   
            
class DataPlots(pg.GraphicsLayoutWidget):
    """graphs to populate different stuff"""
    
    #emitting message, can't define as instance variable
    message = QtCore.pyqtSignal(object)
    def __init__(self, parent = None):
        pg.GraphicsLayoutWidget.__init__(self, parent)
        pg.setConfigOptions(antialias=True)
        graph_names = ["N_BEC_Atoms",
                       "N_Therm_Atoms",
                       "X_Width",
                       "Y_Width",
                       "Temperature",
                       "All"]
        self.graph_dict = {}
        #dictionary to hold data items in graph
        self.graph_data_dict = {}
        k = 0   
        for i in graph_names:
            if k == 3:
                self.nextRow()
            self.graph_dict[i] = self.addPlot(title = i)
            self.graph_dict[i].setLabel('bottom', 'Index')
            k = k + 1
            
            self.graph_data_dict[i] = self.graph_dict[i].plot([0],[0], 
                symbolSize=5, symbolBrush=(100, 100, 255, 50))
            self.graph_data_dict[i].sigPointsClicked.connect(self.emit_it)
        
        
       
    def update_plots(self, results):
        """Update all the Plots"""
        for i in self.graph_dict.keys():
            self.graph_data_dict[i].setData(list(results.ind_results[i].keys()),
                                            list(results.ind_results[i].values()))
       
   
    def emit_it(self, item,points):
        self.message.emit(points[0].pos())
                   
       
  
class ImageWindow(pg.GraphicsLayoutWidget):
    """Image View with custom ROI"""
    def __init__(self, parent = None):
        pg.GraphicsLayoutWidget.__init__(self, parent)
        #define colormap 
        self.cmap = plt.get_cmap('jet')
        #raw image plot

        self.rawImagePlot = self.addPlot(title = 'Raw Image')
        self.img = pg.ImageItem()
        self.data = None
        self.rawImagePlot.addItem(self.img)
        self.brush = (100, 100, 150, 200)
      
    
        # Custom ROI for selecting an image region
        self.roi = pg.ROI([20,20], [200, 200],
                          snapSize = 1, 
                          scaleSnap = True,
                          translateSnap = True,
                          )
        self.roi.addScaleHandle([0.5, 1], [0.5, 0.5])
        self.roi.addScaleHandle([0, .5], [0.5, 0.5])
        self.roi.addRotateFreeHandle([0,0],[.5,.5])
        
        self.rawImagePlot.addItem(self.roi)
        self.roi.setZValue(10)  # make sure ROI is drawn above image
        
        #region of interest plots
        self.region = self.addPlot(title = 'ROI')
        self.region_img = pg.ImageItem()
        self.region_img1 = pg.ImageItem()
        self.region.addItem(self.region_img) 
        
        self.win = pg.GraphicsLayoutWidget()
        self.pop_plot = self.win.addPlot(title = 'Raw Image')
        self.pop_plot.addItem(self.region_img1)
        
        self.nextRow()
        self.xSlice = self.addPlot(title = 'x Slice',
                                   symbolSize=2, 
                                   symbolBrush = self.brush)
        self.ySlice = self.addPlot(title = 'y Slice',
                                   symbolSize=2, 
                                   symbolBrush=self.brush)
                                   
        #self.nextRow()
        #self.pop = QtGui.QPushButton("Large Window",self)
        #self.addItem(self.pop)
        #QtCore.QObject.connect(self.param_select, QtCore.SIGNAL('clicked()'), self.popup)
                                   
        
        self.roi.sigRegionChanged.connect(self.updatePlot)
        
    def popup(self):
        """function to start popup window object"""
        self.win.show()
        
    def updatePlot(self):
        """updates plot, can only be called once plot is initalized with image"""
        sel = self.roi.getArrayRegion(self.data,self.img)
        self.xSlice.plot(sel.sum(axis = 1),
                                   pen=None,  
                                   symbolPen=None, 
                                   symbolSize= 5, 
                                   symbolBrush=self.brush,
                                   clear = True)
        self.ySlice.plot(sel.sum(axis = 0),
                                   pen=None,  
                                   symbolPen=None, 
                                   symbolSize=5, 
                                   symbolBrush=self.brush,
                                   clear = True)
        
        self.region_img.setImage(self.cmap(sel))
        self.region_img1.setImage(self.cmap(sel))
        
    
    
    def setImage(self, im):
        """set image"""
        self.data = im
        self.img.setImage(im)
        self.xSlice.plot(self.data.sum(axis = 1), 
                                   pen=None,  
                                   symbolPen=None, 
                                   symbolSize=5, 
                                   symbolBrush=self.brush,
                                   clear = True)
        self.ySlice.plot(self.data.sum(axis = 0),
                                   pen=None,  
                                   symbolPen=None, 
                                   symbolSize=5, 
                                   symbolBrush=self.brush,
                                   clear = True)
        self.region_img.setImage(
            self.cmap(self.roi.getArrayRegion(self.data,self.img))
            )
        self.region_img1.setImage(
            self.cmap(self.roi.getArrayRegion(self.data,self.img))
            )
    
    def add_lines(self, results):
        """add lines to plot, input it numpy array which is then summed"""
        self.xSlice.plot(results.sum(axis = 1))
        self.ySlice.plot(results.sum(axis =0))
        
        
        

class FitResults(object):
    """class to hold fit results as dictionaries by index"""
    def __init__(self):
        self.names = ["N_BEC_Atoms","N_Therm_Atoms",
                       "X_Width",
                       "Y_Width",
                       "Temperature",
                       "All",
                       "Index"]
        self.ind_results = {}
        for i in self.names:
            self.ind_results[i] = {}
            
    def make_list(self):
        ans = {}
        for i in self.ind_results.keys():
            ans[i] = [self.get(self.ind_results[i][j]) for j in range(len(self.ind_results[i]))]
        return {'spinorvars':ans}   
        
    def get(self,it):
        try:
            return it
        except:
            return None
            
    def pretty_print(self):
        """make into one long string to be saved to file (All can be anything)
        format : index, NBEC,NTHerm,XWidth,Temp,All"""
        form = '{:<14.0f}{:<14.0f}{:<14.0f}{:<14.2f}{:<14.2f}{:<14.2f}{:<14.0f}'
        form1 = '{:<14s}{:<14s}{:<14s}{:<14s}{:<14s}{:<14s}{:<14s}'
        answer = form1.format(*tuple(['index'] + self.names)) + '\n'
        #loop through indexes
        for i in self.ind_results['N_BEC_Atoms'].keys():
            #format string for each one            
            answer = answer + form.format(*tuple([i] + [self.ind_results[j][i] for j in self.names]))
            answer = answer + '\n'
        return answer
            
class TextBox(QtGui.QTextEdit):
    """custom textbox, mostly QTextEdit, with some added functions"""
    def __init__(self):
        QtGui.QTextEdit.__init__(self, parent = None)    
        self.setReadOnly(True)
        
    def output(self, x):
        self.insertPlainText(x)
        self.insertPlainText('\n')
        self.moveCursor(QtGui.QTextCursor.End)
        
class FingerTabBarWidget(QtGui.QTabBar):
    """Class to implement tabbed browsing for options"""
    def __init__(self, parent=None, *args, **kwargs):
        self.tabSize = QtCore.QSize(kwargs.pop('width',100), kwargs.pop('height',25))
        QtGui.QTabBar.__init__(self, parent, *args, **kwargs)
                 
    def paintEvent(self, event):
        painter = QtGui.QStylePainter(self)
        option = QtGui.QStyleOptionTab()
 
        for index in range(self.count()):
            self.initStyleOption(option, index)
            tabRect = self.tabRect(index)
            tabRect.moveLeft(10)
            painter.drawControl(QtGui.QStyle.CE_TabBarTabShape, option)
            painter.drawText(tabRect, QtCore.Qt.AlignVCenter |\
                             QtCore.Qt.TextDontClip, \
                             self.tabText(index));
        painter.end()
    def tabSizeHint(self,index):
        return self.tabSize
        
        
class MainWindow(QtGui.QWidget):
    """Main Window for the app, contains the graphs panel and the options
      panel"""
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.run, self.path = bs.get_run_name()
        self.initUI()
        self.ROI = [20,200,20,200]
        self.processThreadPool = []
        self.process = []
        self.index = 0
        self.fit_results = FitResults()
        self.vis_plots.var_push(self.fit_results.names)
        self.vis_plots.add_init_data(self.fit_results.make_list())
                

        
       
        
        
    def initUI(self):
        """Iniitalize UI and name it"""
        #self.showFullScreen()
        self.resize(1850,950)
        self.center()
        self.setWindowTitle('Spinor BEC Analysis')
        #subwidgets
        self.image = ImageWindow(self)
        self.plots = DataPlots(self)
        self.options = Options(self)
        self.roi_options = RoiOptions(self)
        self.vis_plots = VisualPlotter(self)
        
        #tabs 
        self.tabs = QtGui.QTabWidget()
        self.tabs.setTabBar(FingerTabBarWidget(width=100,height=25))
        self.tabs.setTabPosition(QtGui.QTabWidget.West)
        self.tabs.addTab(self.options, 'Fit Options')   
        self.tabs.addTab(self.roi_options, "ROI Options")
        self.tabs.addTab(self.vis_plots, 'Data Plotter')
        
        
        self.ipy =  QIPythonWidget(customBanner="Spinor BEC Ipython console\n")
        self.set_up_ipy()
       

        #run button and stop button
        self.runButton = QtGui.QPushButton("Run")
        self.stopButton = QtGui.QPushButton("Stop")
        self.bigScreen = QtGui.QPushButton("Big Screen")
        
        #textbox for program output
        self.text_out = TextBox()
        
        #running indicator
        self.col = QtGui.QColor(255, 0, 0)
        self.square = QtGui.QFrame(self)
        self.square.setGeometry(5, 5, 5, 5)
        self.square.setStyleSheet("QWidget { background-color: %s }" %  
        self.col.name())
        #layout
        self.grid = QtGui.QGridLayout()
        self.grid.setSpacing(10)
        #first row
        self.grid.addWidget(self.plots,0,0,6,6)
        self.grid.addWidget(self.image,0,7,6,6)
        #second row
       
        self.grid.addWidget(self.tabs,6,0,5,6)
        self.grid.addWidget(self.text_out,6,11,3,2)
        self.grid.addWidget(self.ipy,6,7,5,4)
        #third row
        self.grid.addWidget(self.square,10,0,1,1)
        #fourth row
        self.grid.addWidget(self.runButton,11,0)
        self.grid.addWidget(self.stopButton,11,1)
        self.grid.addWidget(self.bigScreen,11,2)
       
       
        #connect buttoms- mix of old and new styles
        QtCore.QObject.connect(self.roi_options.get_roi,
                               QtCore.SIGNAL('clicked()'), self.get_roi)
        QtCore.QObject.connect(self.runButton, 
                               QtCore.SIGNAL("clicked()"), self.start)
        QtCore.QObject.connect(self.bigScreen,
                               QtCore.SIGNAL("clicked()"), self.image.popup)
        QtCore.QObject.connect(self.stopButton, 
                               QtCore.SIGNAL("clicked()"), self.end)
        
        self.plots.message.connect(self.on_message)
        self.vis_plots.message.connect(self.on_message)
                               
        self.setLayout(self.grid)
        
        self.text_out.output('Initializing run ' + str(self.run))
        self.get_roi()
        self.show()
        
    
       
    @QtCore.pyqtSlot(object)
    def on_message(self,data):
        self.text_out.output(str(data))
        
    def center(self):
        """Centers Window"""
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
    def get_roi(self):
        """returns region of interest in list [xstart,xend,ystart,yend,angle]"""
        start = self.image.roi.pos()
        size  = self.image.roi.size()
        angle = self.image.roi.angle()
        self.ROI = [start[0],start[0] + size[0], 
                    start[1], start[1] + size[1], angle]
        self.roi_options.set_roi(self.ROI)
        
    def start(self):
        """Function to start listening thread"""
        self.imageThread = IncomingImage()
        QtCore.QObject.connect(self.imageThread,
                               QtCore.SIGNAL('update(QString)'),
                               self.data_recieved)
        QtCore.QObject.connect(self.imageThread,
                               QtCore.SIGNAL('packetReceived(PyQt_PyObject)'),
                               self.data_process)
        self.imageThread.start()
        self.col.setRed(0)
        self.col.setBlue(0)
        self.col.setGreen(255)
        self.square.setStyleSheet("QFrame { background-color: %s }" %
            self.col.name()) 
    
    def end(self):
        """functino to stop listening Thread"""
        self.col.setGreen(0)
        self.col.setRed(255)
        self.square.setStyleSheet("QFrame { background-color: %s }" %
            self.col.name())
            
        #write out parameters
        p = os.path.join(self.path,'run_' + str(self.run) + '_results.txt')
        with open(p,'w') as fp:   
            fp.write(self.fit_results.pretty_print())
            
        try:
            self.imageThread.terminate()
        except:
           print('Thread not Terminated')
        
    def data_recieved(self):
        self.text_out.output('Image {0} recieved'.format(self.index))
        
    def data_process(self, results):
        """process the data, including spawn a thread and increment index"""
        self.image.setImage(results)
        #append thread to thread pool
        self.processThreadPool.append(QtCore.QThread())
        #create new process image object and add to thread just created
        self.process.append(ProcessImage(results,self.get_options(),self.path,self.run))
        self.process[-1].moveToThread(self.processThreadPool[-1])
        #connect start signal
        
        QtCore.QObject.connect(self.processThreadPool[-1],
                               QtCore.SIGNAL('started()'),
                                self.process[-1].run)
        
        QtCore.QObject.connect(self.process[-1],
                               QtCore.SIGNAL('fit_obj'),
                                self.update_data)
                           
        QtCore.QObject.connect(self.process[-1],
                               QtCore.SIGNAL('finished()'),
                                self.processThreadPool[-1].quit)
    
        
        
        #start thread
        self.processThreadPool[-1].start()
        self.index = self.index + 1
        
    def get_options(self):
        """convenience function to return list of options"""
        return [self.options.params,self.ROI,self.index]
        
    def update_data(self, results):
        """function to update plots and push data to ipython notebook"""
        self.text_out.output('Image {0} processed'.format(self.index-1))
        for i in self.fit_results.ind_results.keys():
            self.fit_results.ind_results[i][results['Index']] = results[i] 
       
        updated_data = self.fit_results.make_list()
        self.ipy.pushVariables(updated_data)
       
        #update ipython graphs
        self.ipy._execute('Plot_obj.update(spinorvars)', True)
        #update plots on main gui
        self.plots.update_plots(self.fit_results)
        #update plots created in gui
        self.vis_plots.update_plots(updated_data, self.index)
        #possibly check if image has taken next shot for complicated processing      
        self.image.add_lines(results['fitted'])
        
    def set_up_ipy(self):
        """setup the ipython console for use with useful functions"""
        self.ipy.executeCommand('from BECMonitor_ipython import *')
        self.ipy.printText('imported numpy and matplotlib as np and plt')

        
    
        
        
        

#main routine
if __name__ == '__main__':
      app = QtGui.QApplication(sys.argv)
      win = MainWindow()
      sys.exit(app.exec_())
    