openoni Ubuntu
==============

The following are instructions for installing system level dependencies on Ubuntu:

    sudo apt-get install python-dev python-virtualenv mysql-server libmysqlclient-dev apache2 libapache2-mod-wsgi jetty openjdk-6-jdk libxml2-dev libxslt-dev libjpeg-dev git-core graphicsmagick

When you install mysql-server, you will be prompted for a root password. If you choose one, make a note of what it is. Later you will be asked to enter the password when you create the database for the project.

Get openoni
-----------

Next you need to get the openoni code:

    sudo mkdir /opt/openoni
    sudo chown $USER:users /opt/openoni
    git clone https://github.com/LibraryOfCongress/openoni.git /opt/openoni

Configure Solr
--------------

Download Solr from a mirror site

    wget http://archive.apache.org/dist/lucene/solr/4.4.0/solr-4.4.0.tgz
    tar zxvf solr-4.4.0.tgz
    sudo mv solr-4.4.0/example/ /opt/solr

    sudo useradd -d /opt/solr -s /bin/bash solr
    sudo chown solr:solr -R /opt/solr
    
    sudo cp /opt/openoni/conf/jetty7.sh /etc/init.d/jetty
    sudo chmod +x /etc/init.d/jetty

    sudo cp /opt/openoni/conf/schema.xml /opt/solr/solr/collection1/conf/schema.xml
    sudo cp /opt/openoni/conf/solrconfig.xml /opt/solr/solr/collection1/conf/solrconfig.xml

    sudo cp /opt/openoni/conf/jetty-ubuntu /etc/default/jetty
    sudo service jetty start

Configure Apache
----------------

    sudo a2enmod cache expires rewrite disk_cache
    sudo cp /opt/openoni/conf/openoni.conf /etc/apache2/sites-available/openoni
    sudo a2ensite openoni
    sudo install -o $USER -g users -d /opt/openoni/static
    sudo install -o $USER -g users -d /opt/openoni/.python-eggs
    sudo service apache2 reload

Continue
--------

* You can now return to the Install section in [README.md](https://github.com/LibraryOfCongress/openoni/blob/master/README.md#install)
