# -*- coding: utf-8 -*-
__doc__= """
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
#import objects and functions from other files
try:
    import BECMonitor.Subroutines as bs
    from BECMonitor.Ipython import  QIPythonWidget
    from BECMonitor.Image import ProcessImage, IncomingImage, ProcedureRunner
    from BECMonitor.Visualplotterwidget import VisualPlotter
    from BECMonitor.Optionswidgets import Options, PlotOptions, ProcedureOptions
    from BECMonitor.Datatablewidget import DataTable
    from BECMonitor.Auxwidgets import TextBox, FingerTabBarWidget
    from BECMonitor.Dataplots import DataPlotsWidget, ImageWindow, DataPlotsProcedureWidget
    from BECMonitor.Auxfuncwidget import AuxillaryFunctionContainerWidget
except:
    import Subroutines as bs
    from Ipython import  QIPythonWidget
    from Image import ProcessImage, IncomingImage, ProcedureRunner
    from Visualplotterwidget import VisualPlotter
    from Optionswidgets import Options, PlotOptions, ProcedureOptions
    from Datatablewidget import DataTable
    from Auxwidgets import TextBox, FingerTabBarWidget
    from Dataplots import DataPlotsWidget, ImageWindow, DataPlotsProcedureWidget
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
    :var plots: DataPlotsWidget widget
    :var options: Options widget
    :var plot_options: PlotOptions widget
    :var vis_plots: VisualPlotter widget
    :var data_tables: DataTable widget
    :var aux_funcs: AuxillaryFunctionContainerWidget widget
    :var tabs: QTabWidget, contains other widgets
    :var ipy: QIPythonWidget
    """
    def __init__(self, fname, start_path, procs, testingFrame):
        QtGui.QWidget.__init__(self)
        self.run, self.path = bs.get_run_name(start_path)
        self.fname = fname
        #pandas dataframe for results
        try:
            self.expData = testingFrame
            print(self.expData.index)
            self.index = len(self.expData)
            testing = True
        except:
            self.expData = pd.DataFrame()
            self.index = 0
            testing = False
        self.processThreadPool = {}
        self.process = {}
        self.procs = procs
        self.initUI()
        if testing:
            self.data_tables.bulk_update_pandas_table(self.expData)
        self.ROI = [20,200,20,200]


        print('#############')
        print('Program Initialized')

    def initUI(self):
        """
        Iniitalize UI and name it.  Creat all children widgets and place
        them in layout
        """
        #self.showFullScreen()
        self.resize(1850,950) #work
        self.showMaximized()
        #self.resize(1650,900) #home

        self.center()
        self.setWindowTitle('Spinor BEC Analysis')
        self.setWindowIcon(QtGui.QIcon('icon.png'))
        #subwidgets
        self.image = ImageWindow(self)
        #self.plots = DataPlotsWidget(self)
        self.plots = DataPlotsProcedureWidget(self.procs,self)
        #self.options = Options(self)
        self.options = ProcedureOptions(self.procs,self)
        self.plot_options = PlotOptions(self)
        self.vis_plots = VisualPlotter(self)
        self.data_tables = DataTable(self)
        self.aux_funcs = AuxillaryFunctionContainerWidget(self)

        #some options
        self.running = False
        #self.plots.change_key('Mixture')
        #tabs
        self.tabs = QtGui.QTabWidget()
        self.tabs.setTabBar(FingerTabBarWidget(width=100,height=85))
        self.tabs.setTabPosition(QtGui.QTabWidget.West)
        self.tabs.addTab(self.options, 'Procedure Options')
        #self.tabs.addTab(self.options_n, 'Procedure Options')

        self.tabs.addTab(self.plot_options, "Plot/Image Options")
        self.tabs.addTab(self.vis_plots, 'Data Plotter')
        self.tabs.addTab(self.data_tables, 'Data Tables')
        self.tabs.addTab(self.aux_funcs, 'Aux Functions')

        ###################
        # Ipython interpreter
        ###################
        self.ipy =  QIPythonWidget(customBanner="Spinor BEC Ipython console\n")
        self.set_up_ipy()

        ##################
        #run button and big screen button
        ###########################
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
                               QtCore.SIGNAL("clicked()"), self._change_state)
        QtCore.QObject.connect(self.bigScreen,
                               QtCore.SIGNAL("clicked()"), self.image.popup)


        self.plots.message.connect(self._on_message)
        self.vis_plots.message.connect(self._on_message)
        self.options.message.connect(self._on_message)
        #self.options.fit_name.connect(self.on_fit_name)
        self.options.proc_name.connect(self._on_proc_name)


        self.text_out.output('Initializing run ' + str(self.run))
        self.get_roi()
        #now create menu bar
        #menubar = QtGui.QMenuBar(self)
        #fileMenu = menubar.addMenu('&File')
        self.show()



    @QtCore.pyqtSlot(object)
    def _on_message(self,data):
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

        :param data: name of fit
        :type data: string
        """
        self.plots.change_key(data)

    @QtCore.pyqtSlot(object)
    def _on_proc_name(self, data):
        """triggers change to plot output

        :param data: name of fit
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

    def _change_state(self):
        """start and stop data collection thread"""
        if self.running:
            self._end()
        else:
            self._start()

    def _start(self):
        """Function to start listening thread, connect signals and
        :var imageThread: IncomingImage object listening for images

        """
        self.running = True
        self.imageThread = IncomingImage(self.fname)
        QtCore.QObject.connect(self.imageThread,
                               QtCore.SIGNAL('update(QString)'),
                               self.data_recieved)
        QtCore.QObject.connect(self.imageThread,
                               QtCore.SIGNAL('packetReceived(PyQt_PyObject)'),
                               self.data_process)
        self.imageThread.start()
        self.runButton.setStyleSheet("background-color: green")

    def _end(self):
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
        """process the data, including spawn a thread and increment index

        results_dict is """
        results = results_dict['image'] #image
        self.image.setImage(np.transpose(results))
        print('Plots are ',self.plots.key)
        ind = str(self.index)
        #append thread to thread pool
        self.processThreadPool[ind]= QtCore.QThread(self)
        #create new process image object and add to thread just created
        #self.process[ind] = ProcessImage(results,results_dict['exp_params'],
            #self.get_options(),
            #self.path,self.run)
        self.process[ind] = ProcedureRunner(results,
                                            results_dict['exp_params'],
                                            self.path,
                                            self.run,
                                            **self._prepare_procedure())

        self.process[ind].moveToThread(self.processThreadPool[ind])
        #connect start signal

        QtCore.QObject.connect(self.processThreadPool[ind],
                               QtCore.SIGNAL('started()'),
                                self.process[ind].run)

        QtCore.QObject.connect(self.process[ind],
                               QtCore.SIGNAL('proc_results'),#QtCore.SIGNAL('fit_obj'),
                                self._update_data)#self.update_data)

        QtCore.QObject.connect(self.process[ind],
                               QtCore.SIGNAL('finished()'),
                                lambda: self.finish_thread(ind))


        #start thread
        self.processThreadPool[ind].start()
        self.index = self.index + 1

    def finish_thread(self,ind):
        """pop the process should destroy it all I think/"""
        self.process.pop(ind)
        self.processThreadPool[ind].terminate()
        self.processThreadPool.pop(ind)



    def get_options(self):
        """convenience function to return list of options
        note that function which recieves params must make
        deep copy or there will be problems!!"""
        return [self.options.params,
                self.options.type_of_fit,
                self.ROI,
                self.index]

    def _prepare_procedure(self):
        procs = self.options.get_selected()
        return {'index':self.index,
                'ROI':self.ROI,
                'proc_list':procs,
                'param_list':self.options.get_params(procs)}

    def _update_data(self, results):
        """function to update GUI from all procedures

        :param results: dictionary with all results"""
        #add data to dataframe
        self.expData = self.expData.append(pd.DataFrame(results))

        #update data_tables
        self.data_tables.update_pandas_table(self.expData)

        #update the ipython instance
        self._to_ipy()
        #update the plots
        self.plots.update_plots(self.expData)
        self.vis_plots.update_plots(self.expData, self.index)

        self.text_out.output('Updated Internal Structure')

    def update_data(self, results_passed):
        """function to update plots and push data to ipython notebook
        CHANGE THIS SO IT UPDATES PROPER INDEX FOR LONG PROCESSING
        """
        results = results_passed[0]
        self.text_out.output('Image {0} processed'.format(results_passed[-1]))

        ##make into series then push to pandas array
        results['Shot'] = results['Index']
        self.expData = self.expData.append(
            pd.DataFrame(results, index = [results['Shot']]).drop('Index',1)
            )


        #Do updates of different widgets
        self.data_tables.update_pandas_table(self.expData)
        #update update
        self._to_ipy()
        #self.ipy._execute('Plot_obj.update()', False)

        #update plots
        self.plots.update_plots(self.expData)
        self.vis_plots.update_plots(self.expData, self.index)

        #possibly check if image has taken next shot for complicated processing
        self.image.add_lines(results_passed[1])
        self.text_out.output('Updated Internal Structure')

        #############################
        #TESTING
        #############################
        print('len thread pool',len(self.processThreadPool))
        print('lenprocess', len(self.process))


    def set_up_ipy(self):
        """setup the ipython console for use with useful functions"""
        self.ipy.executeCommand('from BECMonitor.Ipython import *')
        self.ipy.executeCommand('%matplotlib inline')
        self.ipy.printText('imported numpy and matplotlib as np and plt')
        self.ipy.pushVariables({'help_str':'testing this'})

    def _to_ipy(self):
        """push all variables to Ipython notebook"""
        ans = {}
        for i in self.expData.columns:
            ans[i] = self.expData[i].get_values()
        self.ipy.pushVariables(ans)

    def _read_out_gui_state(self):
        """function to read out state for testing convenience"""
        print(dir())

#main routine
if __name__ == '__main__':
      app = QtGui.QApplication(sys.argv)
      win = MainWindow()
      #run this baby
      sys.exit(app.exec_())
