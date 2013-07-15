chronam Ubuntu
==============

The following are instructions for installing system level dependencies on Ubuntu:

    sudo apt-get install python-dev python-virtualenv mysql-server libmysqlclient-dev apache2 libapache2-mod-wsgi jetty openjdk-6-jdk libxml2-dev libxslt-dev libjpeg-dev git-core graphicsmagick

When you install mysql-server, you will be prompted for a root password. If you choose one, make a note of what it is. Later you will be asked to enter the password when you create the database for the project.

Get chronam
-----------

Next you need to get the chronam code:

    sudo mkdir /opt/chronam
    sudo chown $USER:users /opt/chronam
    git clone https://github.com/LibraryOfCongress/chronam.git /opt/chronam

Configure Solr
--------------

Download Solr from a mirror site

    wget http://apache.mirrors.lucidnetworks.net/lucene/solr/4.3.1/solr-4.3.1.tgz
    tar zxvf solr-4.3.1.tgz
    mv solr-4.3.1/example/ /opt/solr-4.3.1

    useradd -d /opt/solr-4.3.1 -s /bin/bash solr
    chown solr:solr -R /opt/solr-4.3.1

    sudo cp /opt/chronam/conf/schema.xml /opt/solr-4.3.1/solr/collection1/conf/schema.xml
    sudo cp /opt/chronam/conf/solrconfig-4.3.0.xml /opt/solr-4.3.1/solr/collection1/conf/solrconfig.xml

    sudo cp /opt/chronam/conf/jetty-ubuntu /etc/default/jetty
    sudo service jetty start

Configure Apache
----------------

    sudo a2enmod cache expires rewrite disk_cache
    sudo cp /opt/chronam/conf/chronam.conf /etc/apache2/sites-available/chronam
    sudo a2ensite chronam
    sudo install -o $USER -g users -d /opt/chronam/static
    sudo install -o $USER -g users -d /opt/chronam/.python-eggs
    sudo service apache2 reload

Continue
--------

* You can now return to the Install section in [README.md](https://github.com/LibraryOfCongress/chronam/blob/master/README.md#install)
