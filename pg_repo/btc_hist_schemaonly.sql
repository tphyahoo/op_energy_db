--
-- PostgreSQL database dump
--

-- Dumped from database version 12.6 (Debian 12.6-1.pgdg100+1)
-- Dumped by pg_dump version 12.6 (Debian 12.6-1.pgdg100+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', true);  -- dbb true
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: plpython3u; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS plpython3u WITH SCHEMA pg_catalog;

--
-- Name: EXTENSION plpython3u; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpython3u IS 'PL/Python3U untrusted procedural language';

--
-- Name: bigint_to_hexstr(bigint); Type: FUNCTION; Schema: public; Owner: opdev
--

CREATE FUNCTION public.bigint_to_hexstr(bigint) RETURNS text
    LANGUAGE plpython3u
    AS $$
  tBInt = args[0]
  return  hex(tBInt)
$$;


ALTER FUNCTION public.bigint_to_hexstr(bigint) OWNER TO opdev;

--
-- Name: calculate_energy_price(integer, bigint, bigint, text, integer, bigint, bigint, text); Type: FUNCTION; Schema: public; Owner: opdev
--

CREATE FUNCTION public.calculate_energy_price(blka_height integer, blka_median_time bigint, blka_chain_reward bigint, blka_chainwork_hex text, blkb_height integer, blkb_median_time bigint, blkb_chain_reward bigint, blkb_chainwork_hex text) RETURNS text
    LANGUAGE plpython3u IMMUTABLE
    AS $$
  ##  assume blkB height > blkA height
  hash_cnt      = int( blkb_chainwork_hex,base=16) - int( blka_chainwork_hex,base=16)
  expected_secs = 600 * ( blkb_height - blka_height )
  actual_secs   = blkb_median_time - blka_median_time
  sats          = blkb_chain_reward - blka_chain_reward

  price_prime,elem  = divmod( (hash_cnt * expected_secs),(actual_secs*sats) )
  return  str(price_prime)

$$;


ALTER FUNCTION public.calculate_energy_price(blka_height integer, blka_median_time bigint, blka_chain_reward bigint, blka_chainwork_hex text, blkb_height integer, blkb_median_time bigint, blkb_chain_reward bigint, blkb_chainwork_hex text) OWNER TO opdev;

--
-- Name: calculate_energy_price_print(integer, bigint, bigint, text, integer, bigint, bigint, text); Type: FUNCTION; Schema: public; Owner: opdev
--

CREATE FUNCTION public.calculate_energy_price_print(blka_height integer, blka_median_time bigint, blka_chain_reward bigint, blka_chainwork_hex text, blkb_height integer, blkb_median_time bigint, blkb_chain_reward bigint, blkb_chainwork_hex text) RETURNS text
    LANGUAGE plpython3u IMMUTABLE
    AS $$
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
$$;


ALTER FUNCTION public.calculate_energy_price_print(blka_height integer, blka_median_time bigint, blka_chain_reward bigint, blka_chainwork_hex text, blkb_height integer, blkb_median_time bigint, blkb_chain_reward bigint, blkb_chainwork_hex text) OWNER TO opdev;


--
-- Name: cbits_to_hexstr(text); Type: FUNCTION; Schema: public; Owner: opdev
--
-- BitcoinD ref:
--  https://github.com/bitcoin/bitcoin/blob/master/src/arith_uint256.cpp#L203
--

CREATE FUNCTION public.cbits_to_hexstr(text) RETURNS text
    LANGUAGE plpython3u
    AS $$
  cbits_hex = int( args[0], 16)
  reg_difficulty  = cbits_hex & 0x007FFFFF
  reg_exp_enc = (cbits_hex & 0xFF000000) >> 24

  exp_const = 1 * 2** (8*(reg_exp_enc-3))
  exp_var = reg_difficulty * 2** (8*(reg_exp_enc-3))
  bCnt = (exp_var.bit_length() +7)/8
  return hex(exp_var)
$$;


ALTER FUNCTION public.cbits_to_hexstr(text) OWNER TO opdev;

--
-- Name: uintstr_to_hexstr(text); Type: FUNCTION; Schema: public; Owner: opdev
--

CREATE FUNCTION public.uintstr_to_hexstr(text) RETURNS text
 AS '
  tStr = args[0]
  tStr = tStr.strip( "\"")
  tStr = tStr.lstrip("0")
  return "0x"+tStr
' LANGUAGE plpython3u;

ALTER FUNCTION public.uintstr_to_hexstr(text) OWNER TO opdev;

--
-- Name: fix_quoted_numbers(text); Type: FUNCTION; Schema: public; Owner: opdev
--

CREATE FUNCTION public.fix_quoted_numbers(text) RETURNS text
 AS '
  tStr = args[0]
  return "0x"+tStr.strip("\"")'
LANGUAGE plpython3u;

ALTER FUNCTION public.fix_quoted_numbers(text) OWNER TO opdev;


--
-- Name: hexstr_to_bigint(text); Type: FUNCTION; Schema: public; Owner: opdev
--

CREATE FUNCTION public.hexstr_to_bigint(text) RETURNS bigint
    LANGUAGE plpython3u
    AS $$
  return int( args[0], base=16)
$$;


ALTER FUNCTION public.hexstr_to_bigint(text) OWNER TO opdev;

--
-- Name: hexstr_to_cbits(text); Type: FUNCTION; Schema: public; Owner: opdev
--
-- BitcoinD ref: 
--  https://github.com/bitcoin/bitcoin/blob/master/src/arith_uint256.cpp#L223
--

CREATE FUNCTION public.hexstr_to_cbits(text) RETURNS text
    LANGUAGE plpython3u
    AS $$
    in_str = args[0]
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
$$;


ALTER FUNCTION public.hexstr_to_cbits(text) OWNER TO opdev;

--
-- Name: int_to_hexstr(integer); Type: FUNCTION; Schema: public; Owner: opdev
--

CREATE FUNCTION public.int_to_hexstr(integer) RETURNS text
    LANGUAGE plpython3u
    AS $$
  tBInt = args[0]
  return  hex(tBInt)
$$;


ALTER FUNCTION public.int_to_hexstr(integer) OWNER TO opdev;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
--
-- PostgreSQL database dump complete
--

