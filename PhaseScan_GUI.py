from PyQt6.uic import loadUiType, loadUi
from PyQt6.QtWidgets import QFileDialog, QWidget, QCheckBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QDialog, QComboBox, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QUuid, QRegularExpression#, QtLiterals
from phasescan import phasescan

import numpy as np
from datetime import datetime,timedelta

from matplotlib.figure import Figure
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

from matplotlib.backends.backend_qtagg import (
    FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)

Ui_MainWindow, QMainWindow = loadUiType('gui_window.ui')

class Main(QMainWindow, Ui_MainWindow):
    def __init__(self, ):
        super(Main, self).__init__()
        self.setupUi(self)
        self.ramplist = []
        self.read_list = []
        self.scanresults = []
        self.phasescan = phasescan()
        self.event_comboBox.addItems(['default','15Hz','52','53','0a'])
        self.evt_dict = {'default':'','15Hz':'@p,15000','52':'@e,52,e,0','53':'@e,53,e,0','0a':'@e,0a,e,0'}

        self.stackedWidget.setCurrentIndex(0)
        self.list_plainTextEdit.setPlainText('ramplist.csv')
        self.scan_plainTextEdit.setPlainText('devicescan.csv')
        self.read_plainTextEdit.setPlainText('Reading_devices.csv')
        
        for checkBox in self.findChildren(QCheckBox):
            checkBox.toggled.connect(self.add_param)
        for dspinBox in self.findChildren(QDoubleSpinBox):
            dspinBox.valueChanged.connect(self.read_deltas)

        for spinBox in self.findChildren(QSpinBox):
            if spinBox.objectName().find('steps')!=-1:
                spinBox.valueChanged.connect(self.read_steps)

        self.debug_pushButton.toggled.connect(self.toggle_debug)
        self.devP_pushButton.clicked.connect(self.toggle_page)
        self.mainP_pushButton.clicked.connect(self.toggle_page)

        self.selectall_pushButton_1.clicked.connect(self.select_all)
        self.selectall_pushButton_2.clicked.connect(self.select_all)

        self.clearall_pushButton_1.clicked.connect(self.clear_all)
        self.clearall_pushButton_2.clicked.connect(self.clear_all)

        self.populate_list()
        
    def toggle_debug(self):
        if self.debug_pushButton.isChecked():
            self.stackedWidget.setCurrentIndex(2)
            self.phasescan.swap_dict()
            #print(self.phasescan.param_dict)
        else:
            self.stackedWidget.setCurrentIndex(0)
            self.phasescan.swap_dict()
            #print(self.phasescan.param_dict)

    def toggle_page(self):
        if self.stackedWidget.currentIndex()==0:
            self.stackedWidget.setCurrentIndex(1)
        else:       
            self.stackedWidget.setCurrentIndex(0)

    def populate_list(self):
        print(self.phasescan.dev_list[0])
        for dev in self.phasescan.dev_list:
            self.listWidget.addItem(dev)
        

    def add_param(self):
        for key in self.phasescan.param_dict:
            for checkBox in self.findChildren(QCheckBox):
                if checkBox.isChecked() and checkBox.text()==key:
                    self.phasescan.param_dict[key]['selected']=True

                elif checkBox.isChecked()==False and checkBox.text()==key:
                    self.phasescan.param_dict[key]['selected']=False
                    self.phasescan.param_dict[key]['phase']=0


    def read_phases(self):
        for key in self.phasescan.param_dict:
            if self.phasescan.param_dict[key]['selected']==True:
                self.phasescan.param_dict[key]['phase']=self.phasescan.get_settings_once([self.phasescan.param_dict[key]['device']])[0]
                
    def read_deltas(self):
        for key in self.phasescan.param_dict:
            if self.phasescan.param_dict[key]['selected']==True:
                if self.debug_pushButton.isChecked():
                    self.phasescan.param_dict[key]['delta']=self.findChild(QDoubleSpinBox,'cube_doubleSpinBox_%d'%(self.phasescan.param_dict[key]['idx'])).value()
                else:
                    self.phasescan.param_dict[key]['delta']=self.findChild(QDoubleSpinBox,'doubleSpinBox_%d'%(self.phasescan.param_dict[key]['idx'])).value()

                    
    def read_steps(self):
        for key in self.phasescan.param_dict:
            if self.phasescan.param_dict[key]['selected']==True:
                if self.debug_pushButton.isChecked():
                    self.phasescan.param_dict[key]['steps']=self.findChild(QSpinBox,'cube_steps_spinBox_%d'%(self.phasescan.param_dict[key]['idx'])).value()
                else:
                    self.phasescan.param_dict[key]['steps']=self.findChild(QSpinBox,'steps_spinBox_%d'%(self.phasescan.param_dict[key]['idx'])).value()

                    
    def select_all(self):
        if self.stackedWidget.currentIndex()==0: 
            [ checkBox.setChecked(True) for checkBox in self.findChildren(QCheckBox) if checkBox.objectName().find('main')!=-1 ]
        elif self.stackedWidget.currentIndex()==1:
            [ checkBox.setChecked(True) for checkBox in self.findChildren(QCheckBox) if checkBox.objectName().find('dev')!=-1 ]
        else:
            return None
            
    def clear_all(self):
        if self.stackedWidget.currentIndex()==0: 
            [ checkBox.setChecked(False) for checkBox in self.findChildren(QCheckBox) if checkBox.objectName().find('main')!=-1 ]
        elif self.stackedWidget.currentIndex()==1:
            [ checkBox.setChecked(False) for checkBox in self.findChildren(QCheckBox) if checkBox.objectName().find('dev')!=-1 ]
        else:
            return None


    def generate_ramp_list(self):
        self.ramplist = []
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


    def reading(self):
        if not self.read_plainTextEdit.toPlainText():
            print('Using default filename')
            self.read_plainTextEdit.setPlainText('Reading_devices.csv')
        filename = self.read_plainTextEdit.toPlainText()
        self.read_list = self.phasescan.readList(filename)
        
            
    def scan(self):
        numevents = self.numevents_spinBox.value()
        evt = self.event_comboBox.currentText()
        self.reading()
        self.read_phases()
        if self.debug_pushButton.isChecked():
            print('Debug mode')
            self.thread = QUuid.createUuid().toString()
            try:
                self.phasescan.apply_settings(self.ramplist,self.read_list,self.evt_dict[evt],self.thread,self.scanresults)   
            except:
                print('Scan failed')
                
    def display_scan_results(self):
        for line in self.scanresults:
            #print(','.join([str(l) for l in line]))
            print(line)

    def write_scan_results(self):        
        if not self.scan_plainTextEdit.toPlainText():
            print('Using default filename')
            self.scan_plainTextEdit.setPlainText('devicescan.csv')
        filename = self.scan_plainTextEdit.toPlainText()
        try:
            self.phasescan.fill_write_dataframe(self.scanresults,filename)
            print('Wrote %s to disk'%filename)
        except Exception as e:
            print('Something went wrong',e)


    def expandMon(self):
        evt = self.event_comboBox.currentText()
        selected = ['%s%s'%(item.text(),self.evt_dict[evt]) for item in self.listWidget.selectedItems()]
        if len(selected)>0:
            dlg = TimePlot(selected,evt,self)
            dlg.show()

    def expandPhase(self):
        evt = self.event_comboBox.currentText()
        selected = [ self.phasescan.param_dict[key]['device'] for key in self.phasescan.param_dict if self.phasescan.param_dict[key]['selected']==True]
        selected = ['%s%s'%(sel,self.evt_dict[evt]) for sel in selected]
        if len(selected)>0:
            dlg = TimePlot(selected,evt,self)
            dlg.show()

    def barLosses(self):
        evt = self.event_comboBox.currentText()
        #selected = [self.listWidget.item(i).text() for i in range(self.listWidget.count()) if self.listWidget.item(i).text().find('LM')!=-1
        #            and self.listWidget.item(i).text().find('LMSM')==-1]
        selected = ['%s%s'%(sel,self.evt_dict[evt]) for sel in self.phasescan.LMs]
        if len(selected)>0:
            dlg = BarPlot(selected,evt,'loss',self)
            dlg.show()
        
    def barTors(self):
        evt = self.event_comboBox.currentText()
        selected = ['%s%s'%(sel,self.evt_dict[evt]) for sel in self.phasescan.TORs]
        if len(selected)>0:
            dlg = BarPlot(selected,evt,'current',self)
            dlg.show()

            
class TimePlot(QDialog):
    def __init__(self, selected,evt,parent=None):
        super().__init__(parent)
        loadUi("expandPlot.ui", self)

        self.thread = QUuid.createUuid().toString()
        self.selected = selected
        self.range_dict = {}
        
        self.comboBox = QComboBox()
        self.comboBox.addItems(self.selected)
        
        self.setRange_pushButton = QPushButton('SetRange')
        self.setRange_pushButton.clicked.connect(self.set_range)
        
        self.hLayout0 = QHBoxLayout()
        self.hLayout0.addWidget(self.comboBox)
        self.hLayout0.addWidget(self.setRange_pushButton)
        self.gridLayout.addLayout(self.hLayout0,0,0)

        self.min_doubleSpinBox = QDoubleSpinBox()
        self.max_doubleSpinBox = QDoubleSpinBox()
        self.min_doubleSpinBox.setMinimum(-1000)
        self.min_doubleSpinBox.setMaximum(1000)
        self.max_doubleSpinBox.setMinimum(-1000)
        self.max_doubleSpinBox.setMaximum(1000)

        self.minLabel = QLabel('MIN')
        self.minLabel.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.maxLabel = QLabel('MAX')
        self.maxLabel.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.hLayout1 = QHBoxLayout()
        self.hLayout1.addWidget(self.minLabel)
        self.hLayout1.addWidget(self.min_doubleSpinBox)
        self.hLayout1.addWidget(self.maxLabel)
        self.hLayout1.addWidget(self.max_doubleSpinBox)
        self.gridLayout.addLayout(self.hLayout1,1,0)

        self.eventLabel = QLabel()
        self.eventLabel.setText('%s'%evt)
        self.eventLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.plot_pushButton=QPushButton('Plot')
        self.plot_pushButton.setCheckable(True)
        self.plot_pushButton.clicked.connect(self.toggle_plot)

        self.close_pushButton=QPushButton('Close')
        self.close_pushButton.clicked.connect(self.close_dialog)
        
        self.hLayout2 = QHBoxLayout()
        self.hLayout2.addWidget(self.eventLabel)
        self.hLayout2.addWidget(self.plot_pushButton)
        self.hLayout2.addWidget(self.close_pushButton)
        self.gridLayout.addLayout(self.hLayout2,3,0)
        
        self.setLayout(self.gridLayout)
        self.init_plot()

    def close_dialog(self):
        if self.thread in self.parent().phasescan.get_list_of_threads():
            self.parent().phasescan.stop_thread('%s'%self.thread)
        self.close()

        
    def init_plot(self):
        self.fig = Figure()

        self.ax = [None]*len(self.selected)
        self.ax[0] = self.fig.add_subplot(111)
        for i in range(1,len(self.selected)):
            self.ax[i] = self.ax[0].twinx()
        self.canvas = FigureCanvas(self.fig)
        self.gridLayout.addWidget(self.canvas,2,0)        

        self.timer = self.canvas.new_timer(50)
        self.timer.add_callback(self.update_plot)
        
    def set_range(self):
        self.range_dict.update({self.comboBox.currentText():{'ymin':self.min_doubleSpinBox.value(),'ymax':self.max_doubleSpinBox.value()}})
        
    def toggle_plot(self):
        if self.plot_pushButton.isChecked() and len(self.selected)>0:
            self.xaxis = np.array([])
            self.yaxes = [np.array([]) for i in range(len(self.selected))]
            self.timer.start()
            self.parent().phasescan.start_thread('%s'%self.thread,self.selected)
        elif self.plot_pushButton.isChecked()==False: 
            self.timer.stop()
            self.parent().phasescan.stop_thread('%s'%self.thread)
        elif self.plot_pushButton.isChecked() and len(self.selected)==0:
            self.timer.stop()
            self.parent().phasescan.stop_thread('%s'%self.thread)
            self.plot_pushButton.setChecked(False)
            
    def update_plot(self):
        try:
            
            data = self.parent().phasescan.get_thread_data('%s'%self.thread)
            if data.count(None)>0:
                return
            labels = [s.split('@')[0] for s in self.selected]

            colors = plt.rcParams['axes.prop_cycle']
            colors = colors.by_key()['color']
            plt.rcParams["axes.titlelocation"] = 'right'
            
            self.xaxis = np.append(self.xaxis,datetime.now())
            for i,d in enumerate(data):
                self.ax[i].cla()
                space= space + '  '*len(labels[i-1]) if i>0 else ''
                self.ax[i].set_title(labels[i]+space,color=colors[i],ha='right',fontsize='small')
                self.yaxes[i] = np.append(self.yaxes[i],d)
                self.ax[i].plot(self.xaxis,self.yaxes[i],c=colors[i],label=labels[i])
                self.ax[i].tick_params(axis='y', colors=colors[i], labelsize='small',rotation=90)
                self.ax[i].yaxis.set_major_locator(MaxNLocator(5))
                self.ax[i].set_ylim(self.range_dict[labels[i]]['ymin'],self.range_dict[labels[i]]['ymax'])

                if i%2==0:
                    self.ax[i].yaxis.tick_left()
                    for yl in self.ax[i].get_yticklabels():
                        yl.set_x( -0.025*(i/2.) )
                        yl.set(verticalalignment='bottom')

                else:
                    self.ax[i].yaxis.tick_right()
                    for yl in self.ax[i].get_yticklabels():
                        yl.set_x( 1.0+0.025*(i-1)/2.)
                        yl.set(verticalalignment='bottom')

            self.fig.subplots_adjust(left=0.12)
            self.fig.subplots_adjust(right=0.88)
            self.fig.subplots_adjust(bottom=0.12)
            self.fig.subplots_adjust(top=0.88)
            self.canvas.draw_idle()

        except Exception as e:
            print('Cannot update time plot',e)

            
class BarPlot(QDialog):
    """Bar plot."""
    def __init__(self, selected, evt, style='',parent=None):
        super().__init__(parent)
        loadUi("expandPlot.ui", self)

        self.thread = QUuid.createUuid().toString()
        self.selected = selected
        self.first = True

        self.style=style
        self.style_dict={'loss':{'ymin':0,'ymax':5,'ylabel':'Beam Loss (cnt)'},
                         'current':{'ymin':0,'ymax':60,'ylabel':'Beam Current (mA)'}}

        self.eventLabel = QLabel()
        self.eventLabel.setText('%s'%evt)
        self.eventLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.plot_pushButton=QPushButton('Plot')
        self.plot_pushButton.setCheckable(True)
        self.plot_pushButton.clicked.connect(self.toggle_plot)

        self.close_pushButton=QPushButton('Close')
        self.close_pushButton.clicked.connect(self.close_dialog)
        
        self.hLayout = QHBoxLayout()
        self.hLayout.addWidget(self.eventLabel)
        self.hLayout.addWidget(self.plot_pushButton)
        self.hLayout.addWidget(self.close_pushButton)
        self.gridLayout.addLayout(self.hLayout,1,0)

        self.setLayout(self.gridLayout)

        self.init_plot()

    def close_dialog(self):
        if self.thread in self.parent().phasescan.get_list_of_threads():
            self.parent().phasescan.stop_thread('%s'%self.thread)
        self.close()
            
    def init_plot(self):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        self.gridLayout.addWidget(self.canvas,0,0)

        self.timer = self.canvas.new_timer(50)
        self.timer.add_callback(self.update_plot)
        self.first_data = np.zeros(len(self.selected))

    def toggle_plot(self):
        if self.plot_pushButton.isChecked() and len(self.selected)>0:
            self.timer.start()
            self.parent().phasescan.start_thread('%s'%self.thread,self.selected)
        elif self.plot_pushButton.isChecked()==False: 
            self.timer.stop()
            self.parent().phasescan.stop_thread('%s'%self.thread)
        elif self.plot_pushButton.isChecked() and len(self.selected)==0:
            self.timer.stop()
            self.parent().phasescan.stop_thread('%s'%self.thread)
            self.plot_pushButton.setChecked(False)
            
    def update_plot(self):
        try:
            self.ax.cla()
            data = self.parent().phasescan.get_thread_data('%s'%self.thread)
            if data.count(None)>0:
                return None

            if self.first:
                self.first_data = data.copy()
                self.first=False

            colors = ['green' if data[i] < self.first_data[i] else 'red' for i in range(len(self.first_data))]
            self.ax.bar([i for i in range(len(self.first_data))],height=np.subtract(self.first_data,data),bottom = data,alpha=0.99,color=colors)
            self.ax.bar([i for i in range(len(data))],height=data,alpha=0.5,color='blue')
            labels = [s.split('@')[0] for s in self.selected]
            self.ax.set_xticks([i for i in range(len(data))],labels,rotation = 'vertical',fontsize=6)
            if self.style in self.style_dict.keys():
                self.ax.set_ylim(self.style_dict[self.style]['ymin'],self.style_dict[self.style]['ymax'])
                self.ax.set_ylabel(self.style_dict[self.style]['ylabel'])
                            
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
