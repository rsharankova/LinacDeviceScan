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


    def expandMon(self):
        selected = [item.text() for item in self.listWidget.selectedItems()]
        dlg = TimePlot(selected,self)
        dlg.show()

    def expandPhase(self):
        selected = [ self.phasescan.param_dict[key]['device'] for key in self.phasescan.param_dict if self.phasescan.param_dict[key]['selected']==True]
        dlg = TimePlot(selected,self)
        dlg.show()

    def barLosses(self):
        #selected = [item.text() for i in self.listWidget.count() if self.listWidget.item(i).text().find('LM')!=-1]
        selected = [self.listWidget.item(i).text() for i in range(self.listWidget.count()) if self.listWidget.item(i).text().find('LM')!=-1]
        dlg = BarPlot(selected,self)
        dlg.show()
        
    def barTors(self):
        selected = [self.listWidget.item(i).text() for i in range(self.listWidget.count()) if self.listWidget.item(i).text().find('TO')!=-1]
        dlg = BarPlot(selected,self)
        dlg.show()

            
class TimePlot(QDialog):
    def __init__(self, selected,parent=None):
        super().__init__(parent)
        loadUi("expandPlot.ui", self)
        self.selected = selected
        self.init_plot()

    def init_plot(self):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        self.verticalLayout.addWidget(self.canvas)

        self.timer = self.canvas.new_timer(200)
        self.timer.add_callback(self.update_plot)
        

    def toggle_plot(self):
        if self.plot_pushButton.isChecked() and len(self.selected)>0:
            self.xaxis = np.array([])
            self.yaxes = [np.array([]) for i in range(len(self.selected))]
            self.timer.start()
        elif self.plot_pushButton.isChecked()==False: 
            self.timer.stop()
        elif self.plot_pushButton.isChecked() and len(self.selected)==0:
            self.timer.stop()
            self.plot_pushButton.setChecked(False)
            
    def update_plot(self):
        try:
            self.ax.cla()
            self.xaxis = np.append(self.xaxis,datetime.now())
            data = np.asarray(self.parent().phasescan.get_readings_once(self.selected))
            for i,d in enumerate(data):
                self.yaxes[i] = np.append(self.yaxes[i],d)
                self.ax.plot(self.xaxis,self.yaxes[i])

            self.fig.subplots_adjust(left=0.1)
            self.fig.subplots_adjust(right=0.95)
            self.fig.subplots_adjust(bottom=0.22)
            self.fig.subplots_adjust(top=0.95)
            self.canvas.draw_idle()

        except Exception as e:
            print('Cannot update time plot',e)

            
class BarPlot(QDialog):
    """Bar plot."""
    def __init__(self, selected, parent=None):
        super().__init__(parent)
        loadUi("expandPlot.ui", self)
        self.selected = selected
        self.init_plot()

    def init_plot(self):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        self.verticalLayout.addWidget(self.canvas)

        self.timer = self.canvas.new_timer(200)
        self.timer.add_callback(self.update_plot)
        

    def toggle_plot(self):
        if self.plot_pushButton.isChecked() and len(self.selected)>0:
            self.timer.start()
        elif self.plot_pushButton.isChecked()==False: 
            self.timer.stop()
        elif self.plot_pushButton.isChecked() and len(self.selected)==0:
            self.timer.stop()
            self.plot_pushButton.setChecked(False)
            
    def update_plot(self):
        try:
            data = np.asarray(self.parent().phasescan.get_readings_once(self.selected))
            self.ax.cla()
            self.ax.set_ylim([0.,max(data)])
            self.ax.bar([i for i in range(len(data))],height=data)
            self.ax.set_xticks([i for i in range(len(data))],self.selected,rotation = 'vertical',fontsize=6)

            self.fig.subplots_adjust(left=0.1)
            self.fig.subplots_adjust(right=0.95)
            self.fig.subplots_adjust(bottom=0.22)
            self.fig.subplots_adjust(top=0.95)
            self.canvas.draw_idle()

        except Exception as e:
            print('Cannot update bar plot',e)

        
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    main = Main()
    main.show()
    sys.exit(app.exec())
