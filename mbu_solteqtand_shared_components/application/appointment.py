import uiautomation as auto

from .handler_base import HandlerBase
from .exceptions import ManualProcessingRequiredError


class AppointmentHandler(HandlerBase):
    """
    Handles appointment-related UI interactions.
    """
    def get_list_of_appointments(self) -> dict:
        """
        Gets list of appointments as found in patient window

        Returns
            booking_list_dict (dict): Dictionary with appointments and informations
            booking_list_ctrls (list): List with the control related to each appointment

        Todo: Assure that view is on patient
        """
        # Open "Stamkort"
        self.open_tab("Stamkort")

        # Read elements in list and check that expected element exists
        # First get the list of appointments
        list_parent = self.find_element_by_property(
            control=self.app_window,
            automation_id='ControlBookingDay'
        )
        booking_list_ctrl = self.find_element_by_property(
            control=list_parent,
            control_type=50008
        )
        # Initiate dictionary for list elements
        booking_list = {'controls': []}
        # Initiate list to hold headers
        booking_list_keys = []
        rowcount = 0

        # Check for header
        if booking_list_ctrl.GetFirstChildControl().ControlType == 50034:
            # Loop through all elements in list
            for elem in booking_list_ctrl.GetChildren():
                # If header, then add each item to list of headers
                if elem.ControlType == 50034:
                    for colname in elem.GetChildren():
                        booking_list_keys.append(colname.Name)
                        booking_list[colname.Name] = []
                # If listitem, then add each item to dict
                if elem.ControlType == 50007:
                    booking_list['controls'].append(elem)  # Adds the control to accessed later
                    vals = elem.GetChildren()  # Extracts all information from control

                    for headercount, val in enumerate(vals):
                        booking_list[booking_list_keys[headercount]].append(val.Name)
                    rowcount += 1

        return booking_list

    def change_appointment_status(
            self,
            appointment_control: auto.ControlType,
            set_status: str,
            send_msg: bool = False
        ):
        """
        Changes status of appointment and optionally sends message

        Args:
            appointment_control (Control): Control element that identifies the appointment to be changed
            set_status (str): The status which the appointment should be changed to.
            send_msg (bool, optional): Indicates whether message should be sent when status is changed.
        """
        appointment_control.GetInvokePattern().Invoke()

        # Find booking control
        booking_control = self.wait_for_control(
            control_type=auto.PaneControl,
            search_params={
                'AutomationId': 'ManageBookingControl'
            },
            search_depth=3
        )

        # Find appointment status dropdown
        status_control = self.find_element_by_property(
            control=booking_control,
            control_type=50003,
            name='Status'
        )
        # Get current status to reset if warning on save
        current_status = status_control.GetValuePattern().Value

        # Open dropdown
        self.find_element_by_property(
            control=status_control,
            control_type=50000
        ).GetInvokePattern().Invoke()

        # Get list control for all status options
        status_list_ctrl = self.wait_for_control(
            control_type=auto.ListControl,
            search_params={
                'ClassName': 'ComboLBox'
            }
        )
        # Load status options into dict with controls, names and lowercase names
        status_dict = {
            'ctrls' : [elem for elem in status_list_ctrl.GetChildren() if elem.ControlType == 50007],
            'names' : [elem.Name for elem in status_list_ctrl.GetChildren() if elem.ControlType == 50007],
            'names_lo': [elem.Name.lower() for elem in status_list_ctrl.GetChildren() if elem.ControlType == 50007]
        }

        # Set new status if valid, otherwise return error
        if set_status.lower() in status_dict['names_lo']:
            list_no = status_dict['names_lo'].index(set_status.lower())
            status_dict['ctrls'][list_no].GetInvokePattern().Invoke()
            # Click "Gem og udsend"
            self.app_window = booking_control
            if send_msg:
                save_button = self.find_element_by_property(
                    control=booking_control,
                    automation_id = "ButtonSavePrint"
                )
            else:
                save_button = self.find_element_by_property(
                    control=booking_control,
                    automation_id = "ButtonOk"
                )
            save_button.SendKeys('{ENTER}')
            # Check for notification window pop up
            try:
                notification_ctrl = self.wait_for_control(
                    control_type=auto.PaneControl,
                    search_params={
                        'AutomationId': 'BookingNotificationsControl'
                    },
                    search_depth=3,
                    timeout=5
                )
                close_button = self.find_element_by_property(
                    control=notification_ctrl,
                    automation_id="ButtonCancel"
                )
                close_button.SendKeys('{ENTER}')
                return
            except TimeoutError:
                pass

            # Check for warning window pop up
            try:
                self.handle_error_on_booking_save(slct_button="ButtonChangeManual")
                # Wait for status list to reappear
                booking_control = self.wait_for_control(
                    control_type=auto.PaneControl,
                    search_params={
                        'AutomationId': 'ManageBookingControl'
                    },
                    search_depth=3
                )
                # Open dropdown
                self.find_element_by_property(
                    control=status_control,
                    control_type=50000
                ).GetInvokePattern().Invoke()
                # Reset to original value
                list_no = status_dict['names_lo'].index(current_status.lower())
                status_dict['ctrls'][list_no].GetInvokePattern().Invoke()
                # Save original status
                save_button = self.find_element_by_property(
                    control=booking_control,
                    automation_id = "ButtonOk"
                )
                save_button.SendKeys('{ENTER}')
                # Accept despite warning
                self.handle_error_on_booking_save(slct_button="ButtonOk")

                raise ManualProcessingRequiredError
            except TimeoutError:
                pass

            #   If warning when sending: press "ret manuelt" -> "annuler" -> return warning error 

            return None
        else:
            print(f"{set_status} not in list. Possible status choices are: {', '.join(status_dict['names'])}")
            raise Exception

    def handle_error_on_booking_save(self, slct_button: str):
        """Handle error window when saving booking. Select button to press"""
        buttons = [
            "ButtonFindNewTimeSlot",
            "ButtonOk",
            "ButtonChangeManual"
        ]
        if slct_button not in buttons:
            print(f"{slct_button} not in buttons. Available buttons are {' '.join(buttons)}")
            raise ValueError
        warning_window = self.wait_for_control(
            control_type=auto.WindowControl,
            search_params={
                "AutomationId": "FormBookingWarnings"
            },
            search_depth=5
        )
        button = self.find_element_by_property(
            control=warning_window,
            control_type=50033,
            automation_id=slct_button
        )
        button.SendKeys("{ENTER}")

    def get_appointments_aftalebog(
            self,
            close_after: bool = False,
            headers_to_keep: list | None = None
    ) -> dict:
        """Function to retrive data on appointments in view in aftalebog"""

        # Get list control
        list_box = self.wait_for_control(
            control_type=auto.GroupControl,
            search_params={
                "AutomationId": "GroupBoxView"
            },
            search_depth=5
        )

        appointment_list = self.find_element_by_property(
            control=list_box,
            control_type=50008
        )

        # Extract headers
        appointment_headers = [
            header.Name
            for header in appointment_list.GetFirstChildControl().GetChildren()
        ]

        # Extract ListItem controls
        appointment_ctrls = [
            ctrl
            for ctrl in appointment_list.GetChildren()
            if ctrl.ControlType == 50007
        ]

        # Package data in dictionary
        # Keep only selected headers if any selected.
        if not headers_to_keep:
            headers_to_keep = appointment_headers

        appointment_data = {
            j: {
                k: v.Name
                for k, v in zip(appointment_headers, ctrl.GetChildren())
                if k in headers_to_keep
            }
            for j, ctrl in enumerate(appointment_ctrls)
        }

        if close_after:
            # Should maybe be in a method of its own?
            list_box.SendKeys('{Control}{F4}')
            self.wait_for_control_to_disappear(
                control_type=auto.WindowControl,
                search_params={
                    "AutomationId": "FormBooking"
                }
            )

        return appointment_data

    def create_booking_reminder(self, booking_reminder_data: dict):
        """
        Creates a booking reminder for the patient.
        """
        try:
            self.open_tab("Stamkort")
            self.open_sub_tab("Behandlingsstatus")

            create_booking_button = self.wait_for_control(
                auto.PaneControl,
                {"AutomationId": "ButtonBookingNew"},
                search_depth=14
                )
            create_booking_button.GetLegacyIAccessiblePattern().DoDefaultAction()

            booking_window = self.wait_for_control(
                auto.WindowControl,
                {"AutomationId": "MainFrame"},
                search_depth=2
                )

            # Fill out ressourcer group
            manage_booking = booking_window.PaneControl(AutomationId="viewPortPanel").PaneControl(AutomationId="ManageBookingControl")
            resources_group = manage_booking.GroupControl(AutomationId="Ressourcer")

            for child in resources_group.GetChildren():
                if child.ControlTypeName == "ComboBoxControl":
                    match child.Name:
                        case "Aftaletype":
                            child.GetPattern(auto.PatternId.ValuePattern).SetValue(booking_reminder_data["comboBoxBookingType"])
                        case "Behandler":
                            child.GetPattern(auto.PatternId.ValuePattern).SetValue(booking_reminder_data["comboBoxDentist"])
                        case "Stol":
                            child.GetPattern(auto.PatternId.ValuePattern).SetValue(booking_reminder_data["comboBoxChair"])

            # Fill out text booking field
            text_booking_field_group = manage_booking.GroupControl(AutomationId="GroupBox5")
            for child in text_booking_field_group.GetChildren():
                match child.AutomationId:
                    case "TextBoxBookingText":
                        if child.GetPattern(auto.PatternId.ValuePattern).Value != booking_reminder_data["textBoxBookingText"]:
                            child.GetPattern(auto.PatternId.ValuePattern).SetValue(booking_reminder_data["textBoxBookingText"])

            # Fill out date and time
            date_and_time_group = manage_booking.GroupControl(AutomationId="GroupBox4")

            for child in date_and_time_group.GetChildren():
                match child.AutomationId:
                    case "DateTimePickerStartTime":
                        child.SendKeys(booking_reminder_data["dateTimePickerStartTime"])
                    case "TextBoxDuration":
                        if child.GetPattern(auto.PatternId.ValuePattern).Value != booking_reminder_data["textBoxDuration"]:
                            child.GetPattern(auto.PatternId.ValuePattern).SetValue(booking_reminder_data["textBoxDuration"])
                    case "ComboBoxStatus":
                        if child.GetPattern(auto.PatternId.ValuePattern).Value != booking_reminder_data["comboBoxStatus"]:
                            child.GetPattern(auto.PatternId.ValuePattern).SetValue(booking_reminder_data["comboBoxStatus"])
                    case "DateTimePickerDate":
                        child.SendKeys(booking_reminder_data["futureDate"])

            manage_booking.PaneControl(AutomationId="ButtonOk").Click(simulateMove=True, waitTime=0)

            booking_window_warning = self.wait_for_control(
                auto.WindowControl,
                {"AutomationId": "FormBookingWarnings"},
                search_depth=4
            )
            booking_window_warning.PaneControl(AutomationId="ButtonOk").Click(simulateMove=True, waitTime=0)
        except Exception as e:
            print(f"Error while creating booking reminder: {e}")
            raise
