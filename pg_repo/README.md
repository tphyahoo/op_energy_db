## Postgresql Construction for OP_ENERGY Calculator ##

This setup builds an analytics environment in PostgreSQL
and python3.   Prerequisites  (will change)

* Postgresql installed on a suitable host *nix, prefer v12+

* SETUP:  Linux user opdev;  Postgresql role opdev  (below) 

* Regenerate data from base block using a live node OR
   use a data file seed -> filename btcdata_0000000000.tgz where 00 is unixtime

* data dir/ contains a data file and a checksum file  

* execute these driver scripts to build a minimal OP_ENERGY calculator


     ./import_from_blockchain.sh


`TBD` add additional historical data, better automation of init


### Create Test Db, Restore from backup ###

Debian/Ubuntu bash --  add linux user thartman to group sudo

    $ sudo adduser thartman sudo
    $ sudo su postgres -c 'createdb thartman_op_energy_db'
    $ sudo su postgres -c 'pg_restore -d thartman_op_energy_db op_energy_db_v0-02.dump'


### Postgres install setup ###


     # OPTIONAL encoding setup for sorting order and string formatting
     # DB is created in the current locale, which might be reset to "C". Put it
     #  back to UTF so the templates will be created using UTF8 encoding.
     unset LC_ALL
     update-locale LC_ALL=en_US.UTF-8
     export LC_NUMERIC="en_US.UTF-8"
     export LC_TIME="en_US.UTF-8"
     export LC_MONETARY="en_US.UTF-8"
     export LC_PAPER="en_US.UTF-8"
     export LC_NAME="en_US.UTF-8"
     export LC_ADDRESS="en_US.UTF-8"
     export LC_TELEPHONE="en_US.UTF-8"
     export LC_MEASUREMENT="en_US.UTF-8"
     export LC_IDENTIFICATION="en_US.UTF-8"

     sudo apt-get install --yes postgresql postgresql-all   ## use default version for OS 
 
     ##-------------------------------------------------
     export PGROLE=pgopdev
     export NIXUSER=opdev
     export NIX_PASS=neveropdev

     export PGVERS=13
     export PGHBA=/etc/postgresql/${PGVERS}/main/pg_hba.conf
     export TS="host     all    ${PGROLE}      127.0.0.1/32   trust"

     echo '' | sudo tee -a ${PGHBA}
     echo '##------------------' | sudo tee -a ${PGHBA}
     echo $TS | sudo tee -a ${PGHBA}
     echo '' | sudo tee -a ${PGHBA}

     ##--------------------------------------------------------
     sudo adduser --gecos "" --disabled-password ${NIXUSER}
     sudo chpasswd <<<"${NIXUSER}:${NIX_PASS}"

     sudo service postgresql restart

     ## note that DB user postgres is more powerful than superuser, in the postgres internal system
     ##  also note that a template1 with plpython3 can be copied instead 
     psql -c "create role ${PGROLE} with superuser createdb login password 'pass'"

     ##-------------------------------------
     export DBNAME=op_energy_db   ## note- match  $PGDATABASE  install_from_blockchain.sh

     sudo -u postgres  createdb -E UTF8 ${DBNAME}
     sudo -u postgres  psql -c 'alter database '$DBNAME' owner to '$PGROLE' '
     sudo -u postgres  psql -d ${DBNAME} -c 'create extension plpython3u;'
     sudo -u postgres  psql -d ${DBNAME} -c 'VACUUM ANALYZE;'


DBNAME is now available to connect via python psycopg2 

     import psycopg2

     conn = psycopg2.connect( "dbname=op_energy_db user=pgopdev host=localhost password=pass" )
     curs = conn.cursor()
     res = curs.execute('select 1')
     curs.fetchone()


