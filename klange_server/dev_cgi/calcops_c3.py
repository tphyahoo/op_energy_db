#!/usr/bin/env python

# calcops_c3.cgi?idBeg=500200&span=2016&idEnd=646000&inc=200&mimetype=png
#
#   params: 'span' defaults to 2016, and is the width of the window in rows
#           'inc'  sets the marching increment
#           'idBeg' and 'idEnd' are the start and end  block heights
#
#    http://dev.bergain.biz:7888/
#      calcops_c3.py?idBeg=100000&idEnd=120000  ## default span=2016, default inc=10
#      calcops_c3.py?idBeg=100000&inc=100&idEnd=120000  ## 200 rows of span 2016
#      calcops_c3.py?idBeg=100000&inc=200&idEnd=120000  ## 100 rows of span 2016
#--

import os, sys
import json, re, random

##-- under python CGI, query params were passed in argv
##--  CGI spec uses env variable QUERY_STRING
#
#  previous method:
#   idBeg = int(sys.argv[1])
#   span  = int(sys.argv[2])
#   idEnd = int(sys.argv[3])

try:
  resQryStr = os.getenv('QUERY_STRING' )
except:
  print( 'FAIL:',sys.argv)
  sys.exit(-1)


##-------------------------------
tD = {}
arg_list = resQryStr.split('&')
for elem in arg_list:
    res_t = elem.split('=')
    if len(res_t) < 2:  break
    tD[res_t[0]] = res_t[1]

if tD.get('idBeg') is None or tD.get('idEnd') is None:
  print('FAIL useage: ?idBeg=0000&idEnd=00000')
  sys.exit(-1)

local_beg = int(tD.get('idBeg'))
local_end = int(tD.get('idEnd'))

local_span = 2016
str_span = tD.get('span')
if  str_span is not None:
  if int(str_span) > 0 and int(str_span) < 64000:
    local_span = int(str_span)

local_inc = 10
str_inc = tD.get('inc')
if  str_inc is not None:
  if int(str_inc) > 0 and int(str_inc) < 64000:
    local_inc = int(str_inc)


##----------------------------------
#  always generate a csv data file
dst_file = '/tmp/res3_{}-{}-{}-{}.csv'.format( local_beg, local_span, local_inc, local_end )
#print(dst_file,tD)
#dst_file = '/tmp/res3.csv'

## check for a cached, previous result as a csv file
if ( not os.path.isfile(dst_file) ):

  ## PG connect and query
  ## rely on a script-built postgresql database -  btc_op_energy
  PGPORT=5432
  import psycopg2 as pg
  try:
    conn  = pg.connect("dbname=btc_op_energy port="+str(PGPORT))
    curs = conn.cursor()
  except pg.OperationalError as e:
    print('#psycopg2: '+str(e))
    sys.exit(-1)

  tSQL_pre = '''  COPY
  (SELECT calcops_28( a.blkheight, a.median_time, a.chain_reward, a.chainwork_hex,
                     b.blkheight, b.median_time, b.chain_reward, b.chainwork_hex),
                     b.blkheight, b.median_time
  FROM data_chain as a, data_chain as b  WHERE
    a.blkheight > %s AND a.blkheight %% %s = 0  AND  a.blkheight < %s AND
    b.blkheight = (a.blkheight+%s)  AND b.median_time <> a.median_time ) to

  '''
  tSQL_post = '''
    with CSV header ;
  '''
  tSQL = tSQL_pre+"'"+dst_file+"'"+tSQL_post
  #tSQL = tSQL_pre

  try:
    res = curs.execute(tSQL,( local_beg, local_inc, local_end, local_span ))

    #res = curs.fetchall()
    #print('SQL:',res)
  except pg.Error as e:
    print( str(e) )
    print('FAIL SQL', curs.query)
    print( 'qry ',resQryStr )
    print( 'dict ',str(tD))
    sys.exit(-1)

  #print(curs.fetchall())

##--------------------------------------------
##-- add PNG support with a mimetype selector

if tD.get('mimetype') is None or tD.get('mimetype') == 'csv':
    #  'Content-Type: text/css; charset=UTF-8'
    print( 'Content-type: text/csv\n' )
    tFile = open( dst_file ,'r')
    buf = tFile.read()
    print(buf)
    exit(0)


# ---

gformat = 'png'
if tD.get('mimetype') == 'svg':
    gformat = 'svg'

dst_chartfile = '/tmp/chart3_{}-{}-{}-{}.{}'.format( local_beg, local_span, local_inc, local_end, gformat )

#if len(sys.argv)>1:
#  if sys.argv[1]  == 'svg': gformat = 'svg'
#  elif sys.argv[1]  == 'pdf': gformat = 'pdf'
#
# ---
# currently charts are drawn with about 1600 pixels across
# a range needs only a few dozen datapoints to be drawn, but
# traders may want a lot of specific details. Many ranges will
# produce many more data points than can be drawn in the chart.
# In general, emit the data CSV in any case, with the desired
# detail, and let the charting layer do the sampling as necessary.


if ( os.path.isfile(dst_chartfile) ):
  tFile = open( dst_chartfile , 'r')
  buf = tFile.read()
  print( 'Content-Length: '+str(len(buf)) )
  print( 'Content-Type: image/'+gformat+'\n')
  print(buf)
  exit(0)

# ---
import matplotlib as mplt
mplt.use('Agg')

import matplotlib.pyplot as plt
import pandas as pd

from datetime import datetime

# ---
df_ex0 = pd.read_csv( dst_file, sep=',' )
# ---
fig = plt.figure(figsize=(12,10))
price_ax = plt.subplot(2,1,1)

if tD.get('linearY') is not None:
  price_ax.plot( df_ex0.blkheight, df_ex0.calcops_28)
else:
  price_ax.semilogy( df_ex0.blkheight, df_ex0.calcops_28)

price_ax.grid(True)

tdict = {
     'fontsize': 14,
     'fontweight' : 'bold',
     'verticalalignment': 'bottom',
     'horizontalalignment': 'center'}

plt.title( 'Hashes per Satoshi -- moving window @'+str(local_inc), fontdict=tdict )

tDateStr = ''
tElemLast = df_ex0.shape[0] -1
tDateBegStr = datetime.utcfromtimestamp(  df_ex0.at[   0, 'median_time']      ).strftime("%Y-%m-%d %H:%M")
tDateEndStr = datetime.utcfromtimestamp(  df_ex0.at[ tElemLast, 'median_time']).strftime("%Y-%m-%d %H:%M")

plt.xlabel("Block    "+tDateBegStr+"  --  "+tDateEndStr)
plt.ylabel("hashes per satoshi")

#out_fname = '/tmp/chart03.{}'.format(gformat)
plt.savefig( dst_chartfile, dpi=144, facecolor='w', edgecolor='w',
        transparent=False, bbox_inches=None, pad_inches=0.1, format=gformat,
        frameon=None)

#--
tFile = open( dst_chartfile ,'r')
buf = tFile.read()
print( 'Content-Length: '+str(len(buf)) )
print('Content-Type: image/'+gformat+'\n')
print(buf)
