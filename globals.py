#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014, Cristian García <cristian99garcia@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import re
from gettext import gettext as _

from gi.repository import Gdk


NICKNAME_USED = _(' is already in use.')
LOST_CONNECTION = _('Lost conection with the server...')
CONNECTION_ERROR = _('Error connecting to the server...closing the socket.')
ALERT_TITLE = _('You already have a session on this host with this channel and with this nickname.')
ALERT_MSG = _('Automatically selected session you tried to create.')

COLOR_BLUE = Gdk.color_parse('#4A90D9')
COLOR_WHITE = Gdk.color_parse('#FFFFFF')

def get_urls(text):
    return re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
