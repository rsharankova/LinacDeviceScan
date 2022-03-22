from PyQt6.uic import loadUiType
from PyQt6.QtWidgets import QFileDialog, QWidget, QCheckBox, QDoubleSpinBox, QPlainTextEdit
from PyQt6.QtCore import Qt
from phasescan import phasescan

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
        self.event_comboBox.addItems(['0a','52','53'])

        for checkBox in self.findChildren(QCheckBox):
            checkBox.toggled.connect(self.add_param)
        for spinBox in self.findChildren(QDoubleSpinBox):
            spinBox.valueChanged.connect(self.read_deltas)


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
                self.phasescan.param_dict[key]['phase']=self.phasescan.get_phases_once([self.phasescan.param_dict[key]['device']])[0]
                
    def read_deltas(self):
        for key in self.phasescan.param_dict:
            if self.phasescan.param_dict[key]['selected']==True:
                self.phasescan.param_dict[key]['delta']=self.findChild(QDoubleSpinBox,'doubleSpinBox_%d'%(self.phasescan.param_dict[key]['idx'])).value()

                    
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

        self.fig1 = Figure()
        self.ax1 = self.fig1.add_subplot(111)
        self.canvas1 = FigureCanvas(self.fig1)
        self.monitors_verticalLayout.addWidget(self.canvas1)

        
    def update_plot(self):
        self.read_phases()
        try:
            self.ax.cla()
            phases = [ self.phasescan.param_dict[key]['phase'] for key in self.phasescan.param_dict if self.phasescan.param_dict[key]['selected']==True]
            self.ax.barh([i for i in range(len(phases))],phases)
            self.ax.set_xlabel('Phase set (deg)')
            self.ax.set_yticks([i for i in range(len(phases))],[ key for key in self.phasescan.param_dict if self.phasescan.param_dict[key]['selected']==True])
            self.canvas.draw_idle()
        except:
            print('Cannot update plot')
        
    def generate_ramp_list(self):
        self.read_phases()
        numevents = self.numevents_spinBox.value()
        self.ramplist = self.phasescan.make_ramp_list(self.phasescan.param_dict,numevents)

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

            
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    main = Main()
    main.show()
    sys.exit(app.exec())
