#!/usr/bin/env python3
"""Verify the DescentBuddy icon PNG is present in the build directory."""

import os
import sys

build_dir = os.path.dirname(os.path.abspath(__file__))
out_path = os.path.join(build_dir, "descentbuddy.png")

if not os.path.isfile(out_path):
    print(f"ERROR: Icon not found at {out_path}")
    sys.exit(1)

print(f"Icon ready: {out_path}")
