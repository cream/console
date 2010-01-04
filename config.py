from cream.config import Configuration, fields

import cream.i18n

try:
    cream.i18n.install('config')
except:
    _ = lambda x: x

class Configuration(Configuration):
    background_color = fields.ColorField(_("Background color"), default='#000000')
    foreground_color = fields.ColorField(_("Foreground color"), default='#FFFFFF')
    font = fields.FontField(_("Font"), default='Monospace 10')
    lines = fields.IntegerField(_("Lines to scroll back"), default=500, max=float('inf'))
