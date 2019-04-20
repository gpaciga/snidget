#!/usr/bin/env python
""" Simply track expenses, income, account balances, etc."""

# To do:
# - Abstract the expense types from the income types
# - More error checking and argument type checking
# - Warn if removing account with non-zero balance
# - When a new Type or Account code is encountered, ask for a name and save it in the options
# - Maybe have some prediction thing, so if the first few fields are similar it'll suggest a
#   complete record? (e.g. for monthly things)

#! If you change the database to a file which does not exist,
#! that error on loading the database will not let us get as far as the -o command to fix it!

import sys # to get command line options
import getopt # to parse command line options

import settings
import database
import transaction
import latex

__version__ = "4.2.1"

# Load the user settings and database
settings = settings.Settings()
database = database.Database(settings)

def usage():
    """ Return the USAGE file as a string """
    usage_filename = "%s/%s" % (sys.path[0], 'USAGE')
    usage_file = file(usage_filename)
    output = ''
    for line in usage_file:
        output += line
    return output


# Unused option letters: jklmyz GHIJKMOPQYZ
def parse_args(argv):
    """ Process command line arguments. """
    try:
        opts, args = getopt.getopt(argv, "acbd:e:f:ghino:pqrstuvwx:A:B:C:D:EF:L:N:RS:T:UV:WX:", [])
    except getopt.GetoptError:
        print("Unrecognized option or bad argument. Use -h to get usage information.")
        sys.exit(2)

    for opt, arg in opts:

        if opt == "-a":
            # Print all visible records, no matter how many there are
            print(database.__str__(len(database.records)))

        elif opt == "-c":
            # Print current balances of all accounts
            balances = database.balances()['all']
            total = 0.0
            for acc in settings.accounts().iterkeys():
                if acc not in settings.deleted_account_keys():
                    if acc in settings.foreign_account_keys():
                        print("%-15s %12.2f = %12.2f" %
                              (settings.account_name(acc), balances[acc],
                               balances[acc]*settings.exchange(acc)))
                        total += balances[acc]*settings.exchange(acc)
                    else:
                        print("%-15s %12.2s   %12.2f" %
                              (settings.account_name(acc), "", balances[acc]))
                        total += balances[acc]
            print("%-15s %12.2s   ============" % ("", ""))
            print("%-15s %12.2s   %12.2f" % ("Total", "", total))

        elif opt == "-b":
            for datapoint in database.integrate_deltas():
                output = ""
                output += "%s " % datapoint[0]
                # +1 because we have a column for the total
                for i in range(0, len(settings.accounts()) + 1):
                    output += "%9.2f " % datapoint[1+i]
                print(output)

        elif opt == "-d":
            # Integrate over some number of days, argument required.
            # -d 7 is the same as -w
            #! Should this be a function in the database class?
            total = 0.0
            num = 0
            try:
                num_days = int(arg)
            except:
                print("Invalid option: -d " + arg)
            for datapoint in database.integrate(num_days):
                # datapoint is a (date, float) tuple
                print("%s %.2f" % datapoint)
                total += float(datapoint[1])
                num += 1
            ave = total/num if num > 0 else 0
            print("# Average: %.2f" % ave)

        elif opt == "-e":
            # Edit an entry identified by uid=arg
            entries = str.split(arg, ',')
            for entry in entries:
                database.edit(entry)
            database.save()

        elif opt == "-g":
            start_gui()

        elif opt == "-h":
            # Print usage
            print(usage())

        elif opt == "-i":
            # Print a new record UID
            print(transaction.new_uid())

        elif opt == "-f":
            if arg == "latex":
                # Print a latex report
                latex.output(__version__, database, settings)
            elif arg == "csv":
                # Print in CSV
                print(database.__str__(csv=True))
            else:
                print("Format '%s' not supported" % (arg))

        elif opt == "-n":
            # Create a new entry in the database
            database.new_record()
            database.save()

        elif opt == "-o":
            if settings.edit(arg):
                settings.save()


        elif opt == "-p":
            # Print the database as it currently stands
            print(database)

        elif opt == "-q":
            # Include a running tally of each account
            print(database.__str__(print_running_balances=True))

        elif opt == "-r":
            # Print recipients
            destsum = 0.0
            for dest in database.balances_by_recipient():
                destsum += float(dest[1])
                print("  %-35s %9.2f" % (dest[0], float(dest[1])))
            print("  =============================================")
            print("  %35s %9.2f" % (" ", destsum))

        elif opt == "-s":
            # Sort records by date
            database.sort()
            database.save()

        elif opt == "-t":
            # Print types
            typesum = 0.0
            for expense_type in database.balances_by_type():
                typesum += float(expense_type[1])
                print("  %-35s %9.2f" % (expense_type[0], float(expense_type[1])))
            print("  =============================================")
            print("  %35s %9.2f" % (" ", typesum))

        elif opt == "-u":
            print("Updating all exchange rates (but you must save explicitly with -o save!)")
            settings.update_exchanges()

        elif opt == "-v":
            # Like -p but print values, not individual accounts
            print(database.__str__(total_value=not settings.total_values()))

        elif opt == "-w":
            # Integrate over n days, defaults to 7.
            #! Should this be a function in the database class?
            total = 0.0
            num = 0
            for datapoint in database.integrate():
                # datapoint is a (date, float) tuple
                print("%s %.2f" % datapoint)
                total += float(datapoint[1])
                num += 1
            ave = total/num if num > 0 else 0
            print("# Average: %.2f" % ave)

        elif opt == "-x":
            # Delete a record by uid
            uids = str.split(arg.rstrip(), ",")
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
            database.filters['types'] = settings.expense_types_string()

        elif opt == "-F":
            # Exclude records of type arg by appending the negation character
            database.filters['types'] = settings.not_character()+arg

        elif opt == "-S":
            # Print only records containing string arg
            database.filters['string'] = arg

        elif opt == "-L":
            # Print only records with a specific recipient
            database.filters['recipients'] = arg

        elif opt == "-N":
            # Set the maximum number of records to print at a time in most cases
            database.filters['maxprint'] = int(arg)

        elif opt == "-R":
            database.reset_filters()

        elif opt == "-T":
            # Print only type arg
            database.filters['types'] = arg

        elif opt == "-U":
            # Remove the maximum limit on things to print
            database.filters['maxprint'] = None

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


def start_gui():
    snidget_gui = gui.SnidgetGUI(database, settings)
    snidget_gui.main()


# If no args, start the gui
# Else, parse the args
if __name__ == "__main__":
    if not sys.argv[1:]:
        import gui
        start_gui()
    else:
        parse_args(sys.argv[1:])
