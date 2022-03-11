#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed July 21 07:07:57 2021

@author: sanjiangli
"""

To generate a batch of games, run xzgame_generator.py

To play a batch of games, run xzgame-all_in_1.py, where you need select
    - game batch: file_name (the one we use is 'game_batch_0302_1000')
    - n_GAME: how many games you want to play (the number we use is 10)
    - changshu: starting from which game? (the number we use is 0)
                             
You may then find the game records in /testRecord/
        
-- strategy is the best basic one; a more advanced one was also developed but not included here
-- dfncy/ the current dfncy calculator is block_dfncy.py, see Ref. [yan2021fast] (https://arxiv.org/abs/2108.06832)
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
@misc{yan2021fast,
  title={A Fast Algorithm for Computing the Deficiency Number of a Mahjong Hand},
  author={Yan, Xueqing and Li, Yongming and Li, Sanjiang},
  year={2021},
  eprint={2108.06832},
  archivePrefix={arXiv},
  primaryClass={cs.AI}
}
--------------------------------------------
