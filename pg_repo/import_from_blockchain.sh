#!/bin/bash

# ------------------------
# Created on 11 June 2021
#
#  @author: thartman, dbb
#

##  Prerequisites:  src repo,  data dir,  postgres role;
##
## invoke this script as linux role  opdev
##  tpath/sw_op_energy/pg_repo$  bash import_from_blockchain.sh
## or from admin account as  opdev
##  tpath/sw_op_energy/pg_repo$  sudo -H -u opdev bash import_from_blockchain.sh
##
##-----------------------------------------------------------------------------

##  set VERBOSE flags, and exit on any error
##    add -x at runtime for additional debug output
set -uve

##-- get working dir
##    use the script current dir for db template file
PG_REPO=$(dirname $(readlink -f $0))   #;echo 'PG_REPO='${PG_REPO}
export PG_REPO


## look for command line options
VERBOSE='true'
SDEBUG='false'
while getopts 'd:v' flag; do
case "${flag}" in
  a) SDEBUG='true' ;;
  v) VERBOSE='true' ;;
  *) error "Unexpected option ${flag}" ;;
esac

echo 'VERBOSE='${VERBOSE}
echo 'SDEBUG='${SDEBUG}
exit

##========================================
##  GET copy of source_data tgz
##
export SRC_DDIR=/var/local/opdev/
SRC_DATAFILE=btcdata_1600585200.tgz
SRC_MD5SUM=$SRC_DATAFILE.md5sum

## compare MD5 to expected, fail if no match
cd $SRC_DDIR
md5sum -c $SRC_MD5SUM

## openssl generated file
## openssl dgst -hex -sha256 btcdata_1600585200.tgz
##   >  btcdata_1600585200.tgz.sha256

## cd work dir with data files
export DST_DDIR=/tmp/btcdata_extract
mkdir -p $DST_DDIR
tar x --directory=$DST_DDIR -f $SRC_DATAFILE
cd $DST_DDIR

##=====================================================
## CREATE (not REPLACE) postgres database
##  init database with btc_hist_schemaonly.sql
##
export PGDATABASE=op_energy_db
export PGHOST=localhost
export PGPORT=5432
export PGUSER=opdev
export PGPASSWORD=opdev

## db init requires a postgresql role w/ credentials
##  and must install plpython3
## TODO this test is flawed - fixme w/ getopts?
#if [[ -z $1 ]] && [[ $1 == '-d' ]]; then
#    psql -c "drop database ${PGDATABASE}"
#fi

createdb -w $PGDATABASE

## remaining MOVED to python setup()
# psql -w $PGDATABASE  -q  < ${PG_REPO}/btc_hist_schemaonly.sql
# psql -w $PGDATABASE -q -f ${SRC_DDIR}/in_btc_raw.sql

##--------------------------------------------------------------
##  invoke the five line importers  TODO py3
##   subshell gets the ENV

python ${PG_REPO}/do_make_base_tables.py

## done
##=======================================================================
##----
##-- err() helper |  useage:
##    [ -n "${docker}" ] || err 1 "Docker not found"
##    [ -x "${docker}" ] || err 2 "Docker is not executable"

err() {
	echo "$2" > /dev/stderr
	exit "$1"
}

