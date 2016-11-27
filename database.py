#    This file is part of Snidget.
#
#    Snidget is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Snidget is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Snidget.  If not, see <http://www.gnu.org/licenses/>.


""" Defines Database class which contains and organizes all transaction records."""

# Defines Database class, the main workhorse in the Snidget program
# It is basically a container object for all the transactions on record,
# including the functions for determining which records to show when printed

class Database:
    """ Database class, which holds and organizes transactions."""
    def __init__(self, settings):
        """ Create a new database from the given filename """
        import sys
        import transaction
        self.settings = settings
        recordFileName = settings.database()
        self.filename = "%s/%s" % (sys.path[0], recordFileName)
        #! If the file cannot be found, we should create it!
        #recordFile = file(self.filename,'r')
        try:
            recordFile = open(self.filename,'r')
        except IOError:
            # Only open with write permissions if file does not exist yet
            print "Creating database file %s" % self.filename
            # For some reason r+ doesn't work to create the file
            # and have to open for write to create, close, and open for read
            recordFile = open(self.filename,'w')
            recordFile.close()
            recordFile = open(self.filename,'r')
            

        self.records = []
        # Read in all the records of the file
        for line in recordFile:#.readlines():
            thisRecord = transaction.Transaction(self, settings, line)
            self.add(thisRecord)
        recordFile.close()
        self.isChanged = False
        self.filters = settings.filters()


    def __str__(self, nprint=None, totalValue=None):
        """ Print the database as a table to the screen """

        if nprint is None:
            try:
                nprint = self.settings.maxprint()
            except:
                print "Unable to find user settings"
                nprint = 25

        if totalValue is None:
            try:
                totalValue = self.settings.totalvalues()
            except:
                print "Unable to find user settings"
                totalValue = False
                    
        self.applyFilters()
        balances = self.balances()

        # Make a list of visible records
        # so we can make use of MAXPRINT in array indices
        printable = []
        for record in self.records:
            if record.visible:
                printable.append(record)

        # Determine appropriate column widths
        printID = False # Don't print the ID column unless there is data there
        wType = 4       # Minimum column widths 
        wDest = 8
        wDesc = 11
        wDate = 10
        for record in printable[-nprint:]:
            if len(record.type) > wType:
                wType = len(record.type)
            if len(record.dest) > wDest:
                wDest = len(record.dest)
            if len(record.desc) > wDesc:
                wDesc = len(record.desc)
            if record.id != "":
                printID = True
        #wType+=2
        #wDest+=2
        #wDesc+=2

        # Write out the header stuff for the table
        #output  = "DATE         TYPE         LOCATION                   DESCRIPTION                            "
        #divider = "----------   ----------   ------------------------   ------------------------------------   "

        # Make a format string with the right size arguments to the %s values
        lineformat = "%%-%ds  %%-%ds  %%-%ds  %%-%ds  " % (wDate, wType, wDest, wDesc)
        output = lineformat % ("DATE", "TYPE", "LOCATION", "DESCRIPTION")
        divider = "%s  %s  %s  %s  " % ("-"*wDate, "-"*wType, "-"*wDest, "-"*wDesc)

        if (totalValue):
            output += "  VALUE   "
            divider += "-------   "
        else:
            for account in self.settings.accounts().itervalues():
                if account not in self.settings.deletedAccountNames() and self.is_printable(account):
                    if len(account)>7:
                        account = account[0:7]
                    output += "%7s   " % account # Account names
                    divider += "-------   "
        if (printID):
            output  += "    ID  "
            divider += "------  "
        output += "   UID\n"
        divider += "------\n"
        output += divider

        # Add the records to the database
        it = 1
        for record in printable[-nprint:]:
            output += record.__str__(totalValue=totalValue, printID=printID, wType=wType, wDest=wDest, wDesc=wDesc)
            output += "\n"
            if it % 5 == 0:
                output += "\n"
            it += 1
        output += divider

        # The number of spaces required to line up the Total labels correctly
        colspace=2
        balanceSpacing = wDate + wType + wDest + wDesc + (colspace*4) - 19

        # Print a line of account totals of visible records
        output += "%s Total visible:  " % (" "*balanceSpacing)
        if (totalValue):
            #output += "%9.2f " % sum(balances['visible'].values())
            output += "%9.2f " % balances['visible']['sum']
        else:
            for k, v in balances['visible'].iteritems():
                if k is not 'sum' and self.is_printable(k):
                    output += "%9.2f " % v
        output += "\n"

        # Print a line of account totals over all records
        output += "%s Total balance:  " % (" "*balanceSpacing)
        if (totalValue):
            #output += "%9.2f " % sum(balances['all'].values())
            output += "%9.2f " % balances['all']['sum']
        else:
            for k, a in balances['all'].iteritems():
                if k is not 'sum' and self.is_printable(k):
                    output += "%9.2f " % a
        output += "\n"

        #vistotal = sum(balances['visible'].values())
        #total = sum(balances['all'].values())
        #weekly = sum(balances['thisweek'].values())
        vistotal = balances['visible']['sum']
        total = balances['all']['sum']
        weekly = balances['thisweek']['sum']

        remaining = self.settings.allowance()+weekly
        output += "    Visible:    %9.2f   (%d records)\n" % (vistotal, len(printable))
        output += "    Balance:    %9.2f\n" % total
        if (self.settings.allowance() > 0.0):
            output += "    This Week:  %9.2f\n" % weekly
            output += "    Remaining:  %9.2f\n" % remaining
        return output

    #--------------------------------------------------------------------------
    # Admin functions for editing the database
    #--------------------------------------------------------------------------

    def add(self, record):
        """ Add a Transaction object (record) to the database """
        self.records.append(record)
        self.isChanged = True

    def newRecord(self):
        """ Make a new record, get user input for it, and add to the database"""
        import transaction
        new = transaction.Transaction(self, self.settings)
        try:
            new.inputValues()
        except (KeyboardInterrupt, SystemExit):
            print "\nCaught Keyboard Interrupt. This record has not been added."
        else:
            self.add(new)
            #! Would be nice to append this new record to the original database file
            #! instead of saving the whole thing
            self.isChanged = True

    def edit(self, uid):
        """ Prompt for new values for a record with given uid """
        for record in self.records:
            if record.uid == uid:
                #! As in newRecord, would like this to handle Ctrl-C nicely,
                #! without saving the changes
                record.inputValues()
                return
        self.isChanged = True

    def delete(self, uid, confirm=True):
        """ Delete record specified by uid """
        for record in self.records:
            if record.uid == uid:
                if confirm == True:
                    prompt = "Delete record [%s]? (yes/no) " % record.encode()
                    answer = raw_input(prompt)
                    if answer == "yes":
                        # Uses __cmp__ to check when equal
                        self.records.remove(record)
                else:
                    self.records.remove(record)
        self.isChanged = True

    def sort(self, perm=True):
        """ Sorts the records in the database. """
        self.records.sort()
        # If database was marked changed by something, leave it marked as such
        if self.isChanged == False:
            self.isChanged = perm

    def encode(self):
        """ Write database out in text file format """
        output = ""
        for record in self.records:
            output += record.encode()
            output += "\n"
        return output

    def save(self, outname=""):
        """ Rewrite the database to a txt, overwriting itself by default """
        if outname == "":
            outname = self.filename
        outfile = file(outname,'w')
        outfile.write(self.encode())
        outfile.close()
    

    ## Downloading from an online database is no longer supported
    #def downloadRecords(self):
    #    """ Download new records from online and add them to the database """
    #    import urllib
    #    import transaction
    #    #! Should check if the file we downloaded is the right format
    #    #! Should check if transactions already exist or if UIDs conflict
    #    # If we have no file defined to download, don't download anything
    #    if self.settings.netbase() == "":
    #        print "Internet database file (NETBASE) not defined"
    #        return
    #    url = self.settings.netbase()
    #    # get the specified url as a tuple (filename, headers)
    #    page = urllib.urlretrieve(url)
    #    #headers = page[1] #this is unused
    #    content = file(page[0],'r')
    #    # translate the contents into records
    #    for line in content:
    #        newRecord = transaction.Transaction(self, self.settings, line)
    #        self.add(newRecord)
    #        self.isChanged = True # database not changed if there are no lines
    #    # Now archive the online records
    #    if self.settings.netpost() != "":
    #        url = self.settings.netpost()
    #        page = urllib.urlretrieve(url)


    #--------------------------------------------------------------------------
    # Functions for printing information about the database
    #--------------------------------------------------------------------------

    def balances(self):
        """ Return a list of balances """
        self.applyFilters()

        balance = {}
        wbalance = {}
        vbalance = {}
        for acc in self.settings.accounts().iterkeys():
            if acc not in self.settings.deletedAccountKeys():
                balance[acc] = 0.0
                wbalance[acc] = 0.0
                vbalance[acc] = 0.0

        for record in self.records:
            for acc, delta in record.deltas.iteritems():
                if acc not in self.settings.deletedAccountKeys():
                    balance[acc] += delta
            if record.visible == True:
                for acc, delta in record.deltas.iteritems():
                    if acc not in self.settings.deletedAccountKeys():
                        if record.date > self.settings.TODAY - self.settings.ONEWEEK:
                            wbalance[acc] += delta
                        vbalance[acc] += delta

        # Now add another field for the sum in the default currency
        balance['sum'] = 0.0
        vbalance['sum'] = 0.0
        wbalance['sum'] = 0.0
        for acc, value in balance.iteritems():
            # protect against the fact that 'sum' will be one of the accounts...
            if ( acc != 'sum' ):
                if acc in self.settings.foreignAccountKeys():
                    balance['sum'] += balance[acc]*self.settings.exchange(acc)
                    vbalance['sum'] += vbalance[acc]*self.settings.exchange(acc)
                    wbalance['sum'] += wbalance[acc]*self.settings.exchange(acc)
                else:
                    balance['sum'] += balance[acc]
                    vbalance['sum'] += vbalance[acc]
                    wbalance['sum'] += wbalance[acc]

        # Return the result
        result = { 'all':balance,
                   'visible':vbalance,
                   'thisweek':wbalance }
        return result

    def balancesByType(self):
        """ Return a dictionary of types and their balances """
        self.applyFilters()
        balances = {}
        for record in self.records:
            if record.visible:
                if record.type not in balances:
                    balances[record.type] = record.value()
                else:
                    balances[record.type] += record.value()

        balances = self.sortBalances(balances)
        return balances # this is a list of tuples

    #! For ByType and ByRecipient, include a field with the number of
    #! transactions --- will need to rework how these functions are used

    def balancesByRecipient(self):
        """ Return a list of recipients with the money spent on them """
        # Respects filters
        self.applyFilters()
        balances = {}
        for record in self.records:
            if record.visible:
                # check that this destination exists yet
                if record.dest not in balances:
                    balances[record.dest] = record.value()
                else:
                    balances[record.dest] += record.value()

        balances = self.sortBalances(balances)                
        return balances # this is a list of tuples


    def sortBalances(self, d):
        """ Helper func to sort dictionaries of balances by value """
        items = [(v, k) for k, v in d.items()]
        items.sort()
        items.reverse()             # so largest is first
        # Our dictionary has become a list of tuples to maintain order
        #return [(k, v) for v, k in items]
        # The GUI requires the value be a string. 
        return [(k, "%.2f" % v) for v, k in items]


    def integrateDeltas(self, visibleOnly=True):
        """ Provides actual balance of the accounts as a function of time """

        from datetime import timedelta

        self.applyFilters()

        values = []
        
        total = 0.0

        balances = {}
        for acc in self.settings.accounts().iterkeys():
            balances[acc] = 0.0

        self.sort(perm=False)
        dateSet = False
        
        for record in self.records:
            if (visibleOnly == True and record.visible == True) or visibleOnly == False:
                if dateSet == False:
                    currentDate = record.date
                    dateSet = True
                thisDate = record.date
                if thisDate == currentDate:
                    for acc, delta in record.deltas.iteritems():
                        balances[acc] += delta
                    total += record.value()
                else:
                    while thisDate != currentDate:
                        thisValue = [ currentDate ]
                        thisValue.extend(balances.values()) # was balances[:]
                        thisValue.append(total)
                        values.append(thisValue)
                        #values.append((currentDate, balances[:], total))
                        currentDate = currentDate+timedelta(1)
                    for acc, delta in record.deltas.iteritems():
                        balances[acc] += delta
                    total += record.value()
                    
        thisValue = [ currentDate ]
        thisValue.extend(balances.values())
        thisValue.append(total)
        values.append(thisValue)
        #values.append((currentDate, balances[:], total))
        return values
                

    def integrate(self, n=7, visibleOnly=True, independent=False):
        """ Return deltas integrated over previous n days, 7 by default """
        
        from datetime import timedelta

        self.applyFilters()

        values = []

        # Declare the array we will hold intermediate values in
        #! This could be extended to keep track of each separate account
        dtotals = []
        for i in range(0, n):
            dtotals.append(0.0)
        
        total = 0.0

        # We require the transactions to be in chronological order
        self.sort(perm=False)

        i = 0 # index of dtotals, should go from 0 to n-1
        ndays = 0 # counts days done so far
        dateSet = False # Need to find first visible record before setting date

        for record in self.records:
            if (visibleOnly == True and record.visible == True) or visibleOnly == False:
                if dateSet == False:
                    # Get the date of the first record we're actually printing
                    currentDate = record.date
                    dateSet = True
                thisDate = record.date
                if thisDate == currentDate:
                    dtotals[i] += record.value()

                else:
                    while thisDate != currentDate:

                        # Go on to the next day
                        if ndays >= (n-1):
                            # Print every day if we don't care about keeping points independent
                            # Else just print every nth point
                            if (not independent) or (ndays%n == n-1):
                                values.append((currentDate, sum(dtotals))) 
                                total += sum(dtotals)
                        i = (i+1)%n
                        currentDate = currentDate+timedelta(1)
                        # If still not at the right day, set this day to 0 value
                        if currentDate != thisDate:
                            dtotals[i] = 0.0
                        ndays += 1

                    # Now we have the correct day, add it
                    dtotals[i] = record.value()

        if ndays >= n:
            if (not independent) or (ndays%n == n-1):
                values.append((currentDate, sum(dtotals))) 
                total += sum(dtotals)

        return values
    #! The above stops on the last record, not the last day in the range

    def predictDest(self, type, n=1):
        """ Get the n last destinations of a given type """
        predictions = []
        for record in reversed(self.records):
            if record.type == type:
                if record.dest not in predictions:
                    if len(predictions) == n-1:
                        # This will be the last prediction asked for
                        predictions.append(record.dest)
                        return predictions
                    else:
                        predictions.append(record.dest)
        # In case we didn't find n unique dests
        return predictions
        
    def predictDesc(self, dest, type=None, n=1):
        """ Get the n last descriptions of a given dest """
        predictions = []
        for record in reversed(self.records):
            if record.dest == dest:
                # Optionally limit ourselves to a specific type
                if record.type == type or type is None:
                    if record.desc not in predictions:
                        if len(predictions) == n-1:
                            predictions.append(record.desc)
                            return predictions
                        else:
                            predictions.append(record.desc)
        return predictions


    def words(self):
        """ Return a list of words in the database for tab-completion """
        words = []
        for record in self.records:
            words.append(record.desc)
            words.append(record.dest)
        # convert to a set, removing duplicates, then back to a list
        words = list(set(words))  
        return words

    def places(self):
        """ Return a list of places in the database """
        places = []
        for record in self.records:
            places.append(record.dest)
        places = list(set(places))
        return places

    def descriptions(self):
        """ Return a list of descriptions in the database """
        descs = []
        for record in self.records:
            descs.append(record.desc)
        descs = list(set(descs))
        return descs

    #--------------------------------------------------------------------------
    # Filter Functions to change what records are visible
    #--------------------------------------------------------------------------

    def resetFilters(self):
        """ Remove all filters applied """
        #self.filters = {
        #    'dates':None,      # e.g., 2009-01-01,2009-07-01 or W1, W52, etc
        #    'accounts':None,   # e.g., BMO,RBC 
        #    'types':None,      # list of types to display
        #    'recipients':None, # list of recipients (more strict than 'string')
        #    'string':None,     # must include this string in desc or dest
        #    'values':None,     # minval,maxval
        #    'uid':None,        # exclude these uids
        #    }
        for filt in self.filters.iterkeys():
            self.filters[filt] = None


    def setFilterDefaults(self):
        """ Set filters back to their defaults """
        #database.filters = self.settings.filters()
        self.filters = self.settings.filters()


    # Filter behaviour may be inconsistent...
    def filterType(self, type, flag=True):
        """ Filter records that match type """
        # Check if the first character is a negation
        if str.find(type,self.settings.notchar()) == 0:
            flag = not(flag)
            type = type[1:]
        types = str.split(type,',')
        for record in self.records:
            if record.visible == True and (record.type in types):
                record.visible = flag
            elif record.visible == True:
                record.visible = not(flag)

    def filterRecipient(self, dest, flag=True):
        """ Filter records that match recipient """
        recips = str.split(dest,',')
        for record in self.records:
            if record.visible == True and (record.dest in recips):
                record.visible = flag
            elif record.visible == True:
                record.visible = not(flag)

    def filterUID(self, uid, flag=True):
        """ Filter for specific UID and only UID"""
        for record in self.records:
            if record.visible == True and record.uid == uid:
                record.visible = flag
            elif record.visible == True:
                record.visible = not(flag)

    def filterString(self, filter, flag=True):
        """ Filter according to whether record description contains a string """
        for record in self.records:
            if record.visible == True:
                if record.desc.find(filter) >= 0 or record.dest.find(filter) >= 0:
                    record.visible = flag
                else:
                    record.visible = not(flag)

    def filterWeek(self, n=1):
        """ Filter out records older than n weeks (default n=1) from today"""
        for record in self.records:
            if record.date <= self.settings.TODAY - self.settings.ONEWEEK*n or record.date > self.settings.TODAY:
                record.visible = False

    def filterValue(self, valmin=None, valmax=None, flag=True):
        """ Filter out records with less than total abs(value) val """
        #import math # not necessary?
        if valmin is None and valmax is None:
            return
        for record in self.records:
            if record.visible == True:
                if valmin != None and record.value()<valmin:
                    record.visible = not flag
                if valmax != None and record.value()>valmax:
                    record.visible = not flag

    def filterAccount(self, account, flag=True):
        """ Filter by requiring account delta is non-zero """

        accounts = str.split(account,',')
        for account in accounts:
            # Get index of account we want. Will be same index as delta array.
            if account in self.settings.accountNames():
                # Given the name we must find the key
                key = 'KERROR' # this should never survive loop below since we already know the name exists
                for acc, name in self.settings.accounts().iteritems():
                    if (name == account):
                        key = acc
                # Now find records with non-zero deltas for this account
                for record in self.records:
                    if key in record.deltas:
                        if record.deltas[key] != 0.0 and record.visible == True:
                            record.visible = flag
                    elif record.visible == True:
                        record.visible = not(flag)
            else:
                print 'Account %s does not exist' % account


    def filterDate(self, mindate, maxdate=None, flag=True):
        """ Include anything between mindate up to but not including maxdate """
        # Takes two DATES for now

        from datetime import timedelta

        if (maxdate is None):
            maxdate = self.settings.TODAY+timedelta(1)

        for record in self.records:
            if record.visible == True:
                if record.date < mindate or record.date >= maxdate:
                    record.visible = not(flag)

    def filterReset(self):
        """ Reset all records to print """
        # Not to be confused with resetFilters, which changes filters dictionary
        for record in self.records:
            record.visible = True

    def filterInvert(self):
        """ Invert the current filters """
        for record in self.records:
            record.visible = not(record.visible)

    def applyFilters(self):
        """ Apply the entire filters dictionary to the database """
        from datetime import date
        #from datetime import timedelta

        self.filterReset()

        # Apply the date filter
        if self.filters['dates'] != None:
            if str.find(self.filters['dates'],'W') == 0:
                # If filter starts with w, filter to number of weeks specified
                # e.g. w52 for one year
                self.filterWeek(int(self.filters['dates'][1:]))
            else:
                # Else we should have the yyyy-mm-dd,yyyy-mm-dd format
                # Get the two possible arguments
                args = str.split(self.filters['dates'],",")

                # Get the first date
                mindate = str.split(args[0],"-")
                mindate = date(int(mindate[0]), int(mindate[1]), int(mindate[2]))

                # Look for second date, and use it to set filter if it's there
                try:
                    maxdate = str.split(args[1],"-")
                    maxdate = date(int(maxdate[0]), int(maxdate[1]), int(maxdate[2])) # Transaction date        
                    self.filterDate(mindate, maxdate)
                except:
                    self.filterDate(mindate)

        # Apply the accounts filter
        if self.filters['accounts'] != None:
            # We print only the account in the string
            self.filterAccount(self.filters['accounts'])
            

        # Apply the filter by type
        if self.filters['types'] != None:
            self.filterType(self.filters['types'])

        # Apply the filter by recipient
        if self.filters['recipients'] != None:
            self.filterRecipient(self.filters['recipients'])


        # Apply the desc/dest string filter
        if self.filters['string'] != None:
            #! Can we put multiple string filters in filter dictionary at once?
            #! eg for filter in self.filters['string']...
            if (self.filters['string'][0] == self.settings.notchar()):
                self.filterString(self.filters['string'][1:], flag=False)
            else:
                self.filterString(self.filters['string'])
            

        if self.filters['values'] != None:
            values = str.split(self.filters['values'],',')
            if values[0] == '':
                values[0] = None
            else:
                values[0] = float(values[0])
            if len(values)>1:
                if values[1] == '':
                    values[1] = None
                else:
                    values[1] = float(values[1])
            else:
                values.append(None) # add a values[1] spot

            # If values are out of order, flip them
            if (values[0] != None) and (values[1] != None) and (values[1]<values[0]):
                minval = values[1]
                values[1] = values[0]
                values[0] = minval

            self.filterValue(values[0], values[1])


        # Remove the UIDs listed
        if self.filters['uid'] != None:
            uids = str.split(self.filters['uid'],',')
            for uid in uids:
                self.filterUID(uid, False)

    def is_printable(self, name):
        """ Return a boolean saying whether the account is allowed by the columns filter """
        if self.filters['columns'] is not None and self.filters['columns'] not in ["None", "none", "All", "all"]:
            allowed = self.filters['columns'].split(',')
            if name in self.settings.accountNames():
                if name in allowed: return True
                else: return False
            elif name in self.settings.accountKeys():
                # First convert the names allowed to their keys
                allowed_keys = []
                for account in allowed: allowed_keys.append(self.settings.accountKey(account))
                if name in allowed_keys: return True
                else: return False
            else:
                print "Error: account %s not recognized in is_printable" % name
        elif self.filters['columns'] in ["None", "none"]: return False
        else: return True # no columns = all columns

    # EXTRA STUFF FOR POSSIBLE GUI
    def headings(self):
        """ Write database column headings to a tuple """
        output = ['Date', 'Type', 'Recipient', 'Description']
        for name in self.settings.accountNames():
            if name not in self.settings.deletedAccountNames():
                output.append(name)
        output.append('ID')
        output.append('UID')
        return tuple(output)

# END Database class
