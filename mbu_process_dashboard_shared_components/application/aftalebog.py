from datetime import datetime

import uiautomation as auto

from .handler_base import HandlerBase


class AftalebogHandler(HandlerBase):
    """Functions within aftalebog"""

    def get_appointments_aftalebog(
        self, close_after: bool = False, headers_to_keep: list | None = None
    ) -> dict:
        """Function to retrive data on appointments in view in aftalebog"""

        # Get list control
        list_box = self.wait_for_control(
            control_type=auto.GroupControl,
            search_params={"AutomationId": "GroupBoxView"},
            search_depth=5,
        )

        appointment_list = self.find_element_by_property(
            control=list_box, control_type=50008
        )

        # Extract headers
        appointment_headers = [
            header.Name
            for header in appointment_list.GetFirstChildControl().GetChildren()
        ]

        # Extract ListItem controls
        appointment_ctrls = [
            ctrl for ctrl in appointment_list.GetChildren() if ctrl.ControlType == 50007
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
            list_box.SendKeys("{Control}{F4}")
            self.wait_for_control_to_disappear(
                control_type=auto.WindowControl,
                search_params={"AutomationId": "FormBooking"},
            )

        return appointment_data

    def set_date_in_aftalebog(self, from_date: datetime, to_date: datetime) -> None:
        """Set to and from dates in aftalebog oversigt"""
        import locale

        dt_picker_from = self.wait_for_control(
            control_type=auto.PaneControl,
            search_params={"AutomationId": "DateTimePickerFromDate"},
            search_depth=7,
        )

        from_keys = (
            f"{from_date.day}"
            + "{right}"
            + f"{from_date.month}"
            + "{right}"
            + f"{from_date.year}"
        )

        dt_picker_from.SendKeys(from_keys)

        try:
            from_date.strftime(format="%d. %B %Y") == dt_picker_from.Name
        except Exception:
            # Should maybe try a number of times until it hits right or ends in systemerror
            # End with raise error where resulting dates are printed
            print("Dates after insert not matching input")
            print(
                (
                    f"'From' input: {from_date.strftime(format='%d. %B %Y')} "
                    + f"Current value: {dt_picker_from.Name}"
                )
            )

        dt_picker_to = self.wait_for_control(
            control_type=auto.PaneControl,
            search_params={"AutomationId": "DateTimePickerToDate"},
            search_depth=7,
        )

        to_keys = (
            f"{to_date.day}"
            + "{right}"
            + f"{to_date.month}"
            + "{right}"
            + f"{to_date.year}"
        )

        dt_picker_to.SendKeys(to_keys)

        locale.setlocale(locale.LC_TIME, "da_dk.utf-8")

        try:
            to_date.strftime(format="%d. %B %Y") == dt_picker_to.Name
        except Exception:
            print("Dates after insert not matching input")
            print(
                (
                    f"'To' input: {to_date.strftime(format='%d. %B %Y')} "
                    + f"Current value: {dt_picker_to.Name}"
                )
            )

    def pick_appointment_types_aftalebog(self, appointment_types: str | list):
        """Set one or more appointment types in aftalebog oversigt"""

        if isinstance(appointment_types, str):
            appointment_types = [appointment_types]

        # deselect all
        slct_none = self.wait_for_control(
            control_type=auto.PaneControl,
            search_params={"AutomationId": "ButtonToggleStatusList"},
            search_depth=7,
        )
        slct_none.SetFocus()
        # If possible to select none click once, otherwise click twice
        try:
            assert slct_none.Name == "Vælge ingen"
            slct_none.SendKeys("{Enter}")
        except AssertionError:
            slct_none.SendKeys("{Enter}{Enter}")

        # Getting status controls
        status_list = self.wait_for_control(
            control_type=auto.ListControl,
            search_params={"AutomationId": "CheckedListBoxStatus"},
            search_depth=7,
        )
        status_ctrls = [
            _child
            for _child in status_list.GetChildren()
            if _child.ControlType == 50002
        ]
        status_names = [
            _child.Name
            for _child in status_list.GetChildren()
            if _child.ControlType == 50002
        ]

        # Toggle all selected appointment types
        for a_type in appointment_types:
            slct_idx = status_names.index(a_type)
            status_ctrls[slct_idx].GetTogglePattern().Toggle()

    def pick_clinic_aftalebog(self, clinic: str):
        """Set clinic in aftalebog oversigt"""

        ## UNFINISHED
        # Press clinic button
        clinic_button = self.wait_for_control(
            control_type=auto.PaneControl,
            search_params={"AutomationId": "ButtonClinic"},
            search_depth=8,
        )
        clinic_button.SetFocus()
        clinic_button.SendKeys("{Enter}")

        # Wait for popup window
        find_clinic = self.wait_for_control(
            control_type=auto.WindowControl,
            search_params={"AutomationId": "FormFindClinics"},
            search_depth=2,
        )
        # Get list and select clinic
        clinic_list = self.find_element_by_property(
            control=find_clinic, automation_id="ListClinics"
        )
        clinic_ctrls = [
            _child
            for _child in clinic_list.GetChildren()
            if _child.ControlType == 50007
        ]
        clinic_names = [
            _child.Name
            for _child in clinic_list.GetChildren()
            if _child.ControlType == 50007
        ]
        try:
            slct_idx = clinic_names.index(clinic)
        except Exception as e:
            print(e)
            print(f"Chosen clinic: {clinic}")
            print("Possibilities: ")
            print(" \n".join(clinic_names[::-1]))
        # Search for the clinic if it is in the list (to get in focus)
        find_clinic.SendKeys(clinic)
        clinic_ctrls[slct_idx].SetFocus()
        clinic_ctrls[slct_idx].SendKeys("{Enter}")
