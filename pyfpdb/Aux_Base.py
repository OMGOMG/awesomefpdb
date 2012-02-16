#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Aux_Base.py

Some base classes for Aux_Hud, Mucked, and other aux-handlers.
These classes were previously in Mucked, and have been split away
for clarity
"""
#    Copyright 2008-2012,  Ray E. Barker
#    
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#    
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#    
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

########################################################################

#    to do

#    Standard Library modules
import logging
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("hud")

#    pyGTK modules
import gtk
import gobject

#   FPDB
import Card


class Aux_Window(object):
    def __init__(self, hud, params, config):
        self.hud     = hud
        self.params  = params
        self.config  = config

#   Override these methods as needed
    def update_data(self, *args): pass
    def update_gui(self, *args):  pass
    def create(self, *args):      pass
    def save_layout(self, *args): pass
    def move_windows(self, *args): pass
    def destroy(self):
        try:
            self.container.destroy()
        except:
            pass

############################################################################
#    Some utility routines useful for Aux_Windows
#
    def get_card_images(self, card_width=30, card_height=42):

        card_images = 53 * [0]
        suits = ('s', 'h', 'd', 'c')
        ranks = (14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2)
        deckimg = self.params['deck']
        try:
            pb = gtk.gdk.pixbuf_new_from_file(self.config.execution_path(deckimg))
        except:
            #FIXME: this can't be right? /usr will not exist on windows
            stockpath = '/usr/share/python-fpdb/' + deckimg
            pb = gtk.gdk.pixbuf_new_from_file(stockpath)
        
        for j in range(0, 13):
            for i in range(0, 4):
                card_images[Card.cardFromValueSuit(ranks[j], suits[i])] = self.cropper(pb, i, j, card_width, card_height)
#    also pick out a card back and store in [0]
        card_images[0] = self.cropper(pb, 2, 13, card_width, card_height)
        return(card_images)
#   cards are 30 wide x 42 high

    def cropper(self, pb, i, j, card_width, card_height):
        """Crop out a card image given an FTP deck and the i, j position."""
        cropped_pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, pb.get_has_alpha(),
                                    pb.get_bits_per_sample(), 30, 42)
        pb.copy_area(30*j, 42*i, 30, 42, cropped_pb, 0, 0)

        if card_height == 42:
            """ no scaling """
            return cropped_pb
        else:
            """Apply scaling to the the 30w x 42h card image """
            scaled_pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, pb.get_has_alpha(),
                                        pb.get_bits_per_sample(),
                                        card_width, card_height)
            scaled_card = cropped_pb.scale_simple(card_width, card_height,
                                                gtk.gdk.INTERP_BILINEAR)

            scaled_card.copy_area(0, 0, self.card_width, self.card_height,
                                        scaled_pb, 0, 0)
            return scaled_pb

    def has_cards(self, cards):
        """Returns the number of cards in the list."""
        n = 0
        for c in cards:
            if c != None and c > 0: n = n + 1
        return n

    def get_id_from_seat(self, seat):
        """Determine player id from seat number, given stat_dict."""
        for id, dict in self.hud.stat_dict.iteritems():
            if seat == dict['seat']:
                return id
        return None
        
class Seat_Window(gtk.Window):
    """Subclass gtk.Window for the seat windows."""
    def __init__(self, aw = None, seat = None):
        super(Seat_Window, self).__init__()
        self.aw = aw
        self.seat = seat
        self.set_skip_taskbar_hint(True)  # invisible to taskbar
        self.set_gravity(gtk.gdk.GRAVITY_STATIC)
        self.set_decorated(False)    # kill titlebars
        self.set_focus(None)
        self.set_focus_on_map(False)
        self.set_accept_focus(False)
        self.connect("configure_event", self.aw.configure_event_cb, self.seat) #normally pointing at Aux_seats class

    def button_press_cb(self, widget, event, *args):
        """Handle button clicks in the event boxes."""
        #double-click events should be avoided
        # these are not working reliably on windows GTK 2.24 toolchain

        if event.button == 1:   # left button event
            self.button_press_left(widget, event, *args)
        elif event.button == 2:   # middle button event
            self.button_press_middle(widget, event, *args)
        elif event.button == 3:   # right button event
            self.button_press_right(widget, event, *args)

    def button_press_left(self, widget, event, *args): pass #superclass will define this
    def button_press_middle(self, widget, event, *args): pass #superclass will define this 
    def button_press_right(self, widget, event, *args):  pass #superclass will define this
    
    def create_contents(self, *args): pass
    def update_contents(self, *args): pass
    
class Aux_Seats(Aux_Window):
    """A super class to display an aux_window or a stat block at each seat."""

    def __init__(self, hud, config, params):
        self.hud     = hud       # hud object that this aux window supports
        self.config  = config    # configuration object for this aux window to use
        self.params  = params    # dict aux params from config
        self.positions = {}      # dict of window positions. normalised for favourite seat and offset
                                 # but _not_ offset to the absolute screen position
        self.displayed = False   # the seat windows are displayed
        self.uses_timer = False  # the Aux_seats object uses a timer to control hiding
        self.timer_on = False    # bool = Ture if the timeout for removing the cards is on

        self.aw_class_window = Seat_Window # classname to be used by the aw_class_window

#    placeholders that should be overridden--so we don't throw errors
    def create_contents(self): pass
    def create_common(self, x, y): pass
    def update_contents(self): pass
    
    def resize_windows(self): 
        #Resize calculation has already happened in HUD_main&hud.py
        # refresh our internal map to reflect these changes
        for i in (range(1, self.hud.max + 1)):
            self.positions[i] = self.hud.layout.location[self.adj[i]]
        self.positions["common"] = self.hud.layout.common
        # and then move everything to the new places
        self.move_windows()

    def move_windows(self):
        for i in (range(1, self.hud.max + 1)):
            self.m_windows[i].move(self.positions[i][0] + self.hud.table.x,
                            self.positions[i][1] + self.hud.table.y)

        self.m_windows["common"].move(self.hud.layout.common[0] + self.hud.table.x,
                                self.hud.layout.common[1] + self.hud.table.y)
        
    def create(self):
        
        self.adj = self.hud.adj_seats(0, self.config)  # move adj_seats to aux and get rid of it in Hud.py
        self.m_windows = {}      # windows to put the card/hud items in

        for i in (range(1, self.hud.max + 1) + ['common']):   
            if i == 'common':
                #    The common window is different from the others. Note that it needs to 
                #    get realized, shown, topified, etc. in create_common
                #    self.hud.layout.xxxxx is updated here after scaling, to ensure
                #    layout and positions are in sync
                (x, y) = self.hud.layout.common
                self.m_windows[i] = self.create_common(x, y)
                self.hud.layout.common = self.create_scale_position(x, y)
            else:
                (x, y) = self.hud.layout.location[self.adj[i]]
                self.m_windows[i] = self.aw_class_window(self, i)
                self.m_windows[i].set_decorated(False)
                self.m_windows[i].set_property("skip-taskbar-hint", True)
                self.m_windows[i].set_focus_on_map(False)
                self.m_windows[i].set_focus(None)
                self.m_windows[i].set_accept_focus(False)
                #self.m_windows[i].connect("configure_event", self.aw_class_window.configure_event_cb, i) ##self.aw_class_window will define this
                self.positions[i] = self.create_scale_position(x, y)
                self.m_windows[i].move(self.positions[i][0] + self.hud.table.x,
                                self.positions[i][1] + self.hud.table.y)
                self.hud.layout.location[self.adj[i]] = self.positions[i]
                if self.params.has_key('opacity'):
                    self.m_windows[i].set_opacity(float(self.params['opacity']))

            # main action below - fill the created window with content
            #    the create_contents method is supplied by the subclass
            #      for hud's this is probably Aux_Hud.stat_window
            self.create_contents(self.m_windows[i], i)

            self.m_windows[i].realize()
            self.hud.table.topify(self.m_windows[i])
            self.m_windows[i].show_all()
            if self.uses_timer:
                self.m_windows[i].hide()
                
        self.hud.layout.height = self.hud.table.height
        self.hud.layout.width = self.hud.table.width
        

    def create_scale_position(self, x, y):
        # for a given x/y, scale according to current height/wid vs. reference
        # height/width
        # This method is needed for create (because the table may not be 
        # the same size as the layout in config)
        
        # any subsequent resizing of this table will be handled through
        # hud_main.idle_resize

        x_scale = (1.0 * self.hud.table.width / self.hud.layout.width)
        y_scale = (1.0 * self.hud.table.height / self.hud.layout.height)
        return (int(x * x_scale), int(y * y_scale))

        
    def update_gui(self, new_hand_id):
        """Update the gui, LDO."""
        for i in self.m_windows.keys():
            self.update_contents(self.m_windows[i], i)
        #reload latest block positions, in case another aux has changed them
        #these lines allow the propagation of block-moves across
        #the hud and mucked handlers for this table
        self.resize_windows()

#   Methods likely to be of use for any Seat_Window implementation
    def destroy(self):
        """Destroy all of the seat windows."""
        try:
            for i in self.m_windows.keys():
                self.m_windows[i].destroy()
                del(self.m_windows[i])
        except AttributeError:
            pass

#   Methods likely to be useful for mucked card windows (or similar) only
    def hide(self):
        """Hide the seat windows."""
        for (i, w) in self.m_windows.iteritems():
            if w is not None: w.hide()
        self.displayed = False

    def save_layout(self, *args):
        """Save new layout back to the aux element in the config file."""
        """ this method is  overridden in the specific aux because
        the HUD's controlling stat boxes set the seat positions and
        the mucked card aux's control the common location
        This class method would only be valid for an aux which has full control
        over all seat and common locations
        """

        log.error(_("Aux_Seats.save_layout called - this shouldn't happen"))
        log.error(_("save_layout method should be handled in the aux"))


    def configure_event_cb(self, widget, event, i, *args):
        """
        This method updates the current location for each statblock.
        This method is needed to record moves for an individual block.
        Move/resize also end up in here due to it being a configure.
        This is not optimal, but isn't easy to work around. fixme.
        """
        if (i): 
            new_abs_position = widget.get_position() #absolute value of the new position
            new_position = (new_abs_position[0]-self.hud.table.x, new_abs_position[1]-self.hud.table.y)
            self.positions[i] = new_position     #write this back to our map
            if i != "common":
                self.hud.layout.location[self.adj[i]] = new_position #update the hud-level dict, so other aux can be told
            else:
                self.hud.layout.common = new_position

