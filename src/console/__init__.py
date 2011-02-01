import math

import gobject
import gtk
import cairo

MODE_SPINNING = 0
MODE_STATIC = 1

def rounded_rectangle(cr, x, y, w, h, r=20):

    if r >= h / 2.0:
        r = h / 2.0

    cr.arc(x + r, y + r, r, math.pi, -.5 * math.pi)
    cr.arc(x + w - r, y + r, r, -.5 * math.pi, 0 * math.pi)
    cr.arc(x + w - r, y + h - r, r, 0 * math.pi, .5 * math.pi)
    cr.arc(x + r, y + h - r, r, .5 * math.pi, math.pi)
    cr.close_path()


class TerminalIcon(gtk.Widget):

    __gtype_name__ = 'TerminalIcon'

    def __init__(self, color=(.5, 0, 0)):

        gtk.Widget.__init__(self)

        self.color = color


    def do_realize(self):

        self.set_flags(self.flags() | gtk.REALIZED | gtk.NO_WINDOW)
        self.window = self.get_parent_window()
        self.style.attach(self.window)


    def do_size_request(self, requisition):

        width, height = 3, 16
        requisition.width = width
        requisition.height = height


    def do_size_allocate(self, allocation):
        #self.allocation = allocation
        
        self.allocation = gtk.gdk.Rectangle(allocation.x, allocation.y, 3, allocation.height)


    def do_expose_event(self, event):
        self._draw()


    def draw(self):

        if self.window:
            self.window.invalidate_rect(self.allocation, True)


    def _draw(self):

        width = self.allocation.width
        height = self.allocation.height

        ctx = self.window.cairo_create()
        ctx.set_operator(cairo.OPERATOR_OVER)

        ctx.translate(self.allocation.x, self.allocation.y)
        ctx.set_line_width(1)
        ctx.set_source_rgb(*self.color)

        rounded_rectangle(ctx, 0, 0, width, height, 2)
        ctx.fill()


if __name__ == '__main__':
    win = gtk.Window()
    t = TerminalIcon()
    win.add(t)
    win.show_all()
    gtk.main()
