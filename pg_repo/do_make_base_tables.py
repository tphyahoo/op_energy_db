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
g_height_imported = 0  # count of imported rows

g_bits_rows  = []  # empty list of response tuples
g_stats_rows = []  #

g_chainreward  = 0L  #bigInt
g_chainfee     = 0L
g_chainsubsidy = 0L


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
      comment_SQL = "COMMENT ON TABLE public.in_bits_raw IS 'import blockbits.txt from datafetch 12nov20';"
      gcurs.execute( init_ibr_SQL )
      gcurs.execute( comment_SQL )
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
      ln0_height      = 1
      ln1_blockhash   = 0x839a8e6886ab5951d76f411475428afc90947ee320161bbf18eb6048
      ln2_cbits     = '0x1d00ffff'
      ln3_difficulty    = 1.0
      ln4_chainwork = '0x200020002'
      local_row = (ln0_height,ln1_blockhash,ln2_cbits,ln3_difficulty,ln4_chainwork )
      g_bits_rows.append(local_row)
      return

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
    #if _verbose: print( str(g_bits_rows))
    bitstxt_fd.close()

    return


#-------------------------------------------------------------
#  read and store a text datafile in custom format
#   rely on table definition in the template; may change
def do_import_bstats():
  global g_chainreward, g_chainfee, g_chainsubsidy
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
  comment_SQL = "COMMENT ON TABLE public.in_stats_raw IS 'import blockstats.txt from datafetch 12nov20';"
  ##-=
  try:
    gcurs.execute( init_stats_SQL )
    gcurs.execute( comment_SQL )
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
    ln1_blockhash   = 0x839a8e6886ab5951d76f411475428afc90947ee320161bbf18eb6048
    ln2_subsidy     = 5000000000
    ln3_totalfee    = 0
    ln4_median_time = 1231469665
    ln5_block_time  = 1231469665
    local_row = (ln0_height,ln1_blockhash,ln2_subsidy,ln3_totalfee,ln4_time,ln5_mediantime)
    g_stats_rows.append(local_row)
    return

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
    if _verbose: print('(ln0_height,ln1_blockhash,ln2_subsidy,ln3_totalfee,ln4_time,ln5_mediantime)')
    if _verbose: print(str(local_row))
    g_stats_rows.append(local_row)


  if _verbose: print( "str(g_stats_rows)")
  #if _verbose: print( str(g_stats_rows))
  bitstats_fd.close()

  return


##----------------------------------------

def do_init_data_chain():
    global g_chainreward, g_chainfee, g_chainsubsidy
    global _test_mode, g_bits_rows, _verbose
    global gcurs, gconn

    ## odd-but-true, sums here have been pre-initialized; may change
    #g_chainreward   = 0L
    #g_chainfee      = 0L
    #g_chainsubsidy  = 0L

    ##-----------------------------------------------------------------
    init_dc_SQL = '''
    DROP table if exists data_chain cascade;
    CREATE TABLE public.data_chain (
      blockheight integer PRIMARY KEY,
      blockhash text         ,
      compact_bits_hex text  ,
      difficulty float       ,
      chainwork_hex text     ,
      chain_reward   bigint  ,
      chain_subsidy  bigint  ,
      chain_totalfee bigint  ,
      median_time    integer ,
      block_time     integer
    );
    '''
    try:
      comment_SQL = "COMMENT ON TABLE public.data_chain IS '-v0-0';"
      gcurs.execute( init_dc_SQL )
      gcurs.execute( comment_SQL )
      gconn.commit()
    except Exception, E:
      print(str(E))

    ## -----------------
    return


#-------------------------------------------------------------
#  get_block_bits_row
#
def get_block_bits_row( in_height ):
  global _verbose
  ## request a row as 1-based $HEIGHT
  local_height = len(g_bits_rows)

  if (in_height <= local_height):
    res_data = g_bits_rows[in_height-1]  # 0-based index here
  else:
    res_data = None

  if _verbose: print(' in_height :'+str(in_height)+'; local_height:'+str(local_height))
  if _verbose: print(' '+str(res_data))
  return res_data



#-------------------------------------------------------------
#  get_block_stats_row
#
def get_block_stats_row( in_height ):
  global _verbose
  ## request a row as 1-based $HEIGHT
  local_height = len(g_stats_rows)

  if (in_height <= local_height):
    res_data = g_stats_rows[in_height-1]  # 0-based index here
  else:
    res_data = None

  if _verbose: print(' get_block_stats_row:')
  if _verbose: print('  in_height :'+str(in_height)+'; local_height:'+str(local_height))
  if _verbose: print(' '+str(res_data))
  return res_data


#----------------------------------------------------------------
#def write_block_bits_row( in_row ):
#  global _verbose
#  try:
#    t_SQL = "INSERT into public.in_bits_raw values ( %s,%s,%s,%s,%s)"
#    gcurs.execute( t_SQL,
#        (in_row[0],in_row[1],in_row[2],in_row[3],in_row[4]))
#    gconn.commit()
#  except Exception, E:
#    print(str(E))
#
#  if _verbose: print('  write_block_bits_row')
#  return

#----------------------------------------------------------------
#def write_block_stats_row( in_row ):
#  global _verbose
#  try:
#    t_SQL = "insert into public.in_stats_raw values ( %s,%s,%s,%s,%s,%s)"
#    gcurs.execute( t_SQL,
#        (in_row[0],in_row[1],in_row[2],in_row[3],in_row[4],in_row[5]))
#    gconn.commit()
#  except Exception, E:
#    print(str(E))
#
#  if _verbose: print('  write_block_stats_row')
#  return

##----------------------------------------
#def do_make_data_chain_row( in_bits, in_stats):
#    global _verbose
#    global g_chainreward, g_chainfee, g_chainsubsidy
#
#    sys.exit(1) ## <unused FAIL error
    ## update aggregate totals
#    fee = int(in_stats[3])       # ln3_totalfee)
#    subsidy = int(in_stats[2])   # ln2_subsidy)
#    g_chainreward = g_chainreward + fee + subsidy
#    g_chainfee = g_chainfee + fee
#    g_chainsubsidy = g_chainsubsidy + subsidy

#    if _verbose:
#      print( '  aggregate totals:')
#      print( '             fee '+str(type(fee))+' '+str(fee)  )
#      print( '         subsidy '+str(type(subsidy))+' '+str(subsidy)  )
#      print( '   g_chainreward'+str(type(g_chainreward))+' '+hex(g_chainreward)  )
#      print( '      g_chainfee'+str(type(g_chainfee))+' '+hex(g_chainfee)  )
#      print( '  g_chainsubsidy'+str(type(g_chainsubsidy))+' '+hex(g_chainsubsidy)  )

    ## - SQL data_chain  uses tables already in place
#    insert_dc_SQL = '''
#    INSERT into  public.data_chain
#    SELECT b.height_str::integer ,
#            b.hash_str ,
#            cbits_str ,
#            b.difficulty_str::float ,
#            chainwork_str ,
#            %s ,   -- derive this, remove in_btc_raw
#            %s ,
#            %s ,
#            in_stats_raw.median_time_str::integer ,
#            in_stats_raw.block_time_str::integer
#      FROM public.in_bits_raw as b
#      LEFT JOIN
#        in_stats_raw on (b.height_str = in_stats_raw.height_str)
#      WHERE b.height_str LIKE %s
#    '''
#    try:
#      tkey = in_bits[0]
#      gcurs.execute( insert_dc_SQL, ( g_chainreward, g_chainsubsidy, g_chainfee, tkey ) )
#      gconn.commit()
#    except Exception, E:
#      print(str(E))

    ##-------------------
#    if _verbose: print("  do_make_data_chain_row")
#    if _verbose: print(  '   '+str(( g_chainreward, g_chainsubsidy, g_chainfee, tkey )) )
#    return


##----------------------------------------
#res_height, g_chainreward, g_chainfee, g_chainsubsidy = do_next_block( 
#         highest_block_in_pgdb,
#         g_chainreward, g_chainfee, g_chainsubsidy )

def INSERT_block_to_pgdb( in_blockheight ):
    global gcurs, gconn
    #global g_chainreward, g_chainfee, g_chainsubsidy
    global _verbose #, g_height_imported

    ##  TEST current $HEIGHT up to date?
    ##
    ##  -- get highest block already known
    ##
    ##  -- ask for $HEIGHT+1
    ##  --   if EMPTY return
    ##         if text file
    ##              extract rows for $HEIGHT+1 from textfile
    ##
    ##  --     else blockchain, look for that block+1, with 100 confirmations.
    ##            (for both scripts) (stats and bits)
    ##
    ##  -- INSERT data
    ##        insert row into raw tables (for sanity / logging)

    ##---------------------------------------------
    ##if ( not in_blockheight > 0):
    ##    print( 'ERR: '+str(in_blockheight))
    ##    return

    ##=======================================================
    ## MONDAY hack -----

    ## ask for a new block row
    ##   if none, sleep and return
    block_bits_row = get_block_bits_row( in_blockheight+1 )
    if block_bits_row is None or block_bits_row == '':
        if _verbose: print('DEBUG loop - nothing to do')
        time.sleep(10)
        return   # nothing to do


    ##--- We know that there is a new BLOCK available
    ##     get the last known row for accumulators

    get_datachain_row_SQL = '''
      SELECT   chain_reward, chain_subsidy, chain_totalfee 
        FROM   public.data_chain 
       WHERE   blockheight = %s
    '''
  
    ##-=
    try:
      gcurs.execute( get_datachain_row_SQL, (in_blockheight,) )
      gconn.commit()
      res_qry = gcurs.fetchone()
      #
      if _verbose: print( 'DEBUG get_datachain_row_SQL = ' + str(res_qry) )
      if _verbose: print( str(res_qry)+'-')
    except Exception, E:
      print(str(E))

    out_chainreward = 0L
    out_chainfee = 0L
    out_chainsubsidy = 0L

    block_stats_row = get_block_stats_row( in_blockheight+1 )

    ## CHANGE HERE - use the data_chain row as the source for values
    ## record the new block row
    #write_block_bits_row( block_bits_row)
    fee     = int( res_qry[2])   # ln3_totalfee)
    subsidy = int( res_qry[1])   # ln2_subsidy)

    out_chainreward = in_chainreward + fee + subsidy
    out_chainfee = in_chainfee + fee
    out_chainsubsidy = g_chainsubsidy + subsidy

    if _verbose:
      print( '  aggregate totals:')
      print( '             fee '+str(type(fee))+' '+str(fee)  )
      print( '         subsidy '+str(type(subsidy))+' '+str(subsidy)  )
      print( '   out_chainreward'+str(type(out_chainreward))+' '+hex(out_chainreward)  )
      print( '      out_chainfee'+str(type(out_chainfee))+' '+hex(out_chainfee)  )
      print( '  out_chainsubsidy'+str(type(out_chainsubsidy))+' '+hex(out_chainsubsidy)  )

    try:
      t_bits_SQL = "INSERT into public.in_bits_raw values ( %s,%s,%s,%s,%s)"
      gcurs.execute( t_bits_SQL,
        (block_bits_row[0],block_bits_row[1],block_bits_row[2],block_bits_row[3],block_bits_row[4]))
      #if _verbose: print('  write_block_bits_row')

      ## get and record a stats row, may require the hash value from step1
      #write_block_stats_row( block_stats_row)

      t_stats_SQL = "insert into public.in_stats_raw values ( %s,%s,%s,%s,%s,%s)"
      gcurs.execute( t_stats_SQL,
        (block_stats_row[0],block_stats_row[1],block_stats_row[2],block_stats_row[3],block_stats_row[4],block_stats_row[5]))

      ## calc and write data_chain row
      #do_make_data_chain_row( block_bits_row, block_stats_row )

      ## update aggregate totals

      ## - SQL data_chain  uses tables already in place
      insert_dc_SQL = '''
      INSERT into  public.data_chain
      SELECT b.height_str::integer ,
            b.hash_str ,
            cbits_str ,
            b.difficulty_str::float ,
            chainwork_str ,
            %s ,   -- derive this, remove in_btc_raw
            %s ,
            %s ,
            in_stats_raw.median_time_str::integer ,
            in_stats_raw.block_time_str::integer
        FROM public.in_bits_raw as b
        LEFT JOIN
          in_stats_raw on (b.height_str = in_stats_raw.height_str)
        WHERE b.height_str LIKE %s
      '''
      tkey = block_bits_row[0]  ##<- CHECK THIS 
      gcurs.execute( insert_dc_SQL, ( out_chainreward, out_chainsubsidy, out_chainfee, tkey ) )

      gconn.commit()
    except Exception, E:
        print(str(E))

    ## update global row list and counter
    #g_height_imported = g_height_imported + 1

    ##------------------ end MONDAY hack


    ##------------------------
    if _verbose: print('DEBUG  loop - returns')
    return

##----------------------------------------------------------------
def do_main_loop():
    #global g_chainreward, g_chainfee, g_chainsubsidy
    global _verbose   #g_height_imported

    while True:
      ## qry the data_chain table, if there are no entries, ask for HEIGHT 1
      ##  note: if there are no data_chain rows yet, MAX() returns NULL
      ##   if max() is NULL , pass a blockheight = 1
      ##   all other cases, pass the MAX known data_chain height
      try:
        qry_SQL = "SELECT max(blockheight) from data_chain"
        gcurs.execute( qry_SQL )
        # safety check
        res_qry = gcurs.fetchone()
        if res_qry[0] is not None:
          highest_block_in_pgdb = int(res_qry[0])
        else:
          highest_block_in_pgdb = 1
      except Exception, E:
        print(str(E))
        sys.exit(-1)

      if _verbose: 
        print('do_main_loop- highest_block_in_pgdb: '+str(highest_block_in_pgdb))
      # next_block = {}
      # next_block = fetch_block( highest_block_in_pgdb + 1)
      # if not found
      #   sleep, do nothing
      # else
      #   insert_block_pgdb ( highest_block_in_pgdb + 1, next_block[in_fee], next_block[in_subsidy] , whatever else)
      INSERT_block_to_pgdb( highest_block_in_pgdb )

    ## done
    return

##-----------------------------------------------------------
##  MAIN -- make it so

setup()

do_main_loop()


##-----------------------------------------------------------


#----
# END

