#!/usr/bin/env python
""" Simply track expenses, income, account balances, etc."""

##############################################################################
#
# Copyright 2010-2016 Gregory Paciga (gpaciga@gmail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################



# To do: Abstract the expense types from the income types
#        More error checking and argument type checking
#        Warn if removing accuont with non-zero balance
#        When a new Type or Account code is encountered, ask for a name and save it in the options
#        Maybe have some prediction thing, so if the first few fields are similar it'll suggest a complete record? (e.g. for monthly things)

#! If you change the database to a file which does not exist, that error on loading the database will not let us get as far as the -o command to fix it!

import sys # to get command line options
import getopt # to parse command line options
#from datetime import date
#from datetime import timedelta
#from time import time

import settings
import database

__version__ = "4.1-beta"

# Load the user settings and database
settings = settings.Settings()
database = database.Database(settings)

def usage():
    """ Return the USAGE file as a string """
    usageFilename = "%s/%s" % (sys.path[0], 'USAGE')
    usageFile = file(usageFilename)
    output = ''
    for line in usageFile:
        output += line 
    return output
# end def usage

# Unused option letters:
#  jkmqyz GHIJKMNOPQUYZ

def parseArgs(argv):
    """ Process command line arguments. """
    try:
        opts, args = getopt.getopt(argv, "acbd:e:ghilno:prstuvwx:A:B:C:D:EF:L:RS:T:V:WX:", [])
    except getopt.GetoptError:
        print "Unrecognized option or bad argument. Use -h to get usage information."
        sys.exit(2)
    for opt, arg in opts:

        if opt == "-a":
            # Print all visible records, no matter how many there are
            print database.__str__(len(database.records))

        elif opt == "-c":
            # Print current balances of all accounts
            balances = database.balances()['all']
            total=0.0
            for acc in settings.accounts().iterkeys():
                if acc not in settings.deletedAccountKeys():
                    if acc in settings.foreignAccountKeys():
                        print "%-15s %12.2f = %12.2f" % (settings.accountName(acc), balances[acc], balances[acc]*settings.exchange(acc))
                        total += balances[acc]*settings.exchange(acc)
                    else:
                        print "%-15s %12.2s   %12.2f" % (settings.accountName(acc), "", balances[acc])
                        total += balances[acc]
            print "%-15s %12.2s   ============" % ("", "")
            print "%-15s %12.2s   %12.2f" % ("Total", "", total)

        elif opt == "-b":
            for datapoint in database.integrateDeltas():
                output = ""
                output += "%s " % datapoint[0]
                for i in range(0, len(settings.accounts())+1): # +1 because we have a column for the total
                    output += "%9.2f " % datapoint[1+i]
                print output

        elif opt == "-d":
            # Integrate over n days, argument required.
            # -d 7 is the same as -w
            #! Should this be a function in the database class?
            total = 0.0
            num = 0
            try:
                n=int(arg)
            except:
                print "Invalid option: -d " + arg
            for datapoint in database.integrate(n):
                # datapoint is a (date, float) tuple
                print "%s %.2f" % datapoint
                total += float(datapoint[1])
                num += 1
            ave = total/num
            print "# Average: %.2f" % ave

        elif opt == "-e":
            # Edit an entry identified by uid=arg
            entries=str.split(arg,',')
            for entry in entries:
                database.edit(entry)
            database.save()

        elif opt == "-g":
            start_gui()

        elif opt == "-h":
            # Print usage
            print usage()

        elif opt == "-i":
            # Print a new record UID
            # newUID() has a 'self' arg so can't just call Transaction.newUID() --- change that? 
            import transaction
            print transaction.Transaction(database, settings).uid 

        elif opt == "-l":
            # Print a latex report
            import latex
            latex.output(database)

        elif opt == "-n":
            # Create a new entry in the database
            database.newRecord()
            database.save()

        elif opt == "-o":
            if (settings.edit(arg)):
                settings.save()
            

        elif opt == "-p":
            # Print the database as it currently stands
            print database

        elif opt == "-r":
            # Print recipients
            destsum=0.0
            for dest in database.balancesByRecipient():
                destsum+=float(dest[1])
                print "  %-35s %9.2f" % (dest[0], float(dest[1]))
            print "  ============================================="
            print "  %35s %9.2f" % (" ", destsum)

        elif opt == "-s":
            # Sort records by date
            database.sort()
            database.save()

        elif opt == "-t":
            # Print types
            typesum=0.0
            for type in database.balancesByType():
                typesum+=float(type[1])
                print "  %-35s %9.2f" % (type[0], float(type[1]))
            print "  ============================================="
            print "  %35s %9.2f" % (" ", typesum)

        elif opt == "-u":
            print "Updating all exchange rates from Google (but you must save explicitly with -o save!)"
            settings.updateExchanges()

        elif opt == "-v":
            # Like -p but print values, not individual accounts
            print database.__str__(totalValue=not(settings.totalvalues()))

        elif opt == "-w":
            # Integrate over n days, defaults to 7.
            #! Should this be a function in the database class?
            total = 0.0
            num = 0
            for datapoint in database.integrate():
                # datapoint is a (date, float) tuple
                print "%s %.2f" % datapoint
                total += float(datapoint[1])
                num += 1
            ave = total/num
            print "# Average: %.2f" % ave

        elif opt == "-x":
            # Delete a record by uid
            uids = str.split(arg.rstrip(),",")            
            for uid in uids:
                database.delete(uid)
            database.save()

        elif opt == "-A":
            # Print only transactions involving account arg
            database.filters['accounts'] = arg

        elif opt == "-B":
            # Print only transactions and involving account arg and only that column
            database.filters['accounts'] = arg
            database.filters['columns'] = arg

        elif opt == "-C":
            # Print only the given column(s)
            database.filters['columns'] = arg

        elif opt == "-D":
            # Filter by date
            database.filters['dates'] = arg

        elif opt == "-E":
            # Remove everything except expense
            database.filters['types'] = settings.extypesString()

        elif opt == "-F":
            # Exclude records of type arg by appending the negation character
            database.filters['types'] = settings.notchar()+arg

        elif opt == "-S":
            # Print only records containing string arg
            database.filters['string'] = arg

        elif opt == "-L":
            # Print only records with a specific recipient
            database.filters['recipients'] = arg

        elif opt == "-R":
            database.resetFilters()

        elif opt == "-T":
            # Print only type arg
            database.filters['types'] = arg

        elif opt == "-V":
            # Print records with total value greater than arg
            database.filters['values'] = arg

        elif opt == "-W":
            # Print only a week worth
            database.filters['dates'] = 'W1'

        elif opt == "-X":
            # Exclude record by UID
            database.filters['uid'] = arg

        #If we ever get around to using long options:
        #elif opt in ("-t", "--test"):
        #and you have to do something else for --test=value type args
# end def parseArgs

def start_gui():
    import gui
    snidget_gui = gui.SnidgetGUI()
    snidget_gui.main()

# If no args, start the gui
# Else, parse the args
if __name__ == "__main__":
    if len(sys.argv[1:]) == 0:
        start_gui()
    else:
        parseArgs(sys.argv[1:])



