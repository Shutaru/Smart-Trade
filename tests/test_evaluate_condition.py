import pytest
from strategy import evaluate_condition

# Minimal fake data
TS = [0,1,2,3]
O=[1,2,3,4]
H=[1,2,3,4]
L=[1,2,3,4]
C=[1,2,3,4]
FEATS={'rsi14':[10,15,25,30], 'ema20':[1.0,1.1,1.2,1.3]}

def test_gt_constant():
 cond={'indicator':'rsi14','op':'>','rhs':20}
 assert evaluate_condition(cond,2,TS,O,H,L,C,FEATS) == True

def test_crosses_above_constant():
 cond={'indicator':'rsi14','op':'crosses_above','rhs':20}
 assert evaluate_condition(cond,2,TS,O,H,L,C,FEATS) == True

def test_crosses_below_constant():
 cond={'indicator':'rsi14','op':'crosses_below','rhs':20}
 assert evaluate_condition(cond,1,TS,O,H,L,C,FEATS) == False

def test_between_list():
 cond={'indicator':'rsi14','op':'between','rhs':[10,20]}
 assert evaluate_condition(cond,1,TS,O,H,L,C,FEATS) == True
