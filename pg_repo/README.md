## Postgresql Construction for OP_ENERGY Calculator ##

This setup builds an analytics environment in PostgreSQL
and python3.   Prerequisites  (will change)

* Postgresql installed on a suitable host *nix, prefer v12+

* SETUP:  Linux user opdev;  Postgresql role opdev 

* Regenerate data from base block using a live node OR
   use a data file seed -> filename btcdata_0000000000.tgz where 00 is unixtime

* data dir contains data file and checksum  

* execute these driver scripts to build a minimal OP_ENERGY calculator

    import_from_blockchain.sh

    SRC_DDIR=/var/local/opdev/
    SRC_DATAFILE=btcdata_1600585200.tgz
    SRC_MD5SUM=$SRC_DATAFILE.md5sum


--
TBD includes additional historical data, automation of init

## Create Test Db, Restore from backup ##

for making thartman sudo

    $ sudo adduser thartman sudo
    $ sudo su postgres -c 'createdb thartman_op_energy_db'
    $ sudo su postgres -c 'pg_restore -d thartman_op_energy_db op_energy_db_v0-02.dump'


postgres install setup NOTES


     # DB is created in the current locale, which was reset to "C". Put it
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

     apt-get install --yes postgresql postgresql-all   ## use default version for OS 

     service postgresql start
     sudo -u postgres createuser --superuser $USER_NAME
     echo "alter role \"${USER_NAME}\" with password 'user'" > /tmp/build_postgres.sql
     sudo -u postgres psql -f /tmp/build_postgres.sql

     #add a gratuitous db called user to avoid psql inconveniences
     sudo -u ${USER_NAME} createdb -E UTF8 $USER_NAME
     sudo -u "${USER_NAME}" psql -d "${USER_NAME}" -c 'VACUUM ANALYZE;'
     sudo -u "${USER_NAME}" psql -d "${USER_NAME}" -c 'create extension plpython3u;'

     sudo echo 'host    all  '${USER_NAME}'    127.0.0.1/32  md5' >> /path/to/pg_hba.conf
