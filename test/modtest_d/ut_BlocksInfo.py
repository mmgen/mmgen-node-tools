#!/usr/bin/env python3
"""
test.unit_tests_d.nt_BlocksInfo: BlocksInfo unit test for the MMGen Node Tools suite
"""

from mmgen_node_tools.BlocksInfo import BlocksInfo

from ..include.common import vmsg

tip = 50000
range_vecs = (
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

	( 'cUr',           (tip,      tip,    None, None, None),  (tip,      tip,    None) ),
	( 'cur-cUR',       (tip,      tip,    None, None, None),  (tip,      tip,    None) ),
	( '0-cur',         (0,        tip,    None, None, None),  (0,        tip,    None) ),
	(f'{tip-1}-cur',   (tip-1,    tip,    None, None, None),  (tip-1,    tip,    None) ),
	( '0-cur+3000',    (0,        tip,    None, None, 3000 ), (0,        tip,    list(range(0,tip+1,3000))) ),
	( '+1440+144',     (tip-1439, tip,    None, 1440, 144 ),  (tip-1439, tip,    list(range(tip-1439,tip+1,144))) ),
	( '+144*10+12*12', (tip-1439, tip,    None, 1440, 144 ),  (tip-1439, tip,    list(range(tip-1439,tip+1,144))) ),
)

full_set = ['aa','bbb','ccc_P2','ddddd','eeeeee','ffffffff','gg']
dfl_set  = ['aa','ddddd','ffffffff']
fields_vecs = (
	( 'Ccc_P2',                 ['ccc_P2'] ),
	( '+CCC_P2',                ['aa','ccc_P2','ddddd','ffffffff'] ),
	( '+Aa',                    dfl_set ),
	( '+ddDDD,FffffffF',        dfl_set ),
	( '+bBb',                   ['aa','bbb','ddddd','ffffffff'] ),
	( '-ddddd',                 ['aa','ffffffff'] ),
	( '-DDDDD,fFffffff',        ['aa'] ),
	( '-ffffffff,AA,DdDdD',     [] ),
	( '+aa,gG,ccC_P2',          ['aa','ccc_P2','ddddd','ffffffff','gg'] ),
	( '+BBB,gg-dDddD,fFffffff', ['aa','bbb','gg'] ),
	( '-dDddD,fFffffff+BBB,gg', ['aa','bbb','gg'] ),
	( 'aLL-Ccc_P2',             [e for e in full_set if e != 'ccc_P2'] ),
	( 'All-dDddd,aa',           [e for e in full_set if e not in ('aa','ddddd')] ),
)

class dummyRPC:
	blockcount = tip
	def info(self,arg):
		return True
	class proto:
		class coin_amt:
			satoshi = 0.00000001

class dummyCfg:
	fields = None
	stats = None
	miner_info = None
	header_info = None
	full_stats = None
	coin = 'BTC'

class unit_tests:

	def parse_field(self,name,ut):
		vmsg('{:28} => {}'.format('FULL SET:',full_set))
		vmsg('{:28} => {}'.format('DFL SET: ',dfl_set))
		b = BlocksInfo
		for opt,chk in fields_vecs:
			ret = b.parse_cslist(opt,full_set,dfl_set,'field')
			vmsg(f'{opt:28} => {ret}')
			assert ret == chk, f'{ret} != {chk}'
		return True

	def parse_rangespec(self,name,ut):

		b = BlocksInfo(dummyCfg(),None,dummyRPC())

		def test(spec,chk,foo):
			ret = b.parse_rangespec(spec)
			vmsg(f'{spec:13} => {BlocksInfo.range_data(*chk)}')
			assert ret == chk, f'{ret} != {chk}'

		for vec in range_vecs:
			if vec[1]:
				test(*vec)

		return True

	def parse_cmd_args(self,name,ut):

		def test(spec,foo,chk):
			b = BlocksInfo(
				dummyCfg(),
				spec if type(spec) == tuple else [spec],
				dummyRPC() )
			ret = (b.first,b.last,b.block_list)
			vmsg('{:13} => {}'.format(
				(repr(spec) if type(spec) == tuple else spec),
				chk ))
			assert ret == chk, f'{ret} != {chk}'

		for vec in range_vecs:
			test(*vec)

		return True
