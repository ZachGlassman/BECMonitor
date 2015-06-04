# -*- coding: utf-8 -*-
"""
Created on Thu Jun  4 10:05:39 2015
Program to Generate Sphinx Documentation
@author: zag
"""
import os
import inspect
#go into each file in directory if it is a .py file and not an .init
#and pull out the classes

path = 'C:\\Users\\zag\\Documents\\BECMonitor\\BECMonitor\\'
os.chdir(path)

onlyfile = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path,f))]
files = [i.rstrip('.py') for i in onlyfile if i != '__init__.py' and i != 'icon.png' and i!= 'sphinxgenerator.py']


mods = {}
classes = {}

for i in files:
    mods[i] = __import__(i)
    temp = inspect.getmembers(mods[i], inspect.isclass)
    #print([m[1].__module__ for m in temp])
    classes[i] = [m[0] for m in temp if m[1].__module__ == i]

#for for each class, create a page
os.chdir( 'C:\\Users\\zag\\Documents\\BECMonitor\\BECMonitor\\docs\\')  
for i in classes.keys():
    #print('import',i)
    print('   '+i)
    f = open(i + '.rst','w')
    #write out contents
    f.write(i + '\n')
    f.write(''.join('=' for k in range(len(i)))+'\n\n')
    f.write('Contents:\n\n')
    f.write('.. toctree::\n')
    f.write('   :maxdepth: 3\n\n')
    for j in classes[i]:
        g = open(j + '.rst', 'w')
        g.write(j + '\n')
        g.write(''.join('=' for k in range(len(j)))+'\n')
        f.write('   ' + j + '\n')
        g.write('.. autoclass:: '+ i+'.'+ j + '\n')
        g.write('    :members:\n')
        g.write('    :undoc-members:')
        g.close()
    f.close()
