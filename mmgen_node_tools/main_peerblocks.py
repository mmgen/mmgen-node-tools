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
mmnode-peerblocks: List blocks in flight, disconnect stalling nodes
"""

import mmgen.opts as opts
from mmgen.util import async_run

opts_data = {
	'text': {
		'desc': 'List blocks in flight, disconnect stalling nodes',
		'usage':   '[opts]',
		'options': """
-h, --help      Print this help message
--, --longhelp  Print help message for long options (common options)
"""
	}
}

async def main():

	cfg = opts.init(opts_data)

	from mmgen.rpc import rpc_init
	rpc = await rpc_init( cfg, cfg._proto )

	from .PeerBlocks import BlocksDisplay,PeersDisplay
	blocks = BlocksDisplay(cfg)
	peers = PeersDisplay(cfg)

	while True:
		await blocks.run(rpc)
		await peers.run(rpc)

async_run(main())
