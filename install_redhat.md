openoni Redhat
==============

The following are instructions for installing system level dependencies on
RHEL, tested with Red Hat Enterprise Linux Server release 6.4 (Santiago).

Enable Extra Packages if you need to (for example, you're using RHEL6 on EC2:

    sudo rpm -Uvh http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-8.noarch.rpm

Install system dependencies:

    sudo yum install mysql-server mysql-devel httpd python-virtualenv gcc libxml2-devel libxslt-devel libjpeg-devel zlib-devel mod_wsgi java-1.6.0-openjdk-devel git

When you install mysql-server, you will be prompted for a root password. If
you choose one, make a note of what it is. Later you will be asked to enter
the password when you create the database for the project.

Get openoni
-----------

    sudo mkdir /opt/openoni
    sudo chown $USER:users /opt/openoni
    git clone https://github.com/LibraryOfCongress/openoni.git /opt/openoni

Configure Solr
--------------

Download solr from a mirror site (tested with Solr 4.3 and 4.4, get the latest version)

    wget http://archive.apache.org/dist/lucene/solr/4.4.0/solr-4.4.0.tgz
    tar zxvf solr-4.4.0.tgz
    sudo mv solr-4.4.0/example/ /opt/solr/
    sudo cp /opt/openoni/conf/schema.xml /opt/solr/solr/collection1/conf/schema.xml
    sudo cp /opt/openoni/conf/solrconfig.xml /opt/solr/solr/collection1/conf/solrconfig.xml

Update the dataDir field in /opt/solr/solr/conf/solrconfig.xml and
point to a directory for where the solr index will live.

    sudo useradd -d /opt/solr -s /bin/bash solr
    sudo chown solr:solr -R /opt/solr

    sudo cp /opt/openoni/conf/jetty7.sh /etc/init.d/jetty
    sudo chmod +x /etc/init.d/jetty

The jetty-redhat config file contains a default heap space allocation- "-Xms2g -Xmx2g".  Change the 2g 
to a sensible default for your system if 2g is too much or too little.

    sudo cp /opt/openoni/conf/jetty-redhat /etc/default/jetty
    sudo cp /opt/openoni/conf/jetty-logging.xml /opt/solr/etc/jetty-logging.xml

    sudo service jetty start

Configure Image Rendering:
--------------------------

If you have the Aware JPEG 2000 library this is how you install it:

    wget --no-check-certificate --http-user your-username --http-password your-password https://svn.rdc.lctl.gov/svn/ndnp/third-party/j2k-3.18.9-linux-x86-64.tar.gz
    tar -zxvf j2k-3.18.9-linux-x86-64.tar.gz
    sudo cp j2k-3.18.9-linux-x86-64/include/* /usr/local/include/
    sudo cp j2k-3.18.9-linux-x86-64/lib/libawj2k.so.2.0.1 /usr/local/lib/
    sudo ln -s /usr/local/lib/libawj2k.so.2.0.1 /usr/local/lib/libawj2k.so
    sudo echo "/usr/local/lib" > /etc/ld.so.conf.d/aware.so.conf
    sudo ldconfig /usr/local/lib/

If not, install GraphicsMagick:

    sudo yum install GraphicsMagick

Configure Apache
----------------

    sudo cp /opt/openoni/conf/openoni.conf /etc/httpd/conf.d/openoni.conf
    sudo install -o `whoami` -g users -d /opt/openoni/static
    sudo install -o `whoami` -g users -d /opt/openoni/.python-eggs

Update the KeepAlive directive in /etc/httpd/conf/httpd.conf config from 'Off' 
to 'On'. If you are the Library of Congress you will also want to canonicalize 
URLs that used by the Chronicling America application at the Library of Congress:

    sudo cp /opt/openoni/conf/openoni-canonical.conf /etc/httpd/conf.d/


Continue
--------

* You can now return to the Install section in [README.md](https://github.com/LibraryOfCongress/openoni/blob/master/README.md#install)
