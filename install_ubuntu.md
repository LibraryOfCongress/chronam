# chronam Ubuntu

The following are instructions for installing system level dependencies on Ubuntu:

    sudo apt-get install python-dev python-virtualenv mysql-server libmysqlclient-dev apache2 libapache2-mod-wsgi libapache2-mod-xsendfile jetty openjdk-8-jdk libxml2-dev libxslt-dev libjpeg-dev git-core graphicsmagick

When you install mysql-server, you will be prompted for a root password. If you choose one, make a note of what it is. Later you will be asked to enter the password when you create the database for the project.

## Get chronam

Next you need to get the chronam code:

    sudo mkdir /opt/chronam
    sudo chown $USER:users /opt/chronam
    git clone https://github.com/LibraryOfCongress/chronam.git /opt/chronam

## Configure Solr

Download Solr from a mirror site

    wget https://archive.apache.org/dist/lucene/solr/4.10.4/solr-4.10.4.tgz
    tar zxvf solr-4.10.4.tgz
    sudo mv solr-4.10.4/example/ /opt/solr

    sudo useradd -d /opt/solr -s /bin/bash solr
    sudo chown solr:solr -R /opt/solr

    sudo cp /opt/chronam/conf/jetty7.sh /etc/init.d/jetty
    sudo chmod +x /etc/init.d/jetty

    sudo cp /opt/chronam/solr/conf/schema.xml /opt/solr/solr/collection1/conf/schema.xml
    sudo cp /opt/chronam/solr/conf/solrconfig.xml /opt/solr/solr/collection1/conf/solrconfig.xml

    sudo mkdir -p /opt/solr/contrib
    sudo wget --output-document=/opt/solr/contrib/lucene-analyzers-stempel-4.10.4.jar https://repo1.maven.org/maven2/org/apache/lucene/lucene-analyzers-stempel/4.10.4/lucene-analyzers-stempel-4.10.4.jar
    sudo wget --output-document=/opt/solr/solr/collection1/conf/lang/stopwords_pl.txt https://raw.githubusercontent.com/apache/lucene-solr/master/lucene/analysis/stempel/src/resources/org/apache/lucene/analysis/pl/stopwords.txt"

    sudo cp /opt/chronam/conf/jetty-ubuntu /etc/default/jetty
    sudo service jetty start

## Configure Apache

    sudo a2enmod cache expires rewrite disk_cache
    sudo cp /opt/chronam/conf/chronam.conf /etc/apache2/sites-available/chronam
    sudo a2ensite chronam
    sudo install -o $USER -g users -d /opt/chronam/static
    sudo install -o $USER -g users -d /opt/chronam/.python-eggs
    sudo service apache2 reload

## Continue

-   You can now return to the Install section in [README.md](README.md#install)
