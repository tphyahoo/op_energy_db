# -*- coding: utf-8 -*-
"""
Created on Sun Jun 13 06:10:03 2021

@author: dbb
"""

import sys,os
import psycopg2

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

#-------------------------------------------------------------
#  read and store a text datafile in custom format
#   rely on table definition in the template; may change
def do_import_bstats():
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
#  read and store a text datafile in custom format
#   rely on table definition in the template; may change
def do_import_bbits():
  global gcurs, gconn

  ## see  bitcoin-cli getblockstats $HEIGHT
  ## height, blockhash, bits, difficulty, chainwork
  init_SQL = '''
  DROP table if exists in_bits_raw cascade;
  CREATE TABLE public.in_bits_raw (
      height_str text PRIMARY KEY,
      hash_str text,
      cbits_str text,
      difficulty_str text,
      chainwork_str text
  );
  '''

  t_SQL = "insert into public.in_bits_raw values ( %s,%s,%s,%s,%s)"

  end_SQL = "COMMENT ON TABLE public.in_bits_raw IS 'import blockbits.txt from datafetch 12nov20';"

  ##----------------
  try:
    gcurs.execute( init_SQL )
    gconn.commit()
  except Exception, E:
    print(str(E))

  ##---------------------------------------------
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
    gcurs.execute( t_SQL,
      (ln0_height, ln1_hash, ln2_bits, ln3_difficulty, ln4_chainwork))
    if (  int(ln0_height) % 1000 == 0):
      gconn.commit()

  gconn.commit()

  ##--------------------------
  try:
    gcurs.execute( end_SQL )
  except Exception, E:
    print(str(E))
  gconn.commit()

  return


##-------------------------------------------------------------
def do_make_hashdata_table():
    ## TODO 


    return

    t_SQL = '''
     -- COPY
    '''

    try:
        gcurs.execute( t_SQL )
    except Exception, E:
      print str(E)
      exit(1)
    gconn.commit()

    return

#---------------------------------------------------------------
def import_table( in_file_name, in_table_name, in_line_count ):

    try:
      rdF = open( in_file_name, 'r' )
    except Exception, E:
      print str(E)
      exit(1)

    return 0   ## DEBUG

    while True:
        ln0 = rdF.readline()
        if (cmp( ln0, '') == 0):
            break

        ln0 = ln0.strip()
        cnt=in_line_count
        ln1 = rdF.readline().strip()
        cnt = cnt - 1
        if (cnt> 0):
            ln2 = rdF.readline().strip()
        ln3 = rdF.readline().strip()
        ln4 = rdF.readline().strip()

        #print ln4
        gcurs.execute( tSQL, (ln0, ln1, ln2, ln3, ln4))
        if (  int(ln0) % 128 == 0):
            gconn.commit()

    print "Done"


##-----------------------------------------------------------
##  make it so

setup()

do_import_bbits()
do_import_bstats()
do_make_hashdata_table()

#for an_import in g_all_imports:
#    import_table( an_import[0], an_import[1], an_import[2] )

do_make_datachain()

#----
# END

