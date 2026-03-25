"""Module responsible for handling journal note operations in the Solteq Tand application."""

import uiautomation as auto

from .handler_base import HandlerBase


class JournalNoteHandler(HandlerBase):
    """
    Handles the processing of journal notes in the Solteq Tand application.
    """

    def create_journal_note(self, note_message: str, checkmark_in_complete: bool):
        """
        Creates a journal note for the given patient.

        Args:
            note_message (str): The note message.
            checkmark_in_complete (bool): Checks the checkmark in 'Afslut'.
        """
        self.open_tab("Journal")

        self.wait_for_control(
            auto.DocumentControl, {"AutomationId": "RichTextBoxInput"}, search_depth=21
        )

        input_box = self.app_window.DocumentControl(AutomationId="RichTextBoxInput")
        input_box_value_pattern = input_box.GetValuePattern()
        input_box_value_pattern.SetValue(value=note_message, waitTime=0)

        if checkmark_in_complete:
            checkbox = self.app_window.CheckBoxControl(
                AutomationId="CheckBoxAssignCompletionStatus"
            )
            checkbox.SetFocus()
            checkbox.Click(simulateMove=False, waitTime=0)

        save_button = self.app_window.PaneControl(AutomationId="buttonSave")
        save_button.SetFocus()
        save_button.Click(simulateMove=False, waitTime=0)

    def _set_checkbox_state(self, checkbox_control, target_state: int) -> None:
        """Ensures checkbox toggle state is exactly 0 (off) or 1 (on)."""
        if target_state not in (0, 1):
            raise ValueError(f"Invalid target_state={target_state!r}, expected 0 or 1")

        toggle_pattern = checkbox_control.GetPattern(auto.PatternId.TogglePattern)
        if toggle_pattern is None:
            raise RuntimeError("TogglePattern is not available on checkbox control")

        for _ in range(3):
            current_state = toggle_pattern.ToggleState
            if current_state == target_state:
                return
            toggle_pattern.Toggle()
            time.sleep(0.05)

        final_state = toggle_pattern.ToggleState
        if final_state != target_state:
            raise RuntimeError(
                f"Failed to set checkbox state to {target_state}, current={final_state}"
            )

    def _activate_journal_row(self, row_item, list_control) -> None:
        """Attempts multiple UIA strategies to bring a row into view and select it."""
        row_item.SetFocus()

        # Try ScrollItemPattern if available.
        try:
            scroll_item_pattern = row_item.GetScrollItemPattern()
            if scroll_item_pattern is not None:
                scroll_item_pattern.ScrollIntoView()
        except Exception:
            pass

        # Fallback for controls exposing an explicit ScrollIntoView method.
        if hasattr(row_item, "ScrollIntoView"):
            try:
                row_item.ScrollIntoView()
            except Exception:
                pass

        # Try SelectionItemPattern to select the row, which may also scroll it into view.
        try:
            selection_item_pattern = row_item.GetSelectionItemPattern()
            if selection_item_pattern is not None:
                selection_item_pattern.Select()
        except Exception:
            pass

        # Ensure list focus before click fallback.
        try:
            list_control.SetFocus()
        except Exception:
            pass

        row_item.DoubleClick(simulateMove=False, waitTime=0)

    def create_journal_sub_note(
        self,
        parent_note_type: str,
        parent_note_message: str,
        note_message: str,
        checkmark_in_complete: bool,
    ):
        """Creates a sub note to an existing journal note in SolteqTand."""
        self.open_tab("Journal")

        self.wait_for_control(
            auto.ListControl, {"AutomationId": "listViewTasks"}, search_depth=21
        )
        journal_note_list = self.app_window.ListControl(AutomationId="listViewTasks")
        journal_note_list.SetFocus()

        def _norm(value: str) -> str:
            normalized = (value or "").strip().casefold()
            normalized = normalized.strip("'\"`´")
            normalized = " ".join(normalized.split())
            return normalized

        wanted_type = _norm(parent_note_type)
        wanted_text = _norm(parent_note_message)

        parent_note_item = None
        timeout_seconds = 30
        poll_seconds = 0.5
        deadline = time.monotonic() + timeout_seconds

        while time.monotonic() < deadline and parent_note_item is None:
            for item in journal_note_list.GetChildren():
                try:
                    note_type_raw = ""
                    sub_note_col_raw = ""
                    note_text_raw = ""

                    grid_pattern = None
                    try:
                        grid_pattern = item.GetGridPattern()
                    except AttributeError:
                        pass

                    if grid_pattern is not None:
                        note_type_raw = grid_pattern.GetItem(0, 3).Name
                        sub_note_col_raw = grid_pattern.GetItem(0, 5).Name
                        note_text_raw = grid_pattern.GetItem(0, 7).Name
                    else:
                        child_cells = [
                            (getattr(child, "Name", "") or "").strip()
                            for child in item.GetChildren()
                        ]

                        if len(child_cells) > 7:
                            note_type_raw = child_cells[3]
                            sub_note_col_raw = child_cells[5]
                            note_text_raw = child_cells[7]
                        else:
                            continue

                    note_type = _norm(note_type_raw)
                    sub_note_col = _norm(sub_note_col_raw)
                    note_text = _norm(note_text_raw)

                except Exception:
                    continue

                if (
                    note_type == wanted_type
                    and sub_note_col in ("", "-")
                    and note_text == wanted_text
                ):
                    parent_note_item = item
                    break

            if parent_note_item is None:
                time.sleep(poll_seconds)

        if parent_note_item is None:
            raise ValueError(
                f"Parent note not found within {timeout_seconds}s "
                f"(type='{parent_note_type}', message='{parent_note_message}')"
            )

        self._activate_journal_row(parent_note_item, journal_note_list)

        pop_up_window = self.wait_for_control(
            auto.WindowControl,
            {"AutomationId": "ToolContextWrapperUI"},
            search_depth=50,
        )

        input_box = pop_up_window.DocumentControl(AutomationId="RichTextBoxInput")
        input_box_value_pattern = input_box.GetValuePattern()
        input_box_value_pattern.SetValue(value=f"{note_message}", waitTime=0)

        checkbox = pop_up_window.CheckBoxControl(
            AutomationId="CheckBoxAssignCompletionStatus"
        )
        self._set_checkbox_state(
            checkbox, target_state=1 if checkmark_in_complete else 0
        )

        save_button = pop_up_window.PaneControl(AutomationId="&Gem")
        if not save_button.IsEnabled:
            raise RuntimeError("Save button is not enabled")
        save_button.Click(simulateMove=False, waitTime=0)

        close_button = pop_up_window.PaneControl(AutomationId="&Luk")
        if not close_button.IsEnabled:
            raise RuntimeError("Close button is not enabled")
        close_button.Click(simulateMove=False, waitTime=0)
