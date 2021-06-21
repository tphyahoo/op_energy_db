## Postgresql Construction for OP_ENERGY Calculator ##

This setup builds an analytics environment in PostgreSQL
and python3.   Prerequisites  (will change)

* Postgresql installed on a suitable host *nix, prefer v12+

* Assumes:  Linux user opdev;  Postgresql role opdev 

* data file btcdata_0000000000.tgz where 00 is unixtime

* data dir contains data file and checksum  

* execute these driver scripts to build a minimal OP_ENERGY calculator


    import_from_blockchain.sh

    SRC_DDIR=/var/local/opdev/
    SRC_DATAFILE=btcdata_1600585200.tgz
    SRC_MD5SUM=$SRC_DATAFILE.md5sum


--
TBD includes additional historical data, automation of init
