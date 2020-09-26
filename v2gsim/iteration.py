import pandas as pd
import numpy as np
import TryOptimization

price_curr = [p1_curr, p2_curr, p3_curr]
price_prev = [p1_prev, p2_prev, p3_prev]
eps = 0.01

while(condition1 and condition2 and condition3):
    price_prev = price_curr
    price_curr = price_curr.update()

for i range(max_iter):
    price_prev = price_curr
    price_curr = price_curr.update()
    if (condition1 and condition2 and condition3):
        break
 
def uc_getprice(out_v2g=None):
    pass

out_v2g = None
for i in range(max_iter):
    price_uc = uc_getprice(out_v2g)
    out_v2g = v2g_getout(price_uc)