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
            auto.DocumentControl,
            {"AutomationId": "RichTextBoxInput"},
            search_depth=21
            )

        input_box = self.app_window.DocumentControl(AutomationId="RichTextBoxInput")
        input_box_value_pattern = input_box.GetValuePattern()
        input_box_value_pattern.SetValue(value=note_message, waitTime=0)

        if checkmark_in_complete:
            checkbox = self.app_window.CheckBoxControl(AutomationId="CheckBoxAssignCompletionStatus")
            checkbox.SetFocus()
            checkbox.Click(simulateMove=False, waitTime=0)

        save_button = self.app_window.PaneControl(AutomationId="buttonSave")
        save_button.SetFocus()
        save_button.Click(simulateMove=False, waitTime=0)
