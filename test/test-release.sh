#!/bin/bash

export MMGEN_TEST_SUITE=1
export PYTHONPATH=.

orig_pwd=$(pwd)

RED="\e[31;1m" GREEN="\e[32;1m" YELLOW="\e[33;1m" BLUE="\e[34;1m" MAGENTA="\e[35;1m" CYAN="\e[36;1m"
RESET="\e[0m"

set -o errtrace
set -o functrace

trap 'echo -e "${GREEN}Exiting at user request$RESET"; exit' INT
trap 'echo -e "${RED}Node tools test suite exited with error$RESET"' ERR
umask 0022

unit_tests_py='test/unit_tests.py --names --quiet'

PROGNAME=$(basename $0)
while getopts hv OPT
do
	case "$OPT" in
	h)  printf "  %-16s The MMGen node tools test suite\n" "${PROGNAME}:"
		echo   "  USAGE:           $PROGNAME [options] [tests or test group]"
		echo   "  OPTIONS: '-h'  Print this help message"
		echo   "           '-v'  Run commands with '--verbose' switch"
		exit ;;
	v)  VERBOSE=1
		unit_tests_py="${unit_tests_py/--quiet/--verbose}" ;;
	*)  exit ;;
	esac
done

shift $((OPTIND-1))

nt_repo='../mmgen-node-tools'
mm_repo='../mmgen'

die()   { echo -e $YELLOW$1$RESET; false; }
gecho() { echo -e $GREEN$1$RESET; }
pecho() { echo -e $MAGENTA$1$RESET; }
becho() { echo -e $BLUE$1$RESET; }

check_mmgen_repo() {
	( cd $mm_repo; python3 ./setup.py --url | grep -iq 'mmgen' )
}

create_links() {
	( cd 'mmgen'; [ -L 'node_tools' ] || ln -s "../$nt_repo/mmgen/node_tools" )
	( cd $mm_repo && [ -L 'mmgen_node_tools' ] || ln -s "$orig_pwd/mmgen_node_tools" )
	(
		cd 'test/unit_tests_d'
		for fn in ../../$nt_repo/test/unit_tests_d/nt_*.py; do
			[ -L "$(basename $fn)" ] || ln -s "$fn"
		done
	)
}

run_unit_tests() {
	pecho 'Running unit tests:'
	$unit_tests_py --node-tools
	pecho 'Completed unit tests'
}

# start execution

set -e

becho 'Starting node tools test suite (WIP)'

check_mmgen_repo || die "No MMGen repository found at $mm_repo!"

cd $mm_repo

create_links

run_unit_tests

becho 'Node tools test suite completed successfully'
