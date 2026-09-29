import os
import sys

# Make the JamZone scripts (one level up) importable by the tests.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
