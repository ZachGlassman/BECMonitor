# -*- coding: utf-8 -*-
"""
Created on Fri Mar 13 16:54:53 2015
This Contains Routines called by BECMonitor
@author: zachglassman
"""
import os
import time

def get_run_name(start_path):
    """get name of run and generate proper file structure if not already structured
    start_path points to overall data folder"""
    #start_path = "C:\\Users\\Administrator\\Documents\\BECMonitor\\Data"
    a = time.strftime("%d/%m/%Y").split('/')
    day = a[0]
    month = a[1]
    year = a[2]
    path = os.path.join(start_path,year,month,day)
    #path = start_path + '\\' + year + '\\' + month + '\\' + day
    #don't change dorectory
    try:
        os.makedirs(path,0o777)
    except:
        print('path not created')

    contents = os.listdir(path)
    if 'run_info.txt' in contents:
        with open(os.path.join(path,'run_info.txt'),'r') as fp:
            info = fp.readlines()
            last_run = int(info[-1])
        with open(os.path.join(path,'run_info.txt'),'w') as fp:
            for i in info:
                fp.write(i)
            fp.write(str(last_run + 1) + '\n')
    else:
        with open(os.path.join(path,'run_info.txt'), 'w') as fp:
            fp.write('1' + '\n')
            last_run = 0
    return last_run + 1, path
