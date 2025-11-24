"""This module contains the EDIHandler class for handling EDI portal interactions."""
import time
import uiautomation as auto

from .handler_base import HandlerBase


class EDIHandler(HandlerBase):
    """
    Handles the EDI Portal UI interactions.
    """

    def open_edi_portal(self):
        """
        Opens the EDI portal in the SolteqTand application.
        """
        try:
            menu_edi_button = self.find_element_by_property(
                control=self.app_window,
                control_type=auto.ControlType.MenuItemControl,
                name="EDI Portal"
            )
            menu_edi_button.Click(simulateMove=False, waitTime=0)
            journalforsendelse_button = self.find_element_by_property(
                control=self.app_window,
                control_type=auto.ControlType.MenuItemControl,
                name="Opret journalforsendelse"
            )
            journalforsendelse_button.Click(simulateMove=False, waitTime=0)

            time.sleep(5)

        except Exception as e:
            print(f"Error while opening EDI Portal: {e}")

    def close_edi_portal(self):
        """
        Closes the current MS Edge window defined by edge_window.
        """
        try:
            edge_window = self.wait_for_control(
                auto.WindowControl, {"ClassName": "Chrome_WidgetWin_1"}, search_depth=3
            )
            edge_window.SetFocus()
            edge_window.GetWindowPattern().Close()
        except Exception as e:
            print(f"Error while closing EDI Portal: {e}")

    def edi_portal_click_next_button(self, sleep_time: int) -> None:
        """
        Clicks the next button in the EDI portal.

        Args:
            sleep_time (int): Time to wait after clicking the next button.
        """
        try:
            edge_window = self.wait_for_control(
                auto.WindowControl, {"ClassName": "Chrome_WidgetWin_1"}, search_depth=3
            )

            edge_window.SetFocus()

            try:
                next_button = self.wait_for_control(
                    auto.ButtonControl, {"Name": "Næste"},
                    search_depth=50,
                    timeout=5
                )
            except TimeoutError:
                next_button = None

            if not next_button:
                try:
                    next_button = self.wait_for_control(
                        auto.ButtonControl, {"AutomationId": "patientInformationNextButton"},
                        search_depth=50,
                        timeout=5
                    )
                except TimeoutError:
                    next_button = None

            if not next_button:
                raise RuntimeError("Next button not found in EDI Portal")
            next_button.Click(simulateMove=False, waitTime=0)
            time.sleep(sleep_time)
        except Exception as e:
            print(f"Error while clicking next button in EDI Portal: {e}")
            raise

    def edi_portal_check_contractor_id(self, extern_clinic_data: dict, sleep_time: int = 5) -> dict:
        """
        Checks if the contractor ID is valid in the EDI portal.

        Args:
            extern_clinic_data (dict): A dictionary containing the contractor ID and phone number.
            sleep_time (int): Time to wait after clicking the next button.

        Returns:
            dict: A dictionary containing the row count and whether the phone number matches.
        """
        try:
            # Handle Hasle Torv Clinic special case
            if extern_clinic_data[0]["contractorId"] == "477052" or extern_clinic_data[0]["contractorId"] == "470678":
                contractor_id = "485055"
                clinic_phone_number = "86135240"
            else:
                contractor_id = extern_clinic_data[0]["contractorId"]
                clinic_phone_number = extern_clinic_data[0]["phoneNumber"]

            self.edi_portal_click_next_button(sleep_time=2)

            class_options = [
                "form-control filter_search",
                "form-control filter_search valid",
            ]

            for class_name in class_options:
                try:
                    search_box = self.wait_for_control(
                        auto.EditControl,
                        {"ClassName": class_name},
                        search_depth=22,
                        timeout=1,
                    )
                except TimeoutError:
                    continue
                if search_box:
                    break
                else:
                    raise RuntimeError("Search box not found")
            search_box.SetFocus()
            search_box_value_pattern = search_box.GetPattern(auto.PatternId.ValuePattern)
            search_box_value_pattern.SetValue(contractor_id)
            search_box.SendKeys("{ENTER}")

            time.sleep(sleep_time)

            table_dentists = self.wait_for_control(
                auto.TableControl,
                {'AutomationId': 'table_id1'},
                search_depth=25,
            )
            grid_pattern = table_dentists.GetPattern(auto.PatternId.GridPattern)
            row_count = grid_pattern.RowCount

            is_phone_number_match = False

            if grid_pattern.GetItem(1, 0).Name == "Ingen data i tabellen":
                return {"rowCount": 0, "isPhoneNumberMatch": False}

            if row_count > 0:
                for row in range(row_count):
                    phone_number = grid_pattern.GetItem(row, 4).Name
                    if phone_number == clinic_phone_number:
                        is_phone_number_match = True
                        break
            return {"rowCount": row_count, "isPhoneNumberMatch": is_phone_number_match}
        except Exception as e:
            print(f"Error while checking contractor ID in EDI Portal: {e}")
            raise
