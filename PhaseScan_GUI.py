from PyQt6.uic import loadUiType, loadUi
from PyQt6.QtWidgets import QFileDialog, QWidget, QCheckBox, QSpinBox, QDoubleSpinBox,QPlainTextEdit, QDialog, QComboBox, QCompleter, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QUuid, QRegularExpression, QSortFilterProxyModel, QSize
from PyQt6.QtGui import QStandardItemModel,QStandardItem, QIcon
from phasescan import phasescan

import numpy as np
import random
from datetime import datetime,timedelta

import matplotlib.colors as mcolors
from matplotlib.figure import Figure
from matplotlib import pyplot as plt
import matplotlib.ticker as mt

from matplotlib.backends.backend_qtagg import (
    FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)


#### Device list search model ####
class ItemModel(QStandardItemModel):
    def __init__(self,data):
        super().__init__()
        self._data = [[dev] for dev in data]
        self._data=sorted(self._data)
        for i,word in enumerate(data):
            item = QStandardItem(word)
            self.setItem(i, 0, item)

#### Searchable, auto-complete combobox ####
class ExtendedCombo( QComboBox ):
    def __init__( self,  parent = None):
        super( ExtendedCombo, self ).__init__( parent )

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus )
        self.setEditable( True )
        self.completer = QCompleter( self )

        # always show all completions
        self.completer.setCompletionMode( QCompleter.CompletionMode.UnfilteredPopupCompletion )
        self.proxy_model = QSortFilterProxyModel( self )
        self.proxy_model.setFilterCaseSensitivity( Qt.CaseSensitivity.CaseInsensitive )

        self.setCompleter( self.completer )

        self.lineEdit().textEdited[str].connect( self.proxy_model.setFilterFixedString )
        self.completer.activated.connect(self.setTextIfCompleterIsClicked)

    def setModel( self, model ):
        super(ExtendedCombo, self).setModel( model )
        self.proxy_model.setSourceModel( model )
        self.completer.setModel(self.proxy_model)

    def setModelColumn( self, column ):
        self.completer.setCompletionColumn( column )
        self.proxy_model.setFilterKeyColumn( column )
        super(ExtendedCombo, self).setModelColumn( column )

    def index( self ):
        return self.currentIndex()

    def setTextIfCompleterIsClicked(self, text):
      if text:
        index = self.findText(text)
        self.setCurrentIndex(index)


#### MAIN WINDOW ####
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

        #### FILTER MODEL ####
        self.model = ItemModel(self.phasescan.dev_list)
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setFilterKeyColumn(-1)  
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity( Qt.CaseSensitivity.CaseInsensitive )
        #self.proxy_model.sort(0, Qt.SortOrder.AscendingOrder)

        #### TABLE SEARCH ####
        self.table.setShowGrid(False) 
        self.table.setModel(self.proxy_model)
        self.table.horizontalHeader().hide()
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(20)
        self.table.horizontalHeader().setDefaultSectionSize(200)

        self.searchbar.textChanged.connect(self.proxy_model.setFilterFixedString)

        #### LAYOUTS ####
        self.dev_comboBox_8 = ExtendedCombo()
        self.dev_comboBox_8.setObjectName('dev_comboBox_8')
        self.dev_comboBox_8.setModel(self.model)
        self.dev_comboBox_8.setModelColumn(0)

        ### DEBUG PAGE ###
        debug_gridLayout = QGridLayout()
        debug_gridLayout.addWidget(self.label_7,0,1,1,1)
        debug_gridLayout.addWidget(self.label_8,0,2,1,1)
        debug_gridLayout.addWidget(self.label_9,0,3,1,1)
        debug_gridLayout.addWidget(self.cube_checkBox_1,1,0,1,1)
        debug_gridLayout.addWidget(self.cube_comboBox_1,1,1,1,1)
        debug_gridLayout.addWidget(self.cube_doubleSpinBox_1,1,2,1,1)
        debug_gridLayout.addWidget(self.cube_steps_spinBox_1,1,3,1,1)
        debug_gridLayout.addWidget(self.cube_checkBox_2,2,0,1,1)
        debug_gridLayout.addWidget(self.cube_comboBox_2,2,1,1,1)
        debug_gridLayout.addWidget(self.cube_doubleSpinBox_2,2,2,1,1)
        debug_gridLayout.addWidget(self.cube_steps_spinBox_2,2,3,1,1)
        debug_gridLayout.addWidget(self.cube_checkBox_3,3,0,1,1)
        debug_gridLayout.addWidget(self.cube_comboBox_3,3,1,1,1)
        debug_gridLayout.addWidget(self.cube_doubleSpinBox_3,3,2,1,1)
        debug_gridLayout.addWidget(self.cube_steps_spinBox_3,3,3,1,1)
        self.cube_groupBox.setLayout(debug_gridLayout)
        ### OTHER DEVICES PAGE###
        dev_gridLayout = QGridLayout()
        dev_gridLayout.addWidget(self.selectall_pushButton_2,0,1,1,1)
        dev_gridLayout.addWidget(self.clearall_pushButton_2,0,2,1,1)
        dev_gridLayout.addWidget(self.mainP_pushButton,0,3,1,1)
        dev_gridLayout.addWidget(self.label_4,1,1,1,1)
        dev_gridLayout.addWidget(self.label_5,1,2,1,1)
        dev_gridLayout.addWidget(self.label_6,1,3,1,1)
        dev_gridLayout.addWidget(self.dev_checkBox_8,2,0,1,1)
        dev_gridLayout.addWidget(self.dev_comboBox_8,2,1,1,1)
        dev_gridLayout.addWidget(self.doubleSpinBox_8,2,2,1,1)
        dev_gridLayout.addWidget(self.steps_spinBox_8,2,3,1,1)
        self.dev_groupBox.setLayout(dev_gridLayout)
        ### MAIN PAGE ###
        main_gridLayout = QGridLayout()
        main_gridLayout.addWidget(self.selectall_pushButton_1,0,1,1,1)
        main_gridLayout.addWidget(self.clearall_pushButton_1,0,2,1,1)
        main_gridLayout.addWidget(self.devP_pushButton,0,3,1,1)
        main_gridLayout.addWidget(self.label_1,1,1,1,1)
        main_gridLayout.addWidget(self.label_2,1,2,1,1)
        main_gridLayout.addWidget(self.label_3,1,3,1,1)

        objects = ['dev_checkBox','dev_comboBox','doubleSpinBox','steps_spinBox']
        classes = [QCheckBox,QComboBox,QDoubleSpinBox,QSpinBox]
        
        for i in range(1,8):
            objs = ['%s_%d'%(obj,i) for obj in objects]
            children = [self.findChild(cl,ob) for cl,ob in zip(classes,objs)]
            for j,c in enumerate(children):
                if isinstance(c,classes[j]):
                    main_gridLayout.addWidget(c,1+i,j,1,1)
        
        self.main_groupBox.setLayout(main_gridLayout)


        #### DEFAULTS ####
        self.stackedWidget.setCurrentIndex(0)
        self.list_plainTextEdit.setPlainText('ramplist.csv')
        self.scan_plainTextEdit.setPlainText('devicescan.csv')
        self.read_plainTextEdit.setPlainText('Reading_devices.csv')

        #### BOX TOGGLE ACTIONS ####
        for checkBox in self.findChildren(QCheckBox):
            checkBox.toggled.connect(self.add_param)

        #### BUTTON ACTIONS ####
        ### SELECT/CLEAR ALL BUTTONS ###
        self.selectall_pushButton_1.clicked.connect(self.select_all)
        self.selectall_pushButton_2.clicked.connect(self.select_all)
        self.clearall_pushButton_1.clicked.connect(self.clear_all)
        self.clearall_pushButton_2.clicked.connect(self.clear_all)

        ### DEVICE LIST FOR PLOTS ###
        self.add_pushButton.clicked.connect(self.add_list_item)
        self.addS_pushButton.clicked.connect(self.add_set_list_item)
        self.remove_pushButton.clicked.connect(self.remove_list_item)

        ### RAMP LIST BUTTONS ###
        self.genList_pushButton.clicked.connect(self.generate_ramp_list)
        self.displayList_pushButton.clicked.connect(self.display_list)
        self.writeList_pushButton.clicked.connect(self.write_list)

        ### PLOT BUTTONS ###
        self.timeplot_pushButton.clicked.connect(self.timePlot)
        self.loss_pushButton.clicked.connect(self.barLosses)
        self.current_pushButton.clicked.connect(self.barTors)
        self.barplot_pushButton.clicked.connect(self.barPlot)

        ### SCAN BUTTONS ###
        self.startScan_pushButton.clicked.connect(self.start_scan)
        self.stopScan_pushButton.clicked.connect(self.stop_scan)
        self.pauseScan_pushButton.clicked.connect(self.pause_scan)
        self.resumeScan_pushButton.clicked.connect(self.resume_scan)
        self.writeScan_pushButton.clicked.connect(self.write_scan_results)

        ### STACKED WIDGET BUTTONS ###
        self.debug_pushButton.toggled.connect(self.toggle_debug)
        self.devP_pushButton.clicked.connect(self.toggle_page)
        self.mainP_pushButton.clicked.connect(self.toggle_page)

        ### ADD/REMOVE ROW BUTTONS ###
        self.addDevice_pushButton.setEnabled(False)
        self.stackedWidget.currentChanged.connect(self.enableAddRemove)
        self.addDevice_pushButton.clicked.connect(self.add_device)
        self.removeDevice_pushButton.setEnabled(False)
        self.stackedWidget.currentChanged.connect(self.enableAddRemove)
        self.removeDevice_pushButton.clicked.connect(self.remove_device)

        #### FONTS #####
        font13 =self.label_13.font()
        font13.setPointSize(16)
        font13.setBold(True)
        self.label_13.setFont(font13)

        font14 =self.label_14.font()
        font14.setPointSize(16)
        font14.setBold(True)
        self.label_14.setFont(font14)
        

    #### CLASS FUNCTIONS ####
    
    def enableAddRemove(self):
        if self.stackedWidget.currentIndex()==1:
            self.addDevice_pushButton.setEnabled(True)
            self.removeDevice_pushButton.setEnabled(True)
        else:
            self.addDevice_pushButton.setEnabled(False)
            self.removeDevice_pushButton.setEnabled(False)
            
    
    def add_device(self):
        num = int(len([cb for cb in self.findChildren(QCheckBox) if cb.objectName().find('cube')==-1])+1)
        row = int(len([cb for cb in self.findChildren(QCheckBox) if cb.objectName().find('dev')!=-1]))-7+2

        checkBox = QCheckBox()
        checkBox.setObjectName('dev_checkBox_%d'%num)
        checkBox.setText('')
        self.dev_groupBox.layout().addWidget(checkBox,row,0,1,1)

        comboBox = ExtendedCombo()
        comboBox.setObjectName('dev_comboBox_%d'%num)
        comboBox.setModel(self.model)
        comboBox.setModelColumn(0)
        self.dev_groupBox.layout().addWidget(comboBox,row,1,1,1)

        doubleSpinBox = QDoubleSpinBox()
        doubleSpinBox.setObjectName('doubleSpinBox_%d'%num)
        self.dev_groupBox.layout().addWidget(doubleSpinBox,row,2,1,1)

        stepsSpinBox = QSpinBox()
        stepsSpinBox.setObjectName('steps_spinBox_%d'%num)
        self.dev_groupBox.layout().addWidget(stepsSpinBox,row,3,1,1)

        checkBox.toggled.connect(self.add_param)

        
    def remove_device(self):
        num = int(len([cb for cb in self.findChildren(QCheckBox) if cb.objectName().find('cube')==-1]))
        if num<=8:
            return None

        objs = ['dev_checkBox','dev_comboBox','doubleSpinBox','steps_spinBox']
        objs = ['%s_%d'%(obj,num) for obj in objs]
        classes = [QCheckBox,QComboBox,QDoubleSpinBox,QSpinBox]

        child = [self.findChild(cl,ob) for cl,ob in zip(classes,objs)]
        for i,c in enumerate(child):
            if isinstance(c,classes[i]):
                c.deleteLater()
                c = None
        
    def add_list_item(self):
        tx=self.searchbar.text()
        self.searchbar.setText("")

        for dev in self.table.selectedIndexes():
            if len(self.listWidget.findItems(dev.data(),Qt.MatchFlag.MatchExactly))==0:
             self.listWidget.addItem(dev.data())


        self.searchbar.setText("Start typing device name")
        self.searchbar.setText(tx)

    def add_set_list_item(self):
        tx=self.searchbar.text()
        self.searchbar.setText("")

        for dev in self.table.selectedIndexes():
            if len(self.listWidget.findItems(dev.data(),Qt.MatchFlag.MatchExactly))==0:
                self.listWidget.addItem(dev.data().replace(':','_'))

        self.searchbar.setText("Start typing device name")
        self.searchbar.setText(tx)

    def remove_list_item(self):
        for dev in self.listWidget.selectedItems():
            self.listWidget.takeItem(self.listWidget.row(dev))
        tx=self.searchbar.text()
        self.searchbar.setText("Start typing device name")
        self.searchbar.setText(tx)

        
    def toggle_debug(self):
        if self.debug_pushButton.isChecked():
            self.stackedWidget.setCurrentIndex(2)
            self.phasescan.swap_dict()

            self.listWidget.addItem('Z_CUBE_X')
            self.listWidget.addItem('Z_CUBE_Y')
            self.listWidget.addItem('Z_CUBE_Z')
            self.listWidget.addItem('Z:CUBE_X')            
            self.listWidget.addItem('Z:CUBE_Y')
            self.listWidget.addItem('Z:CUBE_Z')

        else:
            self.stackedWidget.setCurrentIndex(0)
            self.phasescan.swap_dict()
            for i in reversed(range(self.listWidget.count())):
                if self.listWidget.item(i).text().find('Z:')!=-1 or self.listWidget.item(i).text().find('Z_')!=-1:
                    self.listWidget.takeItem(i)


    def toggle_page(self):
        if self.stackedWidget.currentIndex()==0:
            self.stackedWidget.setCurrentIndex(1)
        else:       
            self.stackedWidget.setCurrentIndex(0)

    def populate_list(self):
        for dev in self.phasescan.dev_list:
            self.listWidget.addItem(dev)
        

    def add_param(self):

        if self.stackedWidget.currentIndex()==2:
            prefix ='cube'
            num = int(len([cb for cb in self.findChildren(QCheckBox) if cb.objectName().find('cube')!=-1]))+1
        else:
            prefix = 'dev'
            num = int(len([cb for cb in self.findChildren(QCheckBox) if cb.objectName().find('cube')==-1]))+1
            
        [self.phasescan.param_dict.update({self.findChild(QComboBox,'%s_comboBox_%d'%(prefix,i)).currentText().split(':')[1]:
                                           {'device':self.findChild(QComboBox,'%s_comboBox_%d'%(prefix,i)).currentText(),'idx':i,'selected':False,'phase':0,'delta':0,'steps':2}})
         for i in range(1,num) if self.findChild(QCheckBox,'%s_checkBox_%d'%(prefix,i)).isChecked()
         and self.findChild(QComboBox,'%s_comboBox_%d'%(prefix,i)).currentText() not in self.phasescan.param_dict]

        for key in self.phasescan.param_dict:
            for i in range(1,num):
                checkBox = self.findChild(QCheckBox,'%s_checkBox_%d'%(prefix,i))
                comboBox = self.findChild(QComboBox,'%s_comboBox_%d'%(prefix,i))
                if checkBox.isChecked():
                    comboBox.setEnabled(False)
                    if comboBox.currentText().split(':')[1]==key:
                        self.phasescan.param_dict[key]['selected']=True

                elif checkBox.isChecked()==False:
                    comboBox.setEnabled(True)
                    if comboBox.currentText().split(':')[1]==key:
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
            [ self.findChild(QCheckBox,'dev_checkBox_%d'%i).setChecked(True) for i in range(1,8)]
        elif self.stackedWidget.currentIndex()==1:
            num = int(len([checkBox for checkBox in self.findChildren(QCheckBox) if checkBox.objectName().find('dev')!=-1 ]))
            [ self.findChild(QCheckBox,'dev_checkBox_%d'%i).setChecked(True) for i in range(8,num+1)]
        else:
            return None
            
    def clear_all(self):
        if self.stackedWidget.currentIndex()==0:
            [ self.findChild(QCheckBox,'dev_checkBox_%d'%i).setChecked(False) for i in range(1,8)]
            #[ checkBox.setChecked(False) for checkBox in self.findChildren(QCheckBox) if checkBox.objectName().find('main')!=-1 ]
        elif self.stackedWidget.currentIndex()==1:
            num = int(len([checkBox for checkBox in self.findChildren(QCheckBox) if checkBox.objectName().find('dev')!=-1 ]))
            [ self.findChild(QCheckBox,'dev_checkBox_%d'%i).setChecked(False) for i in range(8,num+1)]
            #[ checkBox.setChecked(False) for checkBox in self.findChildren(QCheckBox) if checkBox.objectName().find('dev')!=-1 ]
        else:
            return None


    def generate_ramp_list(self):
        self.ramplist = []
        self.read_deltas()
        self.read_steps()
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
        print('Number of reading devices: ',len(self.read_list))
            
    def start_scan(self):
        self.thread = QUuid.createUuid().toString()
        self.scanresults = []
        
        numevents = self.numevents_spinBox.value()
        evt = self.evt_dict[self.event_comboBox.currentText()]

        self.reading()

        set_list = ['%s%s'%(s.replace(':','_'),evt) for s in self.ramplist[0] if str(s).find(':')!=-1] if len(self.ramplist)>0 else []

        drf_list = set_list+['%s%s'%(l,evt) for l in self.read_list if len(self.read_list)!=0]

        try:
            self.phasescan.start_thread('%s'%self.thread,drf_list,self.ramplist,self.phasescan.role,numevents)

        except Exception as e:
            print('Scan failed',e)

    def stop_scan(self):
        if self.thread in self.phasescan.get_list_of_threads():
            self.phasescan.stop_thread('%s'%self.thread)

    def pause_scan(self):
        if self.thread in self.phasescan.get_list_of_threads():
            self.phasescan.pause_thread('%s'%self.thread)

    def resume_scan(self):
        if self.thread in self.phasescan.get_list_of_threads():
            self.phasescan.resume_thread('%s'%self.thread)
        
    def display_scan_results(self):
        self.scanresults.extend(self.phasescan.get_thread_data('%s'%self.thread))
        for line in self.scanresults:
            #print(','.join([str(l) for l in line]))
            print(line)

    def write_scan_results(self):
        self.scanresults.extend(self.phasescan.get_thread_data('%s'%self.thread))
        if not self.scan_plainTextEdit.toPlainText():
            print('Using default filename')
            self.scan_plainTextEdit.setPlainText('devicescan.csv')
        filename = self.scan_plainTextEdit.toPlainText()
        try:
            self.phasescan.fill_write_dataframe(self.scanresults,self.read_list,filename)
            print('Wrote %s to disk'%filename)
        except Exception as e:
            print('Something went wrong',e)


    def timePlot(self):
        evt = self.event_comboBox.currentText()
        selected = ['%s%s'%(item.text(),self.evt_dict[evt]) for item in self.listWidget.selectedItems()]
        if len(selected)>0:
            dlg = TimePlot(selected,evt,self)
            dlg.show()

    def plotPhase(self):
        evt = self.event_comboBox.currentText()
        selected = [ self.phasescan.param_dict[key]['device'] for key in self.phasescan.param_dict if self.phasescan.param_dict[key]['selected']==True]
        selected = ['%s%s'%(sel,self.evt_dict[evt]) for sel in selected]
        if len(selected)>0:
            dlg = TimePlot(selected,evt,self)
            dlg.show()

    def barPlot(self):
        evt = self.event_comboBox.currentText()
        selected = ['%s%s'%(item.text(),self.evt_dict[evt]) for item in self.listWidget.selectedItems()]
        if len(selected)>0:
            dlg = BarPlot(selected,evt,'',self)
            dlg.show()
            
    def barLosses(self):
        evt = self.event_comboBox.currentText()
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


class CustomToolbar(NavigationToolbar):
  def __init__(self, figure_canvas, parent= None):
    self.toolitems = (
        ('Home', 'Home', 'home', 'home'),
        #('Back', 'Back', 'back', 'back'),              
        #('Forward', 'Forward', 'forward', 'forward'),
        ('Pan', 'Pan', 'move', 'pan'),
        ('Zoom', 'Zoom', 'zoom_to_rect', 'zoom'),
        #('Subplots', 'Config subplots', 'subplots', 'configure_subplots'),
        ('Save', 'Save image', 'filesave', 'save_figure'),
        )

    NavigationToolbar.__init__(self, figure_canvas, parent= None)

            
class TimePlot(QDialog):
    def __init__(self, selected,evt,parent=None):
        super().__init__(parent)

        self.setWindowTitle("Time plot")
        self.resize(930,650)

        self.thread = QUuid.createUuid().toString()
        self.selected = selected
        self.range_dict = {}
        self.style_dict = {}
        
        plt.rcParams["axes.titlelocation"] = 'right'
        plt.style.use('dark_background')
        overlap = {name for name in mcolors.CSS4_COLORS
           if f'xkcd:{name}' in mcolors.XKCD_COLORS}

        overlap.difference_update(['aqua','white','black','lime','chocolate','gold'])
        self.colors = [mcolors.XKCD_COLORS[f'xkcd:{color_name}'].upper() for color_name in sorted(overlap)]

        self.col_comboBox = QComboBox()
        self.col_comboBox.addItems(sorted(overlap))
        self.line_comboBox = QComboBox()
        self.line_comboBox.addItems(['solid','dashed','dashdot','dotted','none'])
        self.marker_comboBox = QComboBox()
        self.marker_comboBox.addItems(['','.','x','o','^','v','<','>','*','s','p','h','+','P','d','D'])

        self.comboBox = QComboBox()
        labels = [s.split('@')[0] for s in self.selected]
        self.comboBox.addItems(labels)
        
        self.setRange_pushButton = QPushButton('SetRange')
        self.setRange_pushButton.clicked.connect(self.set_range)

        self.setStyle_pushButton = QPushButton('SetStyle')
        self.setStyle_pushButton.clicked.connect(self.set_style)

        self.min_doubleSpinBox = QDoubleSpinBox()
        self.max_doubleSpinBox = QDoubleSpinBox()
        self.min_doubleSpinBox.setMinimum(-1000)
        self.min_doubleSpinBox.setMaximum(1000)
        self.max_doubleSpinBox.setMinimum(-1000)
        self.max_doubleSpinBox.setMaximum(1000)

        self.minLabel = QLabel('MIN')
        self.minLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.maxLabel = QLabel('MAX')
        self.maxLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.colLabel = QLabel('COLOR')
        self.colLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lineLabel = QLabel('LINE')
        self.lineLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.markerLabel = QLabel('MARKER')
        self.markerLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.eventLabel = QLabel()
        self.eventLabel.setText('%s'%evt)
        self.eventLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.plot_pushButton=QPushButton('')
        self.plot_pushButton.setIcon(QIcon("./icons/draw.png"))
        self.plot_pushButton.setCheckable(True)
        self.plot_pushButton.clicked.connect(self.toggle_plot)

        self.close_pushButton=QPushButton('')
        self.close_pushButton.setIcon(QIcon("./icons/close.png"))
        self.close_pushButton.clicked.connect(self.close_dialog)
        
        self.gridLayout0 = QGridLayout()
        self.gridLayout0.addWidget(self.comboBox,0,0,1,3)
        self.gridLayout0.addWidget(self.minLabel,0,3,1,1)
        self.gridLayout0.addWidget(self.min_doubleSpinBox,0,4,1,2)
        self.gridLayout0.addWidget(self.maxLabel,0,6,1,1)
        self.gridLayout0.addWidget(self.max_doubleSpinBox,0,7,1,2)
        self.gridLayout0.addWidget(self.setRange_pushButton,0,9,1,2)
        self.gridLayout0.addWidget(self.colLabel,1,0,1,1)
        self.gridLayout0.addWidget(self.col_comboBox,1,1,1,2)
        self.gridLayout0.addWidget(self.lineLabel,1,3,1,1)
        self.gridLayout0.addWidget(self.line_comboBox,1,4,1,2)
        self.gridLayout0.addWidget(self.markerLabel,1,6,1,1)
        self.gridLayout0.addWidget(self.marker_comboBox,1,7,1,2)
        self.gridLayout0.addWidget(self.setStyle_pushButton,1,9,1,2)
        
        self.hLayout2 = QHBoxLayout()
        self.hLayout2.addWidget(self.eventLabel)

        self.gridLayout = QGridLayout()
        self.gridLayout.addLayout(self.gridLayout0,0,0)
        self.gridLayout.addLayout(self.hLayout2,2,0)
        
        self.setLayout(self.gridLayout)
        self.init_plot()

    def close_dialog(self):
        if self.thread in self.parent().phasescan.get_list_of_threads():
            self.parent().phasescan.stop_thread('%s'%self.thread)
        self.timer.stop()
        self.close()

    def closeEvent(self, event):
        self.close_dialog()
        event.accept()

    def save_fig(self,event):
        fout = QFileDialog.getSaveFileName(
            self, "Save Image", "image", "Images (*.png *.jpg *.pdf);; All Files (*.*)") 

        self.fig.savefig(fout[0])

    def toggle_zoom(self,event):
        self.bzoom.setChecked(True)
        self.bpan.setChecked(False)

    def toggle_pan(self,event):
        self.bzoom.setChecked(False)
        self.bpan.setChecked(True)

    def zoom_pan(self,event):
        if event.button!=1 or event.inaxes!=self.ax:
            return
        if self.bzoom.isChecked():
            self.fig.canvas.toolbar.drag_zoom(event)
        else:
            self.fig.canvas.toolbar.drag_pan(event)
            

    def zoom_pan_press(self,event):
        if event.name=="figure_enter_event" or event.button!=1 or event.inaxes!=self.ax[-1]:
            return
        if self.bzoom.isChecked():
            self.fig.canvas.toolbar.press_zoom(event)
        else:
            self.fig.canvas.toolbar.press_pan(event)

    def zoom_pan_release(self,event):
        if self.bzoom.isChecked():
            self.fig.canvas.toolbar.release_zoom(event)
        else:
            self.fig.canvas.toolbar.release_pan(event)

        
    def init_plot(self):
        self.fig = Figure()
        self.ax = [None]*len(self.selected)
        self.ax[0] = self.fig.add_subplot(111)
        self.ax[0].xaxis.grid(True, which='major')
        self.ax[0].yaxis.grid(True, which='major')
        for i in range(1,len(self.selected)):
            self.ax[i] = self.ax[0].twinx()
        self.canvas = FigureCanvas(self.fig)
        #self.toolbar = CustomToolbar(self.canvas, self)
        #self.hLayout2.addWidget(self.toolbar,4)

        self.canvas.mpl_connect("button_press_event",self.zoom_pan_press)
        self.canvas.mpl_connect("axes_enter_event",self.zoom_pan_press)
        self.canvas.mpl_connect("button_release_event",self.zoom_pan_release)
        self.canvas.mpl_connect("motion_notify_event",self.zoom_pan)
        toolbar=NavigationToolbar(self.canvas, parent= None)

        self.bhome=QPushButton('',self)
        self.bhome.setIcon(QIcon("./icons/home.png"))
        #self.bhome.setIconSize(QSize(20, 20));
        self.bhome.clicked.connect(self.fig.canvas.toolbar.home)
        self.bzoom=QPushButton('',self)
        self.bzoom.setIcon(QIcon("./icons/magnify-plus-cursor.png"))
        self.bzoom.setCheckable(True)
        self.bzoom.setChecked(True)
        self.bzoom.clicked.connect(self.toggle_zoom)
        self.bpan =QPushButton('',self)
        self.bpan.setIcon(QIcon("./icons/pan.png"))
        self.bpan.setCheckable(True)
        self.bpan.setChecked(False)
        self.bpan.clicked.connect(self.toggle_pan)
        self.bsave=QPushButton('',self)
        self.bsave.setIcon(QIcon("./icons/content-save.png"))
        self.bsave.clicked.connect(self.save_fig)
        
        self.hLayout2.addWidget(self.plot_pushButton)
        self.hLayout2.addWidget(self.bhome)
        self.hLayout2.addWidget(self.bzoom)
        self.hLayout2.addWidget(self.bpan)
        self.hLayout2.addWidget(self.bsave)
        self.hLayout2.addWidget(self.close_pushButton)

        self.gridLayout.addWidget(self.canvas,1,0)        

        self.timer = self.canvas.new_timer(50)
        self.timer.add_callback(self.update_plot)
        
    def set_range(self):
        self.range_dict.update({self.comboBox.currentText():{'ymin':self.min_doubleSpinBox.value(),'ymax':self.max_doubleSpinBox.value()}})

    def set_style(self):
        self.style_dict.update({self.comboBox.currentText():{'c':self.col_comboBox.currentText(),
                                                             'l':self.line_comboBox.currentText(),'m':self.marker_comboBox.currentText()}})

    def toggle_plot(self):
        if self.plot_pushButton.isChecked() and len(self.selected)>0:
            self.xaxes = [np.array([]) for i in range(len(self.selected))]
            self.yaxes = [np.array([]) for i in range(len(self.selected))]
            self.timer.start()
            self.parent().phasescan.start_thread('%s'%self.thread,self.selected,'','',-1)
        elif self.plot_pushButton.isChecked()==False: 
            self.timer.stop()
            self.parent().phasescan.stop_thread('%s'%self.thread)
        elif self.plot_pushButton.isChecked() and len(self.selected)==0:
            self.timer.stop()
            self.parent().phasescan.stop_thread('%s'%self.thread)
            self.plot_pushButton.setChecked(False)
            
    def update_plot(self):
        try:
            buffer = self.parent().phasescan.get_thread_data('%s'%self.thread)
            labels = [s.split('@')[0] for s in self.selected]

            data=[None]*len(labels)
            tstamps=[None]*len(labels)
            for i in range(len(labels)):
                data[i]=[d['data'] for d in buffer if d['name']==labels[i]]
                tstamps[i]=[d['stamp'] for d in buffer if d['name']==labels[i]]

                
            for i,d in enumerate(data):
                self.ax[i].cla()
                if i==0:
                    self.ax[i].xaxis.grid(True, which='major')
                    self.ax[i].yaxis.grid(True, which='major')

                self.ax[i].xaxis_date('US/Central')
                space= space + '  '*len(labels[i-1]) if i>0 else ''
                self.xaxes[i] = np.append(self.xaxes[i],tstamps[i])
                self.yaxes[i] = np.append(self.yaxes[i],d)

                #self.ax[i].yaxis.set_major_locator(MaxNLocator(5))
                if labels[i] not in self.style_dict.keys():
                    self.ax[i].set_title(labels[i]+space,color=self.colors[i],ha='right',fontsize='small')                                
                    self.ax[i].plot(self.xaxes[i],self.yaxes[i],c=self.colors[i],label=labels[i])
                    self.ax[i].tick_params(axis='y', colors=self.colors[i], labelsize='small',rotation=90)

                else:
                    self.ax[i].set_title(labels[i]+space,color=self.style_dict[labels[i]]['c'],ha='right',fontsize='small')                                
                    self.ax[i].plot(self.xaxes[i],self.yaxes[i],c=self.style_dict[labels[i]]['c'], linestyle=self.style_dict[labels[i]]['l'],
                                    marker=self.style_dict[labels[i]]['m'],label=labels[i])
                    self.ax[i].tick_params(axis='y', colors=self.style_dict[labels[i]]['c'], labelsize='small',rotation=90)

                self.ax[i].yaxis.set_major_locator(mt.LinearLocator(5))
                
                if labels[i] in self.range_dict.keys():
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
        #loadUi("expandPlot.ui", self)

        self.setWindowTitle("Bar plot")
        self.resize(930,550)
        
        self.thread = QUuid.createUuid().toString()
        self.selected = selected
        self.first = True

        self.style=style
        self.style_dict={'loss':{'ymin':0,'ymax':5,'ylabel':'Beam Loss (cnt)'},
                         'current':{'ymin':0,'ymax':60,'ylabel':'Beam Current (mA)'}}

        self.eventLabel = QLabel()
        self.eventLabel.setText('%s'%evt)
        self.eventLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        

        self.plot_pushButton=QPushButton('')
        self.plot_pushButton.setIcon(QIcon("./icons/draw.png"))
        self.plot_pushButton.setCheckable(True)
        self.plot_pushButton.clicked.connect(self.toggle_plot)

        self.close_pushButton=QPushButton('')
        self.close_pushButton.setIcon(QIcon("./icons/close.png"))
        self.close_pushButton.clicked.connect(self.close_dialog)
        
        self.hLayout = QHBoxLayout()
        self.hLayout.addWidget(self.eventLabel)

        self.gridLayout = QGridLayout()
        self.gridLayout.addLayout(self.hLayout,1,0)

        self.setLayout(self.gridLayout)

        self.init_plot()

    def close_dialog(self):
        if self.thread in self.parent().phasescan.get_list_of_threads():
            self.parent().phasescan.stop_thread('%s'%self.thread)
        self.timer.stop()
        self.close()

    def closeEvent(self, event):
        self.close_dialog()
        event.accept()

    def save_fig(self,event):
        fout = QFileDialog.getSaveFileName(
            self, "Save Image", "image", "Images (*.png *.jpg *.pdf);; All Files (*.*)") 

        self.fig.savefig(fout[0])

        
    def init_plot(self):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        self.gridLayout.addWidget(self.canvas,0,0)

        self.bhome=QPushButton('',self)
        self.bhome.setIcon(QIcon("./icons/home.png"))
        self.bhome.setDisabled(True)
        #self.bhome.setIconSize(QSize(20, 20));
        self.bzoom=QPushButton('',self)
        self.bzoom.setIcon(QIcon("./icons/magnify-plus-cursor.png"))
        self.bzoom.setDisabled(True)
        self.bpan =QPushButton('',self)
        self.bpan.setIcon(QIcon("./icons/pan.png"))
        self.bpan.setDisabled(True)
        self.bsave=QPushButton('',self)
        self.bsave.setIcon(QIcon("./icons/content-save.png"))
        self.bsave.clicked.connect(self.save_fig)
        
        self.hLayout.addWidget(self.plot_pushButton)
        self.hLayout.addWidget(self.bhome)
        self.hLayout.addWidget(self.bzoom)
        self.hLayout.addWidget(self.bpan)
        self.hLayout.addWidget(self.bsave)
        self.hLayout.addWidget(self.close_pushButton)

        self.timer = self.canvas.new_timer(50)
        self.timer.add_callback(self.update_plot)
        self.first_data = np.zeros(len(self.selected))
        self.data=[None]*len(self.selected)
        
    def toggle_plot(self):
        if self.plot_pushButton.isChecked() and len(self.selected)>0:
            self.timer.start()
            self.parent().phasescan.start_thread('%s'%self.thread,self.selected,'','',-1)
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
            buffer = self.parent().phasescan.get_thread_data('%s'%self.thread)
            devs=[d.split("@")[0] for d in self.selected]
            for d in buffer:
                self.data[devs.index(d['name'])]=d['data']

            if self.data.count(None)>0:
                return None
            
            if self.first:
                self.first_data = self.data.copy()
                self.first=False

            colors = ['green' if abs(self.data[i]) < abs(self.first_data[i]) else 'red' for i in range(len(self.first_data))]
            self.ax.bar([i for i in range(len(self.first_data))],height=np.subtract(self.first_data,self.data),bottom = self.data,alpha=0.99,color=colors)
            self.ax.bar([i for i in range(len(self.data))],height=self.data,alpha=0.5,color='blue')
            labels = [s.split('@')[0] for s in self.selected]
            self.ax.set_xticks([i for i in range(len(self.data))],labels,rotation = 'vertical',fontsize=6)
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
