"""Base UI-Automation helper methods for SolteqTand project."""

import time
import uiautomation as auto


class BaseUI:
    """Base UI-Automation helper methods."""

    def find_element_by_property(self, control, control_type=None, automation_id=None, name=None, class_name=None) -> auto.Control:
        """
        Uses GetChildren to traverse through controls and find an element based on the specified properties.

        Args:
            control (Control): The root control to search from (e.g., main window or pane).
            control_type (ControlType, optional): ControlType to search for.
            automation_id (str, optional): AutomationId of the target element.
            name (str, optional): Name of the target element.
            class_name (str, optional): ClassName of the target element.

        Returns:
            Control: The found element or None if no match is found.
        """
        children = control.GetChildren()

        for child in children:
            if (
                (control_type is None or child.ControlType == control_type) and
                (automation_id is None or child.AutomationId == automation_id) and
                (name is None or child.Name == name) and
                (class_name is None or child.ClassName == class_name)
            ):
                return child

            found = self.find_element_by_property(child, control_type, automation_id, name, class_name)
            if found:
                return found

        return None

    def wait_for_control(self, control_type, search_params, search_depth=1, timeout=30, retry_interval=0.5):
        """
        Waits for a given control type to become available with the specified search parameters.

        Args:
            control_type: The type of control, e.g., auto.WindowControl, auto.ButtonControl, etc.
            search_params (dict): Search parameters used to identify the control.
                                The keys must match the properties used in the control type, e.g., 'AutomationId', 'Name'.
            search_depth (int): How deep to search in the user interface.
            timeout (int): Maximum time to wait for the control, in seconds.
            retry_interval (float): Time to wait between retries, in seconds.

        Returns:
            Control: The control object if found, otherwise raises TimeoutError.

        Raises:
            TimeoutError: If the control is not found within the timeout period.
        """
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                control = control_type(searchDepth=search_depth, **search_params)
                if control.Exists(0, 0):
                    return control
            except Exception as e:
                print(f"Error while searching for control: {e}")

            time.sleep(retry_interval)
            print(f"Retrying to find control: {search_params}...")

        raise TimeoutError(f"Control with parameters {search_params} was not found within the {timeout} second timeout.")

    def wait_for_control_to_disappear(self, control_type, search_params, search_depth=1, timeout=30):
        """
        Waits for a given control type to disappear with the specified search parameters.

        Args:
            control_type: The type of control, e.g., auto.WindowControl, auto.ButtonControl, etc.
            search_params (dict): Search parameters used to identify the control.
                                The keys must match the properties used in the control type, e.g., 'AutomationId', 'Name'.
            search_depth (int): How deep to search in the user interface.
            timeout (int): How long to wait, in seconds.

        Returns:
            bool: True if the control disappeared within the timeout period, otherwise False.
        """
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                control = control_type(searchDepth=search_depth, **search_params)
                if not control.Exists(0, 0):
                    return True
            except Exception as e:
                print(f"Error while searching for control: {e}")

            time.sleep(0.5)
            print(f"Retrying to find control: {search_params}...")

        raise TimeoutError(f"Control with parameters {search_params} did not disappear within the timeout period.")

    def close_window(self, window_to_close: auto.WindowControl) -> None:
        """Closes specified window."""
        window_name = window_to_close.Name
        window_to_close.SetFocus()
        window_to_close.GetWindowPattern().Close()

        # Handle popup when closin main window
        if window_name.lower().startswith("hovedvindue"):

            pop_up_window = window_to_close.WindowControl(Name="TMT - Afslut")
            pop_up_window.SetFocus()
            pop_up_window.ButtonControl(Name="Ja").Click(simulateMove=False, waitTime=0)

            time.sleep(2)

        else:
            self.app_window = self.wait_for_control(search_params={'AutomationId': 'FormFront'}, control_type=auto.WindowControl)
