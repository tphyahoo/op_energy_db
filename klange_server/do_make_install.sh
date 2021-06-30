#!/bin/bash

INSTALL_DIR=/var/local/opdev
mkdir -p ${INSTALL_DIR}


cd cgiserver ; rm -f cgiserver
make || exit
cp -f cgiserver  ${INSTALL_DIR}
cd ..

mkdir -p  ${INSTALL_DIR}/pages/bin
mkdir -p  ${INSTALL_DIR}/pages/images

cp -Ra dev_cgi/*html  ${INSTALL_DIR}/pages/

cp -a dev_cgi/aconcagua.py ${INSTALL_DIR}/pages/bin/
cp -a dev_cgi/calcops_c3.py ${INSTALL_DIR}/pages/bin/

chmod 500 ${INSTALL_DIR}/pages/bin    ## TODO strategy

