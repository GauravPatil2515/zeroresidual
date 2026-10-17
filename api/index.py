import sys
import os

# Ensure src directory is in sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from zeroresidual.server.app import app
