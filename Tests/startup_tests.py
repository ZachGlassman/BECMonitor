from pyqtgraph import QtGui
import sys
from BECMonitor.SpinorMonitor import MainWindow
from BECMonitor.Procedure import Procedure
import pandas as pd
import numpy as np
import nose

def setup_start():
    """n is number of rows i ndataframe"""
    #nock this up
    columns = ['All', 'N_BEC_Atoms', 'N_Therm_Atoms', 'Shot', 'Temperature', 'X_Width',
     'Y_Width', 'spin', 'timing']
    data = np.random.rand(100,len(columns))
    return pd.DataFrame(data,columns=columns)

def test_start_up():
    fname = 'testing_filepath'
    start_path = 'data_path'
    procs = ['hello','sup brah']
    test_df = setup_start()
    app = QtGui.QApplication(sys.argv)
    win = MainWindow(fname,start_path, procs,test_df)

    #now do assertions
    nose.tools.eq_(fname,win.fname)
    nose.tools.eq_(False,win.running)
