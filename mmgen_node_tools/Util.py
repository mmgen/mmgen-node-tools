#!/usr/bin/env python3
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
"""
mmgen_node_tools.Util: utility functions for MMGen node tools
"""

import time
from mmgen.util import suf

def get_hms(t=None,utc=False,no_secs=False):
	secs = t or time.time()
	ret = (time.localtime,time.gmtime)[utc](secs)
	fs,n = (('{:02}:{:02}:{:02}',6),('{:02}:{:02}',5))[no_secs]
	return fs.format(*ret[3:n])

def get_day_hms(t=None,utc=False):
	secs = t or time.time()
	ret = (time.localtime,time.gmtime)[utc](secs)
	return '{:04}-{:02}-{:02} {:02}:{:02}:{:02}'.format(*ret[0:6])

def do_system(cmd,testing=False,shell=False):
	if testing:
		from mmgen.util import msg
		msg("Would execute: '%s'" % cmd)
		return True
	else:
		import subprocess
		return subprocess.call((cmd if shell else cmd.split()),shell,stderr=subprocess.PIPE)

def get_url(url,gzip_ok=False,proxy=None,timeout=60,verbose=False,debug=False):
	if debug:
		print('get_url():')
		print('  url', url)
		print('  gzip_ok:',gzip_ok, 'proxy:',proxy, 'timeout:',timeout, 'verbose:',verbose)
	import pycurl,io
	c = pycurl.Curl()
	c_out = io.StringIO()
	c.setopt(pycurl.WRITEFUNCTION,c_out.write)
	c.setopt(pycurl.TIMEOUT,timeout)
	c.setopt(pycurl.FOLLOWLOCATION,True)
	c.setopt(pycurl.COOKIEFILE,'')
	c.setopt(pycurl.VERBOSE,verbose)
	if gzip_ok:
		c.setopt(pycurl.USERAGENT,'Lynx/2.8.9dev.8 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/3.4.9')
		c.setopt(pycurl.HTTPHEADER, [
	'Accept: text/html, text/plain, text/sgml, text/css, application/xhtml+xml, */*;q=0.01',
	'Accept-Encoding: gzip',
	'Accept-Language: en']
		)
	if proxy:
		c.setopt(pycurl.PROXY,proxy)
	c.setopt(pycurl.URL,url)
	c.perform()
	text = c_out.getvalue()
	if text[:2] == '\x1f\x8b': # gzip magic number
		c_out.seek(0,0)
		import gzip
		with gzip.GzipFile(fileobj=c_out) as f:
			text = f.read()
	c_out.close()
	c.close()
	return text

# big_digits = """
#  ███    █    ███   ███     █  █████  ███  █████  ███   ███
# █   █  ██   █   █     █   ██  █     █         █ █   █ █   █
# █   █   █     ██    ██   █ █  ████  ████     █   ███   ████
# █   █   █    █        █ ████      █ █   █   █   █   █     █
#  ███    █   █████  ███     █  ████   ███   █     ███   ███   ██
#
# """

big_digits = {
	'w': 7, 'h': 6, 'n': 10, 'nums': """
 ████     █    ████   ████      █  █████   ████  ██████  ████   ████
█    █   ██   █    █      █    ██  █      █           █ █    █ █    █
█    █    █       █    ███    █ █  ████   █████      █   ████   █████
█    █    █     ██        █  █  █      █  █    █    █   █    █      █
█    █    █    █          █ █████      █  █    █   █    █    █      █
 ████     █   ██████  ████      █  ████    ████   █      ████   ████
""",
	'pw': 5, 'pn': 2, 'punc': """


      ██

      ██
 ██
"""
}

_bnums_c,_bpunc_c = [[l.strip('\n') + ' ' * (big_digits[m]*big_digits['n'])
	for l in big_digits[k][1:].split('\n')]
		for k,m in (('nums','w'),('punc','pw'))]

_bnums_n,_bpunc_n = [[[l[0+(j*w):w+(j*w)] for l in i]
					for j in range(big_digits[n])] for n,w,i in
						(('n',big_digits['w'],_bnums_c),('pn',big_digits['pw'],_bpunc_c))]

def display_big_digits(s,pre='',suf=''):
	s = [int((d,10,11)[(d in '.:')+(d==':')]) for d in s]
	return pre + ('\n'+pre).join(
		[''.join([(_bnums_n+_bpunc_n)[d][l] for d in s]) + suf for l in range(big_digits['h'])]
	)

if __name__ == '__main__':
	num = '2345.17'
	print(display_big_digits(num,pre='+ ',suf='  +'))
