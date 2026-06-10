import uiautomation as auto

from .handler_base import HandlerBase


class ClinicHandler(HandlerBase):
    """
    Handles changing the primart clinic for a patient (if it's not "Tandplejen Aarhus").
    """

    def change_primary_clinic(self, current_primary_clinic: str, is_field_locked: bool):
        """
        Changes the primary clinic for the patient.
        """
        try:
            self.open_tab("Stamkort")

            if current_primary_clinic != "Tandplejen Aarhus":
                if is_field_locked:
                    locked_field = self.wait_for_control(
                        auto.CheckBoxControl,
                        {"AutomationId": "CheckPatientClinicRegLocked"},
                        search_depth=9,
                    )

                    if locked_field.GetPattern(
                        auto.PatternId.TogglePattern
                    ).ToggleState:
                        locked_field.GetPattern(auto.PatternId.TogglePattern).Toggle()
                        locked_field.SendKeys("{Ctrl}s", waitTime=0)

                box_clinic_parent = self.wait_for_control(
                    auto.GroupControl,
                    {"AutomationId": "GroupBoxPatientDentalInfo"},
                    search_depth=8,
                )
                box_clinic = box_clinic_parent.PaneControl(
                    searchDepth=2, AutomationId="ControlClinicSelectorPatientClinicReg"
                ).PaneControl(searchDepth=2, AutomationId="PictureBoxClinic")
                box_clinic.Click(simulateMove=False, waitTime=0)

                clinic_list = self.wait_for_control(
                    auto.WindowControl,
                    {"AutomationId": "FormFindClinics"},
                    search_depth=2,
                )

                clinic_list_items = clinic_list.ListControl(
                    AutomationId="ListClinics"
                ).ListItemControl(Name="Tandplejen Aarhus")
                clinic_list_items.GetPattern(10017).ScrollIntoView()
                clinic_list_items.SetFocus()
                clinic_list_items.DoubleClick(simulateMove=False, waitTime=0)

                locked_field = self.wait_for_control(
                    auto.CheckBoxControl,
                    {"AutomationId": "CheckPatientClinicRegLocked"},
                    search_depth=9,
                )

                if (
                    locked_field.GetPattern(auto.PatternId.TogglePattern).ToggleState
                    == 0
                ):
                    locked_field.GetPattern(auto.PatternId.TogglePattern).Toggle()
                    locked_field.SendKeys("{Ctrl}s", waitTime=0)

                self.wait_for_control(
                    auto.TextControl, {"Name": "Patient er gemt."}, search_depth=3
                )

                print("Primary clinic changed successfully.")
            print("Patient already has the primary clinic set to 'Tandplejen Aarhus'")
        except Exception as e:
            print(f"Error while changing primary clinic: {e}")
            raise

    def change_private_clinic(self, private_clinic: str):
        """
        Changes the primary clinic for the patient.
        """
        try:
            self.open_tab("Stamkort")
            self.open_sub_tab("Tilhør")

            box_clinic_parent = self.wait_for_control(
                auto.GroupControl,
                {"AutomationId": "GroupBoxPatientPrivateDentist"},
                search_depth=20,
            )
            box_clinic = box_clinic_parent.PaneControl(
                searchDepth=2, AutomationId="ControlClinicSelectorPatientPrivateDentist"
            ).PaneControl(searchDepth=2, AutomationId="PictureBoxClinic")
            box_clinic.Click(simulateMove=False, waitTime=0)

            clinic_list = self.wait_for_control(
                auto.WindowControl, {"AutomationId": "FormFindClinics"}, search_depth=10
            )
            clinic_list.PaneControl(AutomationId="Panel1").PaneControl(
                AutomationId="ButtonReset"
            ).Click(simulateMove=False, waitTime=0)
            clinic_list.PaneControl(AutomationId="Panel1").PaneControl(
                AutomationId="ButtonSearchClinics"
            ).Click(simulateMove=False, waitTime=0)

            clinic_list_updated = self.wait_for_control(
                auto.WindowControl, {"AutomationId": "FormFindClinics"}, search_depth=10
            )
            clinic_list_items = clinic_list_updated.ListControl(
                AutomationId="ListClinics"
            ).ListItemControl(Name=private_clinic, timeout=30)
            clinic_list_items.GetPattern(10017).ScrollIntoView()
            clinic_list_items.SetFocus()
            clinic_list_items.DoubleClick(simulateMove=False, waitTime=0)

            self.app_window.SendKeys("{Ctrl}s", waitTime=0)

            self.wait_for_control(
                auto.TextControl, {"Name": "Patient er gemt."}, search_depth=3
            )

        except Exception as e:
            print(f"Error while changing primary clinic: {e}")
            raise
