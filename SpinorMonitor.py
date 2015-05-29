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
import matplotlib.pyplot as plt
import BECMonitor_subroutines as bs
# Import the console machinery from ipython
from BECMonitor_ipython import  QIPythonWidget
from BECMonitor_image import ProcessImage, IncomingImage
from BECMonitor_visualplotter import VisualPlotter
from BECMonitor_options import Options, RoiOptions
from BECMonitor_datatable import DataTable

#Set main options
#pg.setConfigOption('background', 'b')
#pg.setConfigOption('foreground', 'k')



            
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
        self.processThreadPool = {}
        self.process = {}
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
        self.setWindowIcon(QtGui.QIcon('icon.png'))
        #subwidgets
        self.image = ImageWindow(self)
        self.plots = DataPlots(self)
        self.options = Options(self)
        self.roi_options = RoiOptions(self)
        self.vis_plots = VisualPlotter(self)
        self.data_tables = DataTable()
        self.running = False
        #tabs 
        self.tabs = QtGui.QTabWidget()
        self.tabs.setTabBar(FingerTabBarWidget(width=100,height=85))
        self.tabs.setTabPosition(QtGui.QTabWidget.West)
        self.tabs.addTab(self.options, 'Fit Options')   
        self.tabs.addTab(self.roi_options, "ROI Options")
        self.tabs.addTab(self.vis_plots, 'Data Plotter')
        self.tabs.addTab(self.data_tables, 'Data Tables')
        
        
        self.ipy =  QIPythonWidget(customBanner="Spinor BEC Ipython console\n")
        self.set_up_ipy()
       

        #run button and stop button
        self.runButton = QtGui.QPushButton("Run")
        self.runButton.setStyleSheet("background-color: red")
        self.bigScreen = QtGui.QPushButton("Big Screen")
        
        #textbox for program output
        self.text_out = TextBox()
        
     
        #layout
        layout = QtGui.QVBoxLayout()
        layout.setSpacing(10)
        #first row
        row1 = QtGui.QHBoxLayout()
        row1.addWidget(self.plots)
        row1.addWidget(self.image)
        #second row
        row2 = QtGui.QHBoxLayout()
        row2.addWidget(self.tabs,stretch=1)  
        row2.addWidget(self.ipy)
        row2col3 = QtGui.QVBoxLayout()
        row2col3.addWidget(self.text_out)
        row2col3.addWidget(self.bigScreen)
        row2col3.addWidget(self.runButton)
      
        
        row2.addLayout(row2col3)
        layout.addLayout(row1)
        layout.addLayout(row2)
        self.setLayout(layout)

        #connect buttoms- mix of old and new styles
        QtCore.QObject.connect(self.roi_options.get_roi,
                               QtCore.SIGNAL('clicked()'), self.get_roi)
        QtCore.QObject.connect(self.runButton, 
                               QtCore.SIGNAL("clicked()"), self.change_state)
        QtCore.QObject.connect(self.bigScreen,
                               QtCore.SIGNAL("clicked()"), self.image.popup)
     
        
        self.plots.message.connect(self.on_message)
        self.vis_plots.message.connect(self.on_message)
        self.options.message.connect(self.on_message)
                               
        
        
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
      
    def change_state(self):
        """control start and stop"""
        if self.running:
            self.end()
        else:
            self.start()
            
    def start(self):
        """Function to start listening thread"""
        self.running = True
        self.imageThread = IncomingImage()
        QtCore.QObject.connect(self.imageThread,
                               QtCore.SIGNAL('update(QString)'),
                               self.data_recieved)
        QtCore.QObject.connect(self.imageThread,
                               QtCore.SIGNAL('packetReceived(PyQt_PyObject)'),
                               self.data_process)
        self.imageThread.start()
        self.runButton.setStyleSheet("background-color: green")
    
    def end(self):
        """functino to stop listening Thread"""
        self.running = False
        self.runButton.setStyleSheet("background-color: red")
            
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
        
    def data_process(self, results_dict):
        """process the data, including spawn a thread and increment index"""
        results = results_dict['image']
        self.image.setImage(results)
        ind = str(self.index)
        #append thread to thread pool
        self.processThreadPool[ind]= QtCore.QThread()
        #create new process image object and add to thread just created
        self.process[ind] = ProcessImage(results,self.get_options(),self.path,self.run)
        self.process[ind].moveToThread(self.processThreadPool[ind])
        #connect start signal
        
        QtCore.QObject.connect(self.processThreadPool[ind],
                               QtCore.SIGNAL('started()'),
                                self.process[ind].run)
        
        QtCore.QObject.connect(self.process[ind],
                               QtCore.SIGNAL('fit_obj'),
                                self.update_data)
                           
        QtCore.QObject.connect(self.process[ind],
                               QtCore.SIGNAL('finished()'),
                                lambda: self.finish_thread(ind))
    
        
        
        #start thread
        self.processThreadPool[ind].start()
        self.index = self.index + 1
        
    
    def finish_thread(self,ind):
        """destroy thread on finished signal, will complain, but its okay"""
        self.process.pop(ind)
        self.processThreadPool.pop(ind)
    
    def get_options(self):
        """convenience function to return list of options
        note that function which recieves params must make
        deep copy or there will be problems!!"""
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
      #some stuff for nice looking app
      """
      myappid = u'SpinorApp' # arbitrary string
      try:
          ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
      except:
          print('Not on windows')
      #different icon sizes for use
      app_icon = QtGui.QIcon()
      app_icon.addFile('icon56x56.png', QtCore.QSize(56,56))
      app_icon.addFile('icon70x70.png', QtCore.QSize(70,70))
      app_icon.addFile('icon139x139.png', QtCore.QSize(139,139))
      app_icon.addFile('icon173x173.png', QtCore.QSize(173,173))
      app_icon.addFile('icon216x216.png', QtCore.QSize(216,216))
      app_icon.addFile('icon216x216.ico', QtCore.QSize(216,216))
      app.setWindowIcon(app_icon)
      """
      
      #run this baby
      sys.exit(app.exec_())
    