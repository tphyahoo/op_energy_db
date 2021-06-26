# -*- coding: utf-8 -*-
"""
Created on Sun Jun 13 06:10:03 2021

@author: thartman, dbb
"""

import sys,os
import time
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

## tip of the local data_chain
g_height_imported = 0

g_bits_rows = []  # empty list, ready for tuples

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
  cbits_hex = int( in_text, 16)
  reg_difficulty  = cbits_hex & 0x007FFFFF
  reg_exp_enc = (cbits_hex & 0xFF000000) >> 24

  exp_const = 1 * 2** (8*(reg_exp_enc-3))
  exp_varying = reg_difficulty * exp_const
  bitCnt = ( exp_varying.bit_length() +7)/8
  return hex( exp_varying)

#--------------------------------
def uintstr_to_hexstr( in_text):
  tStr = in_text
  tStr = tStr.strip( "\"")
  tStr = tStr.lstrip("0")
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

    do_import_bbits()
    #do_import_bstats()
    #do_make_data_chain()
    
    return
    # done setup()


#-------------------------------------------------------------
#
def do_import_bbits():
    global _test_mode, g_bits_rows
    global gcurs, gconn

    ##-----------------------------------------------------------------
    ##  import first info file -- blockbits -- 
    ##   ref.  bitcoin-cli getblockstats $HEIGHT
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
      comment_SQL = "COMMENT ON TABLE public.in_bits_raw IS 'import blockbits.txt from datafetch 12nov20';"
      gcurs.execute( init_ibr_SQL )
      gcurs.execute( comment_SQL )
      gconn.commit()
    except Exception, E:
      print(str(E))
    ## -----------------------------------------------
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
      ln2_cbits       =  fix_quoted_numbers( bitstxt_fd.readline().strip() )
      ln3_difficulty  =  bitstxt_fd.readline().strip()
      ln4_chainwork   =  uintstr_to_hexstr( bitstxt_fd.readline().strip() )

      local_row = (ln0_height,ln1_blockhash,ln2_cbits,ln3_difficulty,ln4_chainwork )
      if _verbose: print('local_row (ln0_height,ln1_blockhash,ln2_cbits,ln3_difficulty,ln4_chainwork)')
      if _verbose: print(str(local_row))
      g_bits_rows.append(local_row)

    if _verbose: print( "str(g_bits_rows)")
    if _verbose: print( str(g_bits_rows))
    bitstxt_fd.close()

    return

tmp999 = '''

  ##-------------
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

'''

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
#  get_block_bits_row
#   
#
def get_block_bits_row( in_height ):
  ## request a row as 1-based $HEIGHT
  local_height = len(g_bits_rows)

  if (in_height < local_height):
    res_data = g_bits_rows[in_height-1]  # 0-based index here
  else:
    res_data = None

  if _verbose: print(' in_height :'+str(in_height)+'; local_height:'+str(local_height))
  if _verbose: print(' '+str(res_data))
  return res_data

#----------------------------------------------------------------
def write_block_bits_row( in_row ):

  #-----------
  try:
    t_SQL = "INSERT into public.in_bits_raw values ( %s,%s,%s,%s,%s)"
    gcurs.execute( t_SQL,
        (in_row[0],in_row[1],in_row[2],in_row[3],in_row[4]))
    gconn.commit()
  except Exception, E:
    print(str(E))

  if _verbose: print('  write_block_bits_row')
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
    # check if an update is needed?  if no update needed, just return
    # If an update is needed, 
    #   row = get_block_bits_row()
    #   INSERT the row, done

    ##---------------------------------------------

    if (g_height_imported > 0):
        #try:
        #  qry_SQL = 'with rows as (SELECT height_str::integer as height from in_bits_raw) SELECT max(rows.height) from rows'
        #  gcurs.execute( qry_SQL )
        #except Exception, E:
        #  print(str(E))
        #g_height_imported = gcurs.fetchone()[0]
        print( str(g_height_imported))

    block_bits_row = get_block_bits_row( g_height_imported+1 )
    if block_bits_row is None or block_bits_row == '':
        if _verbose: print('DEBUG loop - nothing to do')
        return   # nothing to do
    
    ## record the new block row
    write_block_bits_row( block_bits_row)

    ## update global row list and counter
    g_height_imported = g_height_imported + 1


    ##------------------------
    if _verbose: print('DEBUG loop - exit')
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


#----
# END

