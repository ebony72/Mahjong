#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed July 21 07:07:57 2021

@author: sanjiangli
"""
Designed several dfncy calculator, block_dfncy_attr is the current selected calculator

-- hytreekong is a first implementaion of the quadtree dfncy calculatoor
     introduced in the 2019 arXiv paper (https://arxiv.org/abs/1903.03294), 
     it is slow and sometimes inaccurate
-- global_dfncy_7attr introduces 7 attributes for each quasi dcmp, 
    the cost of which is calculated by the 7 attributes
-- block_dfncy_7attr further partition the hand H into blocks, generate all quasi
    dcmps for each block, calculate their types, merge these local types into
    types of global quasi dcmps of H, and then calculate their costs
-- block_dfncy_8attr is an earlier version of the 7attr calculator 
