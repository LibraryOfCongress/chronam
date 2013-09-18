chronam
=======

chronam is the [Django](http://djangoproject.com) application that the 
Library of Congress uses to make its 
[Chronicling America](http://chroniclingamerica.loc.gov) website.
The Chronicling America website makes millions of pages of historic American 
newspapers that have been digitized by the 
[National Digital Newspaper Program (NDNP)](http://www.loc.gov/ndnp/) 
browsable and searchable on the Web. A little bit of background is needed to 
understand why this software is being made available.

NDNP is actually a partnership between the Library of Congress, the 
[National Endowment for the Humanities (NEH)](http://www.neh.gov), and 
cultural heritage organizations
([awardees](http://chroniclingamerica.loc.gov/awardees/)) across the 
United States who have applied for grants to help digitize newspapers 
in their state. Awardees digitize newspaper microfilm according 
to a set of [specifications](http://www.loc.gov/ndnp/guidelines/)
and then ship the data back to the Library of Congress where it is 
loaded into Chronicling America. 

Awardee institutions are able to use this data however
they want, including creating their own websites that highlight their 
newspaper content in the local context of their own collections. The idea of
making chronam available here on Github is to provide a technical option to 
these awardees, or other interested parties who want to make their own websites 
of NDNP newspaper content available. chronam provides a core set of functionality 
for loading, modeling and indexing NDNP data, while allowing you to customize 
the look and feel of the website to suit the needs of your organization. 

The NDNP data is in the Public Domain and is itself [available]
(http://chroniclingamerica.loc.gov/data/batches/) on the Web for anyone to use.
The hope is that the chronam software can be useful for others who want to 
work with and/or publish the content.

Install
-------

System level dependencies can be installed by following these operating system 
specific instructions:

* [install_ubuntu.md](https://github.com/LibraryOfCongress/chronam/blob/master/install_ubuntu.md)
* [install_redhat.md](https://github.com/LibraryOfCongress/chronam/blob/master/install_redhat.md)

After you have installed the system level dependencies you will need to 
install some application specific dependencies, and configure the application.

First you will need to set up the local Python environment and install some
Python dependencies:

    cd /opt/chronam/
    virtualenv ENV
    source /opt/chronam/ENV/bin/activate
    cp conf/chronam.pth ENV/lib/python2.6/site-packages/chronam.pth

(There is another small difference here between RedHat and Ubuntu, you may need to change the 2.6 above to a 2.7)

    pip install -U distribute
    pip install -r requirements.pip

Next you need to create some directories for data:

    mkdir /opt/chronam/data/batches
    mkdir /opt/chronam/data/cache
    mkdir /opt/chronam/data/bib

And you will need a MySQL database. If this is a new server, you will need to
start MySQL and assign it a root password:

    sudo service mysqld start
    /usr/bin/mysqladmin -u root password '' # pick a real password
    
You will probably want to change the password 'pick_one' in the example below
to something else:

    echo "DROP DATABASE IF EXISTS chronam; CREATE DATABASE chronam CHARACTER SET utf8; GRANT ALL ON chronam.* to 'chronam'@'localhost' identified by 'pick_one'; GRANT ALL ON test_chronam.* TO 'chronam'@'localhost' identified by 'pick_one';" | mysql -u root -p

You will need to use the settings template to create your application settings.
Add your database password to the settings.py file:

    cp /opt/chronam/settings_template.py /opt/chronam/settings.py

For Django management commands to work you will need to have the
DJANGO_SETTINGS_MODULE environment variable set. You may want to add 
this to your ~/.profile so you do not need to remember to do it 
everytime you log in.

    export DJANGO_SETTINGS_MODULE=chronam.settings


Next you will need to initialize database schema and load some initial data:

    django-admin.py syncdb --noinput --migrate
    django-admin.py chronam_sync --skip-essays

And finally you will need to collect static files (stylesheets, images) 
for serving up by Apache in production settings:

    django-admin.py collectstatic --noinput

Load Data
--------

As mentioned above, the NDNP data that awardees create and ship to the Library
of Congress is in the public domain and is made available on the Web as 
`batches`. Each batch contains newsaper issues for one or more newspaper 
titles. To use chronam you will need to have some of this batch data to load. If
you are an awardee you probably have this data on hand already, but if not
you can use a tool like [wget](http://www.gnu.org/software/wget/) to bulk 
download the batches. For example:

    cd /opt/chronam/data/
    wget --recursive --no-host-directories --cut-dirs 1 --reject index.html* --include-directories /data/batches/batch_uuml_thys_ver01/ http://chroniclingamerica.loc.gov/data/batches/batch_uuml_thys_ver01/

In order to load data you will need to run the load_batch management command by
passing it the full path to the batch directory. So assuming you have downloaded
batch_dlc_jamaica_ver01 you will want to:

    django-admin.py load_batch /opt/chronam/data/batches/batch_uuml_thys_ver01

If this is a new server, you may need to start the web server:

    sudo service httpd start

After this completes you should be able to view the batch in the batches report
via the Web:

    http://www.example.org/batches/

Run Unit Tests
--------------

For the unit tests to work you will need to have the batch_dlc_jamaica_ver01
available. You can use the wget command in the previous section to get get it.
After that you should be able to:

    cd /opt/chronam/
    django-admin.py test core

License
-------

This software is in the Public Domain.
