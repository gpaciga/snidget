# GTK+ GUI for Snidget

from datetime import date, timedelta
import sys
import pygtk
pygtk.require('2.0')
import gtk

import snidget
import transaction
import plotter

#! special transfer dialog
#! dialog for user settings
#! Add and delete types

#! File/Undo or Reload --> Warning, this will undo all your changes since the last save

#! Accounts/New
#! Accounts/Delete
#! Accounts/Transfer Funds

#! View modes (by type and by recipient, as in -t and -r options)

#! Totals
#! Tooltips

class SnidgetGUI(object):

    # --------------------------------------------------------------------------
    # Dialogs
    # --------------------------------------------------------------------------

    def dialog_save(self):
        """ Dialog to ask if we should save """
        # Create the dialog
        dialog = gtk.MessageDialog(None,
                                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                   gtk.MESSAGE_QUESTION,
                                   gtk.BUTTONS_YES_NO,
                                   None)
        dialog.set_markup("<b>Database has been changed.</b>")
        dialog.format_secondary_markup("Do you want to save?")

        dialog.show_all()
        response = dialog.run()
        dialog.destroy()

        # Return True if dialog answered Yes or No
        # Return False if dialog is quit without answering
        if response == gtk.RESPONSE_YES:
            self.save_database()
            return True
        elif response == gtk.RESPONSE_NO:
            return True
        return False


    def dialog_edit(self, record=None):
        """ Dialog to edit transactions """
        dialog = gtk.Dialog("Edit Record",
                            None,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))

        # Get the record or get a new record
        if record is None:
            record = transaction.Transaction(snidget.database, snidget.settings)
            is_new = True # use to know whether to add or not
        else:
            is_new = False

        # Shorthand because vbox didn't always refer to this vbox
        vbox = dialog.vbox

        hbox_top = gtk.HBox(True, 0)
        vbox.pack_start(hbox_top)

        # date
        frame_date = gtk.Frame("Date")
        hbox_date = gtk.HBox()
        frame_date.add(hbox_date)

        # date spinners
        adjust_year = gtk.Adjustment(record.date.year, 1900, 3000, 1, 1)
        spinner_year = gtk.SpinButton(adjust_year, 1, 0)
        adjust_month = gtk.Adjustment(record.date.month, 1, 12, 1, 1)
        spinner_month = gtk.SpinButton(adjust_month, 1, 0)
        adjust_day = gtk.Adjustment(record.date.day, 1, 31, 1, 1)
        spinner_day = gtk.SpinButton(adjust_day, 1, 0)

        hbox_date.pack_start(spinner_year, False, False, 0)
        hbox_date.pack_start(spinner_month, False, False, 0)
        hbox_date.pack_start(spinner_day, False, False, 0)
        hbox_top.pack_start(frame_date, False, False, 5)

        # type
        frame_type = gtk.Frame("Type")
        type_menu = gtk.combo_box_new_text()
        types = snidget.settings.types()
        for index, expense_type in enumerate(types):
            type_menu.append_text(expense_type)
            if record.type == expense_type:
                type_menu.set_active(index)
        frame_type.add(type_menu)
        hbox_top.pack_start(frame_type, False, False, 5)

        # id
        frame_id = gtk.Frame("ID (Optional)")
        entry_id = gtk.Entry()
        entry_id.set_text(record.id)
        frame_id.add(entry_id)
        hbox_top.pack_start(frame_id, False, False, 5)

        # location
        entry_location = gtk.Entry()
        entry_location.set_text(record.dest)
        frame_location = gtk.Frame("Location")

        # Setup the auto-completion widget
        location_completer = gtk.EntryCompletion()
        entry_location.set_completion(location_completer)
        location_list = gtk.ListStore(str)
        for place in snidget.database.places():
            location_list.append([place])
        location_completer.set_model(location_list)
        location_completer.set_text_column(0)
        location_completer.set_minimum_key_length(2)

        frame_location.add(entry_location)
        vbox.pack_start(frame_location, False, False, 5)

        # description
        frame_description = gtk.Frame("Description")
        entry_description = gtk.Entry()
        entry_description.set_text(record.desc)

        # Setup the auto-completion widget
        description_completer = gtk.EntryCompletion()
        entry_description.set_completion(description_completer)
        description_list = gtk.ListStore(str)
        for place in snidget.database.descriptions():
            description_list.append([place])
        description_completer.set_model(description_list)
        description_completer.set_text_column(0)
        description_completer.set_minimum_key_length(2)

        frame_description.add(entry_description)
        vbox.pack_start(frame_description, False, False, 5)

        # deltas, one per account
        hbox_deltas = gtk.HBox()
        acc_frames = []
        acc_adjusts = []
        acc_spinners = []
        for acc in snidget.settings.visible_accounts():
            this_frame = gtk.Frame(snidget.settings.account_name(acc))
            if record.deltas.has_key(acc):
                this_delta = record.deltas[acc]
            else:
                this_delta = 0.0
            this_adjust = gtk.Adjustment(this_delta, -9999999999, 9999999999, 0.01, 1)
            this_spinner = gtk.SpinButton(this_adjust, 0.01, 2)
            acc_frames.append(this_frame)
            acc_adjusts.append(this_adjust)
            acc_spinners.append(this_spinner)
            this_frame.add(this_spinner)
            hbox_deltas.pack_start(this_frame, False, False, 0)

        vbox.pack_start(hbox_deltas, False, False, 5)

        # Now show the dialog and get the input!
        dialog.show_all()
        response = dialog.run()
        dialog.destroy()

        if response == gtk.RESPONSE_OK:
            #! Error correction???
            record.date = date(spinner_year.get_value_as_int(),
                               spinner_month.get_value_as_int(),
                               spinner_day.get_value_as_int())
            record.type = types[type_menu.get_active()]
            record.dest = entry_location.get_text()
            record.desc = entry_description.get_text()
            for ind in range(0, len(snidget.settings.visible_accounts())):
                value = acc_spinners[ind].get_value()
                if value != 0.0:
                    if record.type in snidget.settings.positive_types():
                        record.deltas[snidget.settings.visible_account_keys()[ind]] = value
                    else:
                        record.deltas[snidget.settings.visible_account_keys()[ind]] = value*-1.0
            record.id = entry_id.get_text()

            if is_new:
                snidget.database.add(record)

            #! Dialog might have completed correctly without changes
            snidget.database.is_changed = True

            self.set_status("Added record with UID %s" % record.uid)
            #! Would be nice to only update the one row
            self.write_table()

    def dialog_value(self):
        """ Dialog to set the Value filter """
        # Create the dialog
        dialog = gtk.MessageDialog(None,
                                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                   gtk.MESSAGE_QUESTION,
                                   gtk.BUTTONS_OK_CANCEL,
                                   None)
        dialog.set_markup("<b>Range of values:</b>")
        dialog.format_secondary_markup("Use checkbox to impose max/min limits.")

        # Default values are zeros, no limits imposed
        init_min = 0.0
        init_max = 0.0
        use_min = False
        use_max = False

        # Get current filter values
        current_values = snidget.database.filters['values']
        if current_values is not None:
            # There is a filter
            current_values = current_values.split(',')
            if current_values[0] != '':
                # Use the minimum impoesd
                use_min = True
                init_min = float(current_values[0])
            if current_values[1] != '':
                # Use the maximum imposed
                use_max = True
                init_max = float(current_values[0])

        # Hboxes for the check box and spinners
        hbox_min = gtk.HBox()
        hbox_max = gtk.HBox()

        # Check to impose limit or not
        check_min = gtk.CheckButton(label='Minimum:')
        check_max = gtk.CheckButton(label='Maximum:')

        # Set defaults
        check_min.set_active(use_min)
        check_max.set_active(use_max)

        # Make the spinners and their adjustments
        # args: initial value, min, max, step, right click step
        adjust_min = gtk.Adjustment(init_min, -9999999999, 9999999999, 0.1, 1)
        adjust_max = gtk.Adjustment(init_max, -9999999999, 9999999999, 0.1, 1)
        # args: adjustment, increment, decimals
        spinner_min = gtk.SpinButton(adjust_min, 0.1, 2)
        spinner_max = gtk.SpinButton(adjust_max, 0.1, 2)

        # Pack everything in
        hbox_min.pack_start(check_min)
        hbox_min.pack_start(spinner_min)
        hbox_max.pack_start(check_max)
        hbox_max.pack_start(spinner_max)
        dialog.vbox.pack_start(hbox_min)
        dialog.vbox.pack_start(hbox_max)

        dialog.show_all()
        response = dialog.run()
        dialog.destroy()

        if response == gtk.RESPONSE_OK:
            min_val = spinner_min.get_value()
            max_val = spinner_max.get_value()
            use_min = check_min.get_active()
            use_max = check_max.get_active()

            new_values = None
            if use_min or use_max:
                # Build up a filter string
                new_values = ''
                if use_min:
                    new_values = str(min_val)
                new_values += ','
                if use_max:
                    new_values += str(max_val)

            snidget.database.filters['values'] = new_values
            #! Should make status smarter about what happened
            self.set_status("Limiting values: %s" % new_values)
            self.write_table()


    def dialog_type(self):
        """ Dialog to set the Type filter """
        # Create the dialog
        dialog = gtk.MessageDialog(None,
                                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                   gtk.MESSAGE_QUESTION,
                                   gtk.BUTTONS_OK_CANCEL,
                                   None)
        dialog.set_markup("<b>Included Types:</b>")

        # Get which types are currently included by the filter
        # None means all types are included
        current_types = snidget.database.filters['types']
        if current_types is None:
            current_types = snidget.settings.types()
        else:
            current_types = current_types.split(',')

        # Add all the types to the dialog, checked or not
        type_checks = []
        for expense_type in snidget.settings.types():
            this_check = gtk.CheckButton(label=expense_type)
            if expense_type in current_types:
                this_check.set_active(True)
            type_checks.append(this_check)
            dialog.vbox.pack_start(this_check, False, False, 0)

        # could use something like
        #button.connect("toggled", self.callback, "check button 1")
        # to make live updates? could get intense for big tables
        # maybe a "preview" options?

        dialog.show_all()
        response = dialog.run()
        dialog.destroy()

        if response == gtk.RESPONSE_OK:

            # Write the selected types into a comma separated list
            new_types = ''
            for index, type_check in enumerate(type_checks):
                if type_check.get_active() is True:
                    new_types += snidget.settings.types()[index] + ','

            # Cut off the last comma
            new_types = new_types[0:-1]

            # Set the new filter
            if not new_types:
                snidget.database.filters['types'] = None
            else:
                snidget.database.filters['types'] = new_types

            # Update the table
            self.set_status("Showing types: %s" % new_types)
            self.write_table()


    def dialog_account(self):
        """ Dialog to set the Account filter """
        # Create the dialog
        dialog = gtk.MessageDialog(None,
                                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                   gtk.MESSAGE_QUESTION,
                                   gtk.BUTTONS_OK_CANCEL,
                                   None)
        dialog.set_markup("<b>Included Accounts:</b>")

        # Get which accounts are currently included by the filter
        # None means all accounts are included
        # Recall that accounts are given by NAME in the filter
        current_accounts = snidget.database.filters['accounts']
        if current_accounts is None:
            current_accounts = snidget.settings.account_names()
        else:
            current_accounts = current_accounts.split(',')

        # Add all the types to the dialog, checked or not
        account_checks = []
        for account in snidget.settings.account_names():
            this_check = gtk.CheckButton(label=account)
            if account in current_accounts:
                this_check.set_active(True)
            account_checks.append(this_check)
            dialog.vbox.pack_start(this_check, False, False, 0)

        # could use something like
        #button.connect("toggled", self.callback, "check button 1")
        # to make live updates? could get intense for big tables
        # maybe a "preview" options?

        dialog.show_all()
        response = dialog.run()
        dialog.destroy()

        if response == gtk.RESPONSE_OK:

            # Write the selected types into a comma separated list
            new_accounts = ''
            for index, account_check in enumerate(account_checks):
                if account_check.get_active() is True:
                    new_accounts += snidget.settings.account_names()[index] + ','

            # Cut off the last comma
            new_accounts = new_accounts[0:-1]

            # Set the new filter
            if not new_accounts:
                snidget.database.filters['accounts'] = None
            else:
                snidget.database.filters['accounts'] = new_accounts

            # Update the table
            self.set_status("Showing accounts: %s" % new_accounts)
            self.write_table()


    def dialog_date(self):
        """ Dialog to set the Date range """

        dialog = gtk.MessageDialog(None,
                                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                   gtk.MESSAGE_QUESTION,
                                   gtk.BUTTONS_OK_CANCEL,
                                   None)
        dialog.set_markup("<b>Set Date Range</b>")
        dialog.format_secondary_markup("From the first date up to but not including the second.")

        cal_start = gtk.Calendar()
        cal_end = gtk.Calendar()

        # Set the minimum and maximum possible ranges
        date_min = snidget.database.records[0].date
        date_max = snidget.database.settings.TODAY + timedelta(1)

        # Parse the filter to set the initial dates
        if snidget.database.filters['dates'] is None:
            date_start = date_min
            date_end = date_max
        elif str.find(snidget.database.filters['dates'], 'W') >= 0:
            # Set start date to nweeks ago
            nweeks = int(snidget.database.filters['dates'][1:])
            date_start = snidget.database.settings.TODAY - timedelta(nweeks*7)
            date_end = date_max
        else:
            dates = str.split(snidget.database.filters['dates'], ',')
            if dates[0] == '':
                date_start = date_min
            else:
                newdate = str.split(dates[0], "-")
                date_start = date(int(newdate[0]), int(newdate[1]), int(newdate[2]))
            if dates[1] == '':
                date_end = date_max
            else:
                newdate = str.split(dates[1], "-")
                date_end = date(int(newdate[0]), int(newdate[1]), int(newdate[2]))

        # Note gtk.Calendar starts counting months at 0
        cal_start.select_month(date_start.month-1, date_start.year)
        cal_start.select_day(date_start.day)
        cal_end.select_month(date_end.month-1, date_end.year)
        cal_end.select_day(date_end.day)

        hbox = gtk.HBox()
        hbox.pack_start(cal_start)
        hbox.pack_start(cal_end)

        dialog.vbox.pack_end(hbox, True, True, 0)
        dialog.show_all()
        response = dialog.run()
        dialog.destroy()

        if response == gtk.RESPONSE_OK:
            date_start = cal_start.get_date()
            date_end = cal_end.get_date()

            # Again, remember months start at 0
            filter_string = "%04d-%02d-%02d,%04d-%02d-%02d" % (
                date_start[0], date_start[1]+1, date_start[2],
                date_end[0], date_end[1]+1, date_end[2]
            )

            snidget.database.filters['dates'] = filter_string
            self.set_status("Set date range to %s." % filter_string)
            self.write_table()


    def dialog_text(self, prompt="Enter text:", default=""):
        """ Generic dialog to get text input """
        #! Need to make these look prettier
        dialog = gtk.MessageDialog(None,
                                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                   gtk.MESSAGE_QUESTION,
                                   gtk.BUTTONS_OK_CANCEL,
                                   None)

        dialog.set_markup(prompt)

        # entry field
        entry = gtk.Entry()
        entry.set_text(default)

        # This allows you to press enter to submit
        entry.connect("activate", self.dialog_response, dialog, gtk.RESPONSE_OK)

        hbox = gtk.HBox()
        #hbox.pack_start(gtk.Label(prompt), False, 5, 5)
        hbox.pack_end(entry)

        # Has a vbox built in
        dialog.vbox.pack_end(hbox, True, True, 0)
        dialog.show_all()
        response = dialog.run()
        dialog.destroy()

        if response == gtk.RESPONSE_OK:
            text = entry.get_text()
            return text
        return None


    def dialog_uid(self):
        """ Dialog for UID filter """
        #! Need to make these look prettier
        #! Either include current selection or have a right-click menu
        dialog = gtk.MessageDialog(None,
                                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                   gtk.MESSAGE_QUESTION,
                                   gtk.BUTTONS_OK_CANCEL,
                                   None)

        dialog.set_markup("<b>Exclude UIDs</b>")
        dialog.format_secondary_markup("Enter a comma separated list.")

        # entry field
        entry = gtk.Entry()

        # Set current filter as default
        current_uids = snidget.database.filters['uid']
        if current_uids is None:
            default = ""
        else:
            default = snidget.database.filters['uid']
        entry.set_text(default)

        # This allows you to press enter to submit
        entry.connect("activate", self.dialog_response, dialog, gtk.RESPONSE_OK)

        # Has a vbox built in
        dialog.vbox.pack_end(entry, True, True, 0)
        dialog.show_all()
        response = dialog.run()
        dialog.destroy()

        if response == gtk.RESPONSE_OK:
            new_uids = entry.get_text()
            if new_uids == '':
                new_uids = None
            snidget.database.filters['uid'] = new_uids
            self.set_status("Excluded UID %s" % str(new_uids))
            self.write_table()


    def dialog_string(self):

        # Make the dialog
        dialog = gtk.MessageDialog(None,
                                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                   gtk.MESSAGE_QUESTION,
                                   gtk.BUTTONS_OK_CANCEL,
                                   None)

        dialog.set_markup("<b>Filter by string</b>")
        dialog.format_secondary_markup("Use '!' as the first character to exclude a string.")
        # entry field
        entry = gtk.Entry()

        # Set the default if a string filter exists
        if snidget.database.filters['string'] is None:
            default = ''
        else:
            default = snidget.database.filters['string']
        entry.set_text(default)

        # This allows you to press enter to submit
        entry.connect("activate", self.dialog_response, dialog, gtk.RESPONSE_OK)

        hbox = gtk.HBox()
        #hbox.pack_start(gtk.Label(prompt), False, 5, 5)
        hbox.pack_end(entry)

        # Has a vbox built in
        dialog.vbox.pack_end(hbox, True, True, 0)
        dialog.show_all()
        response = dialog.run()
        dialog.destroy()

        if response == gtk.RESPONSE_OK:
            text = entry.get_text()
            if text == '':
                # empty string means no filter
                snidget.database.filters['string'] = None
                self.set_status("String filter removed.")
            else:
                snidget.database.filters['string'] = str(text)
                self.set_status("String filter '%s' applied." % str(text))
            self.write_table()


    def dialog_response(self, entry, dialog, response):
        #? I don't know what this is for
        dialog.response(response)

    # --------------------------------------------------------------------------
    # Button callback functions
    # --------------------------------------------------------------------------

    def call_showall(self, widget, data):
        """ Write table with no filters """
        snidget.database.reset_filters()
        self.set_status("Reset all filters.")
        self.write_table()


    def call_defaults(self, widget, data):
        """ Write table with default filters """
        snidget.database.set_filter_defaults()
        self.set_status("Applied default filters.")
        self.write_table()


    def call_expenses(self, widget, data):
        """ Set filter to expense types """
        #! Will want to generalize what an expense type is
        snidget.database.filters['types'] = 'Food,School,Household,Extras'
        self.set_status("Applied filter types: %s" % snidget.database.filters['types'])
        self.write_table()


    def call_type(self, widget, data):
        """ Call the type filter dialog """
        self.dialog_type()


    def call_dates(self, widget, data):
        """ Call the date filter dialog """
        self.dialog_date()


    def call_account(self, widget, data):
        self.dialog_account()


    def call_string(self, widget, data):
        """ Call the string filter dialog """
        self.dialog_string()


    def call_value(self, widget, data):
        self.dialog_value()


    def call_uid(self, widget, data):
        self.dialog_uid()


    def call_plot(self, widget, data):
        plotter.plotwindow()


    def call_new(self, widget, data):
        self.dialog_edit()


    def call_delete(self, widget, data):
        print "Not implemented."


    def call_download(self, widget, data):
        print "Not implemented."


    def call_sort(self, widget, data):
        snidget.database.sort()
        self.write_table(save_state=False)


    # --------------------------------------------------------------------------
    # Menu functions
    # --------------------------------------------------------------------------

    def menu_new(self, action):
        self.dialog_edit()


    def menu_back(self, action):
        self.back_state()


    def menu_forward(self, action):
        self.forward_state()


    def menu_recipients(self, action):
        self.display_mode = "Recipients"
        self.set_status("Viewing by recipient")
        self.write_table()


    def menu_types(self, action):
        self.display_mode = "Types"
        self.set_status("Viewing by type")
        self.write_table()


    def menu_transactions(self, action):
        self.display_mode = "Transactions"
        self.set_status("Viewing by transaction")
        self.write_table()


    def menu_quit(self, action):
        self.quit_program()


    # --------------------------------------------------------------------------
    # Save and change state
    # --------------------------------------------------------------------------

    def save_state(self):
        """ Push current state onto history """
        state = {
            'mode': self.display_mode,
            'filters': snidget.database.filters.copy(),
            'status': self.status_text
        }

        # Drop things in the forward direction
        self.history = self.history[0:self.history_index+1]
        self.history.append(state) # add our state to the end
        self.history_index = len(self.history) - 1 #record out new position in the history


    def back_state(self):
        """ Move back one step in the view history """
        if self.history_index > 0:
            # move one down in the history list
            self.history_index = self.history_index - 1
            # Load the state
            state = self.history[self.history_index]
            self.display_mode = state['mode']
            snidget.database.filters = state['filters']
            self.set_status(state['status'])
            self.write_table(save_state=False)


    def forward_state(self):
        """ Move forward one step in the view history """
        if self.history_index < len(self.history) - 1:
            self.history_index = self.history_index + 1
            state = self.history[self.history_index]
            self.display_mode = state['mode']
            snidget.database.filters = state['filters']
            self.set_status(state['status'])
            self.write_table(save_state=False)


    # --------------------------------------------------------------------------
    # Dealing with the table
    # --------------------------------------------------------------------------

    def get_table(self):
        """ Write the database into a ListStore for TreeView """
        listmodel = gtk.ListStore(object)
        snidget.database.apply_filters()
        for record in snidget.database.records:
            if record.visible:
                listmodel.append([record])
        return listmodel


    def write_table(self, save_state=True):
        """ Set the TreeView with the current database """

        # First we need to save the current state
        if save_state:
            self.save_state()

        if self.display_mode == "Transactions":
            # Now get the new listmodel
            listmodel = self.get_table()
            self.treeview.set_model(listmodel)
            self.treeview.columns_autosize()
            #! Tooltips... have a column of .value()?
            #! Is there not a function I can define?
            self.treeview.set_tooltip_column(0)
            return
        elif self.display_mode == "Types":
            print "Don't know how to write table in this display mode"
        elif self.display_mode == "Recipients":
            print "Don't know how to write table in this display mode"
        else:
            print "Don't know this display mode"


    def cell_value(self, column, cell, model, iter, n):
        """ Get the value of the current record in column n """
        record = model.get_value(iter, 0)
        cell.set_property('text', record.tuple()[n])
        return


    def row_doubleclick(self, treeview, path, column):
        # First we get the TreeSelection object
        treeselection = treeview.get_selection()
        # Then we get a (model, iter) tuple
        treemodeliter = treeselection.get_selected()
        # We use the model and iter to get the record
        model = treemodeliter[0]
        it = treemodeliter[1]

        if self.display_mode == "Transactions":
            record = model.get_value(it, 0)
            # Now we can act on the record
            self.dialog_edit(record)
        elif self.display_mode == "Types":
            pass
        elif self.display_mode == "Recipients":
            pass
        else:
            print "Error: display mode not recognized on double click."


    # --------------------------------------------------------------------------
    # Program management type stuff
    # --------------------------------------------------------------------------

    def delete_event(self, widget, event, data=None):
        """ Window's close button pressed """
        self.quit_program()


    def save_database(self):
        """ Save the database """
        snidget.database.save()
        self.set_status("Saved the database.")


    def quit_program(self):
        ok = True # will be made False if save dialog canceled
        if snidget.database.is_changed is True:
            ok = self.dialog_save()
            # We will be quitting if OK, so print the "Saved" message to the terminal
            if ok is True:
                print "Saved database"
        # Go ahead and quit unless something happened
        if ok is True:
            gtk.main_quit()


    def set_status(self, string=""):
        """ Set the text of the status bar """
        #! This needs to be done BEFORE write_table to keep state history accurate
        #! ... meaning this should probably be done IN write_table before save_state
        context_id = self.statusbar.get_context_id('status')
        self.statusbar.push(context_id, string)
        self.status_text = string


    def __init__(self):

        # Internals
        self.display_mode = "Transactions"
        self.history = [] # to save view history
        self.history_index = 0
        self.status_text = '' # because there's no gtk.StatusBar.get_text()?

        # Gui
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title("Snidget")
        self.window.set_border_width(0)
        self.window.set_default_size(1000, 600)

        self.window.set_icon_from_file("%s/%s" % (sys.path[0], "snidget.png"))

        #icon = gtk.Image()
        #icon.set_from_stock(gtk.STOCK_INDEX, gtk.ICON_SIZE_MENU)
        #self.window.set_icon(icon.get_pixbuf())

        # For signals from window manager
        self.window.connect("delete_event", self.delete_event)

        # A VBox for Menu / Main / Statusbar
        self.box_vmain = gtk.VBox(False, 0)
        self.window.add(self.box_vmain)

        # Status bar
        self.statusbar = gtk.Statusbar()
        self.box_vmain.pack_end(self.statusbar, False, False, 0)
        self.set_status("Welcome to Snidget! (version %s)" % snidget.__version__)
        self.statusbar.set_has_resize_grip(True)
        self.statusbar.show()

        # Define menu/toolbars for the top of vbox
        ui = '''<ui>
        <menubar name="MenuBar">
          <menu action="File">
            <menuitem action="New"/>
            <menuitem action="Save"/>
            <menuitem action="Quit"/>
          </menu>
          <menu action="View">
            <menuitem action="Back"/>
            <menuitem action="Forward"/>
          </menu>
        </menubar>
        </ui>'''

        # to be added to menu UI when view mode functionality works
        #            <separator name="sep1"/>
        #            <menuitem action="By Transaction"/>
        #            <menuitem action="By Recipient"/>
        #            <menuitem action="By Category"/>

        uimanager = gtk.UIManager()

        # Add accelerator group to top level window
        accelgroup = uimanager.get_accel_group()
        self.window.add_accel_group(accelgroup)

        # Create an ActionGroup and add stuff to it
        actiongroup = gtk.ActionGroup('SnidgetGUI')
        self.actiongroup = actiongroup
        actiongroup.add_actions([
            ('File', None, '_File'),
            ('New', None, '_New', "<control>n", "New transaction", self.menu_new),
            ('Save', None, '_Save', "<control>s", "Save the database", self.save_database()),
            ('Quit', None, '_Quit', "<control>q", "Quit Snidget", self.menu_quit),
            ('View', None, '_View'),
            ('Back', None, '_Back', "<control>b", "Go back", self.menu_back),
            ('Forward', None, '_Forward', "<control>f", "Go forward", self.menu_forward),
            ('By Recipient', None, '_By Recipient', "<control>r",
             "View total for each recipient", self.menu_recipients),
            ('By Transaction', None, '_By Transaction', "<control>t",
             "View transactions individually", self.menu_transactions),
            ('By Category', None, '_By Category', "<control>c",
             "View total for each type of transaction", self.menu_types)
        ])

        # Add actiongroup and ui to uimanager
        uimanager.insert_action_group(actiongroup, 0)
        uimanager.add_ui_from_string(ui)

        # Create and pack menubar into vbox
        menubar = uimanager.get_widget('/MenuBar')
        self.box_vmain.pack_start(menubar, False)
        menubar.show()

        # Main box where the main UI (table and buttons) go
        self.box_main = gtk.HBox(False, 0) # Inhomogeneous sizing, spacing=0
        self.box_vmain.pack_start(self.box_main, True, True, 0)

        self.box_left = gtk.VBox(True, 0)
        self.box_right = gtk.VBox(False, 0)
        self.box_main.pack_start(self.box_left, True, True, 0)
        self.box_main.pack_start(self.box_right, False, False, 2)


        # -- Buttons for the right hand side ---------------

        expand = False  # True -- button will expand to fill available space
        fill = False    # True -- when button expands, make button bigger
        padding = 0

        # Add a button
        self.button_showall = gtk.Button("Show All")
        self.button_showall.set_tooltip_text("Clear filters and show all transactions")
        self.button_showall.connect("clicked", self.call_showall, "Showall button")
        self.box_right.pack_start(self.button_showall, expand, fill, padding)
        self.button_showall.show()

        self.button_defaults = gtk.Button("Defaults")
        self.button_defaults.set_tooltip_text("Reset filters to default")
        self.button_defaults.connect("clicked", self.call_defaults, "Defaults button")
        self.box_right.pack_start(self.button_defaults, expand, fill, padding)
        self.button_defaults.show()

        self.separator1 = gtk.HSeparator()
        self.box_right.pack_start(self.separator1, expand, fill, 5)
        self.separator1.show()

        self.button_expenses = gtk.Button("Expenses")
        self.button_expenses.set_tooltip_text("Show only expenses")
        self.button_expenses.connect("clicked", self.call_expenses, "Expenses button")
        self.box_right.pack_start(self.button_expenses, expand, fill, padding)
        self.button_expenses.show()

        self.button_type = gtk.Button("Type")
        self.button_type.set_tooltip_text("Select only particular types")
        self.button_type.connect("clicked", self.call_type, "Type button")
        self.box_right.pack_start(self.button_type, expand, fill, padding)
        self.button_type.show()

        self.button_dates = gtk.Button("Dates")
        self.button_dates.set_tooltip_text("Set the date range")
        self.button_dates.connect("clicked", self.call_dates, "Dates button")
        self.box_right.pack_start(self.button_dates, expand, fill, padding)
        self.button_dates.show()

        self.button_account = gtk.Button("Account")
        self.button_account.set_tooltip_text("Show transactions on an account")
        self.button_account.connect("clicked", self.call_account, "Account button")
        self.box_right.pack_start(self.button_account, expand, fill, padding)
        self.button_account.show()

        self.button_string = gtk.Button("String")
        self.button_string.set_tooltip_text("Filter by location or description")
        self.button_string.connect("clicked", self.call_string, "String button")
        self.box_right.pack_start(self.button_string, expand, fill, padding)
        self.button_string.show()

        self.button_value = gtk.Button("Value")
        self.button_value.set_tooltip_text("Filter by value")
        self.button_value.connect("clicked", self.call_value, "Value button")
        self.box_right.pack_start(self.button_value, expand, fill, padding)
        self.button_value.show()

        self.button_uid = gtk.Button("UID")
        self.button_uid.set_tooltip_text("Exclude particular transactions")
        self.button_uid.connect("clicked", self.call_uid, "UID button")
        self.box_right.pack_start(self.button_uid, expand, fill, padding)
        self.button_uid.show()


        # Bottom buttons
        self.button_quit = gtk.Button("Quit")
        self.button_quit.set_tooltip_text("Save and quit")
        self.button_quit.connect("clicked", self.delete_event, None)
        self.box_right.pack_end(self.button_quit, expand, fill, padding)
        self.button_quit.show()

        self.separator2 = gtk.HSeparator()
        self.box_right.pack_end(self.separator2, expand, fill, 5)
        self.separator2.show()

        self.button_sort = gtk.Button("Sort")
        self.button_sort.set_tooltip_text("Sort transactions by date")
        self.button_sort.connect("clicked", self.call_sort, "Sort button")
        self.box_right.pack_end(self.button_sort, expand, fill, padding)
        self.button_sort.show()

        self.button_delete = gtk.Button("Delete")
        self.button_delete.set_tooltip_text("Delete transaction")
        self.button_delete.connect("clicked", self.call_delete, "Delete button")
        self.box_right.pack_end(self.button_delete, expand, fill, padding)
        self.button_delete.show()

        self.button_new = gtk.Button("New")
        self.button_new.set_tooltip_text("New transaction")
        self.button_new.connect("clicked", self.call_new, "New button")
        self.box_right.pack_end(self.button_new, expand, fill, padding)
        self.button_new.show()

        self.button_plot = gtk.Button("Plot")
        self.button_plot.set_tooltip_text("Plot current transactions")
        self.button_plot.connect("clicked", self.call_plot, "Plot button")
        self.box_right.pack_end(self.button_plot, expand, fill, padding)
        self.button_plot.show()

        # TreeView for showing transactions
        self.treeview = gtk.TreeView()

        #! Need to make columns flexible for different view modes
        column_names = snidget.database.headings()
        self.tvcolumn = [None] * len(column_names)
        for index, column_name in enumerate(column_names):
            cell = gtk.CellRendererText()
            self.tvcolumn[index] = gtk.TreeViewColumn(column_name, cell)
            if index > 3:
                cell.set_property('xalign', 1.0)
            self.tvcolumn[index].set_cell_data_func(cell, self.cell_value, index)
            self.tvcolumn[index].set_resizable(True)
            if index < 4 and index > 0:
                self.tvcolumn[index].set_expand(True)
            self.treeview.append_column(self.tvcolumn[index])

        self.treeview.connect('row-activated', self.row_doubleclick)

        # Left box
        self.scrollbox = gtk.ScrolledWindow()
        self.scrollbox.add(self.treeview)
        self.scrollbox.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        # Allow scrollbox to expand to fill the space
        self.box_left.pack_start(self.scrollbox, True, True, 0)

        self.treeview.show()
        self.scrollbox.show()

        # Populate the table
        self.write_table()

        # Display the UI
        self.box_left.show()
        self.box_right.show()
        self.box_vmain.show()
        self.box_main.show()
        #self.window.maximize()
        self.window.show()


    def main(self):
        gtk.main()
        return 0


if __name__ == "__main__":
    snidget = SnidgetGUI()
    snidget.main()
