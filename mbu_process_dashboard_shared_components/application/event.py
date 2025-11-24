import uiautomation as auto

from .handler_base import HandlerBase


class EventHandler(HandlerBase):
    """
    Handles “Hændelser” under “Stamkort”—specifically processes “Afgang til klinik 751”.
    """

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
