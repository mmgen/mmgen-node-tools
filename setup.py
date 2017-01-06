#!/usr/bin/env python
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

import os
from distutils.core import setup
from distutils.command.install_data import install_data
from mmgen.globalvars import g

class my_install_data(install_data):
	def run(self):
		sdir = os.path.join('data_files','audio')
		for f in [e for e in os.listdir(sdir) if e[-4:] == '.wav']:
			os.chmod(os.path.join(sdir,f),0644)
		install_data.run(self)

setup(
		name         = 'mmgen-node-tools',
		description  = 'Optional tools for the MMGen wallet system',
		version      = g.version,
		author       = g.author,
		author_email = g.email,
		url          = g.proj_url,
		license      = 'GNU GPL v3',
		platforms    = 'Linux, MS Windows, Raspberry Pi',
		keywords     = g.keywords,
		packages     = ['mmgen.node_tools'],
		scripts      = ['btc-ticker','mmnode-play-sound'],
		data_files = [('share/mmgen/node_tools/audio', [
				'data_files/audio/ringtone.wav',     # source files must have 0644 mode
				'data_files/audio/Positive.wav',
				'data_files/audio/Rhodes.wav',
				'data_files/audio/Counterpoint.wav'
				])
		],
		cmdclass  = { 'install_data': my_install_data },
	)
