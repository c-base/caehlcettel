import os
import tempfile
import time

import imgkit
import jinja2

from brother_ql.conversion import convert
from brother_ql.backends.helpers import send
from brother_ql.raster import BrotherQLRaster


TEMPLATE_FILE = os.path.join(os.path.dirname(__file__), 'templates/zettel.html.j2')

WKHTML_OPTIONS = options = {
    'format': 'png',
    #'viewport-size': '732x366',
    'width': '732',
    # , 366, 
    #'disable-smart-width': '',
    'encoding': "UTF-8",
    'custom-header' : [
        ('Accept-Encoding', 'gzip')
    ],
    # 'no-outline': None
}


def make_zettel(context, tmpdir, do_open=False):
    with open(TEMPLATE_FILE, 'r') as tpl_fh:
        template = jinja2.Template(tpl_fh.read())

    html = template.render(**context)
    
    tmpfile = str(os.path.join(tmpdir, 'out.png'))
    imgkit.from_string(html, tmpfile, options=WKHTML_OPTIONS)
    if do_open is True:
        os.system('open %s' % tmpfile)
        time.sleep(1.0)

    return tmpfile


def print_zettel(context, tmpdir, backend, model, printer):
    tmp_filename = make_zettel(context, tmpdir)
    qlr = BrotherQLRaster(model)
    qlr.exception_on_warning = True
    kwargs = {}
    kwargs['label'] = '62'
    kwargs['cut'] = True
    kwargs['dither'] = True
    kwargs['images'] = [tmp_filename, ]
    instructions = convert(qlr=qlr, **kwargs)
    send(instructions=instructions, printer_identifier=printer, backend_identifier=backend, blocking=True)