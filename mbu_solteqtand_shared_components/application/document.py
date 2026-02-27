"""Base UI-Automation helper methods for SolteqTand project."""

import os
import shutil
import time

from datetime import datetime

import psutil

import uiautomation as auto

from psutil import NoSuchProcess, ZombieProcess, AccessDenied
from docx2pdf import convert

from .handler_base import HandlerBase


class DocumentHandler(HandlerBase):
    """
    Handles everything under the “Dokumenter” sub-tab in a patient's record,
    including creating a document, merging from a template, converting DOCX → PDF,
    sending via Digital Post, and creating a digital-printed journal.
    """

    def create_document(
        self,
        document_full_path: str = None,
        document_type: str = None,
        document_description: str = None,
    ):
        """
        Creates a new document under the 'Dokumenter' tab.

        Args:
            document_full_path (str, optional): The full path of the document to upload.
            document_type (str, optional): The type of document to select from the dropdown.
        """
        self.open_tab("Stamkort")
        self.open_sub_tab("Dokumenter")

        document_list = self.find_element_by_property(
            control=self.app_window,
            control_type=auto.ControlType.ListControl,
            automation_id="cleverListView1",
        )
        document_list.RightClick(simulateMove=False, waitTime=0)

        document_list_menu = self.wait_for_control(
            auto.MenuControl, {"Name": "Kontekst"}, search_depth=2
        )

        menu_create_document = self.find_element_by_property(
            control=document_list_menu,
            control_type=auto.ControlType.MenuItemControl,
            name="Opret",
        )
        menu_create_document.Click(simulateMove=False, waitTime=0)

        create_document_window = self.wait_for_control(
            auto.WindowControl, {"AutomationId": "UploadFile"}, search_depth=2
        )
        file_path_textbox = self.find_element_by_property(
            control=create_document_window,
            control_type=auto.ControlType.EditControl,
            automation_id="textBoxLocalFilePath",
        )
        legacy_pattern = file_path_textbox.GetLegacyIAccessiblePattern()
        legacy_pattern.SetValue(document_full_path)

        if document_type:
            document_type_drop_down = self.find_element_by_property(
                control=create_document_window,
                control_type=auto.ControlType.ButtonControl,
                name="Åbn",
            )
            document_type_drop_down.Click(simulateMove=False, waitTime=0)

            document_type_button = self.find_element_by_property(
                control=create_document_window,
                control_type=auto.ControlType.ListItemControl,
                name=document_type,
            )
            document_type_button.Click(simulateMove=False, waitTime=0)

        if document_description:
            description_text_field = self.find_element_by_property(
                control=create_document_window,
                control_type=auto.ControlType.DocumentControl,
                automation_id="richTextBoxDescription",
            )
            value_pattern = description_text_field.GetPattern(
                auto.PatternId.ValuePattern
            )
            value_pattern.SetValue(document_description)

        button_create_document = self.find_element_by_property(
            control=create_document_window,
            control_type=auto.ControlType.PaneControl,
            automation_id="buttonOpen",
        )
        button_create_document.Click(simulateMove=False, waitTime=0)

    def kill_process_by_name_safe(self, process_name: str) -> None:
        """
        Safely kills all processes matching the given name.
        Handles race conditions where processes may exit between enumeration and killing.

        Args:
            process_name: Name of the process to kill (e.g., 'WINWORD.EXE')
        """
        print(f"Attempting to kill processes: {process_name}")

        # Find all matching processes first
        target_processes = []
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if proc.info["name"] == process_name:
                    target_processes.append(proc)
            except (NoSuchProcess, ZombieProcess, AccessDenied):
                # Process already gone or inaccessible, skip it
                continue
            except Exception as e:
                print(f"Error checking process {getattr(proc, 'pid', 'unknown')}: {e}")
                continue

        if not target_processes:
            print(f"No processes found matching: {process_name}")
            return

        print(f"Found {len(target_processes)} process(es) matching {process_name}")

        # First, try graceful termination
        for proc in target_processes:
            try:
                proc.terminate()
                print(f"Terminated {process_name} (PID: {proc.pid})")
            except (NoSuchProcess, ZombieProcess):
                # Process already gone - this is actually what we want
                print(f"Process {process_name} (PID: {proc.pid}) already terminated")
                continue
            except AccessDenied:
                print(f"Access denied terminating {process_name} (PID: {proc.pid})")
                continue
            except Exception as e:
                print(f"Error terminating {process_name} (PID: {proc.pid}): {e}")
                continue

        # Wait for processes to exit gracefully
        try:
            gone, alive = psutil.wait_procs(target_processes, timeout=3)

            # Log successful terminations
            for proc in gone:
                print(f"{process_name} (PID: {proc.pid}) exited gracefully")

            # Force kill any remaining processes
            for proc in alive:
                try:
                    proc.kill()
                    print(f"Force killed {process_name} (PID: {proc.pid})")
                except (NoSuchProcess, ZombieProcess):
                    # Process already gone - this is fine
                    print(
                        f"Process {process_name} (PID: {proc.pid}) already gone during force kill"
                    )
                    continue
                except AccessDenied:
                    print(f"Access denied killing {process_name} (PID: {proc.pid})")
                    continue
                except Exception as e:
                    print(f"Error force killing {process_name} (PID: {proc.pid}): {e}")
                    continue

        except Exception as e:
            print(f"Error waiting for processes to terminate: {e}")

    def create_document_from_template(self, metadata: dict) -> None:
        """
        Under “Print/Flet patienter” → select template → merge → wait for Word to open,
        convert to PDF, kill WINWORD.EXE, then create_document() with the new PDF.
        """
        folder_path = rf"{os.environ.get('USERPROFILE')}\AppData\Local\Temp\Care\TMTand"

        try:
            self.open_tab("Stamkort")

            from_date = time.strftime("%d-%m-%Y")
            to_date = time.strftime(
                "%d-%m-%Y", time.localtime(time.time() + 50 * 365 * 86400)
            )

            from_date_field = self.wait_for_control(
                auto.PaneControl,
                {"AutomationId": "DateTimePickerFromDate"},
                search_depth=14,
            )
            to_date_field = self.wait_for_control(
                auto.PaneControl,
                {"AutomationId": "DateTimePickerToDate"},
                search_depth=14,
            )
            from_date_field.SendKeys(from_date)
            to_date_field.SendKeys(to_date)

            list_bookings = self.get_list_of_appointments()

            controls = list_bookings.get("controls") if list_bookings else None
            if not controls or len(controls) == 0:
                raise ValueError("No appointments found in the list.")
            first_booking = controls[0]
            first_booking.RightClick(simulateMove=False, waitTime=0)

            pop_up_right_click_menu = self.wait_for_control(
                auto.MenuControl, {"Name": "Kontekst"}, search_depth=2
            )
            pop_up_right_click_menu.MenuItemControl(
                Name="Print/Flet patienter"
            ).GetLegacyIAccessiblePattern().DoDefaultAction()

            form_print_merge = self.wait_for_control(
                auto.WindowControl,
                {"AutomationId": "FormQueryPrintOrMerge"},
                search_depth=3,
            )
            form_print_merge.RadioButtonControl(
                AutomationId="RadioButtonMerge"
            ).GetLegacyIAccessiblePattern().DoDefaultAction()
            form_print_merge.PaneControl(
                AutomationId="ButtonOK"
            ).GetLegacyIAccessiblePattern().DoDefaultAction()

            form_mail_merge = self.wait_for_control(
                auto.WindowControl, {"AutomationId": "FormMailMerge"}, search_depth=3
            )
            form_mail_merge.ComboBoxControl(AutomationId="ComboTemplet").GetPattern(
                auto.PatternId.ExpandCollapsePattern
            ).Expand()

            form_mail_merge_expanded = self.wait_for_control(
                auto.ListControl, {"ClassName": "ComboLBox"}, search_depth=3
            )

            selection_made = False
            for item in form_mail_merge_expanded.GetChildren():
                if item.Name == metadata["templateName"]:
                    print(f"Selecting '{metadata['templateName']}'")
                    item.Click(simulateMove=False, waitTime=0)
                    selection_made = True
                    break

            if not selection_made:
                raise ValueError(
                    f"Expected status '{metadata['templateName']}' not found in ComboBox list."
                )

            time.sleep(0.5)
            new_value = (
                form_mail_merge.ComboBoxControl(AutomationId="ComboTemplet")
                .GetPattern(auto.PatternId.ValuePattern)
                .Value
            )
            print(f"New selected status: '{new_value}'")
            if new_value != metadata["templateName"]:
                raise ValueError(
                    f"Failed to set the correct status. Expected '{metadata['templateName']}', but got '{new_value}'."
                )

            if os.path.exists(folder_path):
                shutil.rmtree(folder_path, ignore_errors=True)

            form_mail_merge.PaneControl(
                AutomationId="ButtonMerge"
            ).GetLegacyIAccessiblePattern().DoDefaultAction()

            word_window = self.wait_for_control(
                auto.WindowControl, {"ClassName": "OpusApp"}, search_depth=2, timeout=60
            )

            def convert_docx_to_pdf(
                source_file_path: str,
                destination_path: str,
                new_filename: str,
                temp_filename: str,
            ) -> str:
                """
                Converts a DOCX file to a PDF file.

                Args:
                    source_file_path (str): The path to the source DOCX file.
                    destination_file_path (str): The path to the destination PDF file.
                    new_filename (str): The new filename for the PDF file.
                """
                try:
                    source_file_path = os.path.join(folder_path, temp_filename)
                    destination_file_path = os.path.join(
                        destination_path, new_filename + ".pdf"
                    )
                    print(f"{source_file_path=} -> {destination_file_path=}")
                    convert(source_file_path, destination_file_path)
                    timeout = 30
                    start_time = time.time()
                    while not os.path.exists(destination_file_path):
                        if time.time() - start_time > timeout:
                            raise TimeoutError(
                                "Timeout: Failed to create PDF file from Word document."
                            )
                        time.sleep(1)
                    if not os.path.exists(destination_file_path):
                        raise FileNotFoundError(
                            "Failed to create PDF file from Word document."
                        )
                    else:
                        print(f"PDF file created successfully: {destination_file_path}")
                        return destination_file_path
                except Exception as e:
                    print(f"Error while creating PDF file from Word document: {e}")
                    raise

            path_to_converted_file = convert_docx_to_pdf(
                source_file_path=folder_path,
                destination_path=metadata["destinationPath"],
                new_filename=metadata["dischargeDocumentFilename"],
                temp_filename=word_window.Name.split(" - ")[0],
            )

            self.kill_process_by_name_safe("WINWORD.EXE")
            self.open_sub_tab("Dokumenter")
            self.create_document(document_full_path=path_to_converted_file)
        except Exception as e:
            print(f"Error while creating document from template: {e}")
            raise
        finally:
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path, ignore_errors=True)

    def send_discharge_document_digitalpost(self, metadata: dict) -> None:
        """
        Sends the discharge document via Digital Post to the patient.
        """
        try:
            self.open_tab("Stamkort")
            self.open_sub_tab("Dokumenter")

            document_store = self.wait_for_control(
                self.app_window.PaneControl,
                {"AutomationId": "TabPagePatientDocumentStore"},
                search_depth=7,
            )
            list_control = (
                document_store.PaneControl(
                    AutomationId="ControlPatientRecordDocumentStore1"
                )
                .PaneControl(AutomationId="ctrlDocumentStore")
                .ListControl(AutomationId="cleverListView1")
            )
            for item in list_control.GetChildren():
                print(f"Item: {item}, AutomationId: {item.AutomationId}")

            target_filename = metadata["documentTitle"]
            matching_row = None
            latest_created = None

            # 1) Filter rows by filename and track the “latest created” among them.
            for item in list_control.GetChildren():
                children = item.GetChildren()
                if len(children) < 1:
                    # no first child to compare => skip
                    continue

                # --- Check first child’s Name against target_filename ---
                try:
                    name0 = children[0].Name
                except Exception:
                    continue
                if name0 != target_filename:
                    continue

                # --- Parse the “created date” from the 4th child (index 3) ---
                created_obj = None
                if len(children) >= 4:
                    try:
                        date_text_created = children[3].Name.strip()
                        created_obj = datetime.strptime(
                            date_text_created, "%d-%m-%Y %H:%M"
                        )
                    except Exception as e:
                        print(f"Error parsing date: {e}")
                        created_obj = None

                if created_obj is None:
                    continue

                if latest_created is None or created_obj > latest_created:
                    latest_created = created_obj
                    matching_row = item

            if matching_row is None:
                raise ValueError(
                    f"Discharge document '{target_filename}' not found in the document list."
                )

            children = matching_row.GetChildren()
            child9_date = None
            if len(children) >= 9:
                try:
                    date_text_9 = children[8].Name.strip()
                    child9_date = datetime.strptime(date_text_9, "%m-%d-%Y %H:%M")
                except Exception:
                    child9_date = None

            if child9_date is None:
                matching_row.RightClick(simulateMove=False, waitTime=0)
            else:
                raise ValueError(
                    "Send to digitalpost date is not None, which is unexpected."
                )

            right_click_menu = self.wait_for_control(
                auto.MenuControl, {"Name": "Kontekst"}, search_depth=2
            )
            right_click_menu.MenuItemControl(
                Name="Send til digital postkasse"
            ).GetLegacyIAccessiblePattern().DoDefaultAction()

            digital_message_window = self.wait_for_control(
                auto.WindowControl,
                {"AutomationId": "ToolContextWrapperUI"},
                search_depth=2,
            )
            digital_message_window_group = (
                digital_message_window.PaneControl(AutomationId="viewPortPanel")
                .PaneControl(AutomationId="SendNemSMSMessageControl")
                .GroupControl(AutomationId="groupBoxMain")
            )
            digital_message_window_group.EditControl(
                AutomationId="textBoxSubject"
            ).GetPattern(auto.PatternId.ValuePattern).SetValue(
                metadata["digitalPostSubject"]
            )

            is_discharge_document_attachment = (
                digital_message_window_group.PaneControl(AutomationId="panel2")
                .ListControl(AutomationId="listBoxAttachment")
                .ListItemControl(Name=metadata["documentTitle"])
            )
            if is_discharge_document_attachment is None:
                raise ValueError(
                    f"Discharge document '{metadata['documentTitle']}' not found in the attachment list."
                )

            self.wait_for_control(
                auto.PaneControl, {"AutomationId": "&Send"}, search_depth=4, timeout=5
            ).Click(simulateMove=False, waitTime=0)

            try:
                self.wait_for_control(
                    auto.TextControl,
                    {"Name": "Kan ikke sende Digital Post uden modtager."},
                    search_depth=4,
                    timeout=5,
                )

                self.wait_for_control(
                    auto.ButtonControl, {"Name": "OK"}, search_depth=4
                ).Click(simulateMove=False, waitTime=0)

                self.wait_for_control(
                    auto.PaneControl, {"Name": "Annuller"}, search_depth=5
                ).Click(simulateMove=False, waitTime=0)
                raise ValueError("Cannot send Digital Post without a recipient.")
            except TimeoutError:
                pass
            except ValueError as e:
                print(f"Error while sending discharge document via DigitalPost: {e}")
                raise
        except Exception as e:
            print(f"Error while sending discharge document via DigitalPost: {e}")
            raise

    def create_digital_printet_journal(self) -> None:
        """
        Creates a digital printet journal for the patient
        and stores it in the documentsilo.
        """
        try:
            menu_fil_button = self.find_element_by_property(
                control=self.app_window,
                control_type=auto.ControlType.MenuItemControl,
                name="Fil",
            )
            menu_fil_button.Click(simulateMove=False, waitTime=0)
            print_journal_button = self.find_element_by_property(
                control=self.app_window,
                control_type=auto.ControlType.MenuItemControl,
                name="Udskriv journal",
            )
            print_journal_button.Click(simulateMove=False, waitTime=0)

            print_journal_window = self.wait_for_control(
                auto.WindowControl, {"AutomationId": "JournalPrintForm"}, search_depth=3
            )

            stamkort_toggle_state = (
                print_journal_window.CheckBoxControl(AutomationId="datacardCheckbox")
                .GetPattern(auto.PatternId.TogglePattern)
                .ToggleState
            )
            if stamkort_toggle_state == 1:
                print_journal_window.CheckBoxControl(
                    AutomationId="datacardCheckbox"
                ).GetPattern(auto.PatternId.TogglePattern).Toggle()

            print_journal_window.PaneControl(AutomationId="printButton").Click(
                simulateMove=False, waitTime=0
            )

            journal_pdf_window = self.wait_for_control(
                auto.WindowControl,
                {"ClassName": "AcrobatSDIWindow"},
                search_depth=2,
                timeout=60,
            )
            journal_pdf_window.Name.split(" - ")[0]
            journal_pdf_window.GetWindowPattern().Close()
        except Exception as e:
            print(f"Error while creating journal note: {e}")
            raise
