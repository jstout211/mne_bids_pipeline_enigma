#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 15 08:08:35 2022

@author: jstout
"""
import os.path as op
import sys
py_fname=sys.argv[1]

python_path = op.join(op.abspath(op.dirname(__file__)), 
                      'enigma_meg',
                      'bin', 
                      'python')
hash_line = '#!'+python_path


with open(py_fname) as w:
    tmp = w.readlines()

with open(py_fname, 'w') as w:
    print(f'Rewriting header for {py_fname}')
    print(f'{hash_line}')
    w.writelines(hash_line)
    w.writelines(tmp[1:])