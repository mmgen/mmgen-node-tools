#!/usr/bin/env python3
"""
test.unit_tests_d.nt_BlocksInfo:
  BlocksInfo unit test for the MMGen Node Tools suite
"""

from mmgen.common import *
from mmgen.exception import *
from mmgen.node_tools.BlocksInfo import BlocksInfo

tip = 50000
vecs = (
	#                  First     Last FromTip nBlocks Step    First      Last    BlockList
	( (),              (),                                    (tip,      tip,    None) ),
	( (199,2,37),      (),                                    (None,     None,   [199,2,37]) ),
	( '0',             (0,        0,      None, None, None),  (0,        0,      None) ),
	( '0-0',           (0,        0,      None, None, None),  (0,        0,      None) ),
	(f'-{tip}',        (0,        0,      tip,  None, None),  (0,        0,      None) ),
	( '0-10',          (0,        10,     None, None, None),  (0,        10,     None) ),
	( '0+10',          (0,        9,      None, 10,   None),  (0,        9,      None) ),
	( '0+10+2',        (0,        9,      None, 10,   2   ),  (0,        9,      [0,2,4,6,8]) ),

	( '1',             (1,        1,      None, None, None),  (1,        1,      None) ),
	( '1-1',           (1,        1,      None, None, None),  (1,        1,      None) ),
	( '1-10',          (1,        10,     None, None, None),  (1,        10,     None) ),
	( '1+10',          (1,        10,     None, 10,   None),  (1,        10,     None) ),
	( '1+10+2',        (1,        10,     None, 10,   2   ),  (1,        10,     [1,3,5,7,9]) ),

	( '+1',            (tip,      tip,    None, 1,    None),  (tip,      tip,    None) ),
	( '+10',           (tip-9,    tip,    None, 10,   None),  (tip-9,    tip,    None) ),

	( '-1',            (tip-1,    tip-1,  1,    None, None),  (tip-1,    tip-1,  None) ),
	( '-1+1',          (tip-1,    tip-1,  1,    1,    None),  (tip-1,    tip-1,  None) ),
	( '-1+2',          (tip-1,    tip,    1,    2,    None),  (tip-1,    tip,    None) ),
	( '-10',           (tip-10,   tip-10, 10,   None, None),  (tip-10,   tip-10, None) ),
	( '-10+11',        (tip-10,   tip,    10,   11,   None),  (tip-10,   tip,    None) ),
	( '-10+11+2',      (tip-10,   tip,    10,   11,   2   ),  (tip-10,   tip,    list(range(tip-10,tip+1,2))) ),

	( 'cur',           (tip,      tip,    None, None, None),  (tip,      tip,    None) ),
	( 'cur-cur',       (tip,      tip,    None, None, None),  (tip,      tip,    None) ),
	( '0-cur',         (0,        tip,    None, None, None),  (0,        tip,    None) ),
	(f'{tip-1}-cur',   (tip-1,    tip,    None, None, None),  (tip-1,    tip,    None) ),
	( '0-cur+3000',    (0,        tip,    None, None, 3000 ), (0,        tip,    list(range(0,tip+1,3000))) ),
	( '+1440+144',     (tip-1439, tip,    None, 1440, 144 ),  (tip-1439, tip,    list(range(tip-1439,tip+1,144))) ),
	( '+144*10+12*12', (tip-1439, tip,    None, 1440, 144 ),  (tip-1439, tip,    list(range(tip-1439,tip+1,144))) ),
)

class dummyRPC:
	blockcount = tip

class dummyOpt:
	fields = None
	stats = None
	miner_info = None

class unit_tests:

	def rangespec(self,name,ut):

		b = BlocksInfo(0,dummyOpt(),dummyRPC())

		def test(spec,chk,foo):
			ret = b.parse_rangespec(spec)
			vmsg(f'{spec:13} => {BlocksInfo.range_data(*chk)}')
			assert ret == chk, f'{ret} != {chk}'

		for vec in vecs:
			if vec[1]:
				test(*vec)

		return True

	def parse_cmd_args(self,name,ut):

		def test(spec,foo,chk):
			b = BlocksInfo(spec if type(spec) == tuple else [spec],dummyOpt(),dummyRPC())
			ret = (b.first,b.last,b.block_list)
			vmsg('{:13} => {}'.format(repr(spec) if type(spec) == tuple else spec,chk))
			assert ret == chk, f'{ret} != {chk}'

		for vec in vecs:
			test(*vec)

		return True
