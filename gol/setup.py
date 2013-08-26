__author__ = "Bojan Delic <bojan@delic.in.rs>"
__mail__ = "bojan@delic.in.rs"

from distutils.core import setup
import py2exe

setup(windows=['main.py', 'gol.py', 'main_window.py'], options={"py2exe": {"includes": ["sip"]}})