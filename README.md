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
making chronam available here on Github is to provide an technical option to 
these awardees who want to make their own websites of NDNP newspaper content
available. chronam provides a core set of functionality for loading, modeling
and indexing NDNP data, while allowing you to customize the look and feel
of the website to suit the needs of your organization. 

The NDNP data is in the Public Domain and is itself [available
http://chroniclingamerica.loc.gov/data/batches/] on the Web for anyone to use.
The hope is that the chronam software can be useful for others who want to 
work with and/or publish the content.

Install
-------

To learn more about how to install the software see operating specific 
instructions:

* [install_ubuntu.txt](https://github.com/LibraryOfCongress/chronam/blob/master/install_ubuntu.txt)
* [install_redhat.txt](https://github.com/LibraryOfCongress/chronam/blob/master/install_redhat.txt)

Get Data
--------

As mentioned above, the NDNP data that awardees create and ship to the Library
of Congress is in the public domain and is made available on the Web as 
`batches`. Each batch contains newsaper issues for one or more newspaper 
titles. To use chronam you will need to have some of this batch data to load. If
you are an awardee you probably have this data on hand already, but if not
you can use a tool like [wget](http://www.gnu.org/software/wget/) to bulk 
download the batches. For example

    wget --recursive --no-host-directories --cut-dirs 1 --include-directories /data/dlc/batch_dlc_jamaica_ver01 http://chroniclingamerica.loc.gov/data/dlc/batch_dlc_jamaica_ver01

License
-------

This software is in the Public Domain.
