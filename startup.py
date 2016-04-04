# -*- coding: utf-8 -*-
"""
This is the data aquisition software for Paul Lett's sodium spinor experiment.
It collects images, processes them, saves them, and provides
convenient information storage for determined paramters
It is written in pure python 3
@dependencies: pyqtgraph, ipython, matplotlib, lmfit, numpy, scipy
@author: zachglassman
"""
__version__ = '1.0.1'

from pyqtgraph import QtGui
import sys
from BECMonitor.SpinorMonitor import MainWindow
from BECMonitor.ProcedureObject import Procedure
import importlib
import gc
import configparser

def find_procedures(files):
    """function to find procedures from files in startup config
    :param files: list of files"""
    procs = {i: importlib.import_module('BECMonitor.{0}'.format(i)) for i in files}
    #now bind into dictionary
    return {i.name:i for i in gc.get_objects() if isinstance(i, Procedure)}

message = 'Welcome to BECMonitor version {0}.\n You have initalized \
 with\n data_path : {1}\n image_path : {2}'

def get_testing_dataframe(n):
    """n is number of rows i ndataframe"""
    #nock this up
    columns = ['All', 'N_BEC_Atoms', 'N_Therm_Atoms', 'Shot', 'Temperature', 'X_Width',
     'Y_Width', 'spin', 'timing']
    data = np.random.rand(n,len(columns))
    return pd.DataFrame(data,columns=columns)
#main routine
if __name__ == '__main__':
    #load configuartion files
    config = configparser.ConfigParser()
    config.read('experiment.config')
    info = config['System Parameters']
    fname = info['image_path']
    start_path = info['data_path']

    exp_params = config['Experiment Parameters']
    procs_in = config['Procedures']
    files = [procs_in[i] for i in procs_in]


    procs = find_procedures(files)

    print(message.format(__version__,start_path,fname))
    print('Imported Procedures are:')
    for i in procs.keys():
      print(i)
    print('##########################')
    print('All procedure startup tests passed')

    app = QtGui.QApplication(sys.argv)
    #testing
    import pandas as pd
    import numpy as np
    test_df = get_testing_dataframe(100)
    win = MainWindow(fname,start_path, procs, None)
    #run this baby
    sys.exit(app.exec_())
