#    This file is part of Snidget.
#
#    Snidget is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Snidget is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Snidget.  If not, see <http://www.gnu.org/licenses/>.


#! make this a class.... need self. stuff to hold data for various functions?

import snidget

#import numpy as np
#import matplotlib.pyplot as plt

import gtk
from matplotlib.backends.backend_gtk import FigureCanvasGTK as FigureCanvas
from matplotlib.figure import Figure

def plotwindow():
    # set up the window
    win = gtk.Window()
    #win.connect("destroy", lambda x: gtk.main_quit())
    win.set_default_size(600,400)
    win.set_title("Snidget Plot")

    # make a vbox for controls
    vbox = gtk.VBox()
    win.add(vbox)

    # Setup the figure and canvas in the window
    fig = Figure()
    plot = fig.add_subplot(111)
    plot.set_xlabel("Date")
    plot.set_ylabel("Change")
    canvas = FigureCanvas(fig)
    vbox.pack_start(canvas)

    # get the data
    weekly_integration = snidget.database.integrate(n=7)
    dates=[]
    deltas=[]
    for datum in weekly_integration:
        dates.append(datum[0])
        deltas.append(datum[1])

    # plot it
    plot.plot(dates, deltas)

    # rotate labels -- causes crash
    #labels = plot.get_xticklabels()
    #for label in labels:
    #    label.set_rotation(90)

    # show
    fig.canvas.draw()
    win.show_all()


