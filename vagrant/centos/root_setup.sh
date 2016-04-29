#!/usr/bin/env bash

# install Python 2.7
rpm -Uvh https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm
rpm -Uvh http://dl.iuscommunity.org/pub/ius/stable/CentOS/6/x86_64/ius-release-1.0-14.ius.centos6.noarch.rpm
yum -y install python27
yum -y install python27-devel python27-setuptools

easy_install-2.7 pip
pip2.7 install virtualenv

yum -y install mysql-server mysql-devel gcc libxml2-devel libxslt-devel libjpeg-devel zlib-devel java-1.7.0-openjdk-devel git

yum -y install GraphicsMagick

CHRONAM_HOME=/opt/chronam
SOLR_HOME=/opt/solr

# install Solr
useradd -d /opt/solr -s /bin/bash solr

# Solr 4.10.4
wget http://archive.apache.org/dist/lucene/solr/4.10.4/solr-4.10.4.tgz
tar zxvf solr-4.10.4.tgz
install -d -o vagrant -g vagrant -m 755 /opt/solr
mv solr-4.10.4/example/* /opt/solr/
cp $CHRONAM_HOME/conf/schema.xml $SOLR_HOME/solr/collection1/conf/schema.xml
cp $CHRONAM_HOME/conf/solrconfig.xml $SOLR_HOME/solr/collection1/conf/solrconfig.xml
cp $CHRONAM_HOME/conf/jetty-logging.xml $SOLR_HOME/etc/jetty-logging.xml
chown solr:solr -R $SOLR_HOME

# Jetty for Solr
cp $CHRONAM_HOME/conf/jetty7.sh /etc/init.d/jetty
chmod +x /etc/init.d/jetty
cp $CHRONAM_HOME/conf/jetty-redhat /etc/default/jetty
# replace "-Xms2g -Xmx2g" with "-Xms256m -Xmx256m" because 2g is too large for dev VM
sed -i -- 's/-Xms2g -Xmx2g/-Xms256m -Xmx256m/g' /etc/default/jetty

chkconfig --levels 235 jetty on
service jetty start

# start MySQL
chkconfig --levels 235 mysqld on
service mysqld start