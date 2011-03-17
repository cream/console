#! /usr/bin/python
# -*- coding: utf-8 -*-

import os
import gtk
import math
import pango
import vte
from random import random

import cream
import cream.gui

import console

KEY_BINDINGS = {
    gtk.keysyms.T: 'new_tab',
    gtk.keysyms.W: 'close_tab',
    gtk.keysyms.P: 'show_preferences'
}

DEFAULT_TITLE = "Cream Terminal"
HOT_CORNER_RADIUS = 18

COLORS = [
    (.5, 0, 0),
    (0, .5, 0),
    (0, 0, .5),
    (.5, .5, 0),
    (0, .5, .5),
    (.5, 0, .5),
    (.3, 0, 0),
    (0, .3, 0),
    (0, 0, .3),
    (.3, .3, 0),
    (0, .3, .3),
    (.3, 0, .3),
    (.7, 0, 0),
    (0, .7, 0),
    (0, 0, .7),
    (.7, .7, 0),
    (0, .7, .7),
    (.7, 0, .7),
    ]

COLORS_USED = 0

def get_tab_color():
    global COLORS_USED
    n = COLORS_USED
    COLORS_USED += 1
    if n < len(COLORS):
        return COLORS[n]
    else:
        r = random()
        g = random()
        b = random()
        return (r, g, b)

class Console(cream.Module):

    def __init__(self):

        cream.Module.__init__(self, 'org.cream.Console')

        self.terminals = []

        self.base_width = 0
        self.base_height = 0

        self.window = gtk.Window()
        self.window.set_title(DEFAULT_TITLE)
        self.window.connect('delete_event', self.destroy_cb)
        self.window.connect('key-press-event', self.key_cb)

        self.window.resize(620, 320)

        self.notebook = gtk.Notebook()
        self.notebook.set_show_border(False)
        self.notebook.set_show_tabs(False)
        self.notebook.connect('switch-page', self.switch_page_cb)
        self.notebook.connect('page-removed', self.remove_page_cb)
        self.notebook.connect('page-reordered', self.reorder_page_cb)

        self.window.add(self.notebook)

        for option, field in self.config.fields.iteritems():
            field.connect('value-changed',
                          getattr(self, 'on_%s_changed_cb' % option))


    def main(self):

        self.window.show_all()
        self.new_tab()
        cream.Module.main(self)


    def on_background_color_changed_cb(self, sender, field, bgcolor):
        for term in self.terminals:
            term.set_color_background(gtk.gdk.color_parse(bgcolor.to_string()))

    def on_foreground_color_changed_cb(self, sender, field, fgcolor):
        for term in self.terminals:
            term.set_color_foreground(gtk.gdk.color_parse(fgcolor.to_string()))

    def on_font_changed_cb(self, sender, field, font):
        for terminal in self.terminals:
            terminal.set_font(font.to_string())

    def on_lines_changed_cb(self, sender, field, lines):
        for terminal in self.terminals:
            terminal.set_scrollback_lines(lines)

    def on_tab_indicators_changed_cb(self, sender, field, value):
        pass


    def switch_page_cb(self, notebook, page, num):

        if not self.notebook.get_n_pages() > 1:
            self.notebook.set_show_tabs(False)
            self.notebook.set_show_border(False)
        else:
            self.notebook.set_show_tabs(True)
            self.notebook.set_show_border(True)

        title = self.notebook.get_nth_page(num).get_window_title() or \
                DEFAULT_TITLE

        self.window.set_title(title)


    def reorder_page_cb(self, notebook, page, num):
        pass


    def remove_page_cb(self, notebook, page, num):

        if not self.notebook.get_n_pages() > 1:
            self.notebook.set_show_tabs(False)
            self.notebook.set_show_border(False)
        else:
            self.notebook.set_show_tabs(True)
            self.notebook.set_show_border(True)


    def terminal_title_changed_cb(self, terminal):

        title = terminal.get_window_title() or DEFAULT_TITLE
        
        tab = self.notebook.get_tab_label(terminal)

        label = gtk.Label(title)
        label.set_ellipsize(pango.ELLIPSIZE_END)

        if self.config.tab_indicators:
            tab.remove(tab.get_children()[1])
            tab.pack_start(label, True, True, 5)
        else:
            tab.remove(tab.get_children()[0])
            tab.pack_start(label, True, True, 0)
        tab.show_all()

        if self.notebook.page_num(terminal) == self.notebook.get_current_page():
            self.window.set_title(terminal.get_window_title() or DEFAULT_TITLE)


    def terminal_beep_cb(self, terminal):
        pass


    def terminal_char_size_changed_cb(self, terminal, width, height):

        self.char_width = width
        self.char_height = height
        self.update_geometry()


    def update_geometry(self):

        self.window.set_geometry_hints(
            base_width=self.base_width, base_height=self.base_height,
            width_inc=self.char_width, height_inc=self.char_height)


    def terminal_size_allocate_cb(self, terminal, allocation):

        self.base_width = self.window.get_allocation().width - allocation.width
        self.base_height = self.window.get_allocation().height - allocation.height

        self.base_width += terminal.get_padding()[0]
        self.base_height += terminal.get_padding()[1]

        self.update_geometry()


    def new_tab(self):
        """ Function for appending a new terminal to the notebook. """

        # Creating and setting up the terminal widget...
        terminal = vte.Terminal()
        terminal.set_size_request(0, 0)
        terminal.set_app_paintable(True)
        
        terminal.hot_corner_hover = False
        terminal.hot_corner_alpha = .2
        terminal.current_animation = None

        terminal.connect_after('expose-event', self.terminal_expose_cb)
        terminal.connect('motion-notify-event', self.terminal_motion_notify_cb)
        terminal.connect('button-press-event', self.terminal_button_press_cb)
        terminal.connect('leave-notify-event', self.terminal_leave_notify_cb)
        terminal.connect('button-release-event', self.terminal_button_release_cb)
        terminal.connect('child-exited', self.close_tab_cb)
        terminal.connect('window-title-changed', self.terminal_title_changed_cb)
        terminal.connect('beep', self.terminal_beep_cb)
        terminal.connect('char-size-changed', self.terminal_char_size_changed_cb)
        terminal.connect('size-allocate', self.terminal_size_allocate_cb)

        os.chdir(os.getenv('HOME'))
        terminal.fork_command()

        # Set configuration options...
        bg = gtk.gdk.color_parse(self.config.background_color.to_string())
        fg = gtk.gdk.color_parse(self.config.foreground_color.to_string())
        terminal.set_colors(fg, bg, [])
        terminal.set_scrollback_lines(self.config.lines)
        terminal.set_font(self.config.font.to_string())

        # Appending the terminal widget to the notebook.
        n = self.notebook.get_n_pages()
        tab = gtk.HBox()
        label = gtk.Label(DEFAULT_TITLE)
        label.set_ellipsize(pango.ELLIPSIZE_END)
        if self.config.tab_indicators:
            tab.pack_start(console.TerminalIcon(color=get_tab_color()), False, False, 0)
            tab.pack_start(label, True, True, 5)
        else:
            tab.pack_start(label, True, True, 0)
        tab.show_all()
        num = self.notebook.append_page(terminal, tab)
        self.notebook.set_tab_reorderable(terminal, True)
        self.notebook.set_tab_label_packing(terminal, True, True, gtk.PACK_START)

        self.terminals.append(terminal)

        terminal.show_all()

        self.notebook.set_current_page(num)


    def close_tab(self, num=None):
        """
        Close a tab.
        If ``num`` is ``None``, the current tab will be closed, if not, the
        tab with the given number will be closed.
        """

        if num is None:
            num = self.notebook.get_current_page()

        self.notebook.remove_page(num)

        if not self.notebook.get_n_pages() >= 1:
            self.destroy_cb()


    def show_preferences(self):

        self.config.show_dialog()
        
        
    def terminal_expose_cb(self, terminal, event=None):
    
        x, y, width, height = terminal.get_allocation()
        ctx = terminal.window.cairo_create()
        
        if event:
            ctx.rectangle(*event.area)
            ctx.clip()
        
        ctx.arc(width, height, HOT_CORNER_RADIUS, 0, 2*math.pi)
        ctx.set_source_rgba(0, 0, 0, terminal.hot_corner_alpha)
        ctx.fill()
        
        
    def fade_hot_corner(self, terminal, alpha):
        
        x, y, width, height = terminal.get_allocation()
        
        def update_cb(timeline, state):
            terminal.hot_corner_alpha = start_alpha + state*(alpha - start_alpha)
            terminal.window.invalidate_rect(gtk.gdk.Rectangle(width-HOT_CORNER_RADIUS, height-HOT_CORNER_RADIUS, HOT_CORNER_RADIUS, HOT_CORNER_RADIUS), True)
            
        if terminal.current_animation:
            terminal.current_animation.stop()
            
        start_alpha = terminal.hot_corner_alpha
        
        t = cream.gui.Timeline(400, cream.gui.CURVE_SINE)
        t.connect('update', update_cb)
        
        terminal.current_animation = t
        t.run()
    

    def terminal_motion_notify_cb(self, terminal, event):
        
        x, y, width, height = terminal.get_allocation()
        if math.sqrt((width - event.x)**2 + (height-event.y)**2) <= HOT_CORNER_RADIUS:
            cursor = gtk.gdk.Cursor(gtk.gdk.ARROW)
            terminal.window.set_cursor(cursor)
            
            if not terminal.hot_corner_hover:
                terminal.hot_corner_hover = True
                self.fade_hot_corner(terminal, .5)
            return True
        else:
            if terminal.hot_corner_hover:
                terminal.hot_corner_hover = False
                self.fade_hot_corner(terminal, .2)
                
    
    def terminal_leave_notify_cb(self, terminal, event):

        if terminal.hot_corner_hover:
            terminal.hot_corner_hover = False
            self.fade_hot_corner(terminal, .2)
        
        
    def terminal_button_press_cb(self, terminal, event):
        
        x, y, width, height = terminal.get_allocation()
        if math.sqrt((width - event.x)**2 + (height-event.y)**2) <= HOT_CORNER_RADIUS:
            cursor = gtk.gdk.Cursor(gtk.gdk.ARROW)
            terminal.window.set_cursor(cursor)
            return True
        else:
            return False
        
        
    def terminal_button_release_cb(self, terminal, event):
        
        x, y, width, height = terminal.get_allocation()
        if math.sqrt((width - event.x)**2 + (height-event.y)**2) <= HOT_CORNER_RADIUS:
            cursor = gtk.gdk.Cursor(gtk.gdk.ARROW)
            terminal.window.set_cursor(cursor)
            self.show_preferences()
            return True
        else:
            return False


    def key_cb(self, widget, event):

        if event.state & gtk.gdk.CONTROL_MASK and event.state & gtk.gdk.SHIFT_MASK and event.keyval in KEY_BINDINGS:
            getattr(self, KEY_BINDINGS[event.keyval])()
            return True


    def close_tab_cb(self, terminal):

        self.close_tab(self.notebook.page_num(terminal))


    def destroy_cb(self, *args):

        self.quit()


if __name__ == '__main__':
    c = Console()
    c.main()
