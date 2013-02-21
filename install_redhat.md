chronam Redhat
==============

The following are instructions for installing system level dependencies on 
RHEL.

    sudo yum install mysql-server mysql-devel httpd python-virtualenv gcc libxml2-devel libxslt-devel libjpeg-devel zlib-devel mod_wsgi java-1.6.0-openjdk-devel git

When you install mysql-server, you will be prompted for a root password. If 
you choose one, make a note of what it is. Later you will be asked to enter 
the password when you create the database for the project.

Get chronam
-----------

    sudo mkdir /opt/chronam
    sudo chown $USER:users /opt/chronam
    git clone https://github.com/LibraryOfCongress/chronam.git /opt/chronam

Configure Solr
--------------

    wget http://archive.apache.org/dist/lucene/solr/1.4.1/apache-solr-1.4.1.tgz
    gunzip apache-solr-1.4.1.tgz
    tar xvf apache-solr-1.4.1.tar
    mv apache-solr-1.4.1/example/ /opt/solr-1.4.1

    cp /opt/chronam/conf/schema.xml /opt/solr-1.4.1/solr/conf/schema.xml
    cp /opt/chronam/conf/stopwords* /opt/solr-1.4.1/solr/conf/
    cp /opt/chronam/conf/solrconfig-centos.xml /opt/solr-1.4.1/solr/conf/solrconfig.xml

Update the dataDir field in /opt/solr-1.4.1/solr/conf/solrconfig.xml and 
point to a directory for where the solr index will live.

    useradd -d /opt/solr-1.4.1 -s /bin/bash solr
    chown solr:solr -R /opt/solr-1.4.1

    cp /opt/chronam/conf/jetty6.sh /etc/init.d/jetty
    chmod +x /etc/init.d/jetty

    cp /opt/chronam/conf/jetty /etc/default/
    cp /opt/chronam/conf/jetty-logging.xml /opt/solr-1.4.1/etc/jetty-logging.xml

    sudo service jetty start

Configure Aware
---------------

If you have the Aware JPEG 2000 library this is how you install it:

    wget --no-check-certificate --http-user your-username --http-password your-password https://rdc.lctl.gov/svn/ndnp/third-party/j2k-3.18.9-linux-x86-64.tar.gz
    tar -zxvf j2k-3.18.9-linux-x86-64.tar.gz
    sudo cp j2k-3.18.9-linux-x86-64/include/* /usr/local/include/
    sudo cp j2k-3.18.9-linux-x86-64/lib/libawj2k.so.2.0.1 /usr/local/lib/
    sudo ln -s /usr/local/lib/libawj2k.so.2.0.1 /usr/local/lib/libawj2k.so
    sudo echo "/usr/local/lib" > /etc/ld.so.conf.d/aware.so.conf
    sudo ldconfig /usr/local/lib/

Configure Apache
----------------

    sudo cp /opt/chronam/conf/chronam.conf /etc/httpd/conf.d/chronam.conf
    sudo install -o `whoami` -g users -d /opt/chronam/static
    sudo install -o `whoami` -g users -d /opt/chronam/.python-eggs

Update the KeepAlive directive in /etc/httpd/conf/httpd.conf config from 'Off' 
to 'On'. If you are the Library of Congress you will also want to canonicalize 
URLs that used by the Chronicling America application at the Library of Congress:

    sudo cp /opt/chronam/conf/chronam-canonical.conf /etc/httpd/conf.d/


Continue
--------

* You can now return to the Install section in [README.md](https://github.com/LibraryOfCongress/chronam/blob/master/README.md)
