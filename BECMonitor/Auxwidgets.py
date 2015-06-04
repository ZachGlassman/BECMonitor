# -*- coding: utf-8 -*-
"""
Created on Mon Jun  1 14:09:17 2015
Some useful Widgets
@author: zag
"""
from pyqtgraph.Qt import QtCore, QtGui

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
        