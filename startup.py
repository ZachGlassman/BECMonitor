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

message = 'Welcome to BECMonitor version {0}.\n You have initalized \
 with\n data_path : {1}\n image_path : {2}'
#main routine
if __name__ == '__main__':
      info =  elem2dict(etree.parse('experiment.config').getroot())
      fname = info['image_path']
      start_path = info['data_path']
      print(message.format(__version__,start_path,fname))
      app = QtGui.QApplication(sys.argv)
      win = MainWindow(fname,start_path)
      #run this baby
      sys.exit(app.exec_())
