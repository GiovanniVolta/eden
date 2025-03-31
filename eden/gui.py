"""Contains the EDen User interface"""

import sys
import os
import logging as _lg
import numpy as _np
from datetime import datetime as _dt
import time
from collections import OrderedDict
from PyQt5 import QtCore as _qc
from PyQt5 import QtGui as _qg
from PyQt5 import QtWidgets as _qw
from PyQt5 import QtSvg as _qs
from functools import partial

from eden import threads as _thr 
from eden import Class_PSC as _psc

# create module logger
_gui_log = _lg.getLogger("eden.gui")
_gui_log.setLevel(_lg.DEBUG)
_lg.debug("Loading eden.gui")


class MainWindow(_qw.QMainWindow):

    log = _lg.getLogger("eden.gui.MainWindow")

    def __init__(self):

        super().__init__()
        #_qg.QWidget.__init__(self)
        MainWindow.log.debug("Created MainWindow")

        self.psc_connected = False
        self.psc = None
        self.sample_area = None
        self.sample_name = ""
        self.coating_step = ""
        self.sample_defined = False
        self.measurement_running = False
        self.data = _np.array((0))
        #self.data = _np.array(((10,11,12), (20,21,22)))
        self.unsaved_changes = False

        self.timer = _qc.QTimer(self)
        self.timer.timeout.connect(self.updateUI)
        self.timer.start(1000)

        self.startUI()
        self.updateUI()
                
    def startUI(self):
		
        self._init_geom()
        self._init_menu()
        self._init_status_bar()
        self._init_subwindows()
        
                
    def updateUI(self):

        self.update_overview()
       

    def _init_geom(self):
        """Initializes the main window's geometry"""
        MainWindow.log.debug("Called MainWindow._init_geom")
        # set basic attributes
        self.setAttribute(_qc.Qt.WA_DeleteOnClose)
        self.setWindowTitle("(E)lectro (De)position I(n)terphase (alpha)")
        self.resize(800, 600)

        # center window
        win_geom = self.frameGeometry()
        desk_center = _qw.QDesktopWidget().availableGeometry().center()
        win_geom.moveCenter(desk_center)
        self.move(win_geom.topLeft())


    def _init_menu(self):
        """Initializes the menu"""
        # define file menu and entries

        MainWindow.log.debug("Called MainWindow._init_menu")
        self.file_menu = _qw.QMenu("&File", self)
        self.new_measurement_action = self.file_menu.addAction("&New", self.clear_data,
		                 _qc.Qt.CTRL + _qc.Qt.Key_N)
        self.save_measurement_action = self.file_menu.addAction("&Save", self.save_data,
		                 _qc.Qt.CTRL + _qc.Qt.Key_S)
        self.load_measurement_action = self.file_menu.addAction("&Load", self.load_data,
		                 _qc.Qt.CTRL + _qc.Qt.Key_O)
        self.file_menu.addAction("&Quit", self.file_quit,
		                 _qc.Qt.CTRL + _qc.Qt.Key_Q)

        self.menuBar().addMenu(self.file_menu)

        self.measure_menu = _qw.QMenu("&Measurement", self)
        self.start_icon = _qg.QIcon("eden/icons/start_button.png")
        self.start_measurement_action = self.measure_menu.addAction(self.start_icon, "&Run", self.start_measurement,
		                 _qc.Qt.CTRL + _qc.Qt.Key_R)
        self.stop_icon = _qg.QIcon("eden/icons/stop_button.png")
        self.stop_measurement_action = self.measure_menu.addAction(self.stop_icon, "&Stop", self.stop_measurement,
		                 _qc.Qt.CTRL + _qc.Qt.Key_X)
        self.stop_measurement_action.setDisabled(True)

        self.menuBar().addMenu(self.file_menu)
        self.menuBar().addMenu(self.measure_menu)


    def _init_status_bar(self):
        """Initializes the status bar"""
        MainWindow.log.debug("Called MainWindow._init_status_bar")

        self.statusBar().showMessage('Program started')

    def _init_subwindows(self):
        """Create the tabs"""
        MainWindow.log.debug("Called MainWindow._init_subwindows")
        self.main_widget = _qw.QTabWidget(self)
        self.setCentralWidget(self.main_widget)
        self.overviewTab = _qw.QWidget(self.main_widget)
        self.settingsTab = _qw.QWidget(self.main_widget)

        self.main_widget.addTab(self.overviewTab, "Overview")
        self.main_widget.addTab(self.settingsTab, "Settings")
		
        self._init_settings()
        self._init_overview()


    def _init_overview(self):
        MainWindow.log.debug("Called MainWindow._init_overview")
        
        # start the plotter thread
        self.plotter_thread = _thr.Plotter(self)
        self.plotter_thread.start()

        # Add the plot to the widget
        grid_layout_plot = _qw.QGridLayout()
        plot_group_box = _qw.QGroupBox("")
        grid_layout_plot.addWidget(self.plotter_thread.canvas, 1, 1)
        grid_layout_plot.addWidget(self.plotter_thread.nav_toolbar, 2, 1)
        plot_group_box.setLayout(grid_layout_plot)

        # Add LCD displays for voltage and current
        grid_layout_displays = _qw.QGridLayout()
        displays_group_box = _qw.QGroupBox("")
        # Power supply voltage
        ps_voltage_label = _qw.QLabel("U(PS) [V]")
        self.ps_voltage_lcd = _qw.QLCDNumber()
        self.ps_voltage_lcd.setNumDigits(5)
        self.ps_voltage_lcd.setSegmentStyle(_qw.QLCDNumber.Flat)
        self.ps_voltage_lcd.setAutoFillBackground(True)
        # Power supply current
        ps_current_label = _qw.QLabel("I(PS) [A]")
        self.ps_current_lcd = _qw.QLCDNumber()
        self.ps_current_lcd.setNumDigits(5)
        self.ps_current_lcd.setSegmentStyle(_qw.QLCDNumber.Flat)
        self.ps_current_lcd.setAutoFillBackground(True)
        # Aux channel voltage
        aux_voltage_label = _qw.QLabel("U(AUX) [V]")
        self.aux_voltage_lcd = _qw.QLCDNumber()
        self.aux_voltage_lcd.setNumDigits(5)
        self.aux_voltage_lcd.setSegmentStyle(_qw.QLCDNumber.Flat)
        self.aux_voltage_lcd.setAutoFillBackground(True)  
        # add them to the layout
        grid_layout_displays.addWidget(ps_voltage_label, 1, 1)
        grid_layout_displays.addWidget(self.ps_voltage_lcd, 1, 2)
        grid_layout_displays.addWidget(ps_current_label, 2, 1)
        grid_layout_displays.addWidget(self.ps_current_lcd, 2, 2)
        grid_layout_displays.addWidget(aux_voltage_label, 3, 1)
        grid_layout_displays.addWidget(self.aux_voltage_lcd, 3, 2)
        displays_group_box.setLayout(grid_layout_displays)
        
        # Add fields for deposited mass and thickness
        grid_layout_mass_display = _qw.QGridLayout()
        mass_display_group_box = _qw.QGroupBox("Coating progress:")
        deposited_mass_label = _qw.QLabel("Mass (mg)")
        self.deposited_mass_line = _qw.QLineEdit(self.overviewTab)
        self.deposited_mass_line.setDisabled(True)
        deposited_thickness_label = _qw.QLabel("Layer (nm)")
        self.deposited_thickness_line = _qw.QLineEdit(self.overviewTab)
        self.deposited_thickness_line.setDisabled(True)
        # add them to the layout
        grid_layout_mass_display.addWidget(deposited_mass_label,1,1)
        grid_layout_mass_display.addWidget(self.deposited_mass_line,1,2)
        grid_layout_mass_display.addWidget(deposited_thickness_label,2,1)
        grid_layout_mass_display.addWidget(self.deposited_thickness_line,2,2)
        mass_display_group_box.setLayout(grid_layout_mass_display)        
        
        # Add fields for voltage and current control
        grid_layout_set_fields = _qw.QGridLayout()
        set_fields_group_box = _qw.QGroupBox("Control:")
        set_voltage_label = _qw.QLabel("Set Voltage (V)")
        self.set_voltage_line = _qw.QLineEdit(self.overviewTab)
        set_current_label = _qw.QLabel("Set Current (A)")
        self.set_current_line = _qw.QLineEdit(self.overviewTab)
        self.set_submit_button = _qw.QPushButton("&Set values")
        self.set_submit_button.clicked.connect(self.set_values_to_psc)
        # add them to the layout
        grid_layout_set_fields.addWidget(set_voltage_label,1,1)
        grid_layout_set_fields.addWidget(self.set_voltage_line,1,2)
        grid_layout_set_fields.addWidget(set_current_label,2,1)
        grid_layout_set_fields.addWidget(self.set_current_line,2,2)
        grid_layout_set_fields.addWidget(self.set_submit_button,3,1,1,2)
        set_fields_group_box.setLayout(grid_layout_set_fields)
        
        grid_layout = _qw.QGridLayout()
        grid_layout.addWidget(plot_group_box, 1, 1,3,1)
        grid_layout.addWidget(displays_group_box, 1, 2)
        grid_layout.addWidget(mass_display_group_box, 2,2)
        grid_layout.addWidget(set_fields_group_box, 3, 2)
        self.overviewTab.setLayout(grid_layout)
        self.update_overview()
       

    def update_overview(self):
        #MainWindow.log.debug("Called MainWindow.update_overview")
        if self.psc_connected:
        
            self.ps_voltage_lcd.display(self.psc.mea_vol)
            self.ps_current_lcd.display(self.psc.mea_cu)
            # if aux voltage readout
            # updat the lcd for it!
            
            # if we have a reader thread that is recording, take its data
            if self.psc.is_connected:
                if self.psc.reader_thread.is_recording:
                    if len(self.psc.reader_thread.reader_data):
                        self.data = self.psc.reader_thread.reader_data
                        if self.plotter_thread.mass and self.plotter_thread.thickness:
                            self.deposited_mass_line.setText(str(round(self.plotter_thread.mass*1E3, 3)))
                            self.deposited_thickness_line.setText(str(round(self.plotter_thread.thickness*1E-2*1E9, 3)))
                        
                        
        return

    def _init_settings(self):
        MainWindow.log.debug("Called _init_settings")
        frame = _qw.QFrame()
        frame.setFrameShape(_qw.QFrame.StyledPanel)
        vbox_layout = _qw.QVBoxLayout()
        # set main layout
        placeholder = _qw.QLabel(self.settingsTab)
        
        ps_group_box = _qw.QGroupBox("Power supply settings:")
        grid_ps = _qw.QGridLayout()
        # Setting widgets for the PSC and power supply
        psc_com_label = _qw.QLabel("COM Port:")
        self.psc_com_line_edit = _qw.QLineEdit(self.settingsTab)
        psc_channel_label = _qw.QLabel("PSC Channel:")
        self.psc_channel_line_edit = _qw.QLineEdit(self.settingsTab)
        ps_umax_label = _qw.QLabel("U(max):")
        self.ps_umax_line_edit = _qw.QLineEdit(self.settingsTab)
        ps_imax_label = _qw.QLabel("I(max):")
        self.ps_imax_line_edit = _qw.QLineEdit(self.settingsTab)        
        self.connect_psc_button = _qw.QPushButton("&Connect")
        self.connect_psc_button.clicked.connect(self.connect_psc)
        self.disconnect_psc_button = _qw.QPushButton("&Disconnect")
        self.disconnect_psc_button.setEnabled(False)               
        self.disconnect_psc_button.clicked.connect(self.disconnect_psc)

        # Settings for the sample itself
        sample_group_box = _qw.QGroupBox("Sample settings:")
        grid_sample = _qw.QGridLayout()
        sample_name_label = _qw.QLabel("Sample Name:")
        self.sample_name_line_edit = _qw.QLineEdit(self.settingsTab)
        coating_step_label = _qw.QLabel("Coating Step:")
        self.coating_step_line_edit = _qw.QLineEdit(self.settingsTab)
        sample_surface_label = _qw.QLabel("Surface (cm²):")
        self.sample_surface_line_edit = _qw.QLineEdit(self.settingsTab)
        self.submit_sample_button = _qw.QPushButton("&Submit")
        self.submit_sample_button.clicked.connect(self.submit_sample_info)
        

        # layout definition for all widgets defined above
        grid_ps.addWidget(psc_com_label, 1, 1)
        grid_ps.addWidget(self.psc_com_line_edit, 1, 2)
        grid_ps.addWidget(psc_channel_label, 1, 3)
        grid_ps.addWidget(self.psc_channel_line_edit, 1, 4)
        grid_ps.addWidget(ps_umax_label, 2, 1)
        grid_ps.addWidget(self.ps_umax_line_edit, 2, 2)
        grid_ps.addWidget(ps_imax_label, 2, 3)
        grid_ps.addWidget(self.ps_imax_line_edit, 2, 4)        
        grid_ps.addWidget(self.connect_psc_button, 3,1,1,2)
        grid_ps.addWidget(self.disconnect_psc_button, 3,3,1,2)
        ps_group_box.setLayout(grid_ps)
        
        grid_sample.addWidget(sample_name_label, 1,1)
        grid_sample.addWidget(self.sample_name_line_edit, 1,2,1,3)
        grid_sample.addWidget(coating_step_label, 2,1)
        grid_sample.addWidget(self.coating_step_line_edit, 2,2)
        grid_sample.addWidget(sample_surface_label, 2,3)
        grid_sample.addWidget(self.sample_surface_line_edit, 2,4)
        grid_sample.addWidget(self.submit_sample_button, 3,1,1,4)
        
        sample_group_box.setLayout(grid_sample)
        
        vbox_layout.addWidget(ps_group_box)
        vbox_layout.addWidget(sample_group_box)
        self.settingsTab.setLayout(vbox_layout)
        # set defaults
        self.set_eden_defaults()

    def set_eden_defaults(self):

        self.psc_com_line_edit.setText("COM1")
        self.psc_channel_line_edit.setText("1")
        self.ps_umax_line_edit.setText("15")
        self.ps_imax_line_edit.setText("40")
        return

    def connect_psc(self):
        self.statusBar().showMessage('connecting PSC')
        try:
            self.psc = _psc.PSC(self.psc_com_line_edit.text(), int(self.psc_channel_line_edit.text()))
            self.psc.establish_connection()
            self.psc_connected = self.psc.is_connected
            self.psc.activate_chan()
            self.psc.set_max_vol(int(self.ps_umax_line_edit.text()))
            self.psc.set_max_cu(int(self.ps_imax_line_edit.text()))           
        
        except (ValueError, TypeError):
            self.err_msg_sample_values = _qw.QMessageBox.warning(self, "Values",
            "The board channel needs to be an integer!")
            return
            
        self.psc_com_line_edit.setDisabled(True)
        self.psc_channel_line_edit.setDisabled(True)
        self.ps_umax_line_edit.setDisabled(True)
        self.ps_imax_line_edit.setDisabled(True)
        self.connect_psc_button.setEnabled(False)
        self.disconnect_psc_button.setEnabled(True)
        self.start_reader_thread()    

        return

    def disconnect_psc(self):
        self.statusBar().showMessage('disconnecting PSC')
        
        if self.psc.reader_thread.is_recording:
            self.err_msg_sample_values = _qw.QMessageBox.warning(self, "ERROR",
            "Running measurement. Board can not be disconnected!")
            return
      
        # stop the reader thread
        self.psc.reader_thread.stop_thread = True
        while self.psc.board_busy:
            time.sleep(0.1)
        
        self.psc.close_connection()
        self.psc_connected = False    
        self.psc = None
        
        self.psc_com_line_edit.setDisabled(False)
        self.psc_channel_line_edit.setDisabled(False)
        self.ps_umax_line_edit.setDisabled(False)
        self.ps_imax_line_edit.setDisabled(False)
        self.connect_psc_button.setEnabled(True)
        self.disconnect_psc_button.setEnabled(False)         
        
        return

    def submit_sample_info(self):
        # store the inputs from the text fields into the variable names
        try:
            self.sample_area = _np.float(self.sample_surface_line_edit.text().strip())
            self.sample_name = self.sample_name_line_edit.text().strip()
            self.coating_step = self.coating_step_line_edit.text().strip()
            self.sample_defined = True
            
        except (ValueError, TypeError):
            self.err_msg_sample_values = _qw.QMessageBox.warning(self, "Values",
            "Invalid input for the Sample surface!")
            
    def start_measurement(self):
        self.statusBar().showMessage('starting measurement')
        # check that the PSC is connected and the sample is defined
        if self.psc_connected and self.sample_defined:
            # ask for clearing  previous data
            self.clear_data()
            # disable all the sample input fields
            self.sample_name_line_edit.setDisabled(True)
            self.coating_step_line_edit.setDisabled(True)
            self.sample_surface_line_edit.setDisabled(True)
            # disable the start measurement button, enable the stop button
            self.start_measurement_action.setDisabled(True)
            self.stop_measurement_action.setDisabled(False)
            # disable the data actions: new, save and load 
            self.new_measurement_action.setDisabled(True)
            self.load_measurement_action.setDisabled(True)
            self.save_measurement_action.setDisabled(True)
            # start the measurement!
            self.measurement_running = True
            self.psc.reader_thread.is_recording = True
            # we then also have new data, i.e. unsaved changes!
            self.unsaved_changes = True
        else:
            self.err_msg_sample_values = _qw.QMessageBox.warning(self, "Error",
            "PSC board is not connected and/or sample surface is not defined")
        return
        
    def stop_measurement(self):
        self.statusBar().showMessage('stopping measurement')
        # enable all the sample input fields
        self.sample_name_line_edit.setDisabled(False)
        self.coating_step_line_edit.setDisabled(False)
        self.sample_surface_line_edit.setDisabled(False)
        # enable the start measurement button, disable the stop button
        self.start_measurement_action.setDisabled(False)
        self.stop_measurement_action.setDisabled(True)
        # enable the file actions again
        self.new_measurement_action.setDisabled(False)
        self.load_measurement_action.setDisabled(False)
        self.save_measurement_action.setDisabled(False)        
        # stop the measurement!
        self.psc.reader_thread.is_recording = False
        self.measurement_running = False
        return
        
    def start_reader_thread(self):
        self.statusBar().showMessage('starting module reader thread')
        
        if not self.psc.reader_thread:
            module_thread = _thr.PscReader(self.psc)
            self.psc.set_readerthread(module_thread)
            module_thread.start()
            MainWindow.log.debug("reader thread started")
            self.statusBar().showMessage("reader thread started") 
        
        return

    def stop_reader_thread(self, module):
        if not module.is_connected:
            return False
        module.stop_running_thread()      

        while module.board_occupied:
            MainWindow.log.debug("Waiting for thread "+module.name+" to stop")
            self.statusBar().showMessage("Waiting for thread "+module.name+" to stop")
            time.sleep(0.2)
        MainWindow.log.debug("thread "+module.name+" stopped")
        self.statusBar().showMessage("thread "+module.name+" stopped")
        return True

    def set_values_to_psc(self):
            
        try:
            voltage = float(self.set_voltage_line.text())
            current = float(self.set_current_line.text())
            
        except (ValueError, TypeError):
            self.err_msg_no_data = _qw.QMessageBox.warning(self, "Error",
            "Invalid values entered!")
            return
        
        if not self.psc_connected:
            self.err_msg_no_data = _qw.QMessageBox.warning(self, "Error",
            "Connect the PSC first!")
            return
        
        if self.psc.board_busy:
            # halt reader thread
            self.psc.reader_thread.halt_thread = True
            while self.psc.board_busy:
                time.sleep(0.1)
            self.psc.set_set_vol(voltage)
            self.psc.set_set_cu(current)
            self.psc.reader_thread.halt_thread = False
        return


    def clear_data(self):
        if self.data.any() or self.unsaved_changes:
            reply = _qw.QMessageBox.question(self, 'Confirm',
	            'Do you want to save the data?', _qw.QMessageBox.Yes |
	            _qw.QMessageBox.No | _qw.QMessageBox.Cancel, 				
	            _qw.QMessageBox.Cancel)
            if reply == _qw.QMessageBox.Yes:
                self.save_data()
            elif reply == _qw.QMessageBox.No:
                self.data = _np.array((0))
                if self.psc.is_connected:
                    self.psc.reader_thread.reader_data = []
                self.unsaved_changes = False
            else:
                return
        return

    def save_data(self):
        # is there some data?
        if not self.data.any():
            self.err_msg_no_data = _qw.QMessageBox.warning(self, "Error",
            "There is no data to be saved!")
            return
        # Save the acquired data to a file
        default_filename = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
        file_header = "UNIX time, Current (A), PS Voltage (V), REF Voltage (V)\n"
        if self.sample_defined:
            file_header += "SAMPLE_SURFACE = "+str(self.sample_area)+"\n"
        if self.sample_name:
            default_filename += "_"+self.sample_name
            file_header += "SAMPLE_NAME = "+self.sample_name+"\n"
        if self.coating_step:
            default_filename += "_"+self.coating_step
            file_header += "COATING_STEP = "+self.coating_step
        default_filename += ".dat"
        dialog = _qw.QFileDialog()
        dialog.setFileMode(_qw.QFileDialog.AnyFile)
        dialog.setDirectory(os.path.join("eden","data"))
        dialog.selectFile(default_filename)
        dialog.setAcceptMode(_qw.QFileDialog.AcceptSave)
        filename = ""
        if dialog.exec_():
            filename = dialog.selectedFiles()[0]
            _np.savetxt(filename, self.data, header=file_header, delimiter='\t')

        self.unsaved_changes = False
        return
        
    def load_data(self):
        # check if there is data already
        if self.data.any() and self.unsaved_changes:
            reply = _qw.QMessageBox.question(self, 'Confirm',
	            'Do you want to save the data first?', _qw.QMessageBox.Yes |
	            _qw.QMessageBox.No | _qw.QMessageBox.Cancel, 				
	            _qw.QMessageBox.Cancel)
            if reply == _qw.QMessageBox.Yes:
                self.save_data()
            elif reply == _qw.QMessageBox.No:
                self.data = None
                self.unsaved_changes = False
            else:
                return
        dialog = _qw.QFileDialog()
        dialog.setFileMode(_qw.QFileDialog.ExistingFile)
        dialog.setDirectory(os.path.join("eden","data"))
        filename = ""
        if dialog.exec_():
            filename = dialog.selectedFiles()[0]
            self.data = _np.loadtxt(filename, delimiter='\t', skiprows=3)
            # try to get the sample name, coating step and sample surface from file header
            with open(filename, "r") as f_in:
                this_line = f_in.readline()
                while this_line:
                    if not this_line[0] is "#":
                        break
                    else:
                        res1 = this_line.split("# SAMPLE_SURFACE = ")
                        res2 = this_line.split("# SAMPLE_NAME = ")
                        res3 = this_line.split("# COATING_STEP = ")
                        if len(res1) == 2:
                            self.sample_area = float(res1[1].strip())
                            self.sample_surface_line_edit.setText(str(self.sample_area))
                        if len(res2) == 2:
                            self.sample_name = res2[1].strip()
                            self.sample_name_line_edit.setText(self.sample_name)
                        if len(res3) == 2:
                            self.coating_step = res3[1].strip()
                            self.coating_step_line_edit.setText(self.coating_step)
                    this_line = f_in.readline()
        return
        
    def file_quit(self):
        """Closes the application"""
        MainWindow.log.debug("Called MainWindow.file_quit")
        self.statusBar().showMessage("Quitting application")

        reply = _qw.QMessageBox.question(self, 'Confirm',
	        'Are you sure to quit?', _qw.QMessageBox.Yes |
	        _qw.QMessageBox.No | _qw.QMessageBox.Cancel, 				
	        _qw.QMessageBox.Cancel)
        if reply == _qw.QMessageBox.Yes:
            # check if there is unsaved data
            if self.data.any() and self.unsaved_changes:
                reply = _qw.QMessageBox.question(self, 'Confirm',
	                'Do you want to save the data first?', _qw.QMessageBox.Yes |
	                _qw.QMessageBox.No | _qw.QMessageBox.Cancel, 				
	                _qw.QMessageBox.Cancel)
                if reply == _qw.QMessageBox.Yes:
                    self.save_data()
            self.close()
        else:
            return 

