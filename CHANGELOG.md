# Change Log

## TODO
* make default params user editable through GUI
* better plotter would be nice
* manual editing of historical exchange rates would be useful if they are ever used
* add account setting to only count a fraction of the value (e.g. 50 percent for shared accounts or 0 to exclude entirely from total)
* refactor the csv stuff, should support multiple print options so csv and -q can be used simultaneously 

## v4.2.1
* 2019-04-01 - bug fixes highlighted by lgtm.com

## v4.2
* 2017-09-15 - Add option to print running balances for every account (`-q` instead of `-p`).
* 2017-09-27 - Add print format option, with support for csv and latex. Removed `-l` option for latex-only.
* 2017-09-30 - Maximum records to print now set with a filter instead of a setting option. -R now clears this limit entirely.

## v4.1(beta)
* 2010-12-02 - Added -d option. -d 1 is good for total value in each day.
* 2011-08-08 - Added -c option for current balances
* 2011-08-08 - Added support for foreign currency accounts (but not converting between accounts yet)
* 2011-08-11 - Added -C option to only display some columns/accounts
* 2011-08-11 - Added ability to save current filters as the defaults
* 2011-08-11 - Removed support for NETARCH/NETBASE
* 2011-08-12 - Changed -u to download all new exchange rates but will not save by default
* 2012-01-19 - Added smarter date interpretation so can omit year or both year and month
* 2012-09-12 - Slightly modified format of -r and -t tables
* 2013-11-01 - Old exchange rates are saved when updated. Historical rates not used for anything.
* 2015-08-08 - Fixed exchange rates to use a proper/better API
	
## v4.0(beta)
* 2010-10-29 - Added save database functionality to the GUI
* 2010-10-29 - Added not character as a user option
* 2010-10-29 - Made user options add new options without deleting settings.pkl first
* 2010-10-29 - Added negate option for type filters

## v4.0(alpha)
* 2010-08-01 - started writing new GUI using gtk+     

## v3.5(alpha)
* 2010-02-10 - Can use '!' notation to remove records matching a string (Aim to do this for types as well)
* 2010-02-22 - Added option to print only the total value of a record, included in params.py
* 2010-02-22 - Ctrl-C while adding (but not editing!) record exists more gracefully
* 2010-03    - Default parameters can be edited via command line
* 2010-03    - New accounts can be added, and accounts can be deleted, without breaking the database
* 2010-03-26 - Wrote special function for making a transfer between accounts
* 2010-03-28 - Added mechanism for predictive input of destinations and descriptions
* 2010-06-23 - Added tab completion for dest and desc, though with minor bugs 

## v3.4
* 2009-07-26 - Added back and forward options, enabling undoing just one filter
* 2009-07-26 - Added new view modes to the GUI and a stronger recipient filter
* 2009-07-25 - Added a status bar
* 2009-09-20 - Added a latex output option, not customizable

## v3.3
* 2009-07-09 - Redesigned filters. The database now remembers what filters have been applied.
* 2009-07-09 - Wrote new date dialog for setting date ranges in the GUI and added default filters to params.py

## v3.2
* 2009-07-05 - Added plotting functions
* 2009-07-08 - Added balancesByType and balancesByRecipient, currently only accessible in the CLI

## v3.1
* 2009-07-04 - Now a gui is started when called without command line arguments

## v3
* 2009-07-03 - Python version, solving a lot of old shell problems

## v2.1
* 2009-07-01 - created SVN repository
* 2009-07-01 - split code into smaller files, in single directory

## v2
* 2008-09-20 - can print and sort the expense file in a human readable way, and sum totals
* 2008-09-20 - added timestamp and exclusion filter by timestamp
* 2008-09-19 - each account has its own column

## v1
* 2008-09-08 - can save expenses

