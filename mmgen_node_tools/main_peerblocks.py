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

import asyncio
from collections import namedtuple
from mmgen.common import *

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

def format_peer_info(peerinfo):

	pd = namedtuple('peer_data',['id','blocks_data','screen_width'])

	def gen_peers(peerinfo):
		global min_height
		min_height = None
		for d in peerinfo:
			if 'inflight' in d and d['inflight']:
				blocks = d['inflight']
				if not min_height or min_height > blocks[0]:
					min_height = blocks[0]
				line = ' '.join(map(str,blocks))[:term_width - 2 - id_width]
				blocks_disp = line.split()
				yield pd(
					d['id'],
					[(blocks[i],blocks_disp[i]) for i in range(len(blocks_disp))],
					len(line) )
			else:
				yield pd( d['id'], [], 0 )

	def gen_line(peer):
		if peer.blocks_data:
			if peer.blocks_data[0][0] == min_height:
				yield RED + peer.blocks_data[0][1] + RESET
				peer.blocks_data.pop(0)
			for blk,blk_disp in peer.blocks_data:
				yield COLORS[blk % 10] + blk_disp + RESET

	id_width = max(2,max(len(str(i['id'])) for i in peerinfo))

	for peer in tuple(gen_peers(peerinfo)):
		line = '{:>{iw}}: {}'.format(
			peer.id,
			' '.join(gen_line(peer)),
			iw = id_width )
		yield line + ' ' * (term_width - 2 - id_width - peer.screen_width)

def test_format():
	import json
	info = json.loads(open('test_data/peerinfo.json').read())
	print('\n'.join(format_peer_info(info)) + '\n')
	sys.exit(0)

async def inflight_display(rpc):

	count = 1
	while True:
		info = await rpc.call('getpeerinfo')
		msg_r(
			CUR_HOME
			+ f'ACTIVE PEERS ({len(info)}) Blocks in Flight - poll {count}    \n'
			+ ('\n'.join(format_peer_info(info)) + '\n' if info else '')
			+ ERASE_ALL + 'Hit ENTER for disconnect menu: ' )
		await asyncio.sleep(2)
		count += 1

async def do_inflight(rpc):
	task = asyncio.ensure_future(inflight_display(rpc)) # Python 3.7+: create_task()
	from select import select

	while True:
		key = select([sys.stdin], [], [], 0.1)[0]
		if key:
			sys.stdin.read(1)
			task.cancel()
			break
		await asyncio.sleep(0.1)

	try:
		await task
	except asyncio.CancelledError:
		pass

async def do_disconnect_menu(rpc):

	while True:
		peerinfo = await rpc.call('getpeerinfo')
		ids = [str(d['id']) for d in peerinfo]

		msg(f'{CUR_HOME}ACTIVE PEERS ({len(peerinfo)}) Disconnect Menu' + ' '*16)

		def gen_peerinfo():
			for d in peerinfo:
				line = f"{d['id']:>{id_width}}: {d['addr']:30} {d['subver']}"
				yield line + ' ' * (term_width - len(line))

		if peerinfo:
			id_width = max(2,max(len(str(i['id'])) for i in peerinfo))
			msg('\n'.join(gen_peerinfo()))

		msg_r(ERASE_ALL)
		reply = input("Type peer number to disconnect, ENTER to quit menu, 'u' to update peer list: ")

		if reply == '':
			return
		elif reply == 'u':
			msg(f'Updating peer list')
			await asyncio.sleep(0.5)
		elif reply in ids:
			addr = peerinfo[ids.index(reply)]['addr']
			msg(f'Disconnecting peer {reply} ({addr})')
			try:
				await rpc.call('disconnectnode',addr)
			except RPCFailure:
				msg(f'Unable to disconnect peer {addr}')
			await asyncio.sleep(1.5)
		else:
			msg(f'{reply!r}: invalid peer number')
			await asyncio.sleep(0.5)

async def main():

	msg_r(CUR_HOME+ERASE_ALL)

	from mmgen.protocol import init_proto_from_opts
	proto = init_proto_from_opts()

	from mmgen.rpc import rpc_init
	rpc = await rpc_init(proto)

	while True:
		await do_inflight(rpc)
		await do_disconnect_menu(rpc)

opts.init(opts_data)

from mmgen.term import get_terminal_size
term_width = get_terminal_size()[0]

RED,RESET = ('\033[31m','\033[0m')
COLORS = ['\033[38;5;%s;1m' % c for c in (247,248,249,250,251,252,253,254,255,231)]
ERASE_ALL,ERASE_LINE,CUR_HOME,CUR_HIDE,CUR_SHOW = (
	'\033[J','\033[K','\033[H','\033[?25l','\033[?25h')

try:
	run_session(main())
except:
	from subprocess import run
	run(['stty','sane'])
	msg('')
