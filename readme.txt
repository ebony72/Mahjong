#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed July 21 07:07:57 2021

@author: sanjiangli
"""

To generate a batch of games, run xzgame_generator.py
To play a batch of games, run xzgame-all_in_1.py, where you need 
    - select your strategies A & B
    - select game type: 2vs2 or 1vs3
    - save result or not?
    - select game batch: file_name
    - n_GAME: how many games you want to play
    - changshu: starting from which game?

Reorganised on 21.07.21:
-- strategy/ lists several candidate strategies: strategy_21p_7attr is 
       the best basic one; strategyz0614 is an advanced one
-- dfncy/ lists several candidate dfncy calculators, the current one is 
           block_dfncy_7attr.py
-- utils/ contains all utilities we need
         
_________________________________
modules using dfncy calculator
xzplayer.py
all strategies
____________________________________________
@misc{li2019lets,
      title={Let's Play Mahjong!}, 
      author={Sanjiang Li and Xueqing Yan},
      year={2019},
      eprint={1903.03294},
      archivePrefix={arXiv},
      primaryClass={cs.AI}
}
--------------------------------------------