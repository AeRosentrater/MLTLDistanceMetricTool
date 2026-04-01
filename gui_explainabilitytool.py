#!/usr/bin/env python3
#
import os
import numpy as np
import sys

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QGridLayout, QHBoxLayout,
    QPushButton, QComboBox, QTextEdit, QTableWidget, QGroupBox,
    QTableWidgetItem, QHeaderView, QMessageBox, QSpinBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


'''
Ashley Behrendt
February 9, 2026

Timeline Explainability Tool

This module provides a PyQt5-based GUI for visualizing distance metric
data generated from R2U2 contract executions. The tool supports:

- Viewing cumuluative or per-execution results
- Filtering by contract or tasks
- Aggregating contracts under UUID groupings
- Heatmap visualization of distance metrics throughout an execution

The visualization uses Matplotlib embedded with a Qt interface.
'''

    
class ExplainabilityTool(QMainWindow):
    '''
    Main GUI window for the Timeline Explainability Tool.

    This class manages:
    - Loading and parsing contract and execution data
    - Aggregating distance metrics
    - Handling execution and task filtering
    - Rendering interactive heatmap visualizations

    The heatmap displays distance metric values (integers) over time
    for selected contracts or task groupings. 
    '''
    def __init__(self):
        super().__init__()
        current_directory = os.path.dirname(os.path.abspath(__file__))
        self.contracts_list = self.read_contracts(os.path.join(current_directory, "data/contracts.txt"))
        self.uuid_dict = self.read_uuid(os.path.join(current_directory, "data/contracts.txt"))

        self.data_by_exec = {}

        output_files = sorted(
            f for f in os.listdir(os.path.join(current_directory, "data")) if f.startswith("output_exec")
        )

        for i, file in enumerate(output_files):
            file_path = os.path.join(current_directory, "data", file)
            self.data_by_exec[i + 1] = self.read_dist_met(file_path, self.contracts_list)
            pass

        self.num_exec = len(output_files)

        if self.num_exec == 0:
            # No data files found
            self.dist_metric_data = {c: [] for c in self.contracts_list}
            pass
        else:
            # Start with cumulative data
            self.dist_metric_data = self.get_data_for_execution(0)  # 0 = cumulative
            pass
        self.build_main_widget()
        pass

    def build_main_widget(self):
        '''
        Construct the main GUI layout.

        Creates:
        - Title label
        - Execution selection dropdown box (combination box)
        - Task/contract filter dropdown box (combination box)
        - Heatmap display area

        Connects user interface signals to their corresponding handlers.
        '''
        self.setWindowTitle("Timeline Explainability Tool")
        self.resize(1200,800)

        label = QLabel("Distance Metric Visualization")
        label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(30)
        font.setBold(True)
        label.setFont(font)

        self.central_widget = QWidget()
        self.central_layout = QGridLayout(self.central_widget)
        self.central_layout.setAlignment(Qt.AlignCenter)
        self.central_layout.addWidget(label,0, 0,1,4)
        self.setCentralWidget(self.central_widget)

        if self.num_exec > 1:
            exec_str_list = ["CUMULATIVE EXECUTIONS"] + [f"EXECUTION {i+1}" for i in range(self.num_exec)]
            pass
        else:
            exec_str_list = [f"EXECUTION {i+1}" for i in range(self.num_exec)]
            pass

        self.exec_combobox = self.create_combobox(
            exec_str_list,
            self.central_layout,
            1,
            0,
            200
            )
        self.sort_combobox = self.create_combobox(
            ["ALL UUID"] + ["ALL CONTRACTS"] + [f"UUID: {uuid}" for uuid in self.uuid_dict.keys()],
            self.central_layout,
            2,
            0,
            300)

        # Add heatmap to window:
        self.heatmap_widget = QWidget()
        self.heatmap_layout = QVBoxLayout(self.heatmap_widget)
        self.central_layout.addWidget(self.heatmap_widget, 3, 0, 1, 4)

        # Based on the sort selection, we need to sort the page:
        self.exec_combobox.setCurrentText("CUMULATIVE EXECUTIONS")
        self.on_exec_changed(self.exec_combobox.currentText())

        self.sort_combobox.setCurrentText("ALL UUID")
        self.on_sort_changed(self.sort_combobox.currentText())

        self.sort_combobox.currentTextChanged.connect(lambda selection: self.on_sort_changed(selection))
        self.exec_combobox.currentTextChanged.connect(self.on_exec_changed)
        

        self.current_dist_metric_data = self.dist_metric_data        
        return
    
    # ----------------------------------------------------------------
    # READ OUTPUT FILES
    # ----------------------------------------------------------------
        
    def read_dist_met(self,filename,contracts):
        '''
        Parse a distance metric output file.

        Parameters:
        -----------
        filename : str
            Path to output file
        contracts : list[str]
            List of contract names used to initialize the data structure.

        Returns:
        ----------
        dict
            Dictionary mapping contract names to lists of (time, distance) tuples.
        '''
        data = {contract: [] for contract in contracts} # data will be based on the contracts
        with open(filename, "r")as infile:
            for line in infile:
                line = line.strip()
                # Ignore blank lines
                if "" == line:
                    continue


                # Split the line that has format: SPEC: time, bool
                # 1st step: [SPEC] [time, dist]
                contract_str, dat = line.split(":")
                # 2nd step: [time] [dist]
                time_str, dist_str = dat.split(",")

                if contract_str in data:
                    data[contract_str].append((time_str, dist_str))
                    pass
                else:
                    data[contract_str] = [(time_str, dist_str)]
                pass     
        return data

    def read_uuid(self,filename):
        '''
        Parse a contract file and extract UUID-to-contract mappings.

        Parameters:
        -----------
        filename : str
            Path to contract file

        Returns:
        ----------
        dict
            Dictionary mapping UUID strings to lists of associated contracts.
        '''
        # Sorts contracts by their UUID
        contracts= {}
        inside_spec = False
        with open(filename, "r") as infile:
            for line in infile:
                line = line.strip()

                if line.startswith(("FTSPEC","PTSPEC")):
                    inside_spec = True
                    continue # sKip this line
                if inside_spec:
                    if "" == line:
                        continue # blank lines
                    if ":" not in line:
                        continue
                    left,_ = line.split(":",1)
                    uuid, contract = left.split(None,1)
                    contracts.setdefault(uuid, []).append(contract)
                    pass
                pass
            pass
        return contracts

    def read_contracts(self,filename):
        '''
        Parse a contract file and extract contract names.

        Parameters:
        -----------
        filename : str
            Path to contract file

        Returns:
        ----------
        list[str]
            List of contract names
        '''
        # Sorts contracts by their UUID
        contracts= []
        inside_spec = False
        with open(filename, "r") as infile:
            for line in infile:
                line = line.strip()

                if line.startswith(("FTSPEC","PTSPEC")):
                    inside_spec = True
                    continue # skip this line
                if inside_spec:
                    if "" == line:
                        continue # blank lines
                    if ":" not in line:
                        continue
                    left,_ = line.split(":",1)
                    _, contract = left.split(None,1)
                    contracts.append(contract)
                    pass
                pass
            pass
        return contracts

    def get_data_for_execution(self,execution):
        '''
        Retrieve distance metric data for a specific execution.
        
        Parameters:
        -----------
        execution : int
            Execution number
              - 0 indicates cumulative data across all executions.
              - Positive integers correspond to individual executions
       
        Returns:
        ----------
        dict
            Dictionary mapping contract names to lists of (time, distance) tuples.
        '''
        if execution == 0:
            cumulative_data = {c: [] for c in self.contracts_list}
            for exec_data in self.data_by_exec.values():
                for c, events in exec_data.items():
                    cumulative_data[c] += events
                    pass
                pass
            return cumulative_data
        else:
            return self.data_by_exec.get(execution, {})
        pass

    def on_sort_changed(self,selection):
        '''
        Handle changes in UUID/contract filter selection.

        Updates the currently displayed dataset based on the selected filter:
        - ALL CONTRACTS
        - ALL UUID
        - Specific UUID
        - Individual contract

        Parameters
        ----------
        selection : str
        Selected filter value from the combobox.
        '''
        if selection == "ALL CONTRACTS":
            # all contracts will be the full list
            contracts = self.contracts_list
            pass
        elif selection == "ALL UUID":
            # all uuid will be full list of uuids
            contracts = list(self.uuid_dict.keys())
            pass
        elif selection.startswith("UUID:"):
            # If we are selecting an individual UUID, we need its contracts
            uuid = selection.split(":")[1].strip()
            contracts = self.uuid_dict.get(uuid,[])
            pass
        else:
            # We do not know what contracts will always start with so... else
            contracts = [selection]
            pass

        # Now, we need to pull out the UUID
        if selection == "ALL UUID":
            data_dict_filtered = {}
            for uuid, uuid_contracts in self.uuid_dict.items():
                combined_data = []
                for contract in uuid_contracts:
                    combined_data += self.dist_metric_data[contract]
                    pass
                data_dict_filtered[uuid] = combined_data
                pass
            pass
        else:
            data_dict_filtered = {c: self.dist_metric_data.get(c,[]) for c in contracts}
            pass
            
        self.current_dist_metric_data = data_dict_filtered

        self.update_heatmap(list(data_dict_filtered.keys()))
        
        return

    def on_exec_changed(self,text):
        '''
        Handle execution selection changes.

        Updates the underlying distance metric dataset to reflect either:
          - Cumulative execution data
          - A specific execution
        
        Parameters:
        -----------
        text : str
            Selected execution label from the dropdown box (combination box)
        '''
        if text == "CUMULATIVE EXECUTIONS":
            execution_num = 0
            pass
        else:
            execution_num = int(text.split()[-1])  # get iteration number
            pass
        # Update the main data_dict for this selection
        self.dist_metric_data = self.get_data_for_execution(execution_num)

        # Update current selection if any sort filter is applied
        current_selection = self.sort_combobox.currentText()
        self.on_sort_changed(current_selection)
        return

    def create_input_box(self, lab_row, lab_column, box_row, box_column, label_text, placeholder_text,layout, height, width):
        '''
        Create an input box to a desired layout.
        
        Parameters:
        -----------
        lab_row, lab_column : int
            Grid position for the label.
        box_row, box_column : int
            Grid position for the text box.
        label_text : str
            Label displayed above or beside the input box.
        placeholder_text : str
            Placeholder text displayed inside the input box.
        layout : QGridLayout
            Layout to which the widgets are added.
        height : int
            Fixed height of the input box.
        width : int
            Fixed width of the input box.
        
        Returns:
        ----------
        input_box
            The created text input widget
        '''
        
        input_label = QLabel(label_text)
        input_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        input_box = QTextEdit()
        font = QFont()
        font.setPointSize(16)
        
        input_box.setPlaceholderText(placeholder_text)
        input_box.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        input_box.setFixedWidth(width)
        input_box.setFixedHeight(height)
        input_box.setFont(font)
        input_label.setFont(font)
        layout.addWidget(input_label, lab_row, lab_column)
        layout.addWidget(input_box, box_row, box_column)
        return input_box

    def create_button(self, row, column, text=None, table=None, layout=None,image_path=None):
        '''
        Create button for a desired layout or table.
        
        Parameters:
        -----------
        row : int
            Row index for placement.
        column : int
            Column index for placement.
        text : str, optional
            Button text label.
        table : QTableWidget, optional
            Table to insert the button into.
        layout : QLayout, optional
            Layout to insert the button into.
        image_path : str, optional
            Path to an icon image for the button.
        
        Returns:
        ----------
        button
            The created button widget
        '''
        # https://doc.qt.io/archives/qtforpython-5/PySide2/QtGui/QIcon.html
        # https://www.pythonguis.com/faq/built-in-qicons-pyqt/
        
        # Default will be text, but if a path is given, we will use an image as the icon
        if image_path:
            button = QPushButton()
            button.setIcon(QIcon(image_path))
            pass
        if text:
            button = QPushButton(text)
            pass

        if table:
            table.setCellWidget(row, column, button)
            pass
        else:
            layout.addWidget(button,row, column,alignment=Qt.AlignRight)
        return button
            
    def create_combobox(self, items, layout, row, column,width):
        '''
        Create a combination box for a desired layout.
        
        Parameters:
        -----------
        items : list[str]
            Items to populate the dropdown.
        layout : QLayout
            Layout to which the combobox is added.
        row : int
            Row position in the layout.
        column : int
            Column position in the layout.
        width : int
            Fixed width of the combobox.
        
        Returns:
        ----------
        combo_box
            The created combination box widget
        '''
        combo_box = QComboBox()
        combo_box.addItems(items)
        combo_box.setEditable(True)
        combo_box.lineEdit().setAlignment(Qt.AlignLeft)
        combo_box.setEditable(False)
        combo_box.setFixedWidth(width)

        layout.addWidget(combo_box, row, column)
        
        return combo_box
    
    # ----------------------------------------------------------------
    # HEATMAP FEATURES
    # ----------------------------------------------------------------
    def add_heatmap_to_window(self, layout, value_labels=True, selections=None, all_contracts=None, row=None):
        '''
        Add a heatmap to the specified layout. 
        
        Parameters:
        -----------
        layout : QLayout
            Layout where the heatmap canvas will be added.
        value_labels : bool, optional
            Whether to display numeric values in each cell.
        selections : list[str], optional
            Selected contracts or UUIDs to visualize.
        all_contracts : list[str], optional
            Unused parameter reserved for future expansion.
        row : int, optional
            Layout row position for insertion.
        '''
        if selections is None:
            selections = list(self.dist_metric_data.keys())
            pass
        fig = self.create_heatmap(selections,value_labels)
        canvas = FigureCanvas(fig)
        
        if row is None:
            row = layout.rowCount()
            pass
        layout.addWidget(canvas,row,1)

        return
    
    def update_heatmap(self, selections):
        '''
        Refresh the heatmap display using updated selection data.

        Clears the existing heatmap canvas and renders a new
        visualization based on current filtered data.

        Parameters:
        -----------
        selections : list[str]
            Contracts or UUIDs to visualize.
        '''
        # Clear old heatmap
        while self.heatmap_layout.count():
            item = self.heatmap_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                pass
            pass
        

        fig = self.create_heatmap(
            selections=selections,
            value_labels=True,
            data_dict=self.current_dist_metric_data
        )

        canvas = FigureCanvas(fig)
        self.heatmap_layout.addWidget(canvas)
        return 

    def create_heatmap(self, selections, value_labels=True,data_dict=None):
        '''
        Generate a Matplotlib heatmap figure for selected contracts or UUIDs.

        The heatmap displays distance metric values over time.
        Values are averaged when multiple events occur at the same timestamp.

        Parameters:
        -----------
        selections : list[str]
            Contracts or UUIDs to visualize.
        value_labels : bool, optional
            Whether to overlay numeric values on the heatmap.
        data_dict : dict, optional
            Pre-filtered distance metric dataset. If None, the
            current execution dataset is used.

        Returns:
        -----------
        matplotlib.figure.Figure (fig)
            The generated heatmap figure.
        '''
        # Need to make a heatmap where each data point is either pass or fail
        # i.e. pass = 100 percent, fail = 0%
        # failed_times is failed events
        # passed_times is passed events
        # -------------------------------
        # |        |   TIME 
        # -------------------------------
        # Contract | 0 | 1 | 2 | 3 | 4 | ... 
        # -------------------------------
        # | SPEC0  | 1 | 0 | 1 | 0 | 0 | ...
        # | SPEC1  | 0 | 1 | 1 | 0 | 1 | ...
        # | SPEC2  | 1 | 0 | 1 | 0 | 0 | ...
        # We want to have a "stream viewer" similarly to the waveform viewer
        if data_dict is None:
            data_dict = self.dist_metric_data
            pass
        if len(selections) == len(self.dist_metric_data):
            title = "All Selections Status"
            pass
        else:
            title = "Selected Status"
            pass
        # Find The number of columns based on max time data point
        max_time = 0
        for item in selections:
            if item in self.uuid_dict:
                for contract in self.uuid_dict[item]:
                    events = self.dist_metric_data.get(contract, [])
                    if events:
                        max_time = max(max_time, max(int(t) for t, _ in events))
                        pass
                    pass
                pass
            else: 
                events = self.dist_metric_data.get(item, [])
                if events:
                    max_time = max(max_time, max(int(t) for t, _ in events))
                    pass
                pass
            pass
        
        num_times = max_time + 1 # taking time to start at 0


        #contracts = list(self.data_dict.keys())
        


        data_array = np.full((len(selections), num_times), np.nan)

        
        # Fill the array with pass/fail values
        for row_idx, item in enumerate(selections):
            # Case 1: data_dict already has the item (UUID pre-aggregated or normal contract)
            if item in data_dict:
                row_dict = {}
                for t, val in data_dict[item]:
                    col_idx = int(t)
                    if col_idx not in row_dict:
                        row_dict[col_idx] = []
                        pass
                    row_dict[col_idx].append(float(val))
                    pass
                row_array = np.full(num_times, np.nan)
                for col_idx, vals in row_dict.items():
                    row_array[col_idx] = np.mean(vals)
                    pass
                data_array[row_idx, :] = row_array
                continue

            # Case 2: item is a UUID, needs to combine underlying contracts
            elif item in self.uuid_dict:
                contracts_in_uuid = self.uuid_dict[item]
                temp_array = np.full((len(contracts_in_uuid), num_times), np.nan)
                for c_idx, contract in enumerate(contracts_in_uuid):
                    contract_events = self.dist_metric_data.get(contract, [])
                    for t, val in contract_events:
                        col_idx = int(t)
                        temp_array[c_idx, col_idx] = int(val)
                        pass
                    pass
                
                if np.any(~np.isnan(temp_array)):
                    data_array[row_idx, :] = np.nanmean(temp_array, axis=0)
                    pass
                else:
                    print(f"Warning: UUID '{item}' has no valid data.")
                    pass
                pass
            else:
                print(f"Warning: '{item}' not found in data_dict or uuid_dict")
                continue
            pass
           

        base_height = 1.2
        fig_height = max(4, base_height * len(selections))
        fig,ax = plt.subplots(figsize=(8, fig_height))
        cmap = plt.get_cmap('RdYlGn_r')
        cmap.set_bad(color='lightgray')
        im = ax.imshow(data_array,cmap)

        ax.set_title(title)
        ax.set_xlabel("Time")
        ax.set_ylabel("Selection")

        # tick marks for y axis contracts and x axis events
        ax.set_yticks(np.arange(len(selections)))
        ax.set_yticklabels(selections)
        ax.set_xticks(np.arange(num_times))
        ax.set_xticklabels(np.arange(num_times))

        # Add grid lines
        ax.set_xticks(np.arange(-0.5, num_times, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, len(selections),1), minor=True)
        ax.grid(which='minor', color='w', linestyle='-', linewidth=1)
        ax.tick_params(which='minor', length=0) # hide tick marks for grid
                      
        cbar = fig.colorbar(im, ax=ax)
        #cbar.set_ticks([0, 1])
        #cbar.set_ticklabels(["Fail", "Pass"])
        cbar.set_label("Distance Metric Value")
    
        # Optionality to add percentages or values onto the heatmap
        if value_labels:
            if np.all(np.isnan(data_array)):
                vmin = 0
                vmax = 1
                pass
            else:
                vmin = np.nanmin(data_array)
                vmax = np.nanmax(data_array)
                pass
            for i in range(data_array.shape[0]):
                for j in range(data_array.shape[1]):
                    value = data_array[i,j]
                    if not np.isnan(value): # skip nan vals
                        if vmax != vmin:
                            threshold = (vmax + vmin)/2
                            pass
                        else:
                            threshold = vmax/2
                            pass
                        text_color = "white" if value < threshold else "black"
                        ax.text(j,i,
                                f"{value:.2f}",
                                ha = "center",
                                va = "center",
                                color = text_color,
                                fontsize=8)
                        pass
                    pass
                pass
            pass
        
        
        return fig



    

def main():
    app = QApplication(sys.argv)
    # Trying to make this look more modern:
    app.setStyle("Fusion")
    '''
    app.setStyleSheet("""
    /* Base */
    QWidget {
    background-color: #121212;
    color: #e0e0e0;
    font-family: "Helvetica Neue";
    font-size: 14px;
    }
    
    /* Buttons */
    QPushButton {
    background-color: #1f6feb;
    border: none;
    border-radius: 6px;
    padding: 8px 14px;
    }
    
    QPushButton:hover {
    background-color: #388bfd;
    }
    
    QPushButton:pressed {
    background-color: #1a5fd0;
    }
    
    /* Inputs */
    QLineEdit, QTextEdit, QComboBox {
    background-color: #1e1e1e;
    border: 1px solid #333;
    border-radius: 6px;
    padding: 6px;
    }
    
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #1f6feb;
    }
    
    /* Lists & tables */
    QListView, QTableView {
    background-color: #1e1e1e;
    border: none;
    }
    
    QHeaderView::section {
    background-color: #1a1a1a;
    padding: 6px;
    border: none;
    }
    
    /* Scrollbars */
    QScrollBar:vertical {
    background: transparent;
    width: 10px;
    }
    
    QScrollBar::handle:vertical {
    background: #333;
    border-radius: 5px;
    }
    
    QScrollBar::handle:vertical:hover {
    background: #444;
    }
    """)
    '''
    window = ExplainabilityTool()
    window.show() # windows are automatically hidden, so this is required

    app.exec() # starts the event loop
    pass

if __name__ == "__main__":
    main()
