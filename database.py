""" Defines Database class which contains and organizes all transaction records."""

import sys
from datetime import timedelta, date
import transaction

# Defines Database class, the main workhorse in the Snidget program
# It is basically a container object for all the transactions on record,
# including the functions for determining which records to show when printed

class Database(object):
    """ Database class, which holds and organizes transactions."""
    def __init__(self, settings):
        """ Create a new database from the given filename """
        self.settings = settings
        record_filename = settings.database()
        self.filename = "%s/%s" % (sys.path[0], record_filename)
        #! If the file cannot be found, we should create it!
        try:
            record_file = open(self.filename, 'r')
        except IOError:
            # Only open with write permissions if file does not exist yet
            print "Creating database file %s" % self.filename
            # For some reason r+ doesn't work to create the file
            # and have to open for write to create, close, and open for read
            record_file = open(self.filename, 'w')
            record_file.close()
            record_file = open(self.filename, 'r')

        self.records = []
        # Read in all the records of the file
        for line in record_file:#.readlines():
            self.add(transaction.Transaction(self, settings, line))
        record_file.close()
        self.is_changed = False
        self.filters = settings.filters()

    def __str__(self, total_value=None, print_running_balances=False, csv=False):
        """ Print the database as a table to the screen """

        if "maxprint" in self.filters:
            maxprint = self.filters['maxprint']
        else:
            try:
                maxprint = self.settings.maxprint()
            except:
                print "Unable to find user settings, setting maxprint to 25"
                maxprint = 25

        if total_value is None:
            try:
                total_value = self.settings.total_values()
            except:
                print "Unable to find user settings"
                total_value = False

        self.apply_filters()
        balances = self.balances()

        # Make a list of visible records
        # so we can make use of MAXPRINT in array indices
        all_printable = []
        for record in self.records:
            if record.visible:
                all_printable.append(record)
        if maxprint is not None:
            printable = all_printable[-maxprint:]
        else:
            printable = all_printable

        # Determine appropriate column widths
        print_id = False # Don't print the ID column unless there is data there
        w_type = 4       # Minimum column widths
        w_dest = 8
        w_desc = 11
        w_date = 10
        for record in printable:
            if len(record.type) > w_type:
                w_type = len(record.type)
            if len(record.dest) > w_dest:
                w_dest = len(record.dest)
            if len(record.desc) > w_desc:
                w_desc = len(record.desc)
            if record.id != "":
                print_id = True

        # Write out the header stuff for the table
        # Make a format string with the right size arguments to the %s values
        if csv:
            lineformat = "%s,%s,%s,%s"
        else:
            lineformat = "%%-%ds  %%-%ds  %%-%ds  %%-%ds  " % (w_date, w_type, w_dest, w_desc)
        output = lineformat % ("DATE", "TYPE", "LOCATION", "DESCRIPTION")
        divider = "%s  %s  %s  %s  " % ("-"*w_date, "-"*w_type, "-"*w_dest, "-"*w_desc)

        if total_value:
            if csv:
                output += ",VALUE"
            else:
                output += "  VALUE   "
            divider += "-------   "
        else:
            for account in self.settings.accounts().itervalues():
                if (account not in self.settings.deleted_account_names()
                        and self.is_printable(account)):
                    if csv:
                        output += ",%s" % (account)
                    else:
                        if len(account) > 7:
                            account = account[0:7]
                        output += "%7s   " % account # Account names
                    divider += "-------   "
                    if print_running_balances:
                        if csv:
                            output += ",Balance"
                        else:
                            output += "Balance  "
                        divider += "-------  "
        if print_id:
            if csv:
                output += ",ID"
            else:
                output += "    ID  "
            divider += "------  "
        if csv:
            output += ",UID\n"
        else:
            output += "   UID\n"
        divider += "------\n"
        if not csv:
            output += divider

        # Add the records to the database
        n_rows = 1
        for record in printable:
            output += record.__str__(total_value=total_value, print_id=print_id,
                                     w_type=w_type, w_dest=w_dest, w_desc=w_desc,
                                     print_balances=print_running_balances, csv=csv)
            output += "\n"
            if not csv and n_rows % 5 == 0:
                output += "\n"
            n_rows += 1
        if not csv:
            output += divider

        # print summary information only when not csv
        if not csv:
            # The number of spaces required to line up the Total labels correctly
            colspace = 2
            balance_spacing = w_date + w_type + w_dest + w_desc + (colspace*4) - 19

            # Print a line of account totals of visible records
            output += "%s Total visible:  " % (" "*balance_spacing)
            if total_value:
                output += "%9.2f " % balances['visible']['sum']
            else:
                for key, value in balances['visible'].iteritems():
                    if key != 'sum' and self.is_printable(key):
                        output += "%9.2f " % value
            output += "\n"

            # Print a line of account totals over all records
            output += "%s Total balance:  " % (" "*balance_spacing)
            if total_value:
                output += "%9.2f " % balances['all']['sum']
            else:
                for key, value in balances['all'].iteritems():
                    if key != 'sum' and self.is_printable(key):
                        output += "%9.2f " % value
            output += "\n"

            vistotal = balances['visible']['sum']
            total = balances['all']['sum']
            weekly = balances['thisweek']['sum']

            remaining = self.settings.allowance()+weekly
            output += "    Visible:    %9.2f   (%d records)\n" % (vistotal, len(printable))
            output += "    Balance:    %9.2f\n" % total
            if self.settings.allowance() > 0.0:
                output += "    This Week:  %9.2f\n" % weekly
                output += "    Remaining:  %9.2f\n" % remaining

        return output

    #--------------------------------------------------------------------------
    # Admin functions for editing the database
    #--------------------------------------------------------------------------

    def add(self, record):
        """ Add a Transaction object (record) to the database """
        self.records.append(record)
        self.is_changed = True

    def new_record(self):
        """ Make a new record, get user input for it, and add to the database"""
        new = transaction.Transaction(self, self.settings)
        try:
            new.input_values()
        except (KeyboardInterrupt, SystemExit):
            print "\nCaught Keyboard Interrupt. This record has not been added."
        else:
            self.add(new)
            #! Would be nice to append this new record to the original database file
            #! instead of saving the whole thing
            self.is_changed = True

    def edit(self, uid):
        """ Prompt for new values for a record with given uid """
        for record in self.records:
            if record.uid == uid:
                #! As in new_record, would like this to handle Ctrl-C nicely,
                #! without saving the changes
                record.input_values()
                return
        self.is_changed = True

    def delete(self, uid, confirm=True):
        """ Delete record specified by uid """
        for record in self.records:
            if record.uid == uid:
                if confirm is True:
                    prompt = "Delete record [%s]? (yes/no) " % record.encode()
                    answer = raw_input(prompt)
                    if answer == "yes":
                        # Uses __cmp__ to check when equal
                        self.records.remove(record)
                else:
                    self.records.remove(record)
        self.is_changed = True

    def sort(self, perm=True):
        """ Sorts the records in the database. """
        self.records.sort()
        # If database was marked changed by something, leave it marked as such
        if self.is_changed is False:
            self.is_changed = perm

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
        outfile = file(outname, 'w')
        outfile.write(self.encode())
        outfile.close()

    #--------------------------------------------------------------------------
    # Functions for printing information about the database
    #--------------------------------------------------------------------------

    def balances(self):
        """ Return a list of balances """
        self.apply_filters()

        balance = {}
        wbalance = {} # Running balance over last week
        vbalance = {} # Balance of visible records
        for acc in self.settings.accounts().iterkeys():
            if acc not in self.settings.deleted_account_keys():
                balance[acc] = 0.0
                wbalance[acc] = 0.0
                vbalance[acc] = 0.0

        for record in self.records:
            for acc, delta in record.deltas.iteritems():
                if acc not in self.settings.deleted_account_keys():
                    balance[acc] += delta
                    record.set_running_balance(acc, balance[acc])
            if record.visible is True:
                for acc, delta in record.deltas.iteritems():
                    if acc not in self.settings.deleted_account_keys():
                        if record.date > self.settings.TODAY - self.settings.ONEWEEK:
                            wbalance[acc] += delta
                        vbalance[acc] += delta

        # Now add another field for the sum in the default currency
        balance['sum'] = 0.0
        vbalance['sum'] = 0.0
        wbalance['sum'] = 0.0
        for acc, value in balance.iteritems():
            # protect against the fact that 'sum' will be one of the accounts...
            if acc != 'sum':
                if acc in self.settings.foreign_account_keys():
                    balance['sum'] += balance[acc]*self.settings.exchange(acc)
                    vbalance['sum'] += vbalance[acc]*self.settings.exchange(acc)
                    wbalance['sum'] += wbalance[acc]*self.settings.exchange(acc)
                else:
                    balance['sum'] += balance[acc]
                    vbalance['sum'] += vbalance[acc]
                    wbalance['sum'] += wbalance[acc]

        # Return the result
        result = {
            'all':balance,
            'visible':vbalance,
            'thisweek':wbalance
        }
        return result

    def balances_by_type(self):
        """ Return a dictionary of types and their balances """
        self.apply_filters()
        balances = {}
        for record in self.records:
            if record.visible:
                if record.type not in balances:
                    balances[record.type] = record.value()
                else:
                    balances[record.type] += record.value()

        balances = self.sort_balances(balances)
        return balances # this is a list of tuples

    #! For ByType and ByRecipient, include a field with the number of
    #! transactions --- will need to rework how these functions are used

    def balances_by_recipient(self):
        """ Return a list of recipients with the money spent on them """
        # Respects filters
        self.apply_filters()
        balances = {}
        for record in self.records:
            if record.visible:
                # check that this destination exists yet
                if record.dest not in balances:
                    balances[record.dest] = record.value()
                else:
                    balances[record.dest] += record.value()

        balances = self.sort_balances(balances)
        return balances # this is a list of tuples


    def sort_balances(self, balances):
        """ Helper func to sort dictionaries of balances by value """
        items = [(value, key) for key, value in balances.items()]
        items.sort()
        items.reverse() # so largest is first
        # Our dictionary has become a list of tuples to maintain order
        #return [(k, v) for v, k in items]
        # The GUI requires the value be a string.
        return [(key, "%.2f" % value) for value, key in items]


    def integrate_deltas(self, visible_only=True):
        """ Provides actual balance of the accounts as a function of time """

        self.apply_filters()

        values = []

        total = 0.0

        balances = {}
        for acc in self.settings.accounts().iterkeys():
            balances[acc] = 0.0

        self.sort(perm=False)
        date_set = False

        for record in self.records:
            if (visible_only and record.visible) or visible_only is False:
                if date_set is False:
                    current_date = record.date
                    date_set = True
                this_date = record.date
                if this_date == current_date:
                    for acc, delta in record.deltas.iteritems():
                        balances[acc] += delta
                    total += record.value()
                else:
                    while this_date != current_date:
                        this_value = [current_date]
                        this_value.extend(balances.values())
                        this_value.append(total)
                        values.append(this_value)
                        current_date = current_date+timedelta(1)
                    for acc, delta in record.deltas.iteritems():
                        balances[acc] += delta
                    total += record.value()

        this_value = [current_date]
        this_value.extend(balances.values())
        this_value.append(total)
        values.append(this_value)
        return values


    def integrate(self, n=7, visible_only=True, independent=False):
        """ Return deltas integrated over previous n days, 7 by default """

        self.apply_filters()

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
        date_set = False # Need to find first visible record before setting date

        for record in self.records:
            if (visible_only and record.visible) or visible_only is False:
                if date_set is False:
                    # Get the date of the first record we're actually printing
                    current_date = record.date
                    date_set = True
                this_date = record.date
                if this_date == current_date:
                    dtotals[i] += record.value()

                else:
                    while this_date != current_date:

                        # Go on to the next day
                        if ndays >= (n-1):
                            # Print every day if we don't care about keeping points independent
                            # Else just print every nth point
                            if (not independent) or (ndays%n == n-1):
                                values.append((current_date, sum(dtotals)))
                                total += sum(dtotals)
                        i = (i+1)%n
                        current_date = current_date+timedelta(1)
                        # If still not at the right day, set this day to 0 value
                        if current_date != this_date:
                            dtotals[i] = 0.0
                        ndays += 1

                    # Now we have the correct day, add it
                    dtotals[i] = record.value()

        if ndays >= n:
            if (not independent) or (ndays%n == n-1):
                values.append((current_date, sum(dtotals)))
                total += sum(dtotals)

        return values
    #! The above stops on the last record, not the last day in the range


    def predict_destination(self, expense_type, num=1):
        """ Get the n last destinations of a given type """
        predictions = []
        for record in reversed(self.records):
            if record.type == expense_type:
                if record.dest not in predictions:
                    if len(predictions) == num - 1:
                        # This will be the last prediction asked for
                        predictions.append(record.dest)
                        return predictions
                    else:
                        predictions.append(record.dest)
        # In case we didn't find n unique dests
        return predictions

    def predict_description(self, dest, expense_type=None, num=1):
        """ Get the n last descriptions of a given dest """
        predictions = []
        for record in reversed(self.records):
            if record.dest == dest:
                # Optionally limit ourselves to a specific type
                if record.type == expense_type or expense_type is None:
                    if record.desc not in predictions:
                        if len(predictions) == num - 1:
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

    def reset_filters(self):
        """ Remove all filters applied """
        for filt in self.filters.iterkeys():
            self.filters[filt] = None


    def set_filter_defaults(self):
        """ Set filters back to their defaults """
        self.filters = self.settings.filters()


    # Filter behaviour may be inconsistent...
    def filter_type(self, expense_type, flag=True):
        """ Filter records that match type """
        # Check if the first character is a negation
        if str.find(expense_type, self.settings.not_character()) == 0:
            flag = not flag
            expense_type = expense_type[1:]
        types = str.split(expense_type, ',')
        for record in self.records:
            if record.visible and (record.type in types):
                record.visible = flag
            elif record.visible:
                record.visible = not flag

    def filter_recipient(self, dest, flag=True):
        """ Filter records that match recipient """
        recips = str.split(dest, ',')
        for record in self.records:
            if record.visible and (record.dest in recips):
                record.visible = flag
            elif record.visible:
                record.visible = not flag

    def filter_uid(self, uid, flag=True):
        """ Filter for specific UID and only UID"""
        for record in self.records:
            if record.visible and record.uid == uid:
                record.visible = flag
            elif record.visible:
                record.visible = not flag

    def filter_string(self, needle, flag=True):
        """ Filter according to whether record description contains a string """
        for record in self.records:
            if record.visible:
                if record.desc.find(needle) >= 0 or record.dest.find(needle) >= 0:
                    record.visible = flag
                else:
                    record.visible = not flag

    def filter_week(self, num_weeks=1):
        """ Filter out records older than n weeks (default n=1) from today"""
        for record in self.records:
            if (record.date <= self.settings.TODAY - self.settings.ONEWEEK*num_weeks
                    or record.date > self.settings.TODAY):
                record.visible = False

    def filter_value(self, valmin=None, valmax=None, flag=True):
        """ Filter out records with less than total abs(value) val """
        if valmin is None and valmax is None:
            return
        for record in self.records:
            if record.visible:
                if valmin != None and record.value() < valmin:
                    record.visible = not flag
                if valmax != None and record.value() > valmax:
                    record.visible = not flag

    def filter_account(self, account_string, flag=True):
        """ Filter by requiring account delta is non-zero """

        accounts = str.split(account_string, ',')
        for account in accounts:
            # Get index of account we want. Will be same index as delta array.
            if account in self.settings.account_names():
                # Given the name we must find the key
                 # KERROR should never survive loop below since we already know the name exists
                key = 'KERROR'
                for acc, name in self.settings.accounts().iteritems():
                    if name == account:
                        key = acc
                # Now find records with non-zero deltas for this account
                for record in self.records:
                    if key in record.deltas:
                        if record.deltas[key] != 0.0 and record.visible:
                            record.visible = flag
                    elif record.visible:
                        record.visible = not flag
            else:
                print 'Account %s does not exist' % account


    def filter_date(self, mindate, maxdate=None, flag=True):
        """ Include anything between mindate up to but not including maxdate """
        # Takes two DATES for now

        if maxdate is None:
            maxdate = self.settings.TODAY+timedelta(1)

        for record in self.records:
            if record.visible:
                if record.date < mindate or record.date >= maxdate:
                    record.visible = not flag

    def filter_reset(self):
        """ Reset all records to print """
        # Not to be confused with reset_filters, which changes filters dictionary
        for record in self.records:
            record.visible = True

    def filter_invert(self):
        """ Invert the current filters """
        for record in self.records:
            record.visible = not record.visible

    def apply_filters(self):
        """ Apply the entire filters dictionary to the database """
        self.filter_reset()

        # Apply the date filter
        if self.filters['dates'] != None:
            if str.find(self.filters['dates'], 'W') == 0:
                # If filter starts with w, filter to number of weeks specified
                # e.g. w52 for one year
                self.filter_week(int(self.filters['dates'][1:]))
            else:
                # Else we should have the yyyy-mm-dd,yyyy-mm-dd format
                # Get the two possible arguments
                args = str.split(self.filters['dates'], ",")

                # Get the first date
                mindate = str.split(args[0], "-")
                mindate = date(int(mindate[0]), int(mindate[1]), int(mindate[2]))

                # Look for second date, and use it to set filter if it's there
                try:
                    maxdate = str.split(args[1], "-")
                     # Transaction date
                    maxdate = date(int(maxdate[0]), int(maxdate[1]), int(maxdate[2]))
                    self.filter_date(mindate, maxdate)
                except:
                    self.filter_date(mindate)

        # Apply the accounts filter
        if self.filters['accounts'] != None:
            # We print only the account in the string
            self.filter_account(self.filters['accounts'])

        # Apply the filter by type
        if self.filters['types'] != None:
            self.filter_type(self.filters['types'])

        # Apply the filter by recipient
        if self.filters['recipients'] != None:
            self.filter_recipient(self.filters['recipients'])

        # Apply the desc/dest string filter
        if self.filters['string'] != None:
            #! Can we put multiple string filters in filter dictionary at once?
            #! eg for filter in self.filters['string']...
            if self.filters['string'][0] == self.settings.not_character():
                self.filter_string(self.filters['string'][1:], flag=False)
            else:
                self.filter_string(self.filters['string'])

        if self.filters['values'] != None:
            values = str.split(self.filters['values'], ',')
            if values[0] == '':
                values[0] = None
            else:
                values[0] = float(values[0])
            if len(values) > 1:
                if values[1] == '':
                    values[1] = None
                else:
                    values[1] = float(values[1])
            else:
                values.append(None) # add a values[1] spot

            # If values are out of order, flip them
            if (values[0] != None) and (values[1] != None) and (values[1] < values[0]):
                minval = values[1]
                values[1] = values[0]
                values[0] = minval

            self.filter_value(values[0], values[1])

        # Remove the UIDs listed
        if self.filters['uid'] != None:
            uids = str.split(self.filters['uid'], ',')
            for uid in uids:
                self.filter_uid(uid, False)


    def is_printable(self, name):
        """ Return a boolean saying whether the account is allowed by the columns filter """
        if (self.filters['columns'] is not None
                and self.filters['columns'] not in ["None", "none", "All", "all"]):
            allowed = self.filters['columns'].split(',')
            if name in self.settings.account_names():
                return bool(name in allowed)
            elif name in self.settings.account_keys():
                # First convert the names allowed to their keys
                allowed_keys = []
                for account in allowed:
                    allowed_keys.append(self.settings.account_key(account))
                return bool(name in allowed_keys)
            else:
                print "Error: account %s not recognized in is_printable" % name
                return False
        elif self.filters['columns'] in ["None", "none"]:
            return False
        else:
            return True # no columns = all columns

    # EXTRA STUFF FOR POSSIBLE GUI
    def headings(self):
        """ Write database column headings to a tuple """
        output = ['Date', 'Type', 'Recipient', 'Description']
        for name in self.settings.account_names():
            if name not in self.settings.deleted_account_names():
                output.append(name)
        output.append('ID')
        output.append('UID')
        return tuple(output)
