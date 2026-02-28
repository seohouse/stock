#!/usr/bin/env python3
import runpy, sys
d = runpy.run_path('src/aggregator_ws.py')
globals().update(d)
if __name__ == '__main__':
    # if the module defines a main(), call it; otherwise nothing
    if 'main' in globals():
        main()
