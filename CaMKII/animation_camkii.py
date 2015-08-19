#! /usr/bin/env python

from graph_tool.all import *
from numpy.random import *
import sys, os, os.path
import cairo

seed(42)
seed_rng(42)

# We need some Gtk and gobject functions
from gi.repository import Gtk, Gdk, GdkPixbuf, GObject

# We will use the karate-club network
camkiiRing_ = load_graph("camkii_ring.dot")
pos_= sfdp_layout(camkiiRing_)

# We will filter out vertices which are in the "Recovered" state, by masking
# them using a property map.
removed = camkiiRing_.new_vertex_property("bool")

# Initialize all vertices to the S state
state = camkiiRing_.new_vertex_property("int")
state.a = 0

# Images used to draw the nodes. They need to be loaded as cairo surfaces.
unphospho_ = cairo.ImageSurface.create_from_png("_images/face-grin.png")
phospho_ = cairo.ImageSurface.create_from_png("_images/zombie.png")

vertex_sfcs = camkiiRing_.new_vertex_property("object")
for v in camkiiRing_.vertices():
    vertex_sfcs[v] = unphospho_

# Newly infected nodes will be highlighted in red
newlyPhosporylated = camkiiRing_.new_vertex_property("bool")

# If True, the frames will be dumped to disk as images.
offscreen = sys.argv[1] == "offscreen" if len(sys.argv) > 1 else False
max_count = 500
if offscreen and not os.path.exists("./frames"):
    os.mkdir("./frames")

# This creates a GTK+ window with the initial graph layout
if not offscreen:
    win = GraphWindow(camkiiRing_, pos_, geometry=(500, 400),
                      vertex_size=42,
                      vertex_anchor=0,
                      edge_color=[0.6, 0.6, 0.6, 1],
                      vertex_surface=vertex_sfcs,
                      vertex_halo=newlyPhosporylated,
                      vertex_halo_size=1.2,
                      vertex_halo_color=[0.8, 0, 0, 0.6]
                      )
else:
    count = 0
    win = Gtk.OffscreenWindow()
    win.set_default_size(500, 400)
    win.graph = GraphWidget(camkiiRing_, pos,
                            vertex_size=42,
                            vertex_anchor=0,
                            edge_color=[0.6, 0.6, 0.6, 1],
                            vertex_surface=vertex_sfcs,
                            vertex_halo=newlyPhosporylated,
                            vertex_halo_color=[0.8, 0, 0, 0.6])
    win.add(win.graph)


# This function will be called repeatedly by the GTK+ main loop, and we use it
# to update the state according to the SIRS dynamics.
def update_state():
    newlyPhosporylated.a = False
    removed.a = False

    # visit the nodes in random order
    vs = list(camkiiRing_.vertices())
    # Filter out the recovered vertices
    camkiiRing_.set_vertex_filter(removed, inverted=True)

    # The following will force the re-drawing of the graph, and issue a
    # re-drawing of the GTK window.
    win.graph.regenerate_surface()
    win.graph.queue_draw()

    # if doing an offscreen animation, dump frame to disk
    if offscreen:
        global count
        pixbuf = win.get_pixbuf()
        pixbuf.savev(r'./frames/zombies%06d.png' % count, 'png', [], [])
        if count > max_count:
            sys.exit(0)
        count += 1

    # We need to return True so that the main loop will call this function more
    # than once.
    return True


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
