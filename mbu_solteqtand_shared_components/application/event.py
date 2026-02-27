import time
import uiautomation as auto

from .handler_base import HandlerBase


class EventHandler(HandlerBase):
    """
    Handles “Hændelser” under “Stamkort”—specifically processes “Afgang til klinik 751”.
    """

    def create_new_event(self, clinic_name: str, event_text: str):
        """
        Opens and creates a new event for the patient
        """

        try:
            functions_button = self.find_element_by_property(
                control=self.app_window,
                control_type=auto.ControlType.MenuItemControl,
                name="Funktioner"
            )
            functions_button.Click(simulateMove=False, waitTime=0)

            henvis_patient_button = self.find_element_by_property(
                control=self.app_window,
                control_type=auto.ControlType.MenuItemControl,
                name="Henvis patient"
            )
            henvis_patient_button.Click(simulateMove=False, waitTime=0)

            time.sleep(1)

            # --- Wait for Find Klinik window ---
            clinic_window = self.wait_for_control(
                auto.WindowControl,
                {"AutomationId": "FormFindClinics"},
                search_depth=5
            )

            time.sleep(1)

            # --- Focus the clinic list ---
            list_control = clinic_window.ListControl(AutomationId="ListClinics")
            list_control.SetFocus()

            # Small delay to avoid sending keys too early
            time.sleep(2)

            # --- Fast selection: type name + ENTER ---
            list_control.SendKeys(clinic_name + "{ENTER}")

            # Optional: wait a moment to ensure dialog closes
            time.sleep(1)

            # --- Fast selection: type name + ENTER ---
            list_control.SendKeys(event_text + "{ENTER}")

        except Exception as e:
            print(f"Error while opening EDI Portal: {e}")

    def process_event(self):
        """
        Processes the event 'Afgang til klinik 751' under the 'Stamkort' tab.
        """
        try:
            self.open_tab("Stamkort")
            self.open_sub_tab("Hændelser")

            list_view = self.wait_for_control(
                auto.ListControl,
                {"AutomationId": "ListView1"},
                search_depth=9
            )

            target_values = {"Afgang til klinik 751", "Stamklinik afgang", "Nej"}
            for item in list_view.GetChildren():
                if item.ControlType == auto.ControlType.ListItemControl:
                    sub_items = [sub.Name for sub in item.GetChildren()]
                    if target_values.issubset(set(sub_items)):
                        matching_row = item
                        break

            if matching_row:
                if matching_row.GetPattern(auto.PatternId.TogglePattern).ToggleState == 0:
                    matching_row.GetPattern(auto.PatternId.TogglePattern).Toggle()
                process_button = self.wait_for_control(
                    auto.ButtonControl,
                    {"Name": "Afvikl"},
                    search_depth=10
                )
                process_button.GetLegacyIAccessiblePattern().DoDefaultAction()
                create_administrative_note_popup = self.wait_for_control(
                    auto.WindowControl,
                    {"Name": "Opret administrativt notat"},
                    search_depth=3
                )
                create_administrative_note_popup.ButtonControl(Name="Nej").GetLegacyIAccessiblePattern().DoDefaultAction()
            print("Event processed")
        except Exception as e:
            print(f"Error while processing event: {e}")
            raise

    def process_tilflytter_event(self):
        """
        Processes the event 'Tilflytter' under the 'Stamkort' tab.
        """

        matching_row = None

        try:
            self.open_tab("Stamkort")
            self.open_sub_tab("Hændelser")

            list_view = self.wait_for_control(
                auto.ListControl,
                {"AutomationId": "ListView1"},
                search_depth=9
            )

            target_values = {"TEST: Ny tilflytter", "Henvisning", "Nej"}

            for item in list_view.GetChildren():
                if item.ControlType == auto.ControlType.ListItemControl:
                    sub_items = [sub.Name for sub in item.GetChildren()]

                    if target_values.issubset(set(sub_items)):
                        matching_row = item

                        break

            if matching_row:
                if matching_row.GetPattern(auto.PatternId.TogglePattern).ToggleState == 0:
                    matching_row.GetPattern(auto.PatternId.TogglePattern).Toggle()

                process_button = self.wait_for_control(
                    auto.ButtonControl,
                    {"Name": "Afvikl"},
                    search_depth=10
                )

                process_button.GetLegacyIAccessiblePattern().DoDefaultAction()

                create_administrative_note_popup = self.wait_for_control(
                    auto.WindowControl,
                    {"Name": "Opret administrativt notat"},
                    search_depth=3
                )

                create_administrative_note_popup.ButtonControl(Name="Nej").GetLegacyIAccessiblePattern().DoDefaultAction()

            print("Event processed")

        except Exception as e:
            print(f"Error while processing event: {e}")

            raise
