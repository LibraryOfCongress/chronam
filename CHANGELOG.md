Development: v3.9.0 ([changes](https://github.com/LibraryOfCongress/chronam/compare/v3.8.1...master))
-------------------
#### New Features & Updates
* Disallow invalid date ranges #60
* Add OCLC number to JSON view in Directory #59
* Use default stopwords from Solr
* Upgrade to Solr 4.3
* Added German language
* Styling on multiple pages in the core templates
* JQuery BBQ replaced custom javascript
* Newspaper directory sort
* Example app added
* Made javascript elements cacheable #40
* Added secondary sort to newspaper list page #33
* Ignore English articles in sorting #33
* Jenkins integration
* Seadragon files size increased to 512
* Timeout setting to 60 seconds

#### Bug Fixes
* Default date range 1836-1922 on all pages #61
* Remove "None" from list of options
* Numerous corrections to Ubuntu install instructions
* Correct versions for html5lib and rdflib
* Code cleanup in cataloging management code
* Miscellaneous flake8 cleanups


Development: v3.8.1 ([changes](https://github.com/LibraryOfCongress/chronam/compare/v3.8.0...master))
-------------------
#### New Features & Updates
* Upgraded to latest Seadragon | trac 1342
* Updated Sharetools | trac 1353
* New awardees added to initial fixture | trac 1324
* Add additional material formats to parse and index during holding load process. | trac 1333
 * Microfilm Print Master, Microfilm Service Copy, Microform
* Allows holdings to load w/ blank descriptions | trac 1352
* Clean up added for used languages, subjects, and places in the database | trac 1349, 1307
* Updates state list in search to include all states in 752 field | trac 1339
* Jenkins Settings updated -- removes memorius
* Instructions consolidated into README.md and reformatted as Markdown for viewing on Github, with operating specific notes remaining in install_ubuntu.md and install_redhat.md.

#### Bugs Fixes
* Fixes - error displaying in holdings data that has been updated in the 21st century | trac 1331
* Fixes - holdings display error from 866 so that preceding letter and '=' are not striped off in loading process. | trac 1332
 * Example
  * Error: `<1867:3:25-6:17>`
  * Corrected: `s=<1867:3:25-6:17>`
* Updated solr doc to index display_title, which adds 245 $h to the display of the title in search results | trac 1334
* Fixed directory drop down to only put Puerto Rico in as a territory, not a state. | trac 1336
* Fixed title sync process to work w/ fresh install | trac 1347
* Fixed search box stickiness - search term now doesn't disappear | trac 1340

#### Deployment Notes
* Run migration on core: 'django-admin.py migrate core'
* Update awardees
 * django-admin.py loaddata initial_data.json
* Rerun holding loader: `django-admin.py load_holdings`
 * Changes to holding loader will reflect in data.
 * Material type updates will be loaded
 * New holdings loaded b/c blank descriptions allow
* Reindex titles: `django-admin.py index_titles`
 * Updates solr doc to reflect changes


v3.8.0, 02/07/2013 ([changes](https://github.com/LibraryOfCongress/chronam/compare/v3.7.0...v3.8.0))
-------------------
#### New Features
* Add the ability to write the word coordinates separately from the rest of the batch loading process.
* Minor updates to logging in title loader & holding loader

#### Bugs Fixes 
* Holding loader bug on material type fixed.

#### Deployment Notes
* No changes
