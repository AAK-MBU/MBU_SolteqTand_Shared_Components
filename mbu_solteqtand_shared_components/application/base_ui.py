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

    def iter_windows(self, search_depth=2):
        """
        Yields the windows currently open, from the desktop root down to search_depth.

        Only windows are descended into, since Solteq's dialogs are children of the
        application windows rather than of arbitrary panes.

        Args:
            search_depth (int): How deep below the desktop root to look for windows.

        Yields:
            Control: Each WindowControl found.
        """
        level = [auto.GetRootControl()]
        for _ in range(search_depth):
            next_level = []
            for control in level:
                try:
                    children = control.GetChildren()
                except Exception as e:
                    print(f"Error while listing child windows: {e}")
                    continue

                for child in children:
                    if child.ControlType == auto.ControlType.WindowControl:
                        yield child
                        next_level.append(child)

            level = next_level

    def collect_control_texts(self, control, max_depth=4, max_controls=200):
        """
        Collects the names of a control and its descendants.

        The walk is bounded by max_depth and max_controls so it is cheap enough to run
        repeatedly while polling, and so an unexpectedly large window can't stall a process.

        Args:
            control (Control): The control to read text from.
            max_depth (int): How deep below the control to walk.
            max_controls (int): Upper bound on how many controls to visit.

        Returns:
            list[str]: The non-empty names that were found.
        """
        texts = []
        remaining = max_controls
        pending = [(control, 0)]

        while pending and remaining > 0:
            node, depth = pending.pop()
            remaining -= 1

            try:
                name = node.Name
                children = node.GetChildren() if depth < max_depth else []
            except Exception as e:
                print(f"Error while reading control text: {e}")
                continue

            if name:
                texts.append(name)
            pending.extend((child, depth + 1) for child in children)

        return texts

    def find_window_containing_text(self, text_fragment, search_depth=2, max_depth=4):
        """
        Finds the first open window whose title or visible text contains the given fragment.

        Used to spot the modal dialogs Solteq puts in front of the window we are waiting for,
        where the dialog's title is unknown but part of its message is.

        Args:
            text_fragment (str): Text to look for, matched case-insensitively.
            search_depth (int): How deep below the desktop root to look for windows.
            max_depth (int): How deep inside each window to look for the text.

        Returns:
            Control: The matching window, or None if no window contains the fragment.
        """
        fragment = text_fragment.casefold()

        for window in self.iter_windows(search_depth=search_depth):
            texts = self.collect_control_texts(window, max_depth=max_depth)
            if any(fragment in text.casefold() for text in texts):
                return window

        return None

    def dismiss_dialog(self, dialog, button_names=("OK", "Ja")):
        """
        Clicks the first of the given buttons that exists on a dialog.

        Args:
            dialog (Control): The dialog window to dismiss.
            button_names (tuple[str]): Button names to try, in order of preference.

        Returns:
            str: The name of the button that was clicked, or None if none of them were found.
        """
        for button_name in button_names:
            button = dialog.ButtonControl(Name=button_name)
            if button.Exists(0, 0):
                button.SetFocus()
                button.Click(simulateMove=False, waitTime=0)
                return button_name

        return None

    def close_window(self, window_to_close: auto.WindowControl) -> None:
        """Closes specified window."""
        window_name = window_to_close.Name
        window_to_close.SetFocus()
        window_to_close.GetWindowPattern().Close()

        # Handle popup when closin main window
        if window_name.lower().startswith("hovedvindue"):

            pop_up_window = window_to_close.WindowControl(Name="Tand - Afslut")
            pop_up_window.SetFocus()
            pop_up_window.ButtonControl(Name="Ja").Click(simulateMove=False, waitTime=0)

            time.sleep(2)

        else:
            self.app_window = self.wait_for_control(search_params={'AutomationId': 'FormFront'}, control_type=auto.WindowControl)
