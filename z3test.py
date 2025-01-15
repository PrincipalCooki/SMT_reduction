#!/usr/bin/python3

from z3 import *

## Simple check-up of z3 installation
x = Int('x')
y = Int('y')
s = Solver()
s.add(x > 10, y == x + 2)
ans = s.check()
if ans == sat:
    m = s.model()
    print(f"x = {m[x]}")
    print(f"y = {m[y]}")
else:
    print(s.proof())