# -*- coding: utf-8 -*-
"""
Created on Wed Jun  3 11:03:42 2015
Class for auxillary functions
@author: zag
"""
from pyqtgraph import QtGui, QtCore
try:
    import BECMonitor.Auxfunctions as af
except:
    import Auxfunctions as af
import inspect
from imp import reload

class AuxillaryFunctionContainerWidget(QtGui.QWidget):
    """class for displaying container of auxillary function widgets
    will hold a stacked layout of all auxillary functions"""

    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self)
        self.func_stack = QtGui.QStackedWidget()
        self.choose_box = QtGui.QComboBox()
        self.function_widgets = {}
        self.func_list = [name for name, val in af.__dict__.items() if callable(val)]
        for name in self.func_list:
            self.add_element(name)

        #button to inject new functions
        self.inject_b = QtGui.QPushButton('Reload Functions')

        QtCore.QObject.connect(self.inject_b,
                               QtCore.SIGNAL('clicked()'),
                                self.re_import)
        QtCore.QObject.connect(self.choose_box,
                                QtCore.SIGNAL('activated(int)'),

                        self.func_stack.setCurrentIndex)

        layout = QtGui.QVBoxLayout()
        top = QtGui.QHBoxLayout()
        top.addWidget(self.choose_box)
        top.addWidget(self.inject_b)
        layout.addLayout(top)
        layout.addWidget(self.func_stack)
        self.setLayout(layout)

    def add_element(self,name):
        """convenicne function to create function widget and add to proper
        dictionaries"""
        self.function_widgets[name] = AuxillaryFunctionWidget(name)
        self.func_stack.addWidget(self.function_widgets[name])
        self.choose_box.addItem(name)

    def re_import(self):
        reload(af)
        new_func_list = [name for name, val in af.__dict__.items() if callable(val)]

        #remove all old widgets rely on garbage collection
        self.choose_box.clear()
        for name in self.func_list:
            self.func_stack.removeWidget(self.function_widgets[name])
        self.function_widgets.clear()

        for name in new_func_list:
            self.add_element(name)
        self.func_list = new_func_list


class AuxillaryFunctionWidget(QtGui.QWidget):
    """class holding function and entry information"""
    def __init__(self,func, parent = None):
        QtGui.QWidget.__init__(self)
        self.func = getattr(af, func)
        self.args = inspect.getargspec(self.func)[0]
        self.source = inspect.getsource(self.func)

        self.param_entry_boxes = {} #dictionary for QDoubleSpinBox

        self.calculate_b = QtGui.QPushButton('Calculate')
        self.answer = QtGui.QLineEdit()
        self.answer.setReadOnly(True)

        QtCore.QObject.connect(self.calculate_b,
                                QtCore.SIGNAL('clicked()'),
                                self.calculate)


        ans_layout = QtGui.QVBoxLayout()
        ans_layout.addWidget(self.calculate_b)
        ans_layout.addWidget(self.answer)

        layout = QtGui.QHBoxLayout()
        spacer = QtGui.QSpacerItem(100,40,
                                   QtGui.QSizePolicy.Minimum,
                                   QtGui.QSizePolicy.Expanding)
        layout.addLayout(self.generate_info_widgets())
        layout.addItem(spacer)
        layout.addLayout(self.generate_params_widgets())
        layout.addLayout(ans_layout)
        self.setLayout(layout)

    def calculate(self):
        """calculate the function"""
        self.answer.clear()
        ans = self.func(**self.get_params())
        self.answer.setText(str(ans))

    def get_params(self):
        return {key:self.param_entry_boxes[key].value() for key in self.param_entry_boxes.keys()}

    def generate_params_widgets(self):
        """generate parameter sublayout and return layout"""
        layout = QtGui.QVBoxLayout()
        #for each parameter generate label and widget
        for param in self.args:
            self.param_entry_boxes[param] = QtGui.QDoubleSpinBox()
            self.param_entry_boxes[param].setRange(-1e20,1e20)
            self.param_entry_boxes[param].setDecimals(3)
            label = QtGui.QLabel()
            label.setText(param)
            hlayout = QtGui.QHBoxLayout()
            hlayout.addWidget(label)
            hlayout.addWidget(self.param_entry_boxes[param])
            layout.addLayout(hlayout)

        return layout

    def generate_info_widgets(self):
        """generate info sublayouts"""

        source = QtGui.QLabel()
        source.setText(self.source)
        source.setStyleSheet("font: 12pt;")

        source_l = QtGui.QVBoxLayout()
        source_l.addWidget(source)

        return source_l
