#!/bin/bash
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-node-tools
#   https://gitlab.com/mmgen/mmgen-node-tools

# Testing status
#  mmnode-addrbal             OK
#  mmnode-blocks-info         -
#  mmnode-feeview             -
#  mmnode-halving-calculator  OK
#  mmnode-netrate             -
#  mmnode-peerblocks          -
#  mmnode-ticker              OK
#  mmnode-txfind              -

list_avail_tests() {
	echo   "AVAILABLE TESTS:"
	echo   "   unit     - unit tests"
	echo   "   btc_rt   - Bitcoin regtest"
	echo   "   bch_rt   - Bitcoin Cash Node (BCH) regtest"
	echo   "   ltc_rt   - Litecoin regtest"
	echo   "   scripts  - tests of scripts not requiring a coin daemon"
	echo   "   misc     - miscellaneous tests that don't fit in the above categories"
	echo
	echo   "AVAILABLE TEST GROUPS:"
	echo   "   default  - All tests minus the extra tests"
	echo   "   extra    - All tests minus the default tests"
	echo   "   noalt    - BTC-only tests"
	echo   "   quick    - Default tests minus btc_tn, bch, bch_rt, ltc and ltc_rt"
	echo   "   qskip    - The tests skipped in the 'quick' test group"
	echo
	echo   "By default, all tests are run"
}

init_groups() {
	dfl_tests='unit misc scripts btc_rt bch_rt ltc_rt'
	extra_tests=''
	noalt_tests='unit misc scripts btc_rt'
	quick_tests='unit misc scripts btc_rt'
	qskip_tests='bch_rt ltc_rt'
}

init_tests() {
	i_unit='Unit'
	s_unit="The following tests will test various low-level subsystems"
	t_unit="- $unit_tests_py"
	f_unit='Unit tests completed'

	i_misc='Misc'
	s_misc="The following tests will test miscellaneous script features"
	t_misc="- $test_py helpscreens"
	f_misc='Misc tests completed'

	i_scripts='No-daemon scripts'
	s_scripts="The following tests will test scripts not requiring a coin daemon"
	t_scripts="- $test_py scripts"
	f_scripts='No-daemon script tests completed'

	i_btc_rt='Bitcoin regtest'
	s_btc_rt="The following tests will test various scripts using regtest mode"
	t_btc_rt="- $test_py regtest"
	f_btc_rt='Regtest mode tests for BTC completed'

	i_bch_rt='BitcoinCashNode (BCH) regtest'
	s_bch_rt="The following tests will test various scripts using regtest mode"
	t_bch_rt="- $test_py --coin=bch regtest"
	f_bch_rt='Regtest mode tests for BCH completed'

	i_ltc_rt='Litecoin regtest'
	s_ltc_rt="The following tests will test various scripts using regtest mode"
	t_ltc_rt="- $test_py --coin=ltc regtest"
	f_ltc_rt='Regtest mode tests for LTC completed'
}
