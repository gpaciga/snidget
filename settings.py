""" Manage and store user settings """

#! Currently no way to edit the prediction behaviour
#! Also need to add ability to change postypes and extypes

#! If deleting an account, to which no transactions are associated,
#  we can remove it permanently

#! The handling of foreign accounts could be made more consistent
#  by making all accounts "foreign" with currency CAD and exchage 1.0

#! Add a way to print the current filters alone in a nice way
#! and to save the current filters as the default

import urllib2
import json
from datetime import date, timedelta
import sys
import os
import pickle

def get_open_exchange_rates():
    """ Use open exchange rate API to get exchange rates """
    app_id = '07da2e05cce04ac48280eb00ce9e3eca' # should be a setting?
    api_url = 'https://openexchangerates.org/api/latest.json?app_id=' + app_id
    response = urllib2.urlopen(api_url)
    data = json.load(response)
    return data


def protected_types():
    """ Return types which can not be removed """
    protected = ["Income", "Transfer", "Adjustment"]
    return protected


class Settings(object):
    """ Manage and store user settings """

    # Set some convenient constants
    TODAY = date.today()
    ONEWEEK = timedelta(7)

    updated_rates = False

    # This is the default set of options
    # These will be overwritten if settings.pkl exists
    options = {
        'DATABASE': "expenses.txt",
        'MAXPRINT': 25,         # Maximum number of records to print by default (DEPRECATED)
        'ALLOWANCE': 100,       # Basis for calculating "Remaining" total
        'TOTALVALUES': False,   # Whether to print the total value or the value of each account
        'NPREDICT': 6,          # Number of predictions to suggest
        'DOPREDICTDEST': True,  # Whether to predict the destination or use the places array below
        'NOTCHAR': '#',         # Character used to negate strings

        # Only used if prediction of places is turned off
        # Different place options for different types?
        'places': ["Shoppers Drug Mart", "Metro", "Tim Horton's", "Starbucks", "7-11"],

        # Change these if you want, though it's not recommended
        # Dollar values in the types Income, Adjustment, and Transfer are ADDED to account balances
        # Dollar values in any other type of transaction are SUBTRACTED from account balances
        'types'   : [
            "Income", "Transfer", "Adjustment", "Bill", "Food", "School", "Household", "Extras"
        ],
        'postypes': ["Income", "Transfer", "Adjustment"],
        'extypes' : ["Food", "School", "Household", "Extras"],

        # This should only be changed by using -o delaccount or -o addaccount options
        'accounts': {"A0": "Bank", "A1": "Credit", "A2": "Cash"},

        # This holds the keys of accounts which are hidden
        'deletedAccounts': [],

        # Default currency of non-foreign accounts
        'defaultCurrency': "CAD",

        # This holds the currency of foreign accounts
        'foreignCurrencies': {},

        # Exchange rates for foreign accounts
        'exchangeRates': {},

        # will store exchangeRates as a function of time
        'historicalRates': {},

        # Default filters are the ones used when the program first starts up
        # Each one must be a string, enclosed in single quotes, with no spaces
        # They are the same strings you would use on the command line

        # Example filters:
        # dates: Date ranges, e.g. '2009-01-01,2009-07-01'
        #        or a number of weeks to show, e.g. 'W1' or 'W52'
        # accounts: List of accounts to include, e.g. 'BMO,RBC'
        # types: List of types to display, e.g. 'Income,Bill'
        # string: Require this string in the description, e.g. "Tim Horton's"
        # values: A maximum and minimum value for transactions to show,
        #         e.g. '-20,0' means expenses less than $20
        # uid: Exclude UIDs in the list, e.g. '13gG3X,3ys93D,49sKaP'

        'FILTERS': {
            'dates': 'W1',
            'accounts': None,
            'columns': None,
            'types': None,
            'recipients': None,
            'string': None,
            'values': None,
            'uid': None,
            'maxprint': 25,
            }
        }


    def __init__(self, filename=None):
        """ Load options from an existing file or read in defaults """

        if filename is None:
            self.options_file = "%s/%s" % (sys.path[0], 'settings.pkl')
            filename = self.options_file

        if os.path.exists(filename):
            # First backup the default options
            defaults = self.options
            # Now load the saved options
            options_pickle = open(filename, 'rb')
            self.options = pickle.load(options_pickle)
            options_pickle.close()

            # Now go through and add any options that are new since the last save
            do_save = False
            for opt, val in defaults.iteritems():
                if opt not in self.options:
                    print("Adding new option " + opt)
                    self.options[opt] = val
                    do_save = True
            # Similarly, remove options that are no longer needed
            # remembering you can't remove items during an interation
            delete = []
            for opt, val in self.options.iteritems():
                if opt not in defaults:
                    delete.append(opt)
            for opt in delete:
                print("Removing defunct option " + opt)
                self.options.pop(opt)
                do_save = True

            # We need to also go through the special case of the FILTERS
            # This is basically duplicate code and could be cleaned up....
            for filt, val in defaults['FILTERS'].iteritems():
                if filt not in self.options['FILTERS']:
                    print("Adding new filter " + filt)
                    self.options['FILTERS'][filt] = val
                    do_save = True
            delete = []
            for filt, val in self.options['FILTERS'].iteritems():
                if filt not in defaults['FILTERS']:
                    delete.append(filt)
            for filt in delete:
                print("Removing defunct filter " + filt)
                self.options['FILTERS'].pop(filt)
                do_save = True

            if not self.options['historicalRates']:
                self.options['historicalRates'][date(1970, 01, 01)] = self.options['exchangeRates']

            # Settings were updated so we must save
            if do_save:
                self.save()

        else:
            options_pickle = open(filename, 'wb')
            pickle.dump(self.options, options_pickle)
            options_pickle.close()
            print("Pickled default options. You should not get this message again.")


    def __str__(self):
        """ Convert current options into string for printing """
        output = ""
        tmpsettings = self.options.copy()

        output += "Accounts:\n"
        output += "%-12s %-4s %-9s %10s\n" % ("Name", "ID", "Currency", "Exchange")
        for acc, name in tmpsettings['accounts'].iteritems():
            if acc in tmpsettings['foreignCurrencies']:
                currency = tmpsettings['foreignCurrencies'][acc]
                exchange = float(tmpsettings['exchangeRates'][currency])
            else:
                currency = tmpsettings['defaultCurrency']
                exchange = 1.0
            output += "%-12s %-4s %-9s %10f" % (name, acc, currency, exchange)
            if acc in tmpsettings['deletedAccounts']:
                output += "   (hidden)"
            output += "\n"
        output += "\n"

        tmpsettings.pop('accounts')
        tmpsettings.pop('deletedAccounts')
        tmpsettings.pop('foreignCurrencies')
        tmpsettings.pop('exchangeRates')
        tmpsettings.pop('defaultCurrency')

        output += "Default filters applied at beginning of program:\n"
        output += "  "+self.filters_str()+"\n\n"
        tmpsettings.pop('FILTERS')

        output += "Other settings: (MAXPRINT is no longer used and will be removed)\n"
        for name, value in tmpsettings.iteritems():
            output += "%20s: %-40s\n" % (name, value)

        return output


    def save(self, filename=None):
        """ Save current options into file """

        self.save_historical_rates() # will only save if rates are up to date

        if filename is None:
            filename = self.options_file

        options_pickle = open(filename, 'wb')
        pickle.dump(self.options, options_pickle)
        options_pickle.close()
        print("Saved options")


    def edit(self, command):
        """ Change an option """

        # Keep track of whether a change is made
        changed_options = False

        args = str.split(command, '=')

        # Check the format of the argument
        if args[0] == 'print':
            print(self)
            return changed_options
        elif args[0] == 'save':
            self.save_filters()
            return changed_options
        elif args[0] == 'help':
            print("Argument for -o are typically of the format command=argument, where argument is the new value for the setting.")
            print("Avoid using -o with any filters, as you may unintentionally overwrite the default filters in the settings.")
            print("  database=filename       Change the database file used.")
            print("  maxprint=integer        The maximum number of records to print (deprecated, used only when -N or -U not specified)")
            print("  allowance=value         Setting the weekly allowance value (set to 0 to disable)")
            print("  totalvalues=boolean     Whether to display the total value of a record or the delta of each account.")
            print("  not=x                   Set the character used to negate strings and types to x.")
            print("  addplace=name           Add a suggested place name.")
            print("  delplace=name           Remove a suggested place name.")
            print("  addtype=name            Add a new type of record.")
            print("  deltype=name            Remove a type of record.")
            print("  addaccount=name         Add a new account or restore one that has been hidden with 'delaccount'.")
            print("  delaccount=name         Hide an account in a more persistent way than -C provides.")
            print("  addforeign=name:CUR     Add an account with the currency CUR instead of %s." % self.options['defaultCurrency'])
            print("  currency=CUR            Change the presumed currency of non-foreign accounts to CUR instead of %s." % self.options['defaultCurrency'])
            print("  getexchange=CUR         Update the exchange rate for CUR using Google.")
            print("  setexchange=CUR:value   Manually set the exchange rate for CUR to value.")
            print("  save                    Save current filters as the defaults and commit any other changes to settings.")
            print("  print                   Special command to print the current options in an ugly way.")
            print("  help                    Print this help.")
            return changed_options
        elif len(args) != 2:
            print("Options must be changed using command=argument format.")
            print("Use '-o help' for recognized options.")
            return changed_options

        command = args[0]
        arg = args[1]

        # Edit the options accordingly:

        # Change the database file name
        if command == 'database':
            old_database = self.database()
            self.set_database(arg)
            print("Changed database from '%s' to '%s'" % (old_database, self.database()))
            changed_options = True

        elif command == 'maxprint':
            old_maxprint = self.maxprint()
            self.set_maxprint(arg)
            print("Changed maxprint from '%s' to '%s'" % (old_maxprint, self.maxprint()))
            changed_options = True

        elif command == 'allowance':
            old_allowance = self.allowance()
            self.set_allowance(arg)
            print("Changed allowance from '%s' to '%s'" % (old_allowance, self.allowance()))
            changed_options = True

        elif command == 'totalvalues':
            old_total_values = self.total_values()
            if arg == "True" or arg == "true":
                self.set_total_values(True)
            else:
                self.set_total_values(False)
            print("Changed totalvalues from '%s' to '%s'" % (old_total_values, self.total_values()))
            changed_options = True

        elif command == 'not':
            valid = True
            old_not = self.not_character()
            if len(arg) != 1:
                print("NOT character must be a single character")
                valid = False
            if arg in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789":
                print("Alphanumeric characters not recommended for the NOT character")
                valid = False
            if valid is True and arg != old_not:
                self.set_not_character(arg)
                print("Changed not character from %s to %s" % (old_not, self.not_character()))
                changed_options = True

        elif command == 'addplace':
            if self.add_place(arg):
                print("Added '%s' to places" % arg)
                changed_options = True
            else:
                print("Place %s already exists" % arg)

        elif command == 'delplace':
            if self.del_place(arg):
                print("Removed '%s' from places" % arg)
                changed_options = True
            else:
                print("Place not found: %s" % arg)

        elif command == 'addtype':
            if self.add_type(arg):
                print("Added '%s' to types" % arg)
                changed_options = True
            else:
                print("Type %s already exists" % arg)

        elif command == 'deltype':
            if self.del_type(arg):
                print("Removed type %s" % arg)
                changed_options = True
            else:
                print("Could not remove type %s" % arg)

        elif command == 'addaccount':
            if self.add_account(arg):
                print("Added account %s" % arg)
                changed_options = True
            else:
                print("Could not add account %s" % arg)

        elif command == 'delaccount':
            if self.del_account(arg):
                print("Deleted account %s" % arg)
                changed_options = True
            else:
                print("Could not delete account %s" % arg)

        elif command == 'addforeign':
            if self.add_foreign(arg):
                print("Added foreign account %s" % arg)
                changed_options = True
            else:
                print("Could not add account %s" % arg)

        elif command == 'getexchange':
            if self.set_exchange(arg, self.get_exchange_rate(arg)):
                changed_options = True
            else:
                print("Could not set exchange rate")

        elif command == 'setexchange':
            args = arg.split(":")
            if len(args) == 2:
                currency = args[0]
                rate = float(args[1])
                if self.set_exchange(currency, rate):
                    changed_options = True
                else:
                    print("Could not set exchange rate of %s" % currency)
            else:
                print("Count not parse argument %s" % arg)

        elif command == 'renameaccount':
            print("Cannot rename accounts yet")

        else:
            print("Unrecognized command. Use -o help for recognized commands.")

        # If anything changed, this will be true
        return changed_options


    def new_account_key(self):
        """ Create a unique key for a new account """
        i = 0
        while True:
            key = "A%d" % i
            if key not in self.account_keys():
                break
            else:
                i = i+1
        return key


    def filters_str(self):
        """ Return the command line args necessary for creating the current filter set """
        # Note that if the command line options change, this must change
        output = ""
        if self.options['FILTERS']['dates'] is not None:
            output += "-D '"+self.options['FILTERS']['dates']+"' "
        if self.options['FILTERS']['accounts'] is not None:
            output += "-A '"+self.options['FILTERS']['accounts']+"' "
        if self.options['FILTERS']['columns'] is not None:
            output += "-C '"+self.options['FILTERS']['columns']+"' "
        if self.options['FILTERS']['types'] is not None:
            output += "-T '"+self.options['FILTERS']['types']+"' "
        if self.options['FILTERS']['recipients'] is not None:
            output += "-L '"+self.options['FILTERS']['recipients']+"' "
        if self.options['FILTERS']['string'] is not None:
            output += "-S '"+self.options['FILTERS']['string']+"' "
        if self.options['FILTERS']['values'] is not None:
            output += "-V '"+self.options['FILTERS']['values']+"' "
        if self.options['FILTERS']['uid'] is not None:
            output += "-X '"+self.options['FILTERS']['uid']+"' "
        if self.options['FILTERS']['maxprint'] is not None:
            output += "-N "+str(self.options['FILTERS']['maxprint'])+" "
        return output


    # --------------------------------------------------------------------------------
    # Defs to get values of current options
    # --------------------------------------------------------------------------------

    def accounts(self):
        """ Return the accounts dictionary """
        #! Snidget should only need options['accounts'].values() list
        #! Currently uses iteritems, itervalues, and iterkeys...
        #! Can we replace iterkeys by accountKeys() etc?
        return self.options['accounts']


    def account_keys(self):
        """ Return a list of account codes """
        return self.options['accounts'].keys()


    def account_names(self):
        """ Return a list of account names """
        return self.options['accounts'].values()


    def visible_accounts(self):
        """ Return the accounts dictionary with only visible accounts """
        visible = {}
        for acc, name in self.options['accounts'].iteritems():
            if acc not in self.options['deletedAccounts']:
                visible[acc] = name
        return visible


    def visible_account_keys(self):
        """ Return the keys of visible accounts """
        visible = []
        for key in self.options['accounts'].keys():
            if key not in self.options['deletedAccounts']:
                visible.append(key)
        return visible


    def visible_account_names(self):
        """ Return the visible account names """
        visible = []
        for acc, name in self.options['accounts'].iteritems():
            if acc not in self.options['deletedAccounts']:
                visible.append(name)
        return visible


    def foreign_account_keys(self):
        """ Return the foreign account keys """
        return self.options['foreignCurrencies'].keys()


    def account_key(self, name):
        """ Return an account key given its name """
        for key, value in self.options['accounts'].iteritems():
            if value == name:
                return key
        return False


    def account_name(self, key):
        """ Return an account name given its key """
        return self.options['accounts'][key]


    def deleted_accounts(self):
        """ Alias for deletedAccountKeys """
        return self.deleted_account_keys()


    def deleted_account_keys(self):
        """ Return a list of keys of accounts which have been deleted """
        return self.options['deletedAccounts']


    def deleted_account_names(self):
        """ Return a list of names of accounts which have been deleted """
        names = []
        for key in self.deleted_account_keys():
            names.append(self.account_name(key))
        return names


    def types(self, ind=None):
        """ Return the types dictionary """
        if ind is None:
            return self.options['types']
        return self.options['types'][ind]


    def positive_types(self):
        """ Return list of positive types """
        return self.options['postypes']


    def expense_types(self):
        """ Return types which are considered expenses """
        return self.options['extypes']


    def expense_types_string(self):
        """ Return expense types as a comma separated string """
        filter_string = ''
        for expense_type in self.options['extypes']:
            if expense_type in self.types():
                filter_string = filter_string + ',' + expense_type
        if str.find(filter_string, ',') == 0:
            filter_string = filter_string[1:]
        return filter_string


    def places(self, ind=None):
        """ Return the list of places """
        if ind is None:
            return self.options['places']
        return self.options['places'][ind]


    def filters(self):
        """ Return the filters dictionary """
        return self.options['FILTERS']


    def total_values(self):
        """ Return the totalValues setting """
        return self.options.get('TOTALVALUES', False)


    def maxprint(self):
        """ Return the maxprint value """
        return self.options.get('MAXPRINT', 25)


    def allowance(self):
        """ Return the weekly allowance """
        return self.options['ALLOWANCE']


    def number_to_predict(self):
        """ Return the default number of predictions """
        return self.options['NPREDICT']


    def predict_destination(self):
        """ Return a boolean indicating whether we want to predict destinations """
        return self.options['DOPREDICTDEST']


    def database(self):
        """ Return the database file """
        return self.options['DATABASE']


    def not_character(self):
        """ Return the not character """
        return self.options['NOTCHAR']


    def is_foreign(self, acc):
        """ Return where an account is foreign """
        return bool(acc in self.options['foreignCurrencies'].keys())


    def exchange(self, acc):
        """ Return the exchange rate of an account """
        if self.is_foreign(acc):
            currency = self.options['foreignCurrencies'][acc]
            return self.options['exchangeRates'][currency]
        return 1.00


    def get_exchange_rate(self, currency, data=False):
        """
        Return the conversion to multiply the foreign currency by to get the default currency
        """
        currency_from = currency
        currency_to = self.options['defaultCurrency']
        # if being called multiple times, should provide data so as to not call the API every time
        if data is False:
            data = get_open_exchange_rates()
        default_rate = data['rates'][currency_to]
        destination_rate = data['rates'][currency_from]
        return float(default_rate/destination_rate)


    def update_exchanges(self):
        """ Update all the exchange rates using Google """
        rates = get_open_exchange_rates()
        for currency in self.options['exchangeRates'].iterkeys():
            rate = self.get_exchange_rate(currency, data=rates)
            if rate is not False:
                self.set_exchange(currency, rate)
        self.updated_rates = True


    def save_historical_rates(self):
        """ Add the current exchange rates to the historical record """
        if self.updated_rates is True:
            self.options['historicalRates'][self.TODAY] = self.options['exchangeRates']
        else:
            print("Exchange rates have not been updated.")
            print("Since they are out of date, they will not be saved as today's rates.")


    # --------------------------------------------------------------------------------
    # Defs to change values of current options
    # --------------------------------------------------------------------------------
    # These return either True or False indicating whether they were successful

    def set_database(self, filename):
        """ Set the database file name """
        self.options['DATABASE'] = filename
        return True


    def set_maxprint(self, maxval):
        """ Set the maxprint """
        self.options['MAXPRINT'] = int(maxval)
        return True


    def set_allowance(self, value):
        """ Set the weekly allowance """
        self.options['ALLOWANCE'] = float(value)
        return True


    def set_total_values(self, arg):
        """ Set the totalvalues switch """
        self.options['TOTALVALUES'] = bool(arg)
        return True


    def set_not_character(self, arg):
        """ Set the NOT character """
        self.options['NOTCHAR'] = arg
        return True


    def add_place(self, name):
        """ Add a place to the saved suggestions """
        if name in self.places():
            return False
        self.options['places'].append(name)
        return True


    def del_place(self, name):
        """ Remove a place from the saved suggestions """
        if name in self.places():
            self.options['places'].remove(name)
            return True
        return False


    def add_type(self, expense_type):
        """ Add a type """
        if expense_type in self.types():
            self.options['types'].append(expense_type)
            return True
        return False


    def del_type(self, expense_type):
        """ Delete a type """
        if expense_type in self.types():
            if expense_type in protected_types():
                print("Cannot remove protected type")
                return False

            self.options['types'].remove(expense_type)
            return True

        return False


    def add_account(self, name):
        """ Add an account """
        if name not in self.account_names():
            self.options['accounts'][self.new_account_key()] = name
            return True

        if name in self.deleted_account_names():
            self.undel_account(name)
            return True

        print("That account name already exists")
        return False


    def add_foreign(self, args):
        """ Add an account in a foreign currency """
        args = args.split(":")
        try:
            if (len(args[1]) != 3 or not args[1].isalpha()):
                print("%s is not a 3-character currency code" % args[1])
                return False
        except IndexError:
            print("Could not get currency code from %s" % args)
            return False
        name = args[0]
        currency = args[1].upper()

        if self.add_account(name) is False:
            # Adding account must have failed
            return False

        # Get the key of the account we just made
        acc = self.account_key(name)

        # Set the account currency
        self.options['foreignCurrencies'][acc] = currency

        # Try to get the exchange rate
        rate = self.get_exchange_rate(currency)
        if rate is False:
            print("Could not get exchange rate. Please set the exchange rate manually.")
            rate = 0.0

        print("Exchange rate set to %f" % rate)

        # Now save the exchange rate for this currency
        self.options['exchangeRates'][currency] = rate

        return True


    def set_exchange(self, currency, rate):
        if currency in self.options['exchangeRates'].keys():
            self.options['exchangeRates'][currency] = rate
            print("Set exchange rate of %s to %f" % (currency, rate))
            return True

        print("There are no accounts with currency %s" % currency)
        return False


    def undel_account(self, name):
        """ Undelete an account """
        key = self.account_key(name)
        if key in self.deleted_account_keys():
            self.options['deletedAccounts'].remove(key)
            return True
        return False


    def del_account(self, name):
        """ Delete an account """
        #! If we delete an account that has no transactions, we could forget its name permanently.
        #! If we delete an account that does have transactions, we can either forget its name and
        #! have a problem when reading the database, or save its name to come back later, possibly
        #! as a suggestion when reading the database again
        if ((name in self.account_names()) and (name not in self.deleted_account_names())):
            key = self.account_key(name)
            self.options['deletedAccounts'].append(key)
            return True
        return False


    def rename_account(self, oldname, newname):
        """ Rename an account """
        if oldname in self.account_names():
            key = self.account_key(oldname)
            self.options['accounts'][key] = newname
            return True
        return False


    def save_filters(self):
        print("Setting default filters: %s" % self.filters_str())
        self.save()
