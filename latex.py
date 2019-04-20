""" Print database as a latex table """

# A way of outputting a bare-bones financial report from the database
# which, presumably, one can augment as required to make sense of things.

#! Would be nice to write a more general option, which would just print the same thing as
#! the straight up -p version, but with latex markup for adding to a document,
#  (while keeping the option to have \begin{document} etc type markup).

def output(version, database, settings):
    """ Print database as latex table """

    print("\\documentclass{article}")
    print("\\begin{document}")
    print("\\title{Expense Report}")
    print("\\author{Snidget v%s}" % version)

    #! Print balances at beginning of time period
    #! Print balances at end of time period

    # Get the range of dates from the filter
    if database.filters['dates'] != None:

        if str.find(database.filters['dates'], 'W') == 0:
            num_weeks = int(database.filters['dates'][1:])
            start = settings.TODAY - settings.ONEWEEK*num_weeks
            end = settings.TODAY

        else:
            args = str.split(database.filters['dates'], ",")
            start = args[0]
            end = args[1]

    else:
        start = database.records[0].date
        end = settings.TODAY

    print("\\date{%s to %s}" % (start, end))
    print("\\maketitle")

    # Print summary of types
    print("\\section{Total in each Type}")
    print("  \\begin{tabular}{lr}")
    print("    \\hline")
    print("    \\textbf{Type} & \\textbf{Total} \\\\")
    print("    \\hline")
    for expense_type in database.balances_by_type():
        print("       %-14s & %10s \\\\" % expense_type)
    print("    \\hline")
    print("  \\end{tabular}")

    for expense_type in settings.types():
        print("\\section{%s}" % expense_type)
        database.filters['types'] = expense_type
        print("  \\begin{tabular}{lr}")
        print("    \\hline")
        print("    \\textbf{Destination} & \\textbf{Total} \\\\")
        print("    \\hline")
        print("    \\hline")
        for dest in database.balances_by_recipient():
            name = dest[0].replace("&", "\&")
            value = dest[1]
            print("         %-30s & %10s \\\\" % (name, value))
        print("    \\hline")
        print("  \\end{tabular}")

    print("\\end{document}")
