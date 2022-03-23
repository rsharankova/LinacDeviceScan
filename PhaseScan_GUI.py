from PyQt6.uic import loadUiType, loadUi
from PyQt6.QtWidgets import QFileDialog, QWidget, QCheckBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QDialog
from PyQt6.QtCore import Qt
from phasescan import phasescan

import numpy as np
from datetime import datetime,timedelta

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import (
    FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)

Ui_MainWindow, QMainWindow = loadUiType('gui_window.ui')

class Main(QMainWindow, Ui_MainWindow):
    def __init__(self, ):
        super(Main, self).__init__()
        self.setupUi(self)
        self.ramplist = []
        self.scanresults = []
        self.phasescan = phasescan()
        self.init_plot()
        self.event_comboBox.addItems(['0a','52','53','15Hz'])

        for checkBox in self.findChildren(QCheckBox):
            checkBox.toggled.connect(self.add_param)
        for dspinBox in self.findChildren(QDoubleSpinBox):
            dspinBox.valueChanged.connect(self.read_deltas)
        for spinBox in self.findChildren(QSpinBox):
            if spinBox.objectName().find('steps')!=-1:
                spinBox.valueChanged.connect(self.read_steps)


    def add_param(self):
        for key in self.phasescan.param_dict:
            for checkBox in self.findChildren(QCheckBox):
                if checkBox.isChecked() and checkBox.text()==key:
                    self.phasescan.param_dict[key]['selected']=True

                elif checkBox.isChecked()==False and checkBox.text()==key:
                    self.phasescan.param_dict[key]['selected']=False
                    self.phasescan.param_dict[key]['phase']=0
        #print(self.phasescan.param_dict.values())

    def read_phases(self):
        for key in self.phasescan.param_dict:
            if self.phasescan.param_dict[key]['selected']==True:
                self.phasescan.param_dict[key]['phase']=self.phasescan.get_settings_once([self.phasescan.param_dict[key]['device']])[0]
                
    def read_deltas(self):
        for key in self.phasescan.param_dict:
            if self.phasescan.param_dict[key]['selected']==True:
                self.phasescan.param_dict[key]['delta']=self.findChild(QDoubleSpinBox,'doubleSpinBox_%d'%(self.phasescan.param_dict[key]['idx'])).value()

    def read_steps(self):
        for key in self.phasescan.param_dict:
            if self.phasescan.param_dict[key]['selected']==True:
                self.phasescan.param_dict[key]['steps']=self.findChild(QSpinBox,'steps_spinBox_%d'%(self.phasescan.param_dict[key]['idx'])).value()
                    
    def select_all(self):
        for checkBox in self.findChildren(QCheckBox):
            checkBox.setChecked(True)

            
    def clear_all(self):
        for checkBox in self.findChildren(QCheckBox):
            checkBox.setChecked(False)

    def init_plot(self):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        self.phases_verticalLayout.addWidget(self.canvas)

        self.timer = self.canvas.new_timer(200)
        self.timer.add_callback(self.update_phase_plot)
        
        self.fig1 = Figure()
        self.ax1 = self.fig1.add_subplot(111)
        self.canvas1 = FigureCanvas(self.fig1)
        self.monitors_verticalLayout.addWidget(self.canvas1)

        self.timer1 = self.canvas1.new_timer(200)
        self.timer1.add_callback(self.update_monitor_plot)


    def toggle_phase_plot(self):

        selected = [dev for dev in self.phasescan.param_dict if self.phasescan.param_dict[dev]['selected']==True]
        if self.plot_phases_pushButton.isChecked() and len(selected)>0:
            self.xaxis = np.array([])
            self.yaxes = [np.array([]) for i in range(len(selected))]
            self.timer.start()
        elif self.plot_phases_pushButton.isChecked()==False: 
            self.timer.stop()
        else:
            self.timer.stop()
            self.plot_phases_pushButton.setChecked(False)
            
    def update_phase_plot(self):
        
        try:
            self.read_phases()
            phases = [ self.phasescan.param_dict[key]['phase'] for key in self.phasescan.param_dict if self.phasescan.param_dict[key]['selected']==True]
            self.ax.cla()
            self.ax.set_ylim([-50.,250.])
            self.xaxis = np.append(self.xaxis,datetime.now())
            for i,ph in enumerate(phases): 
                self.yaxes[i] = np.append(self.yaxes[i],ph)
                self.ax.plot(self.xaxis,self.yaxes[i])
            
            self.fig.subplots_adjust(left=0.13)
            self.fig.subplots_adjust(right=0.95)
            self.fig.subplots_adjust(bottom=0.12)
            self.fig.subplots_adjust(top=0.95)
            
            self.canvas.draw_idle()

        except Exception as e:
            print('Cannot update phase plot',e)

    def toggle_monitor_plot(self):

        selected = [item.text() for item in self.listWidget.selectedItems()]
        if self.plot_monitor_pushButton.isChecked() and len(selected)>0:
            self.xaxis1 = np.array([])
            self.yaxes1 = [np.array([]) for i in range(len(selected))]
            self.timer1.start()
        elif self.plot_monitor_pushButton.isChecked()==False: 
            self.timer1.stop()
        elif self.plot_monitor_pushButton.isChecked() and len(selected)==0:
            self.timer1.stop()
            self.plot_monitor_pushButton.setChecked(False)
            
    def update_monitor_plot(self):
        items = [item.text() for item in self.listWidget.selectedItems()]

        try:
            mons = np.asarray(self.phasescan.get_readings_once(items))
            self.ax1.cla()
            self.xaxis1 = np.append(self.xaxis1,datetime.now())
            for i,mon in enumerate(mons):
                self.yaxes1[i] = np.append(self.yaxes1[i],mon)
                self.ax1.plot(self.xaxis1,self.yaxes1[i])

            self.fig1.subplots_adjust(left=0.1)
            self.fig1.subplots_adjust(right=0.95)
            self.fig1.subplots_adjust(bottom=0.22)
            self.fig1.subplots_adjust(top=0.95)
            self.canvas1.draw_idle()

        except Exception as e:
            print('Cannot update monitor plot',e)

    def toggle_L11_plot(self):

        selected = [item.text() for item in self.listWidget.selectedItems()]
        if self.plot_monitor_pushButton.isChecked() and len(selected)>0:
            self.timer1.start()
        elif self.plot_monitor_pushButton.isChecked()==False: 
            self.timer1.stop()
        elif self.plot_monitor_pushButton.isChecked() and len(selected)==0:
            self.timer1.stop()
            self.plot_monitor_pushButton.setChecked(False)
            

    def update_L11_plot(self):
        items = [item.text() for item in self.listWidget.selectedItems()]

        try:
            mons = np.asarray(self.phasescan.get_readings_once(items))
            self.ax1.cla()
            self.ax1.set_ylim([0.,50.])
            self.ax1.bar([i for i in range(len(mons))],height=mons)
            self.ax1.set_xticks([i for i in range(len(mons))],items,rotation = 'vertical',fontsize=6)
            self.fig1.subplots_adjust(left=0.1)
            self.fig1.subplots_adjust(right=0.95)
            self.fig1.subplots_adjust(bottom=0.22)
            self.fig1.subplots_adjust(top=0.95)
            self.canvas1.draw_idle()

        except Exception as e:
            print('Cannot update monitor plot',e)

            
    def generate_ramp_list(self):
        self.read_phases()
        numevents = self.numevents_spinBox.value()
        if self.oneD_radioButton.isChecked():
            try:
                self.ramplist = self.phasescan.make_ramp_list(self.phasescan.param_dict,numevents)
            except:
                print('Cannot generate 1-D ramp list.')
        elif self.nD_radioButton.isChecked():
           try:
               self.ramplist = self.phasescan.make_loop_ramp_list(self.phasescan.param_dict,numevents)
           except:
               print('Cannot generate nested ramp list.')
               
    def write_list(self):        
        if not self.list_plainTextEdit.toPlainText():
            print('Using default filename')
            self.list_plainTextEdit.setPlainText('ramplist.csv')
        filename = self.list_plainTextEdit.toPlainText()
        try:
            output = open(r'%s'%filename,'w', newline='' )
            output.writelines(["%s\n"%(','.join([str(l) for l in line])) for line in self.ramplist])
            output.close()
            print('Wrote %s to disk'%filename)
        except:
            print('Something went wrong')

    def display_list(self):
        for line in self.ramplist:
            print(','.join([str(l) for l in line]))

    
    def scan(self):
        numevents = self.numevents_spinBox.value()
        evt = self.event_comboBox.currentText()
        print('Work in porigress')

    def display_scan_results(self):
        for line in self.scanresults:
            print(','.join([str(l) for l in line]))

    def write_scan_results(self):        
        if not self.scan_plainTextEdit.toPlainText():
            print('Using default filename')
            self.scan_plainTextEdit.setPlainText('devicescan.csv')
        filename = self.scan_plainTextEdit.toPlainText()
        try:
            output = open(r'%s'%filename,'w', newline='' )
            output.writelines(["%s\n"%(','.join([str(l) for l in line])) for line in self.scanresults])
            output.close()
            print('Wrote %s to disk'%filename)
        except:
            print('Something went wrong')


    def expand(self):
        """Launch the employee dialog."""
        dlg = ExpandPlot(self)
        dlg.exec()
            
            
class ExpandPlot(QDialog):
    """Expand plot."""
    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi("expandPlot.ui", self)
        self.init_plot()

    def init_plot(self):
        #self.fig = Figure()
        self.fig = self.parent().fig
        #self.ax = self.fig.add_subplot(111)
        self.ax = self.parent().ax
        self.canvas = FigureCanvas(self.fig)
        self.verticalLayout.addWidget(self.canvas)

        self.timer = self.parent().timer
        #self.timer = self.canvas.new_timer(200)
        #self.timer.add_callback(self.parent().update_phase_plot)
    
            
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    main = Main()
    main.show()
    sys.exit(app.exec())
