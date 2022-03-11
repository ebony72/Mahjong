#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed July 21 07:07:57 2021

@author: sanjiangli
"""
Designed a new dfncy calculator, block_dfncy is the current selected calculator

-- block_dfncy partitions the hand H into blocks, generate all quasi
    dcmps for each block, calculate their types, merge these local types into
    types of global quasi dcmps of H, and then calculate their costs

See https://arxiv.org/abs/2108.06832 for details.
