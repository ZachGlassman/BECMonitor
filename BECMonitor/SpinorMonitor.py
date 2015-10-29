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
import numpy as np
from pyqtgraph.Qt import QtCore, QtGui
import pandas as pd
import Subroutines as bs
# Import the console machinery from ipython
from Ipython import  QIPythonWidget
from Image import ProcessImage, IncomingImage
from Visualplotterwidget import VisualPlotter
from Optionswidgets import Options, PlotOptions
from Datatablewidget import DataTable
from Auxwidgets import TextBox, FingerTabBarWidget
from Dataplots import DataPlots, ImageWindow
from Auxfuncwidget import AuxillaryFunctionContainerWidget
#import pyqtgraph as pg
#Set main options
#pg.setConfigOption('background', 'k')
#pg.setConfigOption('foreground', 'b')



class MainWindow(QtGui.QWidget):
    """ Main Window for the app, contains the graphs panel and the options
    panel.  Executes main control of all other panels.

    :var expData: Pandas dataframe where all experiment information is kept
    :var run: Run number for the day
    :var path: Path to data storage folder
    :var processThreadPool: Dictionary of running threads
    :var process: Convenience dictionary to initialize objects
    :var ROI: region of interest
    :var running: Boolean if data collection thread is active
    :var index: keeps track of shot internally
    :var image: ImageWindow widget
    :var plots: DataPlots widget
    :var options: Options widget
    :var plot_options: PlotOptions widget
    :var vis_plots: VisualPlotter widget
    :var data_tables: DataTable widget
    :var aux_funcs: AuxillaryFunctionContainerWidget widget
    :var tabs: QTabWidget, contains other widgets
    :var ipy: QIPythonWidget
    """
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.run, self.path = bs.get_run_name()

        #pandas dataframe for results
        self.expData = pd.DataFrame()
        self.processThreadPool = {}
        self.process = {}
        self.initUI()
        self.ROI = [20,200,20,200]

        self.index = 0




    def initUI(self):
        """
        Iniitalize UI and name it.  Creat all children widgets and place
        them in layout
        """
        #self.showFullScreen()
        self.resize(1850,950) #work
        #self.resize(1650,900) #home

        self.center()
        self.setWindowTitle('Spinor BEC Analysis')
        self.setWindowIcon(QtGui.QIcon('icon.png'))
        #subwidgets
        self.image = ImageWindow(self)
        self.plots = DataPlots(self)
        self.options = Options(self)
        self.plot_options = PlotOptions(self)
        self.vis_plots = VisualPlotter(self)
        self.data_tables = DataTable(self)
        self.aux_funcs = AuxillaryFunctionContainerWidget(self)
        self.running = False
        #tabs
        self.tabs = QtGui.QTabWidget()
        self.tabs.setTabBar(FingerTabBarWidget(width=100,height=85))
        self.tabs.setTabPosition(QtGui.QTabWidget.West)
        self.tabs.addTab(self.options, 'Fit Options')
        self.tabs.addTab(self.plot_options, "Plot/Image Options")
        self.tabs.addTab(self.vis_plots, 'Data Plotter')
        self.tabs.addTab(self.data_tables, 'Data Tables')
        self.tabs.addTab(self.aux_funcs, 'Aux Functions')



        self.ipy =  QIPythonWidget(customBanner="Spinor BEC Ipython console\n")


        self.set_up_ipy()


        #run button and stop button
        self.runButton = QtGui.QPushButton("Run")
        self.runButton.setStyleSheet("background-color: red; color:white")
        self.bigScreen = QtGui.QPushButton("Big Screen")
        self.bigScreen.setStyleSheet("background-color: blue; color:white")

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
        row2.addWidget(self.tabs, stretch = 2)
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
        QtCore.QObject.connect(self.plot_options.get_roi,
                               QtCore.SIGNAL('clicked()'), self.get_roi)
        QtCore.QObject.connect(self.runButton,
                               QtCore.SIGNAL("clicked()"), self.change_state)
        QtCore.QObject.connect(self.bigScreen,
                               QtCore.SIGNAL("clicked()"), self.image.popup)


        self.plots.message.connect(self.on_message)
        self.vis_plots.message.connect(self.on_message)
        self.options.message.connect(self.on_message)
        self.options.fit_name.connect(self.on_fit_name)


        self.text_out.output('Initializing run ' + str(self.run))
        self.get_roi()
        self.show()



    @QtCore.pyqtSlot(object)
    def on_message(self,data):
        """
        Send message to output windows

        :param data: message to send
        :type data: object

        """
        self.text_out.output(str(data))

    @QtCore.pyqtSlot(object)
    def on_fit_name(self, data):
        """
        Triggers the plots.change_key functions with argument data.

        :params data: name of fit
        :type data: string
        """
        self.plots.change_key(data)


    def center(self):
        """Centers Window"""
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def get_roi(self):
        """returns region of interest in list
        :returns: [xstart,xend,ystart,yend,angle]
        :rtype: list
        """
        start = self.image.roi.pos()
        size  = self.image.roi.size()
        angle = self.image.roi.angle()
        self.ROI = [start[0],start[0] + size[0],
                    start[1], start[1] + size[1], angle]
        self.plot_options.set_roi(self.ROI)

    def change_state(self):
        """start and stop data collection thread"""
        if self.running:
            self.end()
        else:
            self.start()

    def start(self):
        """Function to start listening thread, connect signals and
        :var imageThread: IncomingImage object listening for images

        """
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
        """function to stop listening Thread, writes out expData to csv
        in smae folder as data printing
        """
        self.running = False
        self.runButton.setStyleSheet("background-color: red")

        #write out parameters
        p = os.path.join(self.path,'run_' + str(self.run) + '_results.txt')
        self.expData.to_csv(p)
        self.text_out.output('File written to' + p)
        try:
            self.imageThread.terminate()
        except:
           print('Thread not Terminated')

    def data_recieved(self):
        """Send message that data was recieved"""
        self.text_out.output('Image {0} recieved'.format(self.index))

    def data_process(self, results_dict):
        """process the data, including spawn a thread and increment index"""
        results = results_dict['image'] #image
        self.image.setImage(np.transpose(results))

        ind = str(self.index)
        #append thread to thread pool
        self.processThreadPool[ind]= QtCore.QThread(self)
        #create new process image object and add to thread just created
        self.process[ind] = ProcessImage(results,results_dict['exp_params'],
            self.get_options(),
            self.path,self.run)
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
        """pop the process should destroy it all I think/"""
        self.process.pop(ind)
        self.processThreadPool.pop(ind)

    def get_options(self):
        """convenience function to return list of options
        note that function which recieves params must make
        deep copy or there will be problems!!"""
        return [self.options.params,
                self.options.type_of_fit,
                self.ROI,
                self.index]

    def update_data(self, results_passed):
        """function to update plots and push data to ipython notebook"""
        results = results_passed[0]
        self.text_out.output('Image {0} processed'.format(self.index-1))

        #####make into series then push to pandas array
        results['Shot'] = results['Index']
        self.expData = self.expData.append(
            pd.DataFrame(results, index = [results['Shot']]).drop('Index',1))

        #Do updates of different widgets
        self.data_tables.update_pandas_table(self.expData)
        #update update
        self.to_ipy()
        self.ipy._execute('Plot_obj.update()', False)

        #update plots
        self.plots.update_plots(self.expData)
        self.vis_plots.update_plots(self.expData, self.index)

        #possibly check if image has taken next shot for complicated processing

        self.image.add_lines(results_passed[1])
        self.text_out.output('Updated Internal Structure')


    def set_up_ipy(self):
        """setup the ipython console for use with useful functions"""
        self.ipy.executeCommand('from Ipython import *')
        self.ipy.printText('imported numpy and matplotlib as np and plt')
        self.ipy.pushVariables({'help_str':'testing this'})


    def to_ipy(self):
        """push all variables to Ipython notebook"""
        ans = {}
        for i in self.expData.columns:
            ans[i] = self.expData[i].get_values()
        self.ipy.pushVariables(ans)








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
