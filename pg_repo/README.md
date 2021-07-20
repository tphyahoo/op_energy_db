## Postgresql Construction for OP_ENERGY Calculator ##

This setup builds an analytics environment in PostgreSQL
and python3.   Prerequisites  (will change)

* Postgres installed on a suitable host *nix, prefer pg vers 12+

* `SETUP` linux user  $NIXUSER;  postgres role  $PGROLE   (below) 

* Regenerate chain data from base block using a live node feed  OR
   read a seed data file -> btcdata_0000000000.tgz   where 00 is unixtime

* data_dir/ contains a data file and a checksum file;  

      export SRC_DDIR=/var/local/opdev/  

* execute a non-privelaged driver script to build a minimal OP_ENERGY calculator

      ./import_from_blockchain.sh

`TODO` pass PGROLE and NIXUSER as env vars
`TODO` add additional historical data, better automation of init  
`TODO` modify postgresql.conf to enable connection logging


### Create Test Db, Restore from backup ###

Debian/Ubuntu bash --  add linux user thartman to group sudo

    $ sudo adduser thartman sudo
    $ sudo su postgres -c 'createdb thartman_op_energy_db'
    $ sudo su postgres -c 'pg_restore -d thartman_op_energy_db op_energy_db_v0-02.dump'


### Postgres install setup for Debian/Ubuntu OS ###


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
     export HBAPERMSTR="host     all    ${PGROLE}      127.0.0.1/32   trust"
     ## append one rule string+comment lines, to pg_hba.conf  
     ##  TODO insert earlier in the pg_hba.conf order of rules, last is less useful
     echo '' | sudo tee -a ${PGHBA}
     echo '##------------------' | sudo tee -a ${PGHBA}
     echo $HBAPERMSTR | sudo tee -a ${PGHBA}
     echo '' | sudo tee -a ${PGHBA}

     ##--------------------------------------------------------
     sudo adduser --gecos "" --disabled-password ${NIXUSER}
     sudo chpasswd <<<"${NIXUSER}:${NIX_PASS}"

     sudo service postgresql restart

     ## note that DB user postgres is more powerful than superuser, in the postgres internal system
     ##  note that there is an alternate method that does not require superuser for the pg client role
     ##   a template1 database could be available that includes plpython3u, then that template1 can be copied 
     
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


