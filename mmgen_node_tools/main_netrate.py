#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2021 The MMGen Project <mmgen@tuta.io>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

"""
mmnode-netrate: Bitcoin daemon network rate monitor
"""

import sys,time

from mmgen.cfg import Config
from mmgen.util import async_run

opts_data = {
	'text': {
		'desc': 'Bitcoin daemon network rate monitor',
		'usage':   '[opts]',
		'options': """
-h, --help      Print this help message
--, --longhelp  Print help message for long options (common options)
"""
	}
}

cfg = Config(opts_data=opts_data)

ERASE_LINE,CUR_UP = '\033[K','\033[1A'

async def main():

	from mmgen.rpc import rpc_init
	c = await rpc_init(cfg,ignore_wallet=True)

	async def get_data():
		d = await c.call('getnettotals')
		return [float(e) for e in (d['totalbytesrecv'],d['totalbytessent'],d['timemillis'])]

	rs,ss,ts = (None,None,None)
	while True:
		r,s,t = await get_data()

		if rs is not None:
			sys.stderr.write(
				'\rrcvd: {:9.2f} kB/s\nsent: {:9.2f} kB/s '.format(
					(r-rs)/(t-ts),
					(s-ss)/(t-ts) ))

		time.sleep(2)

		if rs is not None:
			sys.stderr.write('{}{}{}'.format(ERASE_LINE,CUR_UP,ERASE_LINE))

		rs,ss,ts = (r,s,t)

try:
	async_run(main())
except KeyboardInterrupt:
	sys.stderr.write('\n')
