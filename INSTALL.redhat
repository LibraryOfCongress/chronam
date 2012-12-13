============
Installation
============

# Installation instructions for building Chronicling America on RedHat EL6. 
# First you'll need to get the latest Chronicling America code. Which
# will include this file.

System Dependencies
===================

sudo yum install mysql-server mysql-devel httpd python-virtualenv gcc libxml2-devel libxslt-devel libjpeg-devel zlib-devel mod_wsgi java-1.6.0-openjdk-devel git

# Note: When you install mysql-server, you will be prompted for a root 
# password. If you choose one, make a note of what it is. Later you will be 
# asked to enter the password when you create the database for the project.

Get Chronam
===========

mkdir /opt/chronam
git clone https://github.com/LibraryOfCongress/chronam.git /opt/chronam
export CHRONAM_HOME=/opt/chronam
cd ${CHRONAM_HOME}


Create Database
===============

cp ${CHRONAM_HOME}/conf/my.cnf /etc/my.cnf

sudo service mysqld start

echo "DROP DATABASE IF EXISTS chronam; CREATE DATABASE chronam CHARACTER SET utf8; GRANT ALL ON chronam.* to 'chronam'@'localhost' identified by 'pick_one'; GRANT ALL ON test_chronam.* TO 'chronam'@'localhost' identified by 'pick_one';" | mysql -u root -p


Configure Solr
==============

wget http://archive.apache.org/dist/lucene/solr/1.4.1/apache-solr-1.4.1.tgz
gunzip apache-solr-1.4.1.tgz
tar xvf apache-solr-1.4.1.tar
mv apache-solr-1.4.1/example/ /opt/solr-1.4.1

cp ${CHRONAM_HOME}/conf/schema.xml /opt/solr-1.4.1/solr/conf/schema.xml
cp ${CHRONAM_HOME}/conf/stopwords_* /opt/solr-1.4.1/solr/conf/
cp ${CHRONAM_HOME}/conf/solrconfig-centos.xml /opt/solr-1.4.1/solr/conf/solrconfig.xml

# Update the dataDir field in /opt/solr-1.4.1/solr/conf/solrconfig.xml and point to a directory for
# where the solr index will live.

useradd -d /opt/solr-1.4.1 -s /bin/bash solr
chown solr:solr -R /opt/solr-1.4.1

cp ${CHRONAM_HOME}/conf/jetty6.sh /etc/init.d/jetty
chmod +x /etc/init.d/jetty

cp ${CHRONAM_HOME}/conf/jetty /etc/default/
cp ${CHRONAM_HOME}/conf/jetty-logging.xml /opt/solr-1.4.1/etc/jetty-logging.xml

sudo service jetty start


Configure Aware
===============

wget --no-check-certificate --http-user your-username --http-password your-password https://rdc.lctl.gov/svn/ndnp/third-party/j2k-3.18.9-linux-x86-64.tar.gz

tar -zxvf j2k-3.18.9-linux-x86-64.tar.gz

sudo cp j2k-3.18.9-linux-x86-64/include/* /usr/local/include/
sudo cp j2k-3.18.9-linux-x86-64/lib/libawj2k.so.2.0.1 /usr/local/lib/
sudo ln -s /usr/local/lib/libawj2k.so.2.0.1 /usr/local/lib/libawj2k.so

sudo echo "/usr/local/lib" > /etc/ld.so.conf.d/aware.so.conf
sudo ldconfig /usr/local/lib/


Configure Apache
================

sudo cp ${CHRONAM_HOME}/conf/chronam.conf /etc/httpd/conf.d/chronam.conf

# The following line is only for the production box which adds the
# redirect to canonical URL:
sudo cp ${CHRONAM_HOME}/conf/chronam-canonical.conf /etc/httpd/conf.d/

sudo install -o `whoami` -g users -d ${CHRONAM_HOME}/static
sudo install -o `whoami` -g users -d ${CHRONAM_HOME}/.python-eggs

# Update the KeepAlive directive in the apache config from 'Off' to 'On':
/etc/httpd/conf/httpd.conf # KeepAlive On

Configure Chronam
=================

virtualenv --no-site-packages ${CHRONAM_HOME}/ENV
source ${CHRONAM_HOME}/ENV/bin/activate
pip install virtualenvwrapper
source ${CHRONAM_HOME}/ENV/bin/virtualenvwrapper.sh
add2virtualenv /opt
export DJANGO_SETTINGS_MODULE=chronam.settings

# install python dependencies
pip install -r requirements.pip

# create directories for data
mkdir ${CHRONAM_HOME}/data/batches
mkdir ${CHRONAM_HOME}/data/cache
mkdir ${CHRONAM_HOME}/data/bib

# create settings file, and set the mysql username/password
cp ${CHRONAM_HOME}/settings_template.py ${CHRONAM_HOME}/settings.py

# Update the settings.py file with necessary settings for the machine

# set up the database and load initial data
django-admin.py syncdb --noinput --migrate
django-admin.py chronam_sync

# collect that static files where apache can serve them up; needed for
# the case where DEBUG=False

django-admin.py collectstatic


Start Up Chronicling America
============================

sudo service httpd restart


Get Sample Data / Run Unit Tests
================================

# Sample data set 1: batch_vi_affirmed_ver01
# The first dataset is provided to be a quick and easy download in order for you to understand how the project works.
cd ${CHRONAM_HOME}/data/batches
wget --recursive --no-host-directories --cut-dirs 1 --include-directories /data/vi/batch_vi_affirmed_ver01 http://chroniclingamerica.loc.gov/data/vi/batch_vi_affirmed_ver01

# Sample data set 2: batch_dlc_jamaica_ver01
# The second dataset is provided to run tests against.
# Beware this will pull down 60G of data, which could take hours to days to download depending on your connection speed.
# Make sure you have a stable connection and enough room on your harddrive.
cd ${CHRONAM_HOME}/data/batches
wget --recursive --no-host-directories --cut-dirs 1 --include-directories /data/dlc/batch_dlc_jamaica_ver01 http://chroniclingamerica.loc.gov/data/dlc/batch_dlc_jamaica_ver01


Run Unit Tests
==============

# Currently chronam.core.tests.batch_loader_tests.BatchLoaderTest checks batch_dlc_jamaica_ver01
# If you grabbed the smaller sample set, the tests will fail.
django-admin.py test core


Loading the Data
================

sudo install -o `whoami` -g users -d ${CHRONAM_HOME}/logs/
cd ${CHRONAM_HOME}/logs/

# or load a specific batch, replace $BATCH_NAME with a specific batch.
django-admin.py load_batch $BATCH_NAME
# Example: django-admin.py load_batch batch_vi_affirmed_ver01

# load up links to flickr using your flickr key
django-admin.py flickr $YOUR_FLICKR_KEY
