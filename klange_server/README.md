## op_klange server ##

This repo contains a single-file http server in C (klange), and
a directory `dev_cgi`  with executable python, html and other web 
assets. 

BUILD: make or cmake in cgiserver/

INSTALL: content and binary files are copied to a common directory 
         for web access.     $  ./do_make_install.sh


**NOTE**  repo op_klange_server fork @
          commit fdc1c6a2364e31df1a9e2417005a927da81c204b

##  Running op_klange server

Invoke `do_make_install.sh` to build the cgiserver binary and copy
the server binary to a new area `/var/local/opdev/`  (or
any convenient directory and user). Install currently :

    /var/local/opdev
     | cgiserver 
     └── pages/
         ├── bin/
         |     server-apps
         └── images/
               results-cache

There are no configuration files needed but http root is 
a required sub-directory, configured at compile-time.
The default cgiserver htdocs dir is named `pages/` and is internal
to the http server only. A feature has been added to this
`cgiserver` to only allow binary executables in a sub-directory
called `bin/`, and get charts from directory `images/`.

The server network port defaults to 80, and can be changed on
the command line `cgiserver 7888` on port 7888 for example.

In this git repo, the directory `dev_cgi` includes html, 
cgi and other web assets. The install script copies assets
into the new server layout, which is subject to change.

Try this server @   http://dev.bergain.biz:7888/bin/aconcagua.py


