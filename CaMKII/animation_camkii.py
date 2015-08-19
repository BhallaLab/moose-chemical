#! /usr/bin/env python

from graph_tool.all import *
from numpy.random import *
import sys, os, os.path
import cairo
from camkii_ring import camkii_ring

seed(42)
seed_rng(42)

steps_ = 0

# We need some Gtk and gobject functions
from gi.repository import Gtk, Gdk, GdkPixbuf, GObject

# If True, the frames will be dumped to disk as images.
offscreen = sys.argv[1] == "offscreen" if len(sys.argv) > 1 else False
max_count = 500
if offscreen and not os.path.exists("./frames"):
    os.mkdir("./frames")

# This creates a GTK+ window with the initial graph layout
if not offscreen:
    win = camkii_ring.graph_window(
            geometry=(500, 400)
            , vertex_size=42
            , vertex_anchor=0
            , edge_color=[0.6, 0.6, 0.6, 1]
            , vertex_halo_size=1.2
            , vertex_halo_color=[0.8, 0, 0, 0.6]
            )
else:
    count = 0
    win = Gtk.OffscreenWindow()
    win.set_default_size(500, 400)
    win.graph = camkii_ring.graph_window(
            vertex_size=42
            , vertex_anchor=0
            , edge_color=[0.6, 0.6, 0.6, 1]
            , vertex_halo_color=[0.8, 0, 0, 0.6]
            )
    win.add(win.graph)

# This function will be called repeatedly by the GTK+ main loop, and we use it
# to update the state according to the SIRS dynamics.
def update_state():
    global steps_
    steps_ += 1
    camkii_ring.update_state()
    win.graph.regenerate_surface()
    win.graph.queue_draw()
    # We need to return True so that the main loop will call this function more
    # than once.
    if steps_ < 1000:
        return True
    else:
        print("Done 1000 steps")
        return False


def main():
    # Bind the function above as an 'idle' callback.
    cid = GObject.idle_add(update_state)
    # We will give the user the ability to stop the program by closing the window.
    win.connect("delete_event", Gtk.main_quit)
    # Actually show the window, and start the main loop.
    win.show_all()
    Gtk.main()

if __name__ == '__main__':
    main()
