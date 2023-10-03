#!/usr/bin/env python3
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
mmgen_node_tools.Sound: audio-related functions for MMGen node tools
"""

import sys,os,time

from mmgen.util import die

from mmgen_node_tools.Util import do_system

_alsa_config_file = '/tmp/alsa-config-' + os.path.basename(sys.argv[0])
_dvols = { 'Master': 78, 'Speaker': 78, 'Headphone': 15, 'PCM': 190 }

def timespec2secs(ts):
	import re
	mul = { 's': 1, 'm': 60, 'h': 60*60, 'd': 60*60*24 }
	pat = r'^([0-9]+)([smhd]*)$'
	m = re.match(pat,ts)
	if m == None:
		die(2,"'%s': invalid time specifier" % ts)
	a,b = m.groups()
	return int(a) * (mul[b] if b else 1)

def parse_repeat_spec(rs):
	return [(timespec2secs(i),timespec2secs(j))
				for i,j in [a.split(':') for a in rs.split(',')]]

def init_sound():
	def _restore_sound():
#	msg('Restoring sound volume')
		do_system('sudo alsactl restore -f ' + _alsa_config_file)
		os.unlink(_alsa_config_file)
	import atexit
	atexit.register(_restore_sound)
	do_system('sudo alsactl store -f ' + _alsa_config_file)

def play_sound(fn,vol,repeat_spec='',remote_host='',kill_flg=None,testing=False):
	if not remote_host:
		do_system('sudo alsactl store -f ' + _alsa_config_file)
		for k in 'Master','Speaker','Headphone':
			do_system(('sudo amixer -q set %s on' % k),testing)
#		do_system('amixer -q set Headphone off')

		vols = dict([(k,int(_dvols[k] * float(vol) / 100)) for k in _dvols])
		for k in vols:
			do_system('sudo amixer -q set %s %s' % (k,vols[k]),testing)

	fn = os.path.expanduser(fn)
	cmd = (
		'aplay -q %s' % fn,
		'ssh %s mmnode-play-sound -v%d %s' % (remote_host,vol,fn)
	)[bool(remote_host)]

	if repeat_spec and kill_flg:
		for interval,duration in parse_repeat_spec(repeat_spec):
			start = time.time()
			while time.time() < start + duration:
				do_system(cmd,testing)
				if kill_flg.wait(interval):
					if not remote_host:
						do_system('sudo alsactl restore -f ' + _alsa_config_file)
					return
	else: # Play once
		do_system(cmd,testing)
		if not remote_host:
			do_system('sudo alsactl restore -f ' + _alsa_config_file)
