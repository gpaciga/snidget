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


""" Defines transaction class, containing info on individual transactions"""

class Transaction:
    """ Transaction class, containing info on individual transactions"""
    def __init__(self, database, settings, recordString=""):
        """ Parse a string into a new transaction, or create an empty one """
        self.database = database
        self.settings = settings
        if recordString == "":
            self.date = self.settings.TODAY
            self.type = ""
            self.dest = ""
            self.desc = ""
            self.deltas = {}
            self.resultingBalance = {}
            self.id = ""
            self.uid = self.newUID()
            self.visible = True

        else:
            from datetime import date

            #Split the string, with trailing whitespace (including \n) removed
            recordList = str.split(recordString.rstrip(),"|")
            
            dateList = str.split(recordList[0],"-")
            self.date = date(int(dateList[0]), int(dateList[1]), int(dateList[2])) # Transaction date        
            
            self.type = recordList[1] # Type
            self.dest = recordList[2] # Destination/Location
            self.desc = recordList[3] # Description
            
            # If these strings are empty, should make 0
            #self.deltas=[]
            #self.newdeltas={}
            #for i in range(0,NACCOUNTS):
            #    self.deltas.append(float(recordList[4+i]))
            #    self.newdeltas["A%d"%i] = float(recordList[4+i])
            #print self.newdeltas
            
            self.deltas = {}

            # split string of deltas into individual An=0.0 strings
            deltastrings = recordList[4].split(',')
            for string in deltastrings:
                arg = string.split('=')

                if (len(arg) == 2):
                    if (arg[0] in self.settings.accounts()):
                        acc = arg[0]
                    else:
                        #! Should ask for a new account name and add it
                        print "Error reading database: Account ID not recognized."
                    delta = arg[1]
                    self.deltas[acc] = float(delta)

            self.id = recordList[5] # ID
            self.uid = recordList[6]  # Unique ID

            # Correct old 5 digit uids
            # Only need to do this once on any database, since the save fixes it permanently
            while len(self.uid)<6:
                self.uid = "0%s" % self.uid

            self.resultingBalance = {}
            self.visible = True

    def strValue(self, printID=True, wDate=10, wType=9, wDest=24, wDesc=34): 
        """ Write transaction as a string, including only the total value """
        lineformat = "%%-%ds  %%-%ds  %%-%ds  %%-%ds  " % (wDate, wType, wDest, wDesc)
        output = lineformat % (self.date, self.type, self.dest, self.desc)
        output += "%9.2f " % self.value()
        if (printID):
            output += "%8s" % self.id
        output += "  %6s" % self.uid
        return output


    def __str__(self, totalValue=None, printID=True, wDate=10, wType=9, wDest=24, wDesc=34, printBalances=False, csv=False): 
        """ Write transaction as a string to be printed """
        # Define the format string using the received inputs for column widths

        if (totalValue is None):
            totalValue = self.settings.totalvalues()

        if csv:
            lineformat = '%s,%s,"%s","%s"' # quotes around destination and description, which can have commas themselves
        else:
            lineformat = "%%-%ds  %%-%ds  %%-%ds  %%-%ds" % (wDate, wType, wDest, wDesc)
        output = lineformat % (self.date, self.type, self.dest, self.desc)
        if (totalValue):
            if csv:
                output += ",%f" % self.value()
            else:
                output += "%9.2f " % self.value()
        else:
            for acc in self.settings.accounts():
                if acc not in self.settings.deletedAccountKeys() and self.database.is_printable(acc):
                    if acc in self.deltas.keys():
                        this_value = self.deltas[acc]
                    else:
                        this_value = float("0.0")
                    if csv:
                        output += ",%f" % this_value
                    else:
                        output += "%9.2f " % this_value
                    if printBalances:
                        if csv: output += ","
                        if acc in self.resultingBalance.keys():
                            output += "%9.2f" % self.resultingBalance[acc]
                        else:
                            output += "        "
                        if not csv: output += " "
        if (printID):
            if csv: output += ","
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
        else:
            return cmp(self.uid, other.uid)

    def encode(self):
        """ Write the record in text file format for saving """
        record = "%s|%s|%s|%s|" % (self.date, self.type, self.dest, self.desc)
        for account, delta in self.deltas.iteritems():
            if (delta != 0.0):
                record += "%s=%.2f," % (account, float(delta))
        if (record[:-1] == ","):
            record = record[:-1] # remove trailing comma
        record += "|%s|%s" % (self.id, self.uid)
        return record

    def edit(self):
        """ Alias for inputValues """
        self.inputValues()

    def value(self):
        """ Return total value of transaction """
        #return sum(self.deltas.values())
        total = 0.0
        for acc, value in self.deltas.iteritems():
            if acc in self.settings.foreignAccountKeys():
                total += value*self.settings.exchange(acc)
            else:
                total += value
        return total

    def setRunningBalance(self, account, balance):
        """ Set the resulting balance of the account after this transaction """
        self.resultingBalance[account] = balance
        return 

    def newUID(self):
        """ Generate a UID based on the current timestamp """
        # Note this is one direction only

        from time import time

        # Backwards timestamp to convert to base 62
        decimal = int(str(int(time()))[::-1])
        
        #ibase = "0123456789"
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
        while len(uid)<6:
            uid = "0%s" % uid

        return uid

    def complete(self, text, state):
        """ Return possible words in database on tab """
        for cmd in self.database.words():
            if cmd.startswith(text):
                if not state:
                    return cmd
                else:
                    state -= 1
        # No idea what the "state" business is about


    #! Can these all be consolidated into one function?
    # Only the list of possibilities changes.

    def complete_dest(self, text, state):
        """ Return possible words in database on tab """
        for cmd in self.database.places():
            if cmd.startswith(text):
                if not state:
                    return cmd
                else:
                    state -= 1
        # No idea what the "state" business is about

    def complete_desc(self, text, state):
        """ Return possible words in database on tab """
        for cmd in self.database.descriptions():
            if cmd.startswith(text):
                if not state:
                    return cmd
                else:
                    state -= 1
        # No idea what the "state" business is about
                    
    def complete_type(self, text, state):
        """ Return possible types on tab """
        print self.settings.types().values()
        for cmd in self.settings.types().values():
            if cmd.startswith(text):
                if not state:
                    return cmd
                else:
                    state -= 1
        # No idea what the "state" business is about

    def inputValues(self):
        """ Get transaction details from keyboard input """

        # Default values are what already exists in the transaction
        # If no input is given on any field, the old value remains

        # Set up required stuff for tab-completion
        import readline        
        readline.parse_and_bind("tab: complete")

        dateOK = False
        
        while not dateOK:
    
            # Get date
            prompt = "Date (%s): " % self.date
            dateString = raw_input(prompt)
            dateString = dateString.strip()

            if dateString != "":
                from datetime import date

                # from number of dashes, figure out what type of input we got
                ndash = dateString.count("-")

                # set the defaults
                inputDay = self.date.day
                inputMonth = self.date.month
                inputYear = self.date.year

                if ndash == 0:
                    # assuming number is date only
                    inputDay = int(dateString)
                elif ndash == 1:
                    dateList = str.split(dateString,"-")
                    inputMonth = int(dateList[0])
                    inputDay = int(dateList[1])
                elif ndash == 2:
                    dateList = str.split(dateString,"-")
                    inputYear = int(dateList[0])
                    inputMonth = int(dateList[1])
                    inputDay = int(dateList[2])
                else:
                    print "ERROR: did not understand date"
                    continue

                #self.date = date(int(dateList[0]), int(dateList[1]), int(dateList[2])) # Transaction date        
                try:
                    self.date = date(inputYear, inputMonth, inputDay) # Transaction date
                except:
                    print "ERROR: could not interpret %d-%d-%d" % (inputYear, inputMonth, inputDay)
                    continue

                # Warn if entered date is a long time ago. Might be, e.g., a typo in the year.
                if (self.settings.TODAY - self.date) > self.settings.ONEWEEK:
                    print 'WARNING: Date entered is greater than one week ago!'
                # Otherwise date stays the same, which will be today if new transaction
            #endif
        
            # if we got past all the continues above, then the date is OK
            dateOK = True

        #endwhile

        # Get transaction type
        types = self.settings.types() # [0]=key, [1]=value
        
        # Try to complete type on tab
        readline.set_completer(self.complete_type)
        
        for i in range(0, len(types)):
            optlist = "[%d] %s " % (i, types[i])
            print optlist,
        print
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
                    print "WARNING: Type not recognized"
                    #! Should abort or retry or something
                

        # Go to special transfer function if deltas not already defined
        if self.type == "Transfer" and len(self.deltas) == 0:
            self.inputTransfer()
            # and deltas is empty...
            return


        # Depending on settings, get fixed list of places or dynamic prediction
        if self.settings.predictdest():
            places = self.database.predictDest(self.type, self.settings.npredict())
        else:
            places = self.settings.places()

        # Try to complete destination on tab
        readline.set_completer(self.complete_dest)

        for i in range(0, len(places)):
            optlist = "[%d] %s " % (i, places[i])
            print optlist,
        print
        prompt = "Places (%s): " % self.dest
        answer = raw_input(prompt)
        answer = answer.strip()
        if answer != "":
            try:
                self.dest = places[int(answer)]
            except ValueError:
                self.dest = answer

        # Get location the old way
        #for i in range(0,len(self.settings.places())):
        #    list="[%d] %s " % (i,self.settings.places(i))
        #    print list,
        #print
        #prompt="Places (%s): " % self.dest
        #answer=raw_input(prompt)
        #if answer != "":
        #    try:
        #        self.dest=self.settings.places(int(answer))
        #    except:
        #        self.dest=answer

        
        # Use predictive input on the description
        #! Can most recent be default? If so, what if I want a null description?
        predictions = self.database.predictDesc(self.dest, self.type, self.settings.npredict())
        for i in range(0, len(predictions)):
            optlist = "[%d] %s " % (i, predictions[i])
            print optlist,
        print

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
            if acc not in self.settings.deletedAccountKeys() and self.database.is_printable(acc):
                if acc in self.deltas:
                    value = self.deltas[acc]
                else:
                    value = 0.0
                prompt = "%s (%.2f): " % (name, value)
                answer = raw_input(prompt)
                answer = answer.strip()
                if answer != "":
                    if self.type in self.settings.postypes():
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
        print self.uid


    def inputTransfer(self):
        """ Automatically subtract from one account and add to the other """
        # Set up required stuff for tab-completion
        import readline        
        readline.parse_and_bind("tab: complete")

        # First get the two accounts we're transfering between
        allkeys = self.settings.accountKeys()
        keys = []
        for key in allkeys:
            if self.database.is_printable(key):
                keys.append(key)
        for i in range(0, len(keys)):
            optlist = "[%d] %s " % (i, self.settings.accountName(keys[i]))
            print optlist,
        print
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
            self.dest = self.settings.accountName(dest)
            
        if dest in self.settings.foreignAccountKeys() or source in self.settings.foreignAccountKeys():
            print "WARNING: Transfering between different currencies isn't well supported"
            print "         You will have to edit this record with -e to adjust the values"

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
            self.deltas[dest]   = float(answer)
            
        # Get user specified ID
        prompt = "ID (%s): " % self.id
        answer = raw_input(prompt)
        if answer != "":
            self.id = answer

        # UID already exists in the record
        print self.uid


    # EXTRA STUFF FOR GUI
    def tuple(self):
        """ Output record as tuple for GUI """
        output = [str(self.date), self.type, self.dest, self.desc]
        for acc in self.settings.accountKeys():
            if acc not in self.settings.deletedAccountKeys():
                if acc in self.deltas.keys():
                    output.append('%.2f' % self.deltas[acc])
                else:
                    output.append('%.2f' % 0.0)
        output.append(self.id)
        output.append(self.uid)
        return tuple(output)

# END Transaction class
