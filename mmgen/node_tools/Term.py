#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2016 Philemon <mmgen-py@yandex.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
node_tools.Term: terminal routines for MMGen node tools
"""

import sys,os,termios

def get_keypress(prompt="",esc_sequences=False):

	import time,tty,select
	sys.stderr.write(prompt)

	fd = sys.stdin.fileno()
#	old = termios.tcgetattr(fd) # see below
	tty.setcbreak(fd) # must do this, even if it was set at program launch

	def osread_chk(n):
		while True:
			try:
				return os.read(fd,n)
			except:
				time.sleep(0.1)

	# Must use os.read() for unbuffered read, otherwise select() will never return true
	s = osread_chk(1)
	if esc_sequences:
		if s == '\x1b':
			if select.select([sys.stdin],[],[],0)[0]:
				s += osread_chk(2)

# Leave the term in cbreak mode, restore at exit
#	termios.tcsetattr(fd, termios.TCSADRAIN, old)
	return s
