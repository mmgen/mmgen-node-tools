#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
mmgen_node_tools.PeerBlocks: List blocks in flight, disconnect stalling nodes
"""

import asyncio
from collections import namedtuple
from mmgen.util import msg,msg_r,is_int
from mmgen.term import get_term,get_terminal_size,get_char
from mmgen.ui import line_input
from .PollDisplay import PollDisplay

RED,RESET = ('\033[31m','\033[0m')
COLORS = ['\033[38;5;%s;1m' % c for c in list(range(247,256)) + [231]]
ERASE_ALL,CUR_HOME = ('\033[J','\033[H')
CUR_HIDE,CUR_SHOW = ('\033[?25l','\033[?25h')
term = None

class Display(PollDisplay):

	poll_secs = 2

	def __init__(self,cfg):

		super().__init__(cfg)

		global term,term_width
		if not term:
			term = get_term()
			term.init(noecho=True)
			term_width = self.cfg.columns or get_terminal_size().width
			msg_r(CUR_HOME+ERASE_ALL+CUR_HOME)

	async def get_info(self,rpc):
		return await rpc.call('getpeerinfo')

	def display(self,count):
		msg_r(
			CUR_HOME
			+ (ERASE_ALL if count == 1 else '')
			+ 'CONNECTED PEERS ({a}) {b} - poll {c}'.format(
				a = len(self.info),
				b = self.desc,
				c = count ).ljust(term_width)[:term_width]
			+ '\n'
			+ ('\n'.join(self.gen_display()) + '\n' if self.info else '')
			+ ERASE_ALL
			+ f"Type a peer number to disconnect, 'q' to quit, or any other key for {self.other_desc} display:"
			+ '\b' )

	async def disconnect_node(self,rpc,addr):
		return await rpc.call('disconnectnode',addr)

	def get_input(self):
		s = get_char(immed_chars='q0123456789',prehold_protect=False,num_bytes=1)
		if not is_int(s):
			return s
		with self.info_lock:
			msg('')
			term.reset()
			# readline required for correct operation here; without it, user must re-type first digit
			ret = line_input( self.cfg, 'peer number> ', insert_txt=s, hold_protect=False )
			term.init(noecho=True)
			self.enable_display = False # prevent display from updating before process_input()
			return ret

	async def process_input(self,rpc):

		ids = tuple(str(i['id']) for i in self.info)
		ret = False
		msg_r(CUR_HIDE)

		if self.input in ids:
			from mmgen.exception import RPCFailure
			addr = self.info[ids.index(self.input)]['addr']
			try:
				await self.disconnect_node(rpc,addr)
			except RPCFailure:
				msg_r(f'Unable to disconnect peer {self.input} ({addr})')
			else:
				msg_r(f'Disconnecting peer {self.input} ({addr})')
			await asyncio.sleep(1)
		elif self.input and is_int(self.input[0]):
			msg_r(f'{self.input}: invalid peer number ')
			await asyncio.sleep(0.5)
		else:
			ret = True

		msg_r(CUR_SHOW)
		return ret

class BlocksDisplay(Display):

	desc = 'Blocks in Flight'
	other_desc = 'address'

	def gen_display(self):

		pd = namedtuple('peer_data',['id','blks_data','blks_width'])
		bd = namedtuple('block_datum',['num','disp'])

		def gen_block_data():
			global min_height
			min_height = None
			for d in self.info:
				if d.get('inflight'):
					blocks = d['inflight']
					min_height = min(blocks) if not min_height else min(min_height,min(blocks))
					line = ' '.join(map(str,blocks))[:blks_field_width]
					blocks_disp = line.split()
					yield pd(
						d['id'],
						[bd(blocks[i],blocks_disp[i]) for i in range(len(blocks_disp))],
						len(line) )
				else:
					yield pd(d['id'],[],0)

		def gen_line(peer_data):
			for blk in peer_data.blks_data:
				yield (RED if blk.num == min_height else COLORS[blk.num % 10]) + blk.disp + RESET

		id_width = max(2, max(len(str(i['id'])) for i in self.info))
		blks_field_width = term_width - 2 - id_width
		fs = '{:>%s}: {}' % id_width

		# we must iterate through all data to get 'min_height' before calling gen_line():
		for peer_data in tuple(gen_block_data()):
			yield fs.format(
				peer_data.id,
				' '.join(gen_line(peer_data)) + ' ' * (blks_field_width - peer_data.blks_width) )

class PeersDisplay(Display):

	desc = 'Address Menu'
	other_desc = 'blocks'

	def gen_display(self):
		id_width = max(2, max(len(str(i['id'])) for i in self.info))
		addr_width = max(len(str(i['addr'])) for i in self.info)
		for d in self.info:
			yield '{a:>{A}}: {b:{B}} {c}'.format(
				a = d['id'],
				A = id_width,
				b = d['addr'],
				B = addr_width,
				c = d['subver']
			).ljust(term_width)[:term_width]
