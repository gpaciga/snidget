#!/usr/bin/env python
""" Simply track expenses, income, account balances, etc."""

import sys # to get command line options

# If no args, start the gui
# Else, parse the args
if __name__ == "__main__":
    if not sys.argv[1:]:
        from snidget import gui
        gui.SnidgetGUI().start()
    else:
        from snidget import cli
        cli.parse_args(sys.argv[1:])
