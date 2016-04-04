from pyqtgraph import QtGui
import sys
import os.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from SpinorMonitor import MainWindow
from ProcedureObject import Procedure
import pandas as pd
from collections import OrderedDict
import numpy as np
import nose
from nose.tools import raises

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


def test_Procedure_output():
    from collections import OrderedDict
    y_dict = {'value':10,'max':100}
    def test_proc_one_func(data,x,y=y_dict):
        return {'val':x * y}
    test_proc_one = Procedure('test_proc_one',test_proc_one_func,data='data')

    input_out = OrderedDict([('x',{'value':0,'min':None,'max':None}),('y',y_dict)])
    assert test_proc_one.input == input_out
    assert test_proc_one.plot_vars == ['val']

@raises(ValueError)
def test_Procedure_output2():
    y_dict = {'value':10,'max':100}
    def test_proc_one_func(data,x,y=y_dict):
        return x*y
    test_proc_one = Procedure('test_proc_one',test_proc_one_func,data='data')

def test_Procedure_output3():
    y_dict = {'value':10,'max':100}
    def test_proc_one_func(data,x,y=y_dict):
        return {'val'+str(i):x * y for i in range(10)}
    test_proc_one = Procedure('test_proc_one',test_proc_one_func,data='data')

    assert len(test_proc_one.get_plot_vars()) == 6

def test_Procedure_output4():
    y_dict = {'value':10,'max':100}
    def test_proc_one_func(data,x,y=y_dict):
        return OrderedDict({'val'+str(i):x * y for i in range(10)})
    test_proc_one = Procedure('test_proc_one',test_proc_one_func,data='data')
