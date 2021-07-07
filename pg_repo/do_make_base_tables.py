# -*- coding: utf-8 -*-
"""

  A single-file python tool to read and store select  BLOCK info

    requires: postgresql and a driver shell script for setup

Created on Sun Jun 13 06:10:03 2021

@author: thartman, dbb
"""

import sys,os
import time
import psycopg2

##----------------------------------------------------------
##  global variables

# in-memory logging tables
g_bits_rows  = []  #
g_stats_rows = []  #

## One PostgreSQL connection, one SQL cursor
gconn = None
gcurs = None

##-- DEBUG examine ENV
#print( 'os.environ.items')
#for k,v in os.environ.items():
#  print( str(k) + ' ' + str(v) )
#exit(1)

##- setup for PG connection
#  check ENV for connection details; ERROR if not found
try:
    _pgrepo     = os.getenv('PG_REPO')+'/'
    _src_ddir   = os.getenv('SRC_DDIR')+'/'
    _dst_ddir   = os.getenv('DST_DDIR')+'/'

    _pgdb       = os.getenv('PGDATABASE')
    _pghost     = os.getenv('PGHOST')
    _pgport     = os.getenv('PGPORT')
    _pguser     = os.getenv('PGUSER')
    _pgpassword = os.getenv('PGPASSWORD')

    _test_mode  = os.getenv('SDEBUG')
    _verbose    = os.getenv('VERBOSE')
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

## tip of the local data_chain -
##  (to-be-deleted, use the db table)
#g_height_imported = 0
#g_chainreward      = 0L  # explicit bigInt
#g_chainfee         = 0L
#g_chainsubsidy     = 0L

##========================================================
##  utils section
#-----------------------------------
def bigint_to_hexstr( in_bigint):
  return  hex( in_bigint)

#-----------------------------------
def calculate_energy_price(
      blka_height, blka_median_time, blka_chain_reward, blka_chainwork_hex,
      blkb_height, blkb_median_time, blkb_chain_reward, blkb_chainwork_hex  ):

  #  integer, bigint, bigint, text, integer, bigint, bigint, text
  ##  assume blkB height > blkA height
  hash_cnt      = int( blkb_chainwork_hex,base=16) - int( blka_chainwork_hex,base=16)
  expected_secs = 600 * ( blkb_height - blka_height )
  actual_secs   = blkb_median_time - blka_median_time
  sats          = blkb_chain_reward - blka_chain_reward

  price_prime,elem  = divmod( (hash_cnt * expected_secs),(actual_secs*sats) )
  return  str(price_prime)

#-----------------------------------
def calculate_energy_price_print(
      blka_height, blka_median_time, blka_chain_reward, blka_chainwork_hex,
      blkb_height, blkb_median_time, blkb_chain_reward, blkb_chainwork_hex  ):

  #  integer, bigint, bigint, text, integer, bigint, bigint, text
  ##  note that postgres casts identifiers to lower-case silently
  res_str = ''
  res_str = 'blkA_height:' + str(blka_height)
  res_str = res_str + '; blkA_median_time:' + str(blka_median_time)
  res_str = res_str + '; blkA_chain_reward:' + str(blka_chain_reward)
  res_str = res_str + '; blkA_chainwork_hex: ' + blka_chainwork_hex
  res_str = res_str + '; blkB_height:' + str(blkb_height)
  res_str = res_str + '; blkB_median_time:' + str(blkb_median_time)
  res_str = res_str + '; blkB_chain_reward:' + str(blkb_chain_reward)
  res_str = res_str + '; blkB_chainwork_hex: ' + blkb_chainwork_hex
  return  res_str

#-----------------------------------
# BitcoinD ref:
#  https://github.com/bitcoin/bitcoin/blob/master/src/arith_uint256.cpp#L203
# --
def cbits_to_hexstr( in_text):
  cbits_hex       = int( in_text, 16)
  reg_difficulty  = cbits_hex & 0x007FFFFF
  reg_exp_enc     = (cbits_hex & 0xFF000000) >> 24

  exp_const   = 1 * 2** (8*(reg_exp_enc-3))
  exp_varying = reg_difficulty * exp_const
  byteCnt = ( exp_varying.bit_length() +7)/8  # check count of bytes
  return hex( exp_varying)

#--------------------------------
def uintstr_to_hexstr( in_text):
  tStr   =  in_text
  tStr   =  tStr.strip( "\"")
  tStr   =  tStr.lstrip("0")
  return "0x"+tStr

#--------------------------------
def fix_quoted_numbers( in_text):
  return "0x"+in_text.strip("\"")

##------------------------------
def hexstr_to_bigint( in_text):
  return int( in_text, base=16)

##-----------------------------------
def hexstr_to_cbits( in_str):
    res = int( in_str, base=16)
    cnt  = 1
    res2 = res
    while True:
        cnt = cnt + 1
        res2,elem = divmod(res2,0x100)
        if res2 < 0x100:
            break

    ## test for high bit, and shift here
    if res2 > 127:
        cnt = cnt + 1

    res2  = res >> ((cnt-3)*8)
    res2b = res2 & 0x007FFFFF
    cnt2 = cnt << 24
    res_str = hex(cnt2 | res2).rstrip('L')
    return (res_str)

#-----------------------------------
def int_to_hexstr( in_integer):
    return  hex( in_integer)

##======================================================================

def setup():
    # Called once at program startup time
    #  - establish a PG connection using credentials passed by ENV
    global gcurs, gconn, _src_ddir
    global _pghost, _pgport, _pgdb, _pguser, _pgpassword

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

    ##- initialize from known data
    do_import_bbits()
    do_import_bstats()
    do_init_data_chain()

    return
    # done setup()

#-------------------------------------------------------------
#
def do_import_bbits():
    global _verbose
    global _test_mode, g_bits_rows
    global gcurs, gconn

    ##-----------------------------------------------------------------
    ##  import first info file -- blockbits -
    ##   ref.  bitcoin-cli getblock $HASH
    ##   ( height, blockhash, bits, difficulty, chainwork )
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
      gcurs.execute( init_ibr_SQL )
      gconn.commit()
    except Exception, E:
      print(str(E))
    ## -----------------------------------------------
    bitstxt_fd = None
    try:
      infile_name = 'blockbits.txt'
      bitstxt_fd = open( _dst_ddir+infile_name, 'r' )
    except Exception, E:
      print( str(E) )

    if bitstxt_fd is None:
      # No startup data file?
      #  init with preformed first row
      ln0_height        = 1
      ln1_blockhash     = '0x839a8e6886ab5951d76f411475428afc90947ee320161bbf18eb6048'
      ln2_cbits         = '0x1d00ffff'
      ln3_difficulty    = 1.0
      ln4_chainwork     = '0x200020002'
      local_row = (ln0_height,ln1_blockhash,ln2_cbits,ln3_difficulty,ln4_chainwork )
      if _verbose: print('DEBUG bitstxt_fd is None')
      g_bits_rows.append(local_row)
      return

    ##-= got a seed datafile and load data into RAM

    if _verbose: print('local_row (ln0_height,ln1_blockhash,ln2_cbits,ln3_difficulty,ln4_chainwork)')
    while True:
      ln0_height = bitstxt_fd.readline()
      if (cmp( ln0_height, '') == 0):
          break

      ln0_height      =  ln0_height.strip()
      ln1_blockhash   =  uintstr_to_hexstr( bitstxt_fd.readline().strip() )
      ln2_cbits       =  fix_quoted_numbers( bitstxt_fd.readline().strip() )
      ln3_difficulty  =  bitstxt_fd.readline().strip()
      ln4_chainwork   =  uintstr_to_hexstr( bitstxt_fd.readline().strip() )

      local_row = (ln0_height,ln1_blockhash,ln2_cbits,ln3_difficulty,ln4_chainwork )
      if _verbose: print(str(local_row))
      g_bits_rows.append(local_row)

    if _verbose: print( "INIT g_bits_rows len=" + str(len(g_bits_rows)))
    #if _verbose: print( str(g_bits_rows))
    bitstxt_fd.close()

    return


#-------------------------------------------------------------
#  read and store a text datafile in custom format
#   rely on table definition in the template; may change
def do_import_bstats():
  # global g_chainreward, g_chainfee, g_chainsubsidy
  global _test_mode, g_stats_rows, _verbose
  global gcurs, gconn

  init_stats_SQL = '''
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

  ##-=
  try:
    gcurs.execute( init_stats_SQL )
    gconn.commit()
  except Exception, E:
    print(str(E))
  ##-----------------------------------------------------------------
  ## open a demo datafile-- blockstats -
  ## see  bitcoin-cli getblockstats $HEIGHT
  ## height, blockhash, subsidy, totalfee, time, mediantime
  try:
    bitstats_fd = None
    bitstats_fd = open( _dst_ddir+'blockstats.txt', 'r' )
  except Exception, E:
    print( str(E) )

  if bitstats_fd is None:
    # No startup data file?
    #  init with preformed first row
    ln0_height      = 1
    ln1_blockhash   = '0x839a8e6886ab5951d76f411475428afc90947ee320161bbf18eb6048'
    ln2_subsidy     = 5000000000L
    ln3_totalfee    = 0L
    ln4_median_time = 1231469665
    ln5_block_time  = 1231469665
    local_row = (ln0_height,ln1_blockhash,ln2_subsidy,ln3_totalfee,ln4_time,ln5_mediantime)
    if _verbose: print('DEBUG bitstats_fd is None')
    g_stats_rows.append(local_row)
    return

  ##-= got a seed datafile, and load data into RAM

  if _verbose: print('(ln0_height,ln1_blockhash,ln2_subsidy,ln3_totalfee,ln4_time,ln5_mediantime)')
  while True:
    ln0_height = bitstats_fd.readline()
    if (cmp( ln0_height, '') == 0):
        break

    ln0_height      =  ln0_height.strip()
    ln1_blockhash   =  uintstr_to_hexstr( bitstats_fd.readline().strip() )
    ln2_subsidy     =  bitstats_fd.readline().strip()
    ln3_totalfee    =  bitstats_fd.readline().strip()
    ln4_time        =  bitstats_fd.readline().strip()
    ln5_mediantime  =  bitstats_fd.readline().strip()

    local_row = (ln0_height,ln1_blockhash,ln2_subsidy,ln3_totalfee,ln4_time,ln5_mediantime)
    if _verbose: print(str(local_row))
    g_stats_rows.append(local_row)


  if _verbose: print( "INIT g_stats_rows len=" + str(len(g_stats_rows)))
  #if _verbose: print( str(g_stats_rows))
  bitstats_fd.close()

  return


##----------------------------------------

def do_init_data_chain():
    global _verbose, g_bits_rows
    global  gcurs,   gconn

    ##-----------------------------------------------------------------
    init_dc_SQL = '''
    DROP table if exists data_chain cascade;
    CREATE TABLE public.data_chain (
      blockheight integer PRIMARY KEY,
      blockhash        text     ,
      compact_bits_hex text     ,
      difficulty       float    ,
      chainwork_hex    text     ,
      chain_reward     bigint   ,
      chain_subsidy    bigint   ,
      chain_totalfee   bigint   ,
      median_time      integer  ,
      block_time       integer
    );
    '''
    try:
      gcurs.execute( init_dc_SQL )
      gconn.commit()
    except Exception, E:
      print(str(E))

    # this looks wrong, shouldn't need to insert a row at init time, for any tables.
    if ( True ):  #len(g_bits_rows) == 1 ):
      ## -------------------------------------------------------------
      ##  to simplify the main loop, there is always one row to start
      init_datachain_SQL = '''
        INSERT into public.data_chain(
         blockheight, blockhash,
         compact_bits_hex, difficulty, chainwork_hex,
         chain_reward, chain_subsidy, chain_totalfee, median_time, block_time)
        VALUES (  1, '0x839a8e6886ab5951d76f411475428afc90947ee320161bbf18eb6048',
         '0x1d00ffff', 1.0, '0x200020002',
          5000000000, 5000000000, 0, 1231469665, 1231469665 );
      '''
      try:
        gcurs.execute( init_datachain_SQL )
        gconn.commit()
      except Exception, E:
        print(str(E))


    ##-- done init data_chain
    return


#-------------------------------------------------------------
#  get_block_bits_row
#    request a row as 1-based $HEIGHT
#
def get_block_bits_row( in_row ):
  global  g_bits_rows, _verbose

  local_rows = len(g_bits_rows)

  if (in_row <= local_rows):
    res_data = g_bits_rows[in_row-1]  # 0-based index here
  else:
    res_data = None

  if _verbose: print(' in_row :'+str(in_row)+'; local_rows:'+str(local_rows))
  if _verbose: print(' '+str(res_data))
  return res_data


#-------------------------------------------------------------
#  get_block_stats_row
#   request a row           ##as 1-based $HEIGHT##
#
def get_block_stats_row( in_row ):
  global g_stats_rows, _verbose

  local_rows = len(g_stats_rows)

  if (in_row <= local_rows):
    res_data = g_stats_rows[ in_row-1]  # 0-based index here
  else:
    res_data = None

  if _verbose: print(' get_block_stats_row:')
  if _verbose: print('  in_row :'+str(in_row)+'; local_rows:'+str(local_rows))
  if _verbose: print(' '+str(res_data))
  return res_data


##----------------------------------------
def INSERT_block_to_pgdb( lowest_block_not_in_pgdb, accum_chainsubsidy, accum_chainfee ):
    global gcurs, gconn
    global g_bits_rows, g_stats_rows
    global _verbose #, g_height_imported

    ##=======================================================

    ## ask for a new BLOCK row
    ##   if none, sleep and return
    # todo it shouldn't be sleep and return. it should keep trying forever. ditto foget_block_stats_row.
    block_bits_row = get_block_bits_row( lowest_block_not_in_pgdb )
    if block_bits_row is None or block_bits_row == '':
        if _verbose: print('DEBUG loop - nothing to do')
        time.sleep(10)
        return   #  no new block; nothing to do

    block_stats_row = get_block_stats_row( lowest_block_not_in_pgdb )

    ##--- A new BLOCK is available  ------------------------------

    ## get fee info from in-memory list
    ## height, blockhash, subsidy, totalfee, time, mediantime
    fee     = long( block_stats_row[3])   # ln3_totalfee)
    subsidy = long( block_stats_row[2])   # ln2_subsidy)

    #local_chainreward  = local_chainreward + fee + subsidy
    local_chainfee     = accum_chainfee + fee # todo, don't mutate vars.
    local_chainsubsidy = accum_chainsubsidy + subsidy
    local_chainreward  = local_chainsubsidy + local_chainfee

    
    if _verbose:
      print( '   aggregate totals:')
      print( '              fee '+str(type(fee))+' '+str(fee)  )
      print( '          subsidy '+str(type(subsidy))+' '+str(subsidy)  )
      print( '   local_chainreward'+str(type(local_chainreward))+' '+hex(local_chainreward)  )
      print( '      local_chainfee'+str(type(local_chainfee))+' '+hex(local_chainfee)  )
      print( '  local_chainsubsidy'+str(type(local_chainsubsidy))+' '+hex(local_chainsubsidy)  )

    try:
      ## -- write logging table   bits
      t_bits_SQL = "INSERT into public.in_bits_raw ( height_str , hash_str , cbits_str , difficulty_str , chainwork_str  ) values ( %s,%s,%s,%s,%s)"
      gcurs.execute( t_bits_SQL,
        (block_bits_row[0],block_bits_row[1],block_bits_row[2],block_bits_row[3],block_bits_row[4]))
      #if _verbose: print('  write_block_bits_row')

      ## -- write logging table   stats
      t_stats_SQL = "insert into public.in_stats_raw ( height_str, hash_str , block_subsidy_str , block_totalfee_str , block_time_str , median_time_str ) values ( %s,%s,%s,%s,%s,%s)"
      gcurs.execute( t_stats_SQL,
        (block_stats_row[0],block_stats_row[1],block_stats_row[2],block_stats_row[3],block_stats_row[4],block_stats_row[5]))

       ## -- calc and write       data_chain
      insert_dc_SQL = '''
      INSERT into  public.data_chain  ( blockheight , blockhash , compact_bits_hex , difficulty , chainwork_hex , chain_reward , chain_subsidy , chain_totalfee , median_time , block_time )
                                      values ( %s,%s,%s,%s,%s,%s,%s,%s,%s,%s )
      '''
      gcurs.execute( insert_dc_SQL, ( block_bits_row[0] , block_bits_row[1], block_bits_row[2], block_bits_row[3], block_bits_row[4],
                                      local_chainreward, local_chainsubsidy, local_chainfee,
                                      block_stats_row[5], block_stats_row[4] ) )

      gconn.commit()
    except Exception, E:
      print(str(E))

    ##------------------------
    if _verbose: print('DEBUG  loop - returns')
    return

def get_accum_data_chain():
    try:
        qry_SQL = "SELECT max(blockheight) from data_chain"
        gcurs.execute( qry_SQL )

        res_qry = gcurs.fetchone()
        # if data_chain has data
        if res_qry[0] is not None:
          highest_row_in_pgdb = int(res_qry[0])
          lowest_block_not_in_pgdb = highest_row_in_pgdb + 1
          ##  get accumulator variables from last recorded data_chain row
          get_datachain_row_SQL = '''
          SELECT chain_totalfee, chain_subsidy
          FROM   public.data_chain
          WHERE  blockheight = %s
          '''

          try:
            gcurs.execute( get_datachain_row_SQL, (highest_row_in_pgdb, ) )
            res_qry_accum = gcurs.fetchone()

            if _verbose: print( 'res_qry_accum:  '+str(res_qry_accum))
            accum_chainfee = res_qry_accum[0]
            accum_chainsubsidy = res_qry_accum[1]
          except Exception, E:
            print("get_datachain_row_SQL: " + str(E) )

        else:
          # if data_chain has no data
          lowest_block_not_in_pgdb = 0
          accum_chainfee     = 0L
          accum_chainsubsidy = 0L
    except Exception, E:
        print("qry_sql: " + str(E))
        sys.exit(-1)
    return {"lowest_block_not_in_pgdb" : lowest_block_not_in_pgdb, "accum_chainfee" : accum_chainfee, "accum_chainsubsidy" : accum_chainsubsidy }

##----------------------------------------------------------------
def do_main_loop():
    global _verbose 

    while True:
      # if data_chain has no data, fetch and insert block 1, since blockchain index starts there. otherwise fetch and insert max block + 1.
      z = get_accum_data_chain()
      print "z: " + str(z)
      INSERT_block_to_pgdb( z["lowest_block_not_in_pgdb"], z["accum_chainsubsidy"], z["accum_chainfee"] )
    return


##-----------------------------------------------------------
##  MAIN -- make it so

setup()

do_main_loop()


##-----------------------------------------------------------


#----
# END

