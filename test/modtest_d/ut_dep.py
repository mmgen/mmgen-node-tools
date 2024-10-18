#!/usr/bin/env python3

"""
test.unit_tests_d.ut_dep: dependency unit tests for the MMGen Node Tools

  Test whether dependencies are installed and functional.
  No data verification is performed.
"""

from ..include.common import vmsg,imsg
from mmgen.color import yellow

class unit_tests:

	def yahooquery(self,name,ut):
		try:
			from yahooquery import Ticker
			return True
		except ImportError:
			imsg(yellow('Unable to import Ticker from yahooquery'))
			return False
