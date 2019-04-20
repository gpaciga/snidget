""" Defines transaction class, containing info on individual transactions"""

from datetime import date
from time import time
import readline


def new_uid():
    """ Generate a UID based on the current timestamp """
    # Backwards timestamp to convert to base 62
    decimal = int(str(int(time()))[::-1])
    obase = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    uid = ""
    p = 1
    #For some reason this doesn't work for while decimal>=0
    while decimal != 0:
        tmp = decimal % 62**p
        digit = obase[tmp/(62**(p-1))]
        uid = "%s%s" % (digit, uid)
        decimal -= tmp
        p += 1

    # Pad with zeros on the left to make exactly six digits long
    while len(uid) < 6:
        uid = "0%s" % uid

    return uid


class Transaction(object):
    """ Transaction class, containing info on individual transactions"""

    def __init__(self, database, settings, record_string=""):
        """ Parse a string into a new transaction, or create an empty one """
        self.database = database
        self.settings = settings
        if record_string == "":
            self.date = self.settings.TODAY
            self.type = ""
            self.dest = ""
            self.desc = ""
            self.deltas = {}
            self.resulting_balance = {}
            self.id = ""
            self.uid = new_uid()
            self.visible = True

        else:
            # Split the string, with trailing whitespace (including \n) removed
            record_list = str.split(record_string.rstrip(), "|")

            date_list = str.split(record_list[0], "-")
             # Transaction date
            self.date = date(int(date_list[0]), int(date_list[1]), int(date_list[2]))

            self.type = record_list[1] # Type
            self.dest = record_list[2] # Destination/Location
            self.desc = record_list[3] # Description

            self.deltas = {}

            # split string of deltas into individual An=0.0 strings
            deltastrings = record_list[4].split(',')
            for string in deltastrings:
                arg = string.split('=')

                if len(arg) == 2:
                    if arg[0] in self.settings.accounts():
                        acc = arg[0]
                    else:
                        #! Should ask for a new account name and add it
                        print("Error reading database: Account ID not recognized.")
                    delta = arg[1]
                    self.deltas[acc] = float(delta)

            self.id = record_list[5] # ID
            self.uid = record_list[6]  # Unique ID

            # Correct old 5 digit uids
            # Only need to do this once on any database, since the save fixes it permanently
            while len(self.uid) < 6:
                self.uid = "0%s" % self.uid

            self.resulting_balance = {}
            self.visible = True


    def str_value(self, print_id=True, w_date=10, w_type=9, w_dest=24, w_desc=34):
        """ Write transaction as a string, including only the total value """
        lineformat = "%%-%ds  %%-%ds  %%-%ds  %%-%ds  " % (w_date, w_type, w_dest, w_desc)
        output = lineformat % (self.date, self.type, self.dest, self.desc)
        output += "%9.2f " % self.value()
        if print_id:
            output += "%8s" % self.id
        output += "  %6s" % self.uid
        return output


    def __str__(self, total_value=None, print_id=True, w_date=10, w_type=9, w_dest=24, w_desc=34,
                print_balances=False, csv=False):
        """ Write transaction as a string to be printed """
        # Define the format string using the received inputs for column widths

        if total_value is None:
            total_value = self.settings.total_values()

        if csv:
             # quotes around destination and description, which can have commas themselves
            lineformat = '%s,%s,"%s","%s"'
        else:
            lineformat = "%%-%ds  %%-%ds  %%-%ds  %%-%ds" % (w_date, w_type, w_dest, w_desc)
        output = lineformat % (self.date, self.type, self.dest, self.desc)
        if total_value:
            if csv:
                output += ",%f" % self.value()
            else:
                output += "%9.2f " % self.value()
        else:
            for acc in self.settings.accounts():
                if (acc not in self.settings.deleted_account_keys()
                        and self.database.is_printable(acc)):
                    if acc in self.deltas.keys():
                        this_value = self.deltas[acc]
                    else:
                        this_value = float("0.0")
                    if csv:
                        output += ",%f" % this_value
                    else:
                        output += "%9.2f " % this_value
                    if print_balances:
                        if csv:
                            output += ","
                        if acc in self.resulting_balance.keys():
                            output += "%9.2f" % self.resulting_balance[acc]
                        else:
                            output += "        "
                        if not csv:
                            output += " "
        if print_id:
            if csv:
                output += ","
            output += "%8s" % self.id
        if csv:
            output += ",%s" % self.uid
        else:
            output += "  %6s" % self.uid
        return output


    def __cmp__(self, other):
        """ Compare transactions for sorting """
        # Must check all attributes, since this tells us when transactions are equal
        #! Possibly if uid==uid, return 0 (to mean they are equal, I think)
        #! Could use to ignore duplicate entries when merging two databases?
        if self.date != other.date:
            return cmp(self.date, other.date)
        elif self.type != other.type:
            return cmp(self.type, other.type)
        elif self.dest != other.dest:
            return cmp(self.dest, other.dest)
        elif self.desc != other.desc:
            return cmp(self.desc, other.desc)
        elif self.value() != other.value():
            return cmp(self.value(), other.value())
        elif self.id != other.id:
            return cmp(self.id, other.id)
        return cmp(self.uid, other.uid)


    def encode(self):
        """ Write the record in text file format for saving """
        record = "%s|%s|%s|%s|" % (self.date, self.type, self.dest, self.desc)
        for account, delta in self.deltas.iteritems():
            if delta != 0.0:
                record += "%s=%.2f," % (account, float(delta))
        if record[:-1] == ",":
            record = record[:-1] # remove trailing comma
        record += "|%s|%s" % (self.id, self.uid)
        return record


    def edit(self):
        """ Alias for input_values """
        self.input_values()


    def value(self):
        """ Return total value of transaction """
        total = 0.0
        for acc, value in self.deltas.iteritems():
            if acc in self.settings.foreign_account_keys():
                total += value*self.settings.exchange(acc)
            else:
                total += value
        return total


    def set_running_balance(self, account, balance):
        """ Set the resulting balance of the account after this transaction """
        self.resulting_balance[account] = balance
        return


    #! Can these all completers be consolidated into one function?
    # Only the list of possibilities changes.
    def complete(self, text, state):
        """ Return possible words in database on tab """
        for cmd in self.database.words():
            if cmd.startswith(text):
                if not state:
                    return cmd
                else:
                    state -= 1
        return None


    def complete_dest(self, text, state):
        """ Return possible words in database on tab """
        for cmd in self.database.places():
            if cmd.startswith(text):
                if not state:
                    return cmd
                else:
                    state -= 1
        return None


    def complete_desc(self, text, state):
        """ Return possible words in database on tab """
        for cmd in self.database.descriptions():
            if cmd.startswith(text):
                if not state:
                    return cmd
                else:
                    state -= 1
        return None


    def complete_type(self, text, state):
        """ Return possible types on tab """
        print(self.settings.types().values())
        for cmd in self.settings.types().values():
            if cmd.startswith(text):
                if not state:
                    return cmd
                else:
                    state -= 1
        return None


    def input_values(self):
        """ Get transaction details from keyboard input """

        # Default values are what already exists in the transaction
        # If no input is given on any field, the old value remains

        # Set up required stuff for tab-completion
        readline.parse_and_bind("tab: complete")

        date_ok = False

        while not date_ok:

            # Get date
            prompt = "Date (%s): " % self.date
            date_string = raw_input(prompt)
            date_string = date_string.strip()

            if date_string != "":
                # from number of dashes, figure out what type of input we got
                num_dashes = date_string.count("-")

                # set the defaults
                input_day = self.date.day
                input_month = self.date.month
                input_year = self.date.year

                if num_dashes == 0:
                    # assuming number is date only
                    input_day = int(date_string)
                elif num_dashes == 1:
                    date_list = str.split(date_string, "-")
                    input_month = int(date_list[0])
                    input_day = int(date_list[1])
                elif num_dashes == 2:
                    date_list = str.split(date_string, "-")
                    input_year = int(date_list[0])
                    input_month = int(date_list[1])
                    input_day = int(date_list[2])
                else:
                    print("ERROR: did not understand date")
                    continue

                try:
                    self.date = date(input_year, input_month, input_day) # Transaction date
                except ValueError:
                    print("ERROR: could not interpret %s" % date_string)
                    continue

                # Warn if entered date is a long time ago. Might be, e.g., a typo in the year.
                if (self.settings.TODAY - self.date) > self.settings.ONEWEEK:
                    print('WARNING: Date entered is greater than one week ago!')
                # Otherwise date stays the same, which will be today if new transaction

            # if we got past all the continues above, then the date is OK
            date_ok = True

        # Get transaction type
        types = self.settings.types()

        # Try to complete type on tab
        readline.set_completer(self.complete_type)

        optlist = ""
        for index, expense_type in enumerate(types):
            optlist += "[%d] %s  " % (index, expense_type)
        print(optlist)
        prompt = "Type (%s): " % self.type
        answer = raw_input(prompt)
        answer = answer.strip()
        if answer != "":
            try:
                self.type = types[int(answer)]
            except ValueError:
                if answer in types:
                    self.type = answer
                else:
                    print("WARNING: Type not recognized")
                    #! Should abort or retry or something

        # Go to special transfer function if deltas not already defined
        if self.type == "Transfer" and not self.deltas:
            self.input_transfer()
            # and deltas is empty...
            return

        # Depending on settings, get fixed list of places or dynamic prediction
        if self.settings.predict_destination():
            places = self.database.predict_destination(self.type, self.settings.number_to_predict())
        else:
            places = self.settings.places()

        # Try to complete destination on tab
        readline.set_completer(self.complete_dest)
        optlist = ""
        for index, place in enumerate(places):
            optlist += "[%d] %s  " % (index, place)
        print(optlist)
        prompt = "Places (%s): " % self.dest
        answer = raw_input(prompt)
        answer = answer.strip()
        if answer != "":
            try:
                self.dest = places[int(answer)]
            except ValueError:
                self.dest = answer

        # Use predictive input on the description
        #! Can most recent be default? If so, what if I want a null description?
        predictions = self.database.predict_description(
            self.dest, self.type, self.settings.number_to_predict())
        optlist = ""
        for index, prediction in enumerate(predictions):
            optlist += "[%d] %s  " % (index, prediction)
        print(optlist)

        # Try to complete description on tab
        readline.set_completer(self.complete_desc)

        # Get description
        prompt = "Description (%s): " % self.desc
        answer = raw_input(prompt)
        answer = answer.strip()
        if answer != "":
            try:
                self.desc = predictions[int(answer)]
            except ValueError:
                self.desc = answer

        # Turn off tab completion
        readline.set_completer(None)

        for acc, name in self.settings.accounts().iteritems():
            # Get default value for this account, if it already exists in deltas
            if acc not in self.settings.deleted_account_keys() and self.database.is_printable(acc):
                if acc in self.deltas:
                    value = self.deltas[acc]
                else:
                    value = 0.0
                prompt = "%s (%.2f): " % (name, value)
                answer = raw_input(prompt)
                answer = answer.strip()
                if answer != "":
                    if self.type in self.settings.positive_types():
                        self.deltas[acc] = float(answer)
                    else:
                        self.deltas[acc] = float(answer)*-1

        # Get user specified ID
        prompt = "ID (%s): " % self.id
        answer = raw_input(prompt)
        answer = answer.strip()
        if answer != "":
            self.id = answer

        # UID already exists in the record
        print(self.uid)


    def input_transfer(self):
        """ Automatically subtract from one account and add to the other """
        # Set up required stuff for tab-completion
        readline.parse_and_bind("tab: complete")

        # First get the two accounts we're transfering between
        allkeys = self.settings.account_keys()
        keys = []
        for key in allkeys:
            if self.database.is_printable(key):
                keys.append(key)
        optlist = ""
        for index, key in enumerate(keys):
            optlist += "[%d] %s  " % (index, self.settings.account_name(key))
        print(optlist)
        prompt = "From: "
        answer = raw_input(prompt)
        answer = answer.strip()
        if answer != "":
            source = keys[int(answer)]
        prompt = "To: "
        answer = raw_input(prompt)
        answer = answer.strip()
        if answer != "":
            dest = keys[int(answer)]
            self.dest = self.settings.account_name(dest)

        if (dest in self.settings.foreign_account_keys()
                or source in self.settings.foreign_account_keys()):
            print("WARNING: Transfering between different currencies isn't well supported")
            print("         You will have to edit this record with -e to adjust the values")

        # Try to complete destination on tab
        readline.set_completer(self.complete_desc)

        # Get description
        prompt = "Description (%s): " % self.desc
        answer = raw_input(prompt)
        answer = answer.strip()
        if answer != "":
            self.desc = answer

        # Get ammount
        prompt = "Amount: "
        answer = raw_input(prompt)
        answer = answer.strip()
        if answer != "":
            self.deltas[source] = float(answer)*-1
            self.deltas[dest] = float(answer)

        # Get user specified ID
        prompt = "ID (%s): " % self.id
        answer = raw_input(prompt)
        if answer != "":
            self.id = answer

        # UID already exists in the record
        print(self.uid)


    # EXTRA STUFF FOR GUI
    def tuple(self):
        """ Output record as tuple for GUI """
        output = [str(self.date), self.type, self.dest, self.desc]
        for acc in self.settings.account_keys():
            if acc not in self.settings.deleted_account_keys():
                if acc in self.deltas.keys():
                    output.append('%.2f' % self.deltas[acc])
                else:
                    output.append('%.2f' % 0.0)
        output.append(self.id)
        output.append(self.uid)
        return tuple(output)
