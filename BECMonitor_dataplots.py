# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 19:06:09 2015
Classes for plotting in the top
@author: zag
"""
from pyqtgraph import QtGui, QtCore
import pyqtgraph as pg
import matplotlib.pyplot as plt
class PlotGrid(QtGui.QWidget):
    def __init__(self, parent = None):
        """convenience container widget"""
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
            
class DataPlots(QtGui.QWidget):
    """graphs to populate different stuff
    we will create all the plots, but only update the ones we care about
    to save some computation"""
    #emitting message, can't define as instance variable
    message = QtCore.pyqtSignal(object)
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        
        self.graph_names = {}
        self.graph_names['Mixture'] = ["N_BEC_Atoms",
                       "N_Therm_Atoms",
                       "X_Width",
                       "Y_Width",
                       "Temperature",
                       "All"]
                       
        self.graph_names['Stern-Gerlach'] = ['N_BEC_Atoms1',
                            'N_BEC_Atoms0',
                            'N_BEC_Atoms-1',
                            'X_Width1',
                            'X_Width0',
                            'X_Width-1']
    
        self.graph_dict = {i:{} for i in self.graph_names.keys()}
        #dictionary to hold data items in graph
        self.graph_data_dict = {i:{} for i in self.graph_names.keys()}
        self.key = 'Mixture' #type of fit to do!!!
       
        self.plot_grid = {}
        #initiate all plots and put them in stacked widgets
        self.plotting_stack = QtGui.QStackedWidget()
        for key in self.graph_names.keys():
            k = 0
            self.plot_grid[key] = PlotGrid()
            row1 = QtGui.QHBoxLayout()
            row2 = QtGui.QHBoxLayout()
            for i in self.graph_names[key]:
                #create the plot widgets
                self.graph_dict[key][i] = pg.PlotWidget(self,title = i)
                self.graph_dict[key][i].setLabel('bottom', 'Index')
                if k < 3:
                    row1.addWidget(self.graph_dict[key][i])
                else:
                    row2.addWidget(self.graph_dict[key][i])
                k = k + 1
                self.graph_data_dict[key][i] = self.graph_dict[key][i].plot([0],[0],
                    symbolSize=5, symbolBrush=(100, 100, 255, 50))
                self.graph_data_dict[key][i].sigPointsClicked.connect(self.emit_it)
        #add to layouts
            self.plot_grid[key].layout.addLayout(row1)
            self.plot_grid[key].layout.addLayout(row2)
            #add to stack
            self.plotting_stack.addWidget(self.plot_grid[key])
        
        layout = QtGui.QVBoxLayout()
        layout.setSpacing(0)
        layout.addWidget(self.plotting_stack)
        self.setLayout(layout)
        
        
    def create_graphs(self):
        """function to create the graphs"""
    def update_plots(self, df):
        """Update all the Plots"""
        for i in self.graph_dict[self.key].keys():
            self.graph_data_dict[self.key][i].setData(list(df.index),
                                            list(df[i]))
       
   
    def emit_it(self, item,points):
        self.message.emit(points[0].pos())
        
    def change_key(self, key):
        self.key = key
        self.plotting_stack.setCurrentWidget(self.plot_grid[key])
                   
       
  
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
        
        
            
