# -*- coding: utf-8 -*-
"""
Created on Sun Jun 13 06:10:03 2021

@author: thartman, dbb
"""

import sys,os
import time
import psycopg2

from misc_utils import uintstr_to_hexstr

## define one PG connection, one cursor
gconn = None
gcurs = None

##-- examine ENV
#print( 'os.environ.items')
#for k,v in os.environ.items():
#  print( str(k) + ' ' + str(v) )
#exit(1)

##- setup for PG connection
# if 'PGDATABASE' in os.environ:
try:
  _pgrepo   = os.getenv('PG_REPO')+'/'
  _src_ddir = os.getenv('SRC_DDIR')+'/'
  _dst_ddir = os.getenv('DST_DDIR')+'/'

  _pgdb       = os.getenv('PGDATABASE')
  _pghost     = os.getenv('PGHOST')
  _pgport     = os.getenv('PGPORT')
  _pguser     = os.getenv('PGUSER')
  _pgpassword = os.getenv('PGPASSWORD')

  _test_mode  = False    ## TODO get from ENV
except:
  print( sys.argv[0] )
  print( ' ENV not complete' )
  exit(1)

## tables to import  UNDER CONSTRUCTION
##   datafile name, dest table name, col count
g_all_imports = {
    ( 'blockbits.txt', 'in_bits_raw',  5 ),
    ( 'blockstats.txt','in_stats_raw', 6 )
}

## tip of the local data_chain
g_height_imported = 0

g_bits_rows = []  # empty list, ready for tuples

#--------------
def setup():
    # establish a PG connection using credentials passed by ENV
    global gcurs, gconn, _src_ddir

    conn_string = "host={} port={} dbname={} user={} password={}".format(
      _pghost, _pgport, _pgdb, _pguser, _pgpassword )

    #print( "DEBUG: DSN="+conn_string )
    try:
      gconn = psycopg2.connect( conn_string )
      gconn.set_session( readonly=False, autocommit=False)
      gcurs = gconn.cursor()
    except Exception, E:
      print str(E)
      exit(1)

    # -- init tables with template sql
    with open( _pgrepo+"btc_hist_schemaonly.sql" , "r") as fd0:
      tBuf = fd0.read()
      try:
        gcurs.execute( tBuf)
        gconn.commit()
      except Exception, E:
        print str(E)
        exit(1)

    ## see  bitcoin-cli getblockstats $HEIGHT
    ## height, blockhash, bits, difficulty, chainwork
    init_ibr_SQL = '''
    DROP table if exists in_bits_raw cascade;
    CREATE TABLE public.in_bits_raw (
      height_str text PRIMARY KEY,
      hash_str text,
      cbits_str text,
      difficulty_str text,
      chainwork_str text
    );
    '''

    try:
      comment_SQL = "COMMENT ON TABLE public.in_bits_raw IS 'import blockbits.txt from datafetch 12nov20';"
      gcurs.execute( init_ibr_SQL )
      gcurs.execute( comment_SQL )
      gconn.commit()
    except Exception, E:
      print(str(E))

    ##-----------------------------------------------------------------
    try:
      infile_name = 'blockbits.txt'
      bitstxt_fd = open( _dst_ddir+infile_name, 'r' )
    except Exception, E:
      print( str(E) )
      exit(1)

  
    while True:
      ln0_height = bitstxt_fd.readline()
      if (cmp( ln0_height, '') == 0):
          break

      ln0_height      =  ln0_height.strip()
      ln1_blockhash   =  uintstr_to_hexstr( bitstxt_fd.readline().strip() )
      ln2_subsidy     =  bitstxt_fd.readline().strip()
      ln3_totalfee    =  bitstxt_fd.readline().strip()
      ln4_time        =  bitstxt_fd.readline().strip()
      ln5_mediantime  =  bitstxt_fd.readline().strip()

      local_row = (ln0_height,ln1_blockhash,ln2_subsidy,ln3_totalfee,ln4_time )
      g_bits_rows.append(local_row)

    print( "str(g_bits_rows)")
    print( str(g_bits_rows))
    exit
    return
    # done setup()

#-------------------------------------------------------------
#  read and store a text datafile in custom format
#   rely on table definition in the template; may change
def do_import_bstats():

  global _test_mode
  global gcurs, gconn

  t_SQL = "insert into public.in_stats_raw values ( %s,%s,%s,%s,%s,%s)"

  init_SQL = '''
  DROP table if exists public.in_stats_raw cascade;
  CREATE TABLE public.in_stats_raw (
    height_str text PRIMARY KEY,
    hash_str text,
    block_subsidy_str  text,
    block_totalfee_str text,
    block_time_str text,
    median_time_str text
  )
  '''
  end_SQL = "COMMENT ON TABLE public.in_stats_raw IS 'import blockstats.txt from datafetch 12nov20';"
  ##--

  try:
    gcurs.execute( init_SQL )
  except Exception, E:
    print(str(E))
  gconn.commit()

  ## see  bitcoin-cli getblockstats $HEIGHT
  ## height, blockhash, subsidy, totalfee, time, mediantime
  try:
    rdF = open( _dst_ddir+'blockstats.txt', 'r' )
  except Exception, E:
    print( str(E) )
    exit(1)

  while True:
    ln0_height = rdF.readline()
    if (cmp( ln0_height, '') == 0):
        break

    ln0_height      =  ln0_height.strip()
    ln1_blockhash   =  rdF.readline().strip()
    ln2_subsidy     =  rdF.readline().strip()
    ln3_totalfee    =  rdF.readline().strip()
    ln4_time        =  rdF.readline().strip()
    ln5_mediantime  =  rdF.readline().strip()
    #print ln4
    gcurs.execute( t_SQL,
      (ln0_height, ln1_blockhash, ln2_subsidy, ln3_totalfee, ln4_time, ln5_mediantime))
    if (  int(ln0_height) % 1000 == 0):
      gconn.commit()

  gconn.commit()
  try:
      gcurs.execute( end_SQL )
      gconn.commit()
  except Exception, E:
      print(str(E))

  return

#-------------------------------------------------------------
def get_block_bits_row( in_height ):
  res_data     = None
  local_height = len(g_bits_rows)

  if local_height > in_height :
    res_data = g_bits_rows[in_height]

  return res_data


#-------------------------------------------------------------
#
#  TOP Level Design is:   
#   this function will get called every time the tool is run
#   check if an update is needed?  if no update needed, just return
#   If an update is needed, call function get_block_bits_row()
#    to get the row, INSERT the row, done
#

def do_import_bbits():
  global _test_mode
  global gcurs, gconn

  try:
    rdF = open( _dst_ddir+'blockbits.txt', 'r' )
  except Exception, E:
    print( str(E) )
    exit(1)

  while True:
    ln0_height = rdF.readline()
    if (cmp( ln0_height, '') == 0):
      break

    ln0_height = ln0_height.strip()
    ln1_hash = rdF.readline().strip()
    ln2_bits = rdF.readline().strip()
    ln3_difficulty = rdF.readline().strip()
    ln4_chainwork = rdF.readline().strip()

    #print ln4
    t_SQL = "insert into public.in_bits_raw values ( %s,%s,%s,%s,%s)"
    gcurs.execute( t_SQL,
      (ln0_height, ln1_hash, ln2_bits, ln3_difficulty, ln4_chainwork))
    if (  int(ln0_height) % 1000 == 0):
      gconn.commit()

    if _test_mode:
      break


  gconn.commit()


  return

##----------------------------------------
def do_next_block():
    global g_height_imported

    ##  TEST current $HEIGHT up to date?
    ##
    ##  -- get highest block in_bit_raw  (already known)
    ##
    ##  -- ask for $HEIGHT+1
    ##  --   if EMPTY return else 
    ##         if text file  else
    ##              extract rows for $HEIGHT+1 from textfile
    ##
    ##  --     blockchain, look for that block+1, with 100 confirmations. 
    ##            (for both scripts) (stats and bits)
    ##
    ##  -- INSERT data
    ##        insert row into raw tables (for sanity / logging)
    ##----------------
    ##---------------------------------------------

    if (g_height_imported > 0):
        try:
          qry_SQL = 'with rows as (SELECT height_str::integer as height from in_bits_raw) SELECT max(rows.height) from rows'
          gcurs.execute( qry_SQL )
        except Exception, E:
          print(str(E))
        g_height_imported = gcurs.fetchone()[0]
        #g_height_imported

    block_bits_row = get_block_bits_row( g_height_imported+1 )
    if block_bits_row is None or block_bits_row == '':
        return   # nothing to do
    
    ## update global row list and counter
    g_bits_rows.append( block_bits_row)
    g_height_imported = g_height_imported + 1

    #
    try:
      t_SQL = "insert into public.in_bits_raw values ( %s,%s,%s,%s,%s)"
      gcurs.execute( t_SQL,
        (block_bits_row[0],block_bits_row[1],block_bits_row[2],block_bits_row[3],block_bits_row[4]))
      gconn.commit()
    except Exception, E:
      print(str(E))

    ##------------------------
    return


##----------------------------------------------------------------
def do_main_loop():

    looping_flag = True
    while (looping_flag):

        do_next_block()  ##- tmp make this work, add bstats+data_chain after

        #if _test_mode:
        #  exit(0)

        #do_import_bstats()

        #do_make_datachain()
        time.sleep(1)


    ## done 
    return

##-----------------------------------------------------------
##  MAIN -- make it so

setup()

do_main_loop()


##-----------------------------------------------------------
##  reference and TBD

##========================
def do_make_datachain():

    t_SQL = '''
    create table data_chain as (
      SELECT b.height_str::integer           as blockheight,
            fix_quoted_numbers(b.hash_str)   as blockhash,
            uintstr_to_hexstr(cbits_str)      as compact_bits_hex,
            b.difficulty_str::float          as difficulty,
            uintstr_to_hexstr(chainwork_str) as chainwork_hex,
            0::bigint as chain_reward,   -- derive this, remove in_btc_raw
            0::bigint as chain_subsidy,
            0::bigint as chain_totalfee,
            in_stats_raw.median_time_str::integer as median_time,
            in_stats_raw.block_time_str::integer  as block_time
      FROM public.in_bits_raw as b
      LEFT JOIN
        in_stats_raw on (b.height_str = in_stats_raw.height_str)
    )
    '''
    end_SQL = "ALTER TABLE data_chain add PRIMARY KEY(blockheight);"

    try:
        gcurs.execute( t_SQL )
    except Exception, E:
      print str(E)
      exit(1)

    try:
        gcurs.execute( end_SQL )
    except Exception, E:
      print str(E)
      exit(1)

    gconn.commit()

    return

#----
# END

