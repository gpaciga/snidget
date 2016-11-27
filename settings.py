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

""" Manage and store user settings """

#! Currently no way to edit the prediction behaviour
#! Also need to add ability to change postypes and extypes

#! If deleting an account, to which no transactions are associated,
#  we can remove it permanently


class Settings:
    """ Manage and store user settings """

    from datetime import date
    from datetime import timedelta
    from time import time

    # Set some convenient constants
    TODAY = date.today()
    ONEWEEK = timedelta(7)

    # This is the default set of options
    # These will be overwritten if settings.pkl exists
    options = {
        'DATABASE' : "expenses.txt",
        'NETBASE' : "",
        'NETPOST' : "",
        'MAXPRINT' : 25,           # Maximum number of records to print by default
        'ALLOWANCE' : 100,         # Basis for calculating "Remaining" total
        'TOTALVALUES' : False,     # Whether to print the total value or the value of each account
        'NPREDICT' : 6,            # Number of predictions to suggest
        'DOPREDICTDEST' : True,    # Whether to predict the destination or use the places array below
        'NOTCHAR' : '!',           # Character used to negate strings

        # Only used if prediction of places is turned off
        # Different place options for different types?
        'places' : [ "Shoppers Drug Mart", "Metro", "Tim Horton's", "Starbucks", "7-11", ],

        # Change these if you want, though it's not recommended
        # Dollar values in the types Income, Adjustment, and Transfer are ADDED to account balances
        # Dollar values in any other type of transaction are SUBTRACTED from account balances
        'types'    : [ "Income", "Transfer", "Adjustment", "Bill", "Food", "School", "Household",  "Extras" ],
        'postypes' : [ "Income", "Transfer", "Adjustment" ],
        'extypes'  : [ "Food", "School", "Household", "Extras" ],
        
        # This should only be changed by using -o delaccount or -o addaccount options
        'accounts' : { "A0":"Bank", "A1":"Credit", "A2":"Cash" },
        
        # This holds the keys of accounts which are hidden
        'deletedAccounts': [],
        
        # Default filters are the ones used when the program first starts up
        # Each one must be a string, enclosed in single quotes, with no spaces
        # They are the same strings you would use on the command line
        
        # Example filters:
            # dates: Date ranges, e.g. '2009-01-01,2009-07-01' or a number of weeks to show, e.g. 'W1' or 'W52'
        # accounts: List of accounts to include, e.g. 'BMO,RBC'
        # types: List of types to display, e.g. 'Income,Bill'
        # string: Require this string in the description, e.g. "Tim Horton's"
        # values: A maximum and minimum value for transactions to show, e.g. '-20,0' means expenses less than $20
        # uid: Exclude UIDs in the list, e.g. '13gG3X,3ys93D,49sKaP'
        
        'FILTERS' : {
            'dates':'W1',
            'accounts':None,
            'types':None,
            'recipients':None,
            'string':None,
            'values':None,
            'uid':None,
            }
        }

    def __init__(self, filename=None):
        """ Load options from an existing file or read in defaults """

        import sys
        import os
        import pickle

        # Before doing anything, set the correct default filter type
        #self.options['FILTERS']['types'] = self.extypesString()
    

        if (filename==None):
            self.OPTIONSFILE = "%s/%s" % (sys.path[0], 'settings.pkl')
            filename = self.OPTIONSFILE

        if (os.path.exists(filename)):
            # First backup the default options
            defaults = self.options
            # Now load the saved options
            optionsPickle = open(filename,'rb')          
            self.options = pickle.load(optionsPickle)
            optionsPickle.close()
            # Now go through and add any options that are new since the last save
            doSave = False
            for opt,val in defaults.iteritems():
                if opt not in self.options:
                    print "Adding new option "+opt
                    self.options[opt] = val
                    doSave = True
            # Similarly, remove options that are no longer needed
            # remembering you can't remove items during an interation
            delete=[]
            for opt,val in self.options.iteritems():
                if opt not in defaults:
                    delete.append(opt)
            for opt in delete:
                print "Removing defunct option "+opt
                self.options.pop(opt)
                doSave = True
            # Settings were updated so we must save
            if doSave: self.save()
                    
        else:
            #import defaults
            #self.options = defaults.options
            optionsPickle = open(filename,'wb')
            pickle.dump(self.options, optionsPickle)
            optionsPickle.close()
            print "Imported and pickled default options. You should not get this message again."
    # end def init

    def __str__(self):
        """ Convert current options into string for printing """
        output = ""
        for name, value in self.options.iteritems():
            output += "%s = %s\n" % (name, value)
        return output
    # end def __str__



    def save(self, filename=None):
        """ Save current options into file """
        
        #import os
        import pickle

        if (filename==None):
            filename = self.OPTIONSFILE

        optionsPickle = open(filename,'wb')
        pickle.dump(self.options, optionsPickle)
        optionsPickle.close()
        print "Saved options"
    #end def save

    def edit(self, command):
        """ Change an option """

        # Keep track of whether a change is made
        changedOptions = False

        args = str.split(command,'=')

        # Check the format of the argument
        if (args[0] == 'print'):
            print self
            return
        elif (args[0] == 'help'):
            print "Argument for -o are of the format command=argument, where argument is the new value for the setting."
            print "  database=filename       Change the database file used."
            print "  netbase=url             Remove database we can download to get new records"
            print "  netpost=url             URL to access to indicate netbase successfully downloaded"
            print "  maxprint=integer        The maximum number of records to print"
            print "  allowance=value         Setting the weekly allowance value"
            print "  totalvalues=boolean     Whether to display the total value of a record or the delta of each account."
            print "  not=x                   Set the character used to negate strings and types to x."
            print "  addplace=name           Add a suggested place name"
            print "  delplace=name           Remove a suggested place name"
            print "  addtype=name            Add a new type of record"
            print "  deltype=name            Remove a type of record"
            print "  addaccount=name         Add a new account"
            print "  delaccount=name         Delete an account"
            print "  print                   Special command to print the current options in an ugly way"
            return
        elif (len(args) != 2):
            print "Options must be changed using command=argument format. Use -o help for recognized options."
            return

        command = args[0]
        arg = args[1]
    
        # Edit the options accordingly:

        # Change the database file name
        if (command == 'database'):
            oldDatabase = self.database()
            self.setDatabase(arg)
            print "Changed database from '%s' to '%s'" % (oldDatabase, self.database())
            changedOptions = True

        #   netbase='txt'
        elif (command == 'netbase'):
            oldNetbase = self.netbase()
            self.setNetbase(arg)
            print "Changed netbase from '%s' to '%s'" % (oldNetbase, self.netbase())
            changedOptions = True

        #   netpost='script'
        elif (command == 'netpost'):
            oldNetpost = self.netpost()
            self.setNetpost(arg)
            print "Changed netpost from '%s' to '%s'" % (oldNetpost, self.netpost())
            changedOptions = True

        #   maxprint=integer
        elif (command == 'maxprint'):
            oldMaxprint = self.maxprint()
            self.setMaxprint(arg)
            print "Changed maxprint from '%s' to '%s'" % (oldMaxprint, self.maxprint())
            changedOptions = True

        #   allowance=float
        elif (command == 'allowance'):
            oldAllowance = self.allowance()
            self.setAllowance(arg)
            print "Changed allowance from '%s' to '%s'" % (oldAllowance, self.allowance())
            changedOptions = True
            
        #   totalvalues=boolean
        elif (command == 'totalvalues'):
            oldTotalValues = self.totalvalues()
            self.setTotalvalues(arg)
            print "Changed totalvalues from '%s' to '%s'" % (oldTotalValues, self.totalvalues())
            changedOptions = True

        #   not=x
        elif (command == 'not'):
            valid=True
            oldNot = self.notchar()
            if len(arg) != 1:
                print "NOT character must be a single character"
                valid=False
            if arg in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789":
                print "Alphanumeric characters not recommended for the NOT character"
                valid=False
            if valid is True and arg != oldNot:
                self.setNot(arg)
                print "Changed not character from %s to %s" % (oldNot, self.notchar()) 
                changedOptions = True

        #   addplace=string
        elif (command == 'addplace'):
            if self.addPlace(arg):
                print "Added '%s' to places" % arg
                changedOptions = True
            else:
                print "Place %s already exists" % arg                
            
        #   delplace=string
        elif (command == 'delplace'):
            if self.delPlace(arg):
                print "Removed '%s' from places" % arg
                changedOptions = True
            else:
                print "Place not found: %s" % arg

        #   addtype=word
        elif (command == 'addtype'):
            if self.addType(arg):
                print "Added '%s' to types" % arg
                changedOptions = True
            else:
                print "Type %s already exists" % arg

        #   deltype=word
        elif (command == 'deltype'):
            if self.delType(arg):
                print "Removed type %s" % arg
                changedOptions = True
            else:
                print "Could not remove type %s" % arg

        #   addaccount=word
        elif (command == 'addaccount'):
            if self.addAccount(arg):
                print "Added account %s" % arg
                changedOptions = True
            else:
                print "Could not add account %s" % arg

        #   delaccount=word
        elif (command == 'delaccount'):
            if self.delAccount(arg):
                print "Deleted account %s" % arg
                changedOptions = True
            else:
                print "Could not delete account %s" % arg

        elif (command == 'renameaccount'):
            # self.renameAccount(oldname, newname) <- how to read in two arguments? command line? keyboard input?
            print "Cannot rename accounts yet"
            

        #!   filters???

        else:
            print "Unrecognized command. Use -o help for recognized commands."

        # If anything changed, this will be true
        return changedOptions
    #end def edit

    def newAccountKey(self):
        """ Create a unique key for a new account """
        i = 0
        while True:
            key = "A%d" % i
            if key not in self.accountKeys():
                break
            else:
                i = i+1
        return key
        

    # --------------------------------------------------------------------------------
    # Defs to get values of current options
    # --------------------------------------------------------------------------------

    def accounts(self):
        """ Return the accounts dictionary """
        #! Snidget should only need options['accounts'].values() list
        #! Currently uses iteritems, itervalues, and iterkeys...
        #! Can we replace iterkeys by accountKeys() etc?
        return self.options['accounts']

    def accountKeys(self):
        """ Return a list of account codes """
        return self.options['accounts'].keys()

    def accountNames(self):
        """ Return a list of account names """
        return self.options['accounts'].values()

    def visibleAccounts(self):
        """ Return the accounts dictionary with only visible accounts """
        visible = {}
        for acc, name in self.options['accounts'].iteritems():
            if acc not in self.options['deletedAccounts']:
                visible[acc] = name
        return visible

    def visibleAccountKeys(self):
        """ Return the keys of visible accounts """
        visible = []
        for key in self.options['accounts'].keys():
            if key not in self.options['deletedAccounts']:
                visible.append(key)
        return visible

    def visibleAccountNames(self):
        """ Return the visible account names """
        visible = []
        for acc, name in self.options['accounts'].iteritems():
            if acc not in self.options['deletedAccounts']:
                visible.append(name)
        return visible

    def accountKey(self, name):
        """ Return an account key given its name """
        for key, value in self.options['accounts'].iteritems():
            if (value==name):
                return key
        return False
    
    def accountName(self, key):
        """ Return an account name given its key """
        return self.options['accounts'][key]
        
    def deletedAccounts(self):
        """ Alias for deletedAccountKeys """
        return self.deletedAccountKeys()

    def deletedAccountKeys(self):
        """ Return a list of keys of accounts which have been deleted """
        return self.options['deletedAccounts']
    
    def deletedAccountNames(self):
        """ Return a list of names of accounts which have been deleted """
        names = []
        for key in self.deletedAccountKeys():
            names.append(self.accountName(key))
        return names

    def types(self, ind=None):
        """ Return the types dictionary """
        if (ind==None):
            return self.options['types']
        else:
            return self.options['types'][ind]

    def postypes(self):
        """ Return list of positive types """
        return self.options['postypes']

    def protectedTypes(self):
        """ Return types which can not be removed """
        protected = [ "Income", "Transfer", "Adjustment" ]
        return protected

    def extypes(self):
        """ Return types which are considered expenses """
        return self.options['extypes']

    def extypesString(self):
        """ Return expense types as a comma separated string """
        filter=''
        for type in self.options['extypes']:
            if type in self.types():
                filter=filter+','+type
        if str.find(filter,',') == 0:
            filter = filter[1:]
        return filter


    def places(self, ind=None):
        """ Return the list of places """
        if (ind==None):
            return self.options['places']
        else:
            return self.options['places'][ind]

    def filters(self):
        """ Return the filters dictionary """
        return self.options['FILTERS']

    def totalvalues(self):
        """ Return the totalValues setting """
        return self.options['TOTALVALUES']

    def maxprint(self):
        """ Return the maxprint value """
        return self.options['MAXPRINT']

    def allowance(self):
        """ Return the weekly allowance """
        return self.options['ALLOWANCE']

    def netbase(self):
        """ Return the network database address """
        return self.options['NETBASE']

    def netpost(self):
        """ Return the network postscript """
        return self.options['NETPOST']

    def npredict(self):
        """ Return the default number of predictions """
        return self.options['NPREDICT']

    def predictdest(self):
        """ Return a boolean indicating whether we want to predict destinations """
        return self.options['DOPREDICTDEST']

    def database(self):
        """ Return the database file """
        return self.options['DATABASE']
    
    def notchar(self):
        """ Return the not character """
        return self.options['NOTCHAR']

    # --------------------------------------------------------------------------------
    # Defs to change values of current options
    # --------------------------------------------------------------------------------
    
    # These return either True or False indicating whether they were successful

    def setDatabase(self, filename):
        """ Set the database file name """
        self.options['DATABASE'] = filename
        return True

    def setNetbase(self, url):
        """ Set the netbase url """
        self.options['NETBASE'] = url
        return True

    def setNetpost(self, url):
        """ Set the netpost url """
        self.options['NETPOST'] = url
        return True

    def setMaxprint(self, maxval):
        """ Set the maxprint """
        self.options['MAXPRINT'] = int(maxval)
        return True

    def setAllowance(self, value):
        """ Set the weekly allowance """
        self.options['ALLOWANCE'] = float(value)
        return True

    def setTotalvalues(self, arg):
        """ Set the totalvalues switch """
        self.options['TOTALVALUES'] = bool(arg)
        return True

    def setNot(self, arg):
        """ Set the NOT character """
        self.options['NOTCHAR'] = arg
        return True

    def addPlace(self, name):
        """ Add a place to the saved suggestions """
        if (name in self.places()):
            return False
        else:
            self.options['places'].append(name)
            return True

    def delPlace(self, name):
        """ Remove a place from the saved suggestions """
        if (name in self.places()):
            self.options['places'].remove(name)
            return True
        else:
            return False

    def addType(self, type):
        """ Add a type """
        if (type in self.types()):
            self.options['types'].append(type)
            return True
        else:
            return False

    def delType(self, type):
        """ Delete a type """
        if (type in self.types()):
            if (type not in self.protectedTypes()):
                self.options['types'].remove(type)
                return True
            else:
                print "Cannot remove protected type"
                return False
        else:
            return False
        
    def addAccount(self, name):
        """ Add an account """
        if (name not in self.accountNames()):
            self.options['accounts'][self.newAccountKey()] = name
            return True
        else:
            if (name in self.deletedAccountNames()):
                self.undelAccount(name)
                return True
            else:
                print "That account already exists"
                return False

    def undelAccount(self, name):
        """ Undelete an account """
        key = self.accountKey(name)
        if key in self.deletedAccountKeys():
            self.options['deletedAccounts'].remove(key)
            return True
        else:
            return False


    def delAccount(self, name):
        """ Delete an account """
        #! If we delete an account that has no transactions, we could forget its name permanently...
        #! If we delete an account that does have transactions, we can either forget its name and have a problem when reading the database,
        #!          or save its name to come back later, possibly as a suggestion when reading the database again
        if ((name in self.accountNames()) and (name not in self.deletedAccountNames())):
            key = self.accountKey(name)
            self.options['deletedAccounts'].append(key)
            return True
        return False
        
    def renameAccount(self, oldname, newname):
        """ Rename an account """
        if (oldname in self.accountNames()):
            key = self.accountKey(oldname)
            self.options['accounts'][key] = newname
            return True
        else:
            return False
