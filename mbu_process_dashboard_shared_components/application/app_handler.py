"""This module provides the main application handler for Solteq Tand, integrating various components."""

import os

import uiautomation as auto

from .aftalebog import AftalebogHandler
from .appointment import AppointmentHandler
from .base_ui import BaseUI
from .clinic import ClinicHandler
from .document import DocumentHandler
from .edi_portal import EDIHandler
from .event import EventHandler
from .journal_note import JournalNoteHandler
from .patient import PatientHandler


class SolteqTandApp(
    BaseUI,
    PatientHandler,
    DocumentHandler,
    AppointmentHandler,
    EDIHandler,
    ClinicHandler,
    EventHandler,
    JournalNoteHandler,
    AftalebogHandler,
):
    """
    Main application handler for Solteq Tand, integrating various components.

    Inherits from:
        BaseUI: Provides basic UI interaction methods.
        PatientHandler: Handles patient-related operations.
        DocumentHandler: Manages document operations.
        AppointmentHandler: Manages appointment operations.
        EDIHandler: Handles EDI portal interactions.
        ClinicHandler: Manages clinic-related operations.
        EventHandler: Processes events in the application.
        JournalNoteHandler: Handles journal note operations.
    """

    def __init__(self, app_path: str, username: str = None, password: str = None):
        """
        Initializes the Solteq Tand application handler.

        Args:
            app_path (str): Path to the Solteq Tand application executable.
        """
        self.app_path = app_path
        self.username = username
        self.password = password
        self.app_window = None

    def start_application(self):
        """
        Starts the application using the specified path.
        """
        os.startfile(self.app_path)

    def login(self):
        """
        Logs into the application by entering the username and password.
        Checks if the login window is open and ready.
        Checks if the main window is opened and ready.
        """
        self.app_window = self.wait_for_control(
            auto.WindowControl,
            {"AutomationId": "FormLogin"},
            search_depth=3,
            timeout=60,
        )
        self.app_window.SetFocus()

        username_box = self.app_window.EditControl(AutomationId="TextLogin")
        username_box.SendKeys(text=self.username)

        password_box = self.app_window.EditControl(AutomationId="TextPwd")
        password_box.SendKeys(text=self.password)

        login_button = self.app_window.PaneControl(AutomationId="ButtonLogin")
        login_button.SetFocus()
        login_button.SendKeys("{ENTER}")

        self.app_window = self.wait_for_control(
            auto.WindowControl,
            {"AutomationId": "FormFront"},
            search_depth=2,
            timeout=60,
        )

    def open_sub_tab(self, sub_tab_name: str):
        """
        Opens a specific sub-tab in the patient's main card.

        Args:
            sub_tab_name (str): The name of the sub-tab to open (e.g., "Dokumenter").
        """
        sub_tab_button = self.app_window.TabItemControl(Name=sub_tab_name)
        is_sub_tab_selected = sub_tab_button.GetPattern(10010).IsSelected

        if not is_sub_tab_selected:
            sub_tab_button.SetFocus()
            sub_tab_button.SendKeys("{ENTER}")

    def open_tab(self, tab_name: str):
        """
        Opens a specific tab in the patient's main card.
        Poosibly functionality on other parts of Solteq with tabs as well.

        Args:
            tab_name (str): The name of the tab to open (e.g., "Frit valg").
        """
        match tab_name:
            case "Stamkort":
                tab_name_modified = "S&tamkort"
            case "Fritvalg":
                tab_name_modified = "F&ritvalg"
            case "Journal":
                tab_name_modified = "&Journal"
            case "Oversigt":
                tab_name_modified = "O&versigt"
            case _:
                tab_name_modified = tab_name

        tab_button = self.find_element_by_property(
            control=self.app_window,
            control_type=auto.ControlType.TabItemControl,
            name=tab_name_modified,
        )
        is_tab_selected = tab_button.GetPattern(10010).IsSelected

        if not is_tab_selected:
            tab_button.SetFocus()
            tab_button.SendKeys("{ENTER}")

    def open_from_main_menu(self, menu_item: str) -> None:
        """
        Opens menu item from Solteq main menu"""

        # Find hyperlink
        menu_link = self.wait_for_control(
            control_type=auto.HyperlinkControl,
            search_params={"Name": menu_item},
            search_depth=5,
        )

        menu_link.GetInvokePattern().Invoke()

        self.app_window = self.wait_for_control(
            control_type=auto.WindowControl,
            search_params={"AutomationId": "FormBooking"},
            search_depth=2,
        )

    def close_solteq_tand(self):
        """Closes the Solteq Tand application gracefully."""
        try:
            if self.app_window:
                self.close_window(self.app_window)
                self.app_window = None
        except Exception as error:
            print(f"Error closing Solteq Tand application window: {error}")
