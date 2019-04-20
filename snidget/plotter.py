from __future__ import print_function
import gtk
from matplotlib.backends.backend_gtk import FigureCanvasGTK as FigureCanvas
from matplotlib.figure import Figure

def plot_window(database):
    # set up the window
    win = gtk.Window()
    #win.connect("destroy", lambda x: gtk.main_quit())
    win.set_default_size(600, 400)
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
    weekly_integration = database.integrate(num_days=7)
    dates = []
    deltas = []
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
