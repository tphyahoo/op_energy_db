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
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: histprice; Type: SCHEMA; Schema: -; Owner: opdev
--

CREATE SCHEMA histprice;


ALTER SCHEMA histprice OWNER TO opdev;


--
-- Name: in_bitfinex; Type: TABLE; Schema: histprice; Owner: opdev
--

CREATE TABLE histprice.in_bitfinex (
    timestamp7 integer,
    interval7 integer,
    open7 double precision,
    high7 double precision,
    low7 double precision,
    close7 double precision,
    volume7 double precision
);


ALTER TABLE histprice.in_bitfinex OWNER TO opdev;

--
-- Name: TABLE in_bitfinex; Type: COMMENT; Schema: histprice; Owner: opdev
--

COMMENT ON TABLE histprice.in_bitfinex IS 'Bitfinex 1364774820-1603583940 60 1m.csv';


--
-- Name: in_bitfloor; Type: TABLE; Schema: histprice; Owner: opdev
--

CREATE TABLE histprice.in_bitfloor (
    timestamp7 integer,
    interval7 integer,
    open7 double precision,
    high7 double precision,
    low7 double precision,
    close7 double precision,
    volume7 double precision
);


ALTER TABLE histprice.in_bitfloor OWNER TO opdev;

--
-- Name: TABLE in_bitfloor; Type: COMMENT; Schema: histprice; Owner: opdev
--

COMMENT ON TABLE histprice.in_bitfloor IS 'Bitfloor 1337780160-1366236000 60 1m.csv';


--
-- Name: in_bitstamp; Type: TABLE; Schema: histprice; Owner: opdev
--

CREATE TABLE histprice.in_bitstamp (
    timestamp7 integer,
    interval7 integer,
    open7 double precision,
    high7 double precision,
    low7 double precision,
    close7 double precision,
    volume7 double precision
);


ALTER TABLE histprice.in_bitstamp OWNER TO opdev;

--
-- Name: TABLE in_bitstamp; Type: COMMENT; Schema: histprice; Owner: opdev
--

COMMENT ON TABLE histprice.in_bitstamp IS 'Bitstamp 1315921980-1603583940 60 1m.csv';


--
-- Name: in_mtgox; Type: TABLE; Schema: histprice; Owner: opdev
--

CREATE TABLE histprice.in_mtgox (
    timestamp7 integer,
    interval7 integer,
    open7 double precision,
    high7 double precision,
    low7 double precision,
    close7 double precision,
    volume7 double precision
);


ALTER TABLE histprice.in_mtgox OWNER TO opdev;

--
-- Name: TABLE in_mtgox; Type: COMMENT; Schema: histprice; Owner: opdev
--

COMMENT ON TABLE histprice.in_mtgox IS 'www.drgs.no/Bitcoin-Historical-Data/Mt. Gox/Mt. Gox 1279408140-1393293540 60 1m.csv';


--
-- Name: in_tradehill; Type: TABLE; Schema: histprice; Owner: opdev
--

CREATE TABLE histprice.in_tradehill (
    timestamp7 integer,
    interval7 integer,
    open7 double precision,
    high7 double precision,
    low7 double precision,
    close7 double precision,
    volume7 double precision
);


ALTER TABLE histprice.in_tradehill OWNER TO opdev;

--
-- Name: TABLE in_tradehill; Type: COMMENT; Schema: histprice; Owner: opdev
--

COMMENT ON TABLE histprice.in_tradehill IS 'Tradehill 1307563920-1329171960 60 1m.csv';



--
-- Name: view0_bitfinex_hist; Type: VIEW; Schema: public; Owner: opdev
--

CREATE VIEW histprice.view0_bitfinex_hist AS
 SELECT (to_timestamp((in_bitfinex.timestamp7)::double precision))::timestamp without time zone AS rowtime,
    in_bitfinex.open7,
    in_bitfinex.high7,
    in_bitfinex.low7,
    in_bitfinex.close7,
    in_bitfinex.volume7
   FROM histprice.in_bitfinex;


ALTER TABLE histprice.view0_bitfinex_hist OWNER TO opdev;

--
-- Name: view0_bitfloor_hist; Type: VIEW; Schema: public; Owner: opdev
--

CREATE VIEW histprice.view0_bitfloor_hist AS
 SELECT (to_timestamp((in_bitfloor.timestamp7)::double precision))::timestamp without time zone AS rowtime,
    in_bitfloor.open7,
    in_bitfloor.high7,
    in_bitfloor.low7,
    in_bitfloor.close7,
    in_bitfloor.volume7
   FROM histprice.in_bitfloor;


ALTER TABLE histprice.view0_bitfloor_hist OWNER TO opdev;

--
-- Name: view0_bitstamp_hist; Type: VIEW; Schema: public; Owner: opdev
--

CREATE VIEW histprice.view0_bitstamp_hist AS
 SELECT (to_timestamp((in_bitstamp.timestamp7)::double precision))::timestamp without time zone AS rowtime,
    in_bitstamp.open7,
    in_bitstamp.high7,
    in_bitstamp.low7,
    in_bitstamp.close7,
    in_bitstamp.volume7
   FROM histprice.in_bitstamp;


ALTER TABLE histprice.view0_bitstamp_hist OWNER TO opdev;

--
-- Name: view0_mtgox_hist; Type: VIEW; Schema: public; Owner: opdev
--

CREATE VIEW histprice.view0_mtgox_hist AS
 SELECT (to_timestamp((in_mtgox.timestamp7)::double precision))::timestamp without time zone AS rowtime,
    in_mtgox.open7,
    in_mtgox.high7,
    in_mtgox.low7,
    in_mtgox.close7,
    in_mtgox.volume7
   FROM histprice.in_mtgox;


ALTER TABLE histprice.view0_mtgox_hist OWNER TO opdev;

--
-- Name: view0_tradehill_hist; Type: VIEW; Schema: public; Owner: opdev
--

CREATE VIEW histprice.view0_tradehill_hist AS
 SELECT (to_timestamp((in_tradehill.timestamp7)::double precision))::timestamp without time zone AS rowtime,
    in_tradehill.open7,
    in_tradehill.high7,
    in_tradehill.low7,
    in_tradehill.close7,
    in_tradehill.volume7
   FROM histprice.in_tradehill;


ALTER TABLE histprice.view0_tradehill_hist OWNER TO opdev;

