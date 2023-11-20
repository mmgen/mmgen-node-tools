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
mmgen_node_tools.PollDisplay: update and display RPC data; get input from user
"""

import sys,threading
from mmgen.util import msg
from mmgen.term import get_char

class PollDisplay:

	info = None
	input = None
	poll_secs = 1

	def __init__(self,cfg):
		self.cfg = cfg
		self.info_lock = threading.Lock() # self.info accessed by 2 threads
		self.display_kill_flag = threading.Event()

	def get_input(self):
		return get_char(immed_chars='q',prehold_protect=False,num_bytes=1)

	async def process_input(self,rpc):
		return True

	async def run(self,rpc):

		async def do_display():
			with self.info_lock:
				self.info = None
			self.input = None
			self.enable_display = True
			count = 1
			while True:
				with self.info_lock:
					if self.enable_display:
						self.info = await self.get_info(rpc)
						self.display(count)
				if self.display_kill_flag.wait(self.poll_secs):
					self.display_kill_flag.clear()
					return
				count += 1

		async def process_input():
			if self.input == None:
				sys.exit(1)
			elif self.input == 'q':
				msg('')
				sys.exit(0)
			elif self.info:
				if await self.process_input(rpc):
					return True
			else:
				return True

		def get_input():
			self.input = self.get_input()
			self.display_kill_flag.set()

		while True:
			threading.Thread(target=get_input,daemon=True).start()
			await do_display()
			if await process_input():
				break
