#! /usr/bin/python
# -*- coding: utf-8 -*-

import os
import gtk
import vte

import cream

KEY_BINDINGS = {
    gtk.keysyms.T: 'new_tab',
    gtk.keysyms.W: 'close_tab',
    gtk.keysyms.P: 'show_preferences'
}

DEFAULT_TITLE = "Cream Terminal"

class Console(cream.Module):

    def __init__(self):

        cream.Module.__init__(self)

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
        print num


    def remove_page_cb(self, notebook, page, num):

        if not self.notebook.get_n_pages() > 1:
            self.notebook.set_show_tabs(False)
            self.notebook.set_show_border(False)
        else:
            self.notebook.set_show_tabs(True)
            self.notebook.set_show_border(True)


    def terminal_title_changed_cb(self, terminal):

        title = terminal.get_window_title() or DEFAULT_TITLE
        if len(title) > 25:
            title = title[:22] + "..."

        self.notebook.set_tab_label(terminal, gtk.Label(title))

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
        num = self.notebook.append_page(terminal, gtk.Label(DEFAULT_TITLE))
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

        self.config.show_window()


    def key_cb(self, widget, event):

        if event.state & gtk.gdk.CONTROL_MASK and event.state & gtk.gdk.SHIFT_MASK and event.keyval in KEY_BINDINGS:
            getattr(self, KEY_BINDINGS[event.keyval])()
            return True


    def close_tab_cb(self, terminal):

        self.close_tab(self.notebook.page_num(terminal))


    def destroy_cb(self, *args):

        self.quit()


if __name__ == '__main__':
    console = Console()
    console.main()
