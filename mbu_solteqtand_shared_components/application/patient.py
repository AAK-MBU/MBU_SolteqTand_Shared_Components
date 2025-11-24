"""This module contains the PatientHandler class, which manages patient-related actions in the Solteq Tand application."""
import time
import uiautomation as auto

from .handler_base import HandlerBase
from .exceptions import PatientNotFoundError, NotMatchingError


class PatientHandler(HandlerBase):
    """Handles all patient-related actions in the Solteq Tand application."""

    def get_ssn_stamkort(self):
        """
        Gets the SSN from the 'Stamkort' tab.
        """
        self.open_tab("Stamkort")
        stamkort = self.wait_for_control(
            auto.PaneControl,
            search_params={
                'AutomationId': 'TabPageRecord'
            },
            search_depth=3
        )
        ssn = self.find_element_by_property(
            control=stamkort,
            control_type=50004,
            automation_id='TextPatientCprNumber'
        )
        ssn = ssn.GetValuePattern().Value
        return ssn

    def check_matching_ssn(self, ssn):
        """
        Checks if the SSN found in the 'Stamkort' tab matches the input SSN.
        """
        # Navigate to stamkort
        found_ssn = self.get_ssn_stamkort()
        found_ssn = found_ssn.replace("-","")
        if found_ssn != ssn:
            raise NotMatchingError(in_msg=f"Found SSN {found_ssn} does not match input {ssn}")
        else:
            return True

    def open_patient(self, ssn):
        """
        When the main window is open, presses Ctrl + O to open the 'Open Patient' window,
        searches for the SSN, and opens the patient.
        """
        self.app_window = self.wait_for_control(
            auto.WindowControl,
            {'AutomationId': 'FormFront'},
            search_depth=2,
            timeout=5
        )

        self.app_window.SetFocus()
        self.app_window.SendKeys('{Ctrl}o', waitTime=0)

        open_patient_window = self.wait_for_control(
            auto.WindowControl,
            {'AutomationId': 'FormOpenPatient'},
            search_depth=2
        )
        open_patient_window.SetFocus()

        ssn_input = open_patient_window.EditControl(AutomationId="TextBoxCpr")
        search_button = open_patient_window.PaneControl(AutomationId="ButtonOk")

        ssn_input.SendKeys(text=ssn)
        search_button.SetFocus()
        search_button.SendKeys('{ENTER}')

        # Here we handle possible error window popup.
        try:
            patient_window = self.wait_for_control(
                auto.WindowControl,
                {'AutomationId': 'FormPatient'},
                timeout=5
            )
            self.app_window = patient_window

        except TimeoutError:
            error_window = self.wait_for_control(
                auto.WindowControl,
                {'Name': 'TMT - Åbn patient'},
                search_depth=2,
                timeout=10
            )

            if error_window is not None:
                error_window_button = error_window.ButtonControl(Name="OK")
                error_window_button.SetFocus()
                error_window_button.Click(simulateMove=False, waitTime=0)

                raise PatientNotFoundError

        self.app_window = self.wait_for_control(
            auto.WindowControl,
            {'AutomationId': 'FormPatient'},
            timeout=10
        )

        self.check_matching_ssn(ssn=ssn)

        self.app_window.Maximize()

    def close_patient_window(self):
        """
        Closes the current patient's window and ensures the application returns to the main window.

        Raises:
            TimeoutError: If the patient window does not close within the expected time.
        """

        self.app_window.SetFocus()
        self.app_window.GetWindowPattern().Close()

        self.app_window = self.wait_for_control_to_disappear(
            auto.WindowControl,
            {'AutomationId': 'FormPatient'},
            search_depth=2,
            timeout=30
        )

        self.app_window = self.wait_for_control(
            auto.WindowControl,
            {'AutomationId': 'FormFront'},
            search_depth=2,
            timeout=5
        )
        self.app_window.SetFocus()

    def change_status(self, status: str) -> None:
        """
        Changes the status of a patient by interacting with the UI controls.
        This method verifies that the provided status is not None, retrieves the current status
        from a combo box, and if the desired status differs, it expands the combo box, selects the
        new status, collapses the combo box, and finally simulates a save action. A ValueError is
        raised if the status is None or if the expected status is not found in the combo box list.

        Args:
            status (str): The new status to be applied. Must not be None and should exist in the combo box.

        Raises:
            ValueError: If the provided status is None or if the expected status is not found in the combo box.
            Exception: For any unexpected errors that occur during the status change process.
        """
        try:
            if status is None:
                raise ValueError("Status cannot be None.")

            self.open_tab("Stamkort")

            status_combobox = self.wait_for_control(
                auto.ComboBoxControl,
                {'AutomationId': 'ComboPatientStatus'},
                search_depth=10
            )
            value_pattern = status_combobox.GetPattern(auto.PatternId.ValuePattern)
            current_value = value_pattern.Value
            print(f"Current selected status: '{current_value}'")
            expand_collapse_pattern = status_combobox.GetPattern(auto.PatternId.ExpandCollapsePattern)

            if current_value != status:
                expand_collapse_pattern.Expand()
                status_combobox_expanded = self.wait_for_control(
                    auto.ListControl,
                    {'ClassName': 'ComboLBox'},
                    search_depth=3
                )

                selection_made = False
                for item in status_combobox_expanded.GetChildren():
                    if item.Name == status:
                        print(f"Selecting '{status}'")
                        item.Click(simulateMove=False, waitTime=0)
                        selection_made = True
                        break

                if not selection_made:
                    raise ValueError(f"Expected status '{status}' not found in ComboBox list.")

                expand_collapse_pattern.Collapse()
                self.app_window.SendKeys('{Ctrl}S', waitTime=0)
                time.sleep(0.5)
            else:
                print("Patient is over 16 years old. No change needed.")
        except Exception as e:
            print(f"Error while changing patient status: {e}")
            raise

    def change_primary_patient_dentist(self, new_value: str):
        """
        Changes the primary patient dentist to the specified value.
        """
        try:
            self.open_tab("Stamkort")

            patient_dentist_combobox = self.wait_for_control(
                auto.ComboBoxControl,
                {"AutomationId": "ComboPatientDentistReg"},
                search_depth=10
                )

            def _get_selected_value():
                """Get the selected value from the ComboBox."""
                try:
                    return patient_dentist_combobox.GetValuePattern().Value
                except auto.PatternNotSupportedError:
                    pass

                for child in patient_dentist_combobox.GetChildren():
                    if isinstance(child, auto.EditControl):
                        return child.Name

                return patient_dentist_combobox.Name

            current_value = _get_selected_value()
            print(f"Current selected status: '{current_value}'")

            expected_value = new_value

            if current_value == expected_value:
                print("Status is already set correctly. No change needed.")
                return

            patient_dentist_combobox.GetPattern(auto.PatternId.ExpandCollapsePattern).Expand()
            patient_dentist_combobox_expanded = self.wait_for_control(
                auto.ListControl,
                {'ClassName': 'ComboLBox'},
                search_depth=3
            )

            selection_made = False
            for item in patient_dentist_combobox_expanded.GetChildren():
                if item.Name == expected_value:
                    print(f"Selecting '{expected_value}'")
                    item.Click(simulateMove=False, waitTime=0)
                    selection_made = True
                    break

            if not selection_made:
                raise ValueError(f"Expected status '{expected_value}' not found in ComboBox list.")

            patient_dentist_combobox.GetPattern(auto.PatternId.ExpandCollapsePattern).Collapse()
            time.sleep(0.5)
            combobox_new_value = _get_selected_value()
            print(f"New selected status: '{combobox_new_value}'")
            if combobox_new_value != expected_value:
                raise ValueError(f"Failed to set the correct status. Expected '{expected_value}', but got '{combobox_new_value}'.")

            self.app_window.SendKeys('{Ctrl}S', waitTime=0)

            try:
                pop_up_dialog = self.wait_for_control(
                    auto.WindowControl,
                    {'Name': 'Hændelser'},
                    search_depth=3,
                    timeout=5
                )
                pop_up_dialog.ButtonControl(Name="Nej").GetLegacyIAccessiblePattern().DoDefaultAction()
            except TimeoutError:
                print("No pop-up window found.")
        except Exception as e:
            print(f"Error while changing primary treater: {e}")
            raise
