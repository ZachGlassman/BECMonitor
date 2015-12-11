# -*- coding: utf-8 -*-
"""
This is the data aquisition software for Paul Lett's sodium spinor experiment.
It collects images, processes them, saves them, and provides
convenient information storage for determined paramters
It is written in pure python 3
@dependencies: pyqtgraph, ipython, matplotlib, lmfit, numpy, scipy,lxml
@author: zachglassman
"""
__version__ = '0.2'
from lxml import etree
from pyqtgraph import QtGui
import sys
from BECMonitor.SpinorMonitor import MainWindow
from BECMonitor.Procedure import Procedure
import importlib
import gc

def elem2dict(node):
    """
    Convert an lxml.etree node tree into a dict.
    modified from https://gist.github.com/jacobian/795571
    """
    d = {}
    for e in node.iterchildren():
        key = e.tag.split('}')[1] if '}' in e.tag else e.tag
        value = e.text.replace('\n','').replace(' ', '') if e.text else elem2dict(e)
        d[key] = value
    return d

def find_procedures(files):
    """function to find procedures from files in startup config
    first import all files
    then get all instances of Procedure"""
    procs = {i: importlib.import_module('BECMonitor.{0}'.format(i)) for i in files.split(',')}
    #now bind into dictionary
    return {i.name:i for i in gc.get_objects() if isinstance(i, Procedure)}

message = 'Welcome to BECMonitor version {0}.\n You have initalized \
 with\n data_path : {1}\n image_path : {2}'
#main routine
if __name__ == '__main__':
      info =  elem2dict(etree.parse('experiment.config').getroot())
      fname = info['image_path']
      start_path = info['data_path']
      files = info['procedures']
      procs = find_procedures(files)


      print(message.format(__version__,start_path,fname))
      print('Imported Procedures are:')
      for i in procs.keys():
          print(i)
      #app = QtGui.QApplication(sys.argv)
      #win = MainWindow(fname,start_path, procs)
      #run this baby
      #sys.exit(app.exec_())
