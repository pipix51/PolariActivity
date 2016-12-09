#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2016, Cristian García <cristian99garcia@gmail.com>
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

from gettext import gettext as _

from consts import CONNECTION_ERROR, NICKNAME_USED, SUGAR, CHAT_FONT, Color, \
                   Key

from utils import get_urls
from nicknames_listbox import NicknamesListBox

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango
from gi.repository import GObject


class ChatBox(Gtk.VBox):

    __gsignals__ = {
        "stop-widget": (GObject.SIGNAL_RUN_FIRST, None, [str]),  # Channel
        "send-message": (GObject.SIGNAL_RUN_FIRST, None, [str, str]),  # Channel, message
        "command": (GObject.SIGNAL_RUN_FIRST, None, [str, str, str]),   # Channel, command, parameters
        "change-nickname": (GObject.SIGNAL_RUN_FIRST, None, [str]),  # New nickname
        "query": (GObject.SIGNAL_RUN_FIRST, None, [str]),  # Nickname
    }

    def __init__(self):
        Gtk.VBox.__init__(self)

        self.nick = None
        self.current_channel = None
        self.channels = [ ]
        self.last_nick = { }  # channel: str
        self.nicks = { }  # channel: list
        self.views = { }  # channel: GtkTextView
        self.buffers = { }  # channel: GtkTextBuffer
        self.nicks_listboxs = { }  # channel: NicknamesListBox

        self.set_size_request(400, -1)
        self.set_margin_left(10)
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)

        self.connect("key-press-event", self.__key_press_cb)

        self.hbox = Gtk.HBox()
        self.pack_start(self.hbox, True, True, 5)

        self.scroll = Gtk.ScrolledWindow()
        self.hbox.pack_start(self.scroll, True, True, 0)

        self.nicks_box = Gtk.VBox()
        self.hbox.pack_end(self.nicks_box, False, False, 0)

        hbox = Gtk.HBox()
        hbox.set_margin_left(10)
        hbox.set_margin_right(10)
        self.pack_end(hbox, False, False, 5)

        self.nicker = Gtk.Entry()
        self.nicker.set_size_request(100, -1)
        self.nicker.set_max_length(16)
        self.nicker.set_sensitive(False)
        self.nicker.connect("activate", self._change_nickname)
        hbox.pack_start(self.nicker, False, False, 1)

        self.entry = Gtk.Entry()
        self.entry.set_sensitive(False)
        self.entry.set_placeholder_text(_("Speak"))
        self.entry.connect("activate", self.send_message)
        hbox.pack_start(self.entry, True, True, 0)

        self.set_entries_theme()

    def __key_press_cb(self, widget, event):
        if event.keyval == Key.TAB and self.entry.has_focus():
            pos = self.entry.props.cursor_position
            text = self.entry.get_text()[:pos].split(" ")[-1]

            for nick in self.nicks[self.current_channel]:
                if nick.startswith(text):
                    # TODO: Autocomplete
                    pass

            return True

        return False

    def _change_nickname(self, widget):
        self.emit("change-nickname", self.nicker.get_text())
        self.nicker.set_text("")

    def add_channel(self, channel):
        if channel not in self.channels:
            self.channels.append(channel)
            self.views[channel] = self.make_textview_for_channel(channel)
            self.buffers[channel] = self.views[channel].get_buffer()
            self.last_nick[channel] = None
            self.nicks[channel] = []
            self.nicks_listboxs[channel] = NicknamesListBox()
            self.nicks_listboxs[channel].connect("query", self._query)

            self.create_tags(channel)

    def remove_channel(self, channel):
        if channel in self.channels:
            idx = self.channels.index(channel)
            self.channels.remove(channel)
            self.views.pop(channel)
            self.buffers.pop(channel)
            self.nicks.pop(channel)
            self.nicks_listboxs.pop(channel)

    def switch_channel(self, channel):
        if channel == self.current_channel:
            return

        if self.scroll.get_child() != None:
            self.scroll.remove(self.scroll.get_child())

        if self.nicks_box.get_children() != []:
            self.nicks_box.remove(self.nicks_box.get_children()[0])

        self.current_channel = channel
        self.scroll.add(self.views[self.current_channel])

        if channel.startswith("#"):  # Is a channel, not a nickname
            self.nicks_box.pack_start(self.nicks_listboxs[channel], True, True, 0)

        self.show_all()

    def make_textview_for_channel(self, channel):
        view = Gtk.TextView()
        view.set_editable(False)
        view.set_cursor_visible(False)
        view.set_wrap_mode(Gtk.WrapMode.WORD)
        view.modify_font(Pango.FontDescription(CHAT_FONT))

        return view

    def set_nickname(self, nick):
        self.nick = nick
        self.nicker.set_placeholder_text(self.nick)

    def send_message(self, widget):
        message = self.entry.get_text()

        if not message.startswith("/"):
            self.emit("send-message", self.current_channel, message)
            self.add_message_to_view(self.current_channel, self.nick, message, force=True)

        else:
            command = message.split(" ")[0]
            parameters = message[len(command):].strip()
            self.emit("command", self.current_channel, command, parameters)

        self.entry.set_text("")

    def add_text_with_tag(self, channel, text, tag):
        end = self.buffers[channel].get_end_iter()
        self.buffers[channel].insert_with_tags_by_name(end, text, tag)

    def add_system_message(self, channel, message):
        self.last_nick[channel] = "<SYSTEM>"
        self.add_text_with_tag(channel, message + "\n", "sys-msg")

    def add_message_to_view(self, channel, user, message, force=False):
        if user != self.nick or force:
            if user == self.last_nick[channel]:
                user = " "  * (len(user) + 2)

            else:
                self.last_nick[channel] = user
                user += ": "

        self.add_text_with_tag(channel, user, "nick")

        end = self.buffers[channel].get_end_iter()
        offset = end.get_offset()

        self.add_text_with_tag(channel, message + "\n", "message")
        end = self.buffers[channel].get_iter_at_offset(offset)

        if self.last_nick[channel] != self.nick:
            self.search_and_mark(channel, self.nick, end, "mention")

        offset = end.get_offset()

        for url in get_urls(message):
            end = self.buffers[channel].get_iter_at_offset(offset)
            self.search_and_mark(channel, url, end, "url")

    def search_and_mark(self, channel, text, start, tag):
        end = self.buffers[channel].get_end_iter()
        match = start.forward_search(text, 0, end)

        if match != None:
            match_start, match_end = match
            self.buffers[channel].apply_tag_by_name(tag, match_start, match_end)
            self.search_and_mark(channel, text, match_end, tag)

    def message_recived(self, channel, nick, message):
        self.add_message_to_view(channel, nick, message)

    def set_entries_theme(self):
        theme_entry = "GtkEntry {border-radius:0px 30px 30px 0px;}"
        css_provider_entry = Gtk.CssProvider()
        css_provider_entry.load_from_data(theme_entry)

        style_context = self.entry.get_style_context()
        style_context.add_provider(css_provider_entry,
                                   Gtk.STYLE_PROVIDER_PRIORITY_USER)

        theme_nicker = "GtkEntry {border-radius:30px 0px 0px 30px;}"
        css_provider_nicker = Gtk.CssProvider()
        css_provider_nicker.load_from_data(theme_nicker)

        style_context = self.nicker.get_style_context()
        style_context.add_provider(css_provider_nicker,
                                   Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def create_tags(self, channel):
        buffer = self.buffers[channel]
        buffer.create_tag("nick", foreground=Color.NICK_TAG)
        buffer.create_tag("mention", foreground=Color.MENTION_TAG)
        buffer.create_tag("sys-msg", foreground=Color.SYS_MESSAGE_TAG)
        buffer.create_tag("url", underline=Pango.Underline.SINGLE, foreground=Color.URL_TAG)

        if not SUGAR:
            buffer.create_tag("message", background=Color.MESSAGE_TAG)

        else:
            buffer.create_tag("message")

    def get_entry(self):
        return self.entry

    def set_nicknames(self, channel, nicknames):
        if channel in self.channels:  # twisted factory add a hash to nicks too
            self.nicks[channel] = nicknames
            self.nicks_listboxs[channel].set_list(nicknames)

    def add_nickname(self, channel, nickname):
        self.nicks[channel].append(nickname)
        self.nicks_listboxs[channel].add_nickname(nickname)

    def remove_nickname(self, channel, nickname):
        self.nicks[channel].remove(nickname)
        self.nicks_listboxs[channel].remove_nickname(nickname)

    def remove_nickname_from_all_channels(self, nickname):
        for channel in self.nicks.keys():
            if nickname in self.nicks[channel]:
                self.remove_nickname(channel, nickname)

    def _query(self, widget, nickname):
        self.emit("query", nickname)
