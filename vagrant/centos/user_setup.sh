#!/usr/bin/env bash

CHRONAM_HOME=/opt/chronam
ENV_HOME=$CHRONAM_HOME/ENV

virtualenv -p /usr/bin/python2.7 $ENV_HOME

cp $CHRONAM_HOME/conf/chronam.pth $ENV_HOME/lib/python2.7/site-packages/chronam.pth
source $ENV_HOME/bin/activate
pip install -r $CHRONAM_HOME/requirements.pip

if [ ! -d $CHRONAM_HOME/data/cache ]; then
    mkdir $CHRONAM_HOME/data/cache
fi

if [ ! -d $CHRONAM_HOME/data/bib ]; then
    mkdir $CHRONAM_HOME/data/bib
fi

echo "CREATE DATABASE chronam CHARACTER SET utf8; GRANT ALL ON chronam.* to 'chronam'@'localhost' identified by 'pick_one';" | mysql -u root 

# config env
if [ ! -f $CHRONAM_HOME/settings.py ]; then
    ln -s $CHRONAM_HOME/settings_template.py $CHRONAM_HOME/settings.py 
fi

echo "export DJANGO_SETTINGS_MODULE=chronam.settings" >> /home/vagrant/.bashrc

source /home/vagrant/.bashrc

django-admin.py migrate
django-admin.py loaddata initial_data
django-admin.py chronam_sync --skip-essays

django-admin.py collectstatic --noinput

# load sample batch
if [ ! -d $CHRONAM_HOME/data/batches/batch_uuml_thys_ver01 ]; then
    cd $CHRONAM_HOME/data/
    wget --recursive --no-host-directories --cut-dirs 1 --reject index.html* --include-directories /data/batches/batch_uuml_thys_ver01/ http://chroniclingamerica.loc.gov/data/batches/batch_uuml_thys_ver01/
fi
django-admin.py load_batch $CHRONAM_HOME/data/batches/batch_uuml_thys_ver01

ln -s $CHRONAM_HOME/vagrant/runserver.sh /home/vagrant/
