
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

