# Change Log

## TODO
* make default params user editable through GUI
* better plotter would be nice
	
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

