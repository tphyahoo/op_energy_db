#!/usr/bin/env python

#  aconcagua   -- return form
#  aconcagua?
#    idBeg   span  idEnd  mimetype  chartopts
#--

import os, sys
import json, re, random

##--  CGI spec uses env variable QUERY_STRING
#

try:
  resQryStr = os.getenv('QUERY_STRING' )
except:
  print( 'FAIL:',sys.argv)
  sys.exit(-1)


# print( str(os.environ) )
##-------------------------------------------------------
form_Header = '''
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
  <head>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <title>Calculate Hashes per Satoshi</title>

  <style>
body {
  padding: 3px;
  margin: 5px;
  background-color: #F6FFFF;
  font-family: "Gill Sans", sans-serif;
}

.form1 {
  background-color: #FFFFF0;
}
input {
  padding: 5px 5px;
  margin: 3px;
}
table {  /* table */
  border: 1px solid black;
  border-spacing: 5px;
  border-collapse: separate;
}
th, td {  /* cells */
  border: 1px solid #aaa;
  padding: 5px 10px;
}
  </style>

  </head>
  <body>
    <h3> aconcagua &mdash; alpha build cgi interface </h3>
'''

form_BA = '''
    <hr size="2" width="100%"> <br>
    <form action="aconcagua.py" method="get" class="form1">
      <div class="form1">
       <label for="name">Start Block: </label>
        <input name="idBeg" id="idBeg" required="" maxlength="6"><br/>

       <label for="inc">&nbsp;inc: &nbsp;</label>
        <input name="inc" id="inc" required="" maxlength="6" width=170px;>

       <label for="span">&nbsp; span:&nbsp; </label>
        <input name="span" id="spanID" value="2016" required="" maxlength="6" width=170px;><br/>

       <label for="idEnd">End Block: </label>
        <input name="idEnd" id="idEnd" required="" maxlength="6">
      <br>
      <input id="makeChartid" name="makeChartname" value="Chart"
        type="checkbox"> <label for="makeChart"> Chart the csv results
        below</label> <br>
      <br>
      <input value="Calculate OP_ENERGY" type="submit">
     </div>
    </form>
    <br>
    <hr size="2" width="100%">
    <br>

'''

form_Trailer = '''
  </body>
</html>

'''

def do_form():
  print( form_Header )

  print( form_BA )

  ra_str = os.getenv('REMOTE_ADDR')
  ua_str = os.getenv('HTTP_USER_AGENT')
  tStr = "IP {};<br>HTTP_USER_AGENT {}; ".format( ra_str, ua_str )
  print( "<pre>"+tStr+"</pre>")
  print( "<pre>"+str(tD)+"</pre>" )

  print( form_Trailer )

##-------------------------------
if resQryStr is None:
  do_form()
  exit(0)

tD = {}
arg_list = resQryStr.split('&')
for elem in arg_list:
    res_t = elem.split('=')
    if len(res_t) < 2:  break
    tD[res_t[0]] = res_t[1]

if len(tD.keys()) == 0:
  do_form()
  exit(0)

##--
if tD.get('idBeg') is None or tD.get('idEnd') is None:
  print('FAIL useage: ?idBeg=0000&idEnd=00000')
  sys.exit(-1)

local_beg = int(tD.get('idBeg'))
local_end = int(tD.get('idEnd'))

if local_end <= local_beg:
  print('FAIL useage: ?idBeg=0000&idEnd=00000')
  sys.exit(-1)

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
dst_file = 'res3_{}-{}-{}-{}.csv'.format( local_beg, local_span, local_inc, local_end )

if ( not os.path.isfile( '/tmp/'+dst_file) ):

  ## PG connect and query
  ## rely on a script-built postgresql database -  btc_op_energy
  PGPORT=5432
  import psycopg2 as pg
  try:
    conn  = pg.connect("dbname=op_energy_db port="+str(PGPORT))
    curs = conn.cursor()
  except pg.OperationalError as e:
    print('#psycopg2: '+str(e))
    sys.exit(-1)

  tSQL_pre = '''  COPY
  (SELECT calculate_energy_price( a.blkheight, a.median_time, a.chain_reward, a.chainwork_hex,
                     b.blkheight, b.median_time, b.chain_reward, b.chainwork_hex),
                     b.blkheight, b.median_time
  FROM data_chain as a, data_chain as b  WHERE
    a.blkheight > %s AND a.blkheight %% %s = 0  AND  a.blkheight < %s AND
    b.blkheight = (a.blkheight+%s)  AND b.median_time <> a.median_time ) to

  '''
  tSQL_post = '''
    with CSV header ;
  '''
  tSQL = tSQL_pre+"'/tmp/"+dst_file+"'"+tSQL_post
  #tSQL = tSQL_pre

  try:
    res = curs.execute(tSQL,( local_beg, local_inc, local_end, local_span ))

  except pg.Error as e:
    print( str(e) )
    print('FAIL SQL', curs.query)
    print( 'qry ',resQryStr )
    print( 'dict ',str(tD))
    sys.exit(-1)

  #print(curs.fetchall())
os.system( 'cp /tmp/'+dst_file+' ../images/' )

##-- emit the results in HTML tags
print( form_Header )

print( "<pre>"+str(tD)+"</pre>" )
print('<p> &nbsp; <a href=../images/'+dst_file+'> CSV-link </a></p>' )

# placeholder for more chart choices TBD
# if any value is defined, make one chart
if tD.get('makeChartname') is not None:
  gformat = 'png'
  if tD.get('mimetype') == 'svg':
      gformat = 'svg'

  dst_chartfile = 'chart3_{}-{}-{}-{}.{}'.format( local_beg, local_span, local_inc, local_end, gformat )
  if ( True ) :   #not os.path.isfile( '/tmp/'+dst_chartfile) ):

    import matplotlib as mplt
    mplt.use('Agg')

    import matplotlib.pyplot as plt
    import pandas as pd
    from datetime import datetime

    print('<p><a href=../images/'+dst_chartfile+'>chart-link</a></p>' )

    # ---
    df_ex0 = pd.read_csv( '/tmp/'+dst_file, sep=',' )
    # ---
    fig = plt.figure(figsize=(12,10))
    price_ax = plt.subplot(2,1,1)

    if tD.get('linearY') is not None:
      price_ax.plot( df_ex0.blkheight, df_ex0.calcops_28)
    else:
      price_ax.semilogy( df_ex0.blkheight, df_ex0.calcops_28)

    price_ax.grid(True)

    tdict = {
       'fontsize': 13,
       'fontweight' : 'bold',
       'verticalalignment': 'bottom',
       'horizontalalignment': 'center'}


    tDateStr = ''
    tElemLast = df_ex0.shape[0] -1
    tDateBegStr = datetime.utcfromtimestamp(  df_ex0.at[   0, 'median_time']      ).strftime("%Y-%m-%d %H:%M")
    tDateEndStr = datetime.utcfromtimestamp(  df_ex0.at[ tElemLast, 'median_time']).strftime("%Y-%m-%d %H:%M")

    plt.title( 'Hashes per Satoshi - ' + str(local_span)+ ' Block Span - '+ tDateBegStr+" to "+tDateEndStr, fontdict=tdict )

    plt.xlabel(" Block")
    plt.ylabel("hashes per satoshi")

    #out_fname = '/tmp/chart03.{}'.format(gformat)
    plt.savefig( "/tmp/"+dst_chartfile, dpi=144, facecolor='w', edgecolor='w',
            transparent=False, bbox_inches=None, pad_inches=0.1, format=gformat,
            frameon=None)

    os.system( 'cp /tmp/'+dst_chartfile+' ../images/' )

print( form_BA )

##-- get CSV result
#tFile = open( dst_file ,'r')
#buf = tFile.read()
#print( "<br><pre>"+buf+"</pre>")

ra_str = os.getenv('REMOTE_ADDR')
ua_str = os.getenv('HTTP_USER_AGENT')
tStr = "SERVER {};<br>HTTP_USER_AGENT {}; ".format( ra_str, ua_str )
print( "<pre>"+tStr+"</pre>")

print( form_Trailer )


