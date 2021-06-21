#!/bin/bash

# https://stackoverflow.com/questions/59895/how-can-i-get-the-source-directory-of-a-bash-script-from-within-the-script-itsel
#SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

PG_REPO=$(dirname $(readlink -f $0))
echo 'PG_REPO='${PG_REPO}

PGPORT=5432

psql -p ${PGPORT} -c 'create database btc_op_energy'

psql -p ${PGPORT} -q btc_op_energy < ${PG_REPO}/btc_hist_schemaonly.sql
psql -p ${PGPORT} -q btc_op_energy < ${PG_REPO}/data_chain.sql

echo 'done'

