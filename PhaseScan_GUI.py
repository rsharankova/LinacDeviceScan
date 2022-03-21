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
        self.param_dict = {'RFQ':{'device':'L:RFQPAH','idx':1,'selected':False,'phase':0,'delta':0},
                           'RFB':{'device':'L:RFBPAH','idx':2,'selected':False,'phase':0,'delta':0},
                           'Tank 1':{'device':'L:V1QSET','idx':3,'selected':False,'phase':0,'delta':0},
                           'Tank 2':{'device':'L:V2QSET','idx':4,'selected':False,'phase':0,'delta':0},
                           'Tank 3':{'device':'L:V3QSET','idx':5,'selected':False,'phase':0,'delta':0},
                           'Tank 4':{'device':'L:V4QSET','idx':6,'selected':False,'phase':0,'delta':0},
                           'Tank 5':{'device':'L:V5QSET','idx':7,'selected':False,'phase':0,'delta':0}}
        self.phasescan = phasescan()
        self.init_plot()
        self.event_comboBox.addItems(['0a','52','53'])

        for checkBox in self.findChildren(QCheckBox):
            checkBox.toggled.connect(self.add_param)
        for spinBox in self.findChildren(QDoubleSpinBox):
            spinBox.valueChanged.connect(self.read_deltas)


    def add_param(self):
        for key in self.param_dict:
            for checkBox in self.findChildren(QCheckBox):
                if checkBox.isChecked() and checkBox.text()==key:
                    self.param_dict[key]['selected']=True
                    self.param_dict[key]['phase']=self.phasescan.get_phases_once([self.param_dict[key]['device']])[0]
                elif checkBox.isChecked()==False and checkBox.text()==key:
                    self.param_dict[key]['selected']=False
                    self.param_dict[key]['phase']=0
        #print(self.param_dict.values())

    def read_deltas(self):
        for key in self.param_dict:
            if self.param_dict[key]['selected']==True:
                self.param_dict[key]['delta']=self.findChild(QDoubleSpinBox,'doubleSpinBox_%d'%(self.param_dict[key]['idx'])).value()

                    
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

    def update_plot(self):

        try:
            self.ax.cla()
            phases = [ self.param_dict[key]['phase'] for key in self.param_dict if self.param_dict[key]['selected']==True]
            self.ax.bar([i for i in range(len(phases))],height=phases)
            self.ax.set_ylabel('Phase (deg)')
            self.ax.set_xticks([i for i in range(len(phases))],[ key for key in self.param_dict if self.param_dict[key]['selected']==True])
            self.canvas.draw_idle()
        except:
            print('bugger')
        
    def generate_ramp_list(self):
        numevents = self.numevents_spinBox.value()
        self.ramplist = self.phasescan.make_ramp_list(self.param_dict,numevents)

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
