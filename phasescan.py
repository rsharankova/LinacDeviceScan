import acsys.dpm
import threading
import asyncio
import io
import pandas as pd
from functools import reduce
from urllib.request import urlopen
import re
import sys

async def set_once(con,drf_list,value_list,settings_role):
    settings = [None]*len(drf_list)
    async with acsys.dpm.DPMContext(con) as dpm:
        await dpm.enable_settings(role=settings_role)
        for i, dev in enumerate(drf_list):
            await dpm.add_entry(i, dev+'@i')
        await dpm.start()
        async for reply in dpm.replies():
            if reply.isReading:
                settings[reply.tag]= reply.data + value_list[reply.tag]
            if settings.count(None)==0:
                break

        setpairs = list(enumerate(settings))
        print(setpairs)
        await dpm.apply_settings(setpairs)
        print('settings applied')

    return None


async def set_many(con,thread_context):
    async with acsys.dpm.DPMContext(con) as dpm:
        await dpm.enable_settings(role=thread_context['role'])
        
        await dpm.add_entries(list(enumerate(thread_context['param_list'])))

        await dpm.start()
        print("Start ramp")
        for rr in thread_context['ramp_list']:
            one_data = [None]*len(thread_context['param_list'])
            setpairs = list(enumerate([n for n in rr if isinstance(n,float)]))
            await dpm.apply_settings(setpairs)
        
            async for reply in dpm:
                if thread_context['stop'].is_set():
                    break
                thread_context["pause"].wait()
                if reply.isReading:
                    one_data[reply.tag]= reply.data
                    with thread_context['lock']:
                        #thread_context['data'].append({'tag':reply.tag,'stamp':reply.stamp,'data': reply.data,'name':reply.meta['name']})
                        thread_context['data'].append({'tag':reply.tag,'stamp':reply.stamp,'data': reply.data,
                                                       'name':thread_context['param_list'][reply.tag].split('@')[0]})
                if one_data.count(None)==0:
                    break
        print("Ended ramp")
    return None

async def read_once(con,drf_list):

    settings = [None]*len(drf_list)
    async with acsys.dpm.DPMContext(con) as dpm:
        for i in range(len(drf_list)):
            await dpm.add_entry(i, drf_list[i]+'@i')

            await dpm.start()

        async for reply in dpm:
            settings[reply.tag]=reply.data
            if settings.count(None) ==0:
                break
    return settings

async def read_many(con, thread_context):
    """Read many values from the DPM."""
    async with acsys.dpm.DPMContext(con) as dpm:
        #thread_context['daq_task'] = dpm
        await dpm.add_entries(list(enumerate(thread_context['param_list'])))

        it = int(thread_context['Nmeas'])*len(thread_context['param_list'])
        await dpm.start()
        async for reply in dpm:
            if thread_context['stop'].is_set():
                break
            thread_context["pause"].wait()
            if reply.isReading:
                it = it-1
                with thread_context['lock']:
                    #thread_context['data'].append({'tag':reply.tag,'stamp':reply.stamp,'data': reply.data,'name':reply.meta['name']})
                    thread_context['data'].append({'tag':reply.tag,'stamp':reply.stamp,'data': reply.data,
                                                   'name':thread_context['param_list'][reply.tag].split('@')[0]})
                    if (len(thread_context['data'])>5000000):
                        print("Buffer overflow, deleting",thread_context['data'][0]['name'],thread_context['data'][0]['name'])
                        thread_context['data'].pop(0)
            elif reply.isStatus:
                print(f'Status: {reply}')
            else:
                print(f'Unknown response: {reply}')
            if it==0:
                thread_context['stop'].set()

        print('Ending read_many loop')

class phasescan:
    def __init__(self):
        self.thread_dict = {}

        self.TORs = ['L:ATOR','L:BTOR','L:TO1IN','L:TO3IN','L:TO4IN','L:TO4OUT','L:TO5OUT',
                     'L:D0TOR','L:D1TOR','L:D2TOR','L:D3TOR','L:D4TOR','L:D5TOR','L:D7TOR','L:TORSIS','L:TORSOS','L:TORMDS']
        self.LMs = ['L:D00LM','L:D0VLM','L:D11LM','L:D12LM','L:D13LM','L:D14LM','L:D21LM','L:D22LM','L:D23LM','L:D24LM',
                    'L:D31LM','L:D32LM','L:D33LM','L:D34LM','L:D41LM','L:D42LM','L:D43LM','L:D44LM',
                    'L:D51LM','L:D52LM','L:D53LM','L:D54LM','L:D61LM','L:D62LM','L:D63LM','L:D64LM',
                    'L:D71LM','L:D72LM','L:D73LM','L:D74LM','L:DELM1','L:DELM2','L:DELM3','L:DELM4','L:DELM5','L:DELM7','L:DELM9',]
        
        self.main_dict = {'RFQPAH':{'device':'L:RFQPAH','idx':1,'selected':False,'phase':0,'delta':0,'steps':2},
                          'RFBPAH':{'device':'L:RFBPAH','idx':2,'selected':False,'phase':0,'delta':0,'steps':2},
                          'V1QSET':{'device':'L:V1QSET','idx':3,'selected':False,'phase':0,'delta':0,'steps':2},
                          'V2QSET':{'device':'L:V2QSET','idx':4,'selected':False,'phase':0,'delta':0,'steps':2},
                          'V3QSET':{'device':'L:V3QSET','idx':5,'selected':False,'phase':0,'delta':0,'steps':2},
                          'V4QSET':{'device':'L:V4QSET','idx':6,'selected':False,'phase':0,'delta':0,'steps':2},
                          'V5QSET':{'device':'L:V5QSET','idx':7,'selected':False,'phase':0,'delta':0,'steps':2}}
        self.debug_dict={'Z:CUBE_X':{'device':'Z:CUBE_X','idx':1,'selected':False,'phase':0,'delta':0,'steps':2},
                         'Z:CUBE_Y':{'device':'Z:CUBE_Y','idx':2,'selected':False,'phase':0,'delta':0,'steps':2},
                         'Z:CUBE_Z':{'device':'Z:CUBE_Z','idx':3,'selected':False,'phase':0,'delta':0,'steps':2}}

        self.param_dict=self.main_dict

        self.debug_role='testing'
        self.main_role='linac_daily_rf_tuning'
        self.role=self.main_role

        self.dev_list = self.read_dev_list()
        #self.dev_list = self.TORs+self.LMs
        self.add_400MeV_devs()
                
    def swap_dict(self):
        if self.param_dict==self.main_dict:
            self.param_dict=self.debug_dict
            self.role=self.debug_role
        else:
            self.param_dict=self.main_dict
            self.role=self.main_role

    def read_dev_list(self):
        URL='https://www-bd.fnal.gov/cgi-bin/acl.pl?acl=list/notitle/noheadings+name=L:%+"%nm"'
        dev_list = urlopen(URL).read().decode()
        devfilt=re.compile("^L:[a-zA-Z].*")
        dev_list=[dev.strip() for dev in dev_list.splitlines() if devfilt.match(dev)]

        return dev_list

    def add_400MeV_devs(self):
        bdevs = []
        #quads
        bdevs.append('LAM')
        [bdevs.append('Q%d'%i) for i in range(2,18)]
        #htrims
        bdevs.extend(['HTDEB','HTMV2','HTMH2','HTINJ1','HTINJ2'])
        [bdevs.append('HTQ%d'%i) for i in range (3,14) if i not in [9,10,11]]
        #vtrims
        bdevs.extend(['VTDEB','VTMH22','VTINJ1','VTINJ2'])
        [bdevs.append('VTQ%d'%i) for i in range (3,14) if i not in [9,10,11]]
        #super trims
        bdevs.extend(['STH1','STH2','STV1','STV2'])
        #bends
        bdevs.extend(['MH1','MH2','MV1','MV2'])
        #horiz bpms
        [bdevs.append('HPQ%d'%i) for i in range(1,18) if i!=11]
        #vert bpms
        [bdevs.append('VPQ%d'%i) for i in range(1,18)]
        #phase bpms
        [bdevs.append('BQ%dF'%i) for i in range(1,18)]

        bdevs = ['B:%s'%dev for dev in bdevs]

        self.dev_list.extend(bdevs)
        
    
    def _acnet_daq_scan(self,thread_name):
        event_loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(event_loop)
            if len(self.thread_dict[thread_name]['ramp_list'])==0:
                acsys.run_client(read_many, thread_context=self.thread_dict[thread_name])
            else:
                acsys.run_client(set_many, thread_context=self.thread_dict[thread_name])
        finally:
            event_loop.close()
            self.thread_dict[thread_name]['stop'].set()
            
    def _acnet_daq(self, thread_name):
        """Run the ACNet DAQ."""
        event_loop = asyncio.new_event_loop()

        try:
            asyncio.set_event_loop(event_loop)
            acsys.run_client(read_many, thread_context=self.thread_dict[thread_name])
        finally:
            event_loop.close()

    def get_thread_data(self, thread_name):
        """Get the data from the thread."""
        with self.thread_dict[thread_name]['lock']:
            data=self.thread_dict[thread_name]['data'].copy()
            self.thread_dict[thread_name]['data'].clear()
            return data

    def start_thread(self, thread_name, param_list, ramp_list, role, Nmeas):
        """Start the thread."""
        print('Starting thread', thread_name)
        daq_thread = threading.Thread(
            target=self._acnet_daq_scan,
            args=(thread_name,)
        )

        self.thread_dict[thread_name] = {
            'thread': daq_thread,
            'lock': threading.Lock(),
            'data': [],
            'param_list': param_list,
            'ramp_list':ramp_list,
            'role':role,
            'Nmeas':Nmeas,
            'pause': threading.Event(),
            'stop': threading.Event()
        }
        self.thread_dict[thread_name]['pause'].set() #not paused when set

        daq_thread.start()

    def stop_thread(self, thread_name):
        """Stop the thread."""
        print('Stopping thread', thread_name)
        self.thread_dict[thread_name]['pause'].set() #make sure not paused
        self.thread_dict[thread_name]['stop'].set()
        # Close the DPM context.
        #self.thread_dict[thread_name]['daq_task'].cancel()
        # Clean up the thread.
        self.thread_dict[thread_name]['thread'].join()

    def pause_thread(self,thread_name):
        print("Pause thread",thread_name)
        self.thread_dict[thread_name]['pause'].clear()

    def resume_thread(self,thread_name):
        print("Resume thread",thread_name)
        self.thread_dict[thread_name]['pause'].set()

    def stop_all_threads(self):
        for t in self.thread_dict:
            self.stop_thread(t)

    def get_list_of_threads(self):
        return [key for key in self.thread_dict.keys() if not self.thread_dict[key]['stop'].is_set()]
    
    def build_set_device_list(self,devlist):
        drf_list=[]
        for dev in devlist:
            drf = f'{dev}.SETTING'
            drf_list.append(drf)
            
        return drf_list
    
    def get_settings_once(self,paramlist):
        if paramlist and len(paramlist)!=0:
            drf_list = self.build_set_device_list(paramlist)
        else:
            print('Device list empty')
            drf_list = [self.debug_dict[key]['device'] for key in self.debug_dict]
        phases= acsys.run_client(read_once, drf_list=drf_list) 
        return phases

    def get_readings_once(self,paramlist):
        if paramlist and len(paramlist)!=0:
            drf_list = paramlist
        else:
            print('Device list empty')
            drf_list = [self.debug_dict[key]['device'] for key in self.debug_dict]
        phases= acsys.run_client(read_once, drf_list=drf_list) 
        return phases

    def apply_settings_once(self,paramlist,values):
        if paramlist and len(paramlist)!=0:
            drf_list = self.build_set_device_list(paramlist)
        else:
            print('Device list empty. Reading dummy devices')
            drf_list = self.build_set_device_list(self.paramlist)
        print(drf_list)
        acsys.run_client(set_once, drf_list=drf_list, value_list=values,settings_role='testing') 

    def readList(self,filename):
        try:
            file = io.open(r'%s'%filename)
            lines = file.readlines()
            read_list = []
            for line in lines:
                devs = [dev.strip('\n') for dev in line.split(',') if (dev.find(':')!=-1 or dev.find('_')!=-1) and isinstance(dev,str)] 
                [read_list.append(dev) for dev in devs]

        except:
            read_list = []
            print('Read device list empty')
        return read_list
        

    def fill_write_dataframe(self,data,read_list,filename):
        df = pd.DataFrame.from_records(data)
        devlist = df.name.unique()
        dflist=[]
        for dev in read_list:
            if dev in devlist:
                dfdev= df[df.name==dev][['stamp','data']]
                dfdev['stamp']= pd.to_datetime(dfdev['stamp'])
                dfdev['TS']=dfdev['stamp']
                dfdev.rename(columns={'data':dev, 'TS':'%s Timestamp'%dev},inplace=True)
                dfdev.set_index('stamp').reset_index(drop=False, inplace=True)
                dflist.append(dfdev)        
        
        ddf = reduce(lambda  left,right: pd.merge_asof(left,right,on=['stamp'],direction='nearest',tolerance=pd.Timedelta('10ms')), dflist)
        ddf.drop(columns=['stamp'], inplace=True)
        print( ddf.head() )
        
        #today = date.today().isoformat()
        ddf.to_csv('%s'%(filename),index_label='idx')

    def fill_write_dataframe_oneTS(self,data,read_list,filename):
        df = pd.DataFrame.from_records(data)
        devlist = df.name.unique()
        
        dflist=[]
        for dev in read_list:
            if dev in devlist:
                dfdev= df[df.name==dev][['stamp','data']]
                dfdev['stamp']= pd.to_datetime(dfdev['stamp'])
                dfdev.rename(columns={'data':dev,'stamp':'Time'},inplace=True)
                dfdev.set_index('Time').reset_index(drop=False, inplace=True)
                dflist.append(dfdev)        
        
        ddf = reduce(lambda  left,right: pd.merge_asof(left,right,on=['Time'],direction='nearest',tolerance=pd.Timedelta('10ms')), dflist)
        print( ddf.head() )
        
        #today = date.today().isoformat()
        ddf.to_csv('%s'%(filename),index=False)

    
    def make_ramp_list(self,param_dict,numevents):
        tmplist = []
        devlist=[dev for dev in param_dict if param_dict[dev]['selected']==True]
        tmplist.append(sum([[val['device'],val['phase']] for key,val in param_dict.items() if val['selected']==True],['1']))
        for dev in devlist:
            phase=param_dict[dev]['phase']
            steps= -1 if param_dict[dev]['delta']==0 else param_dict[dev]['steps']

            ramp=[phase-param_dict[dev]['delta']+2*param_dict[dev]['delta']/steps*i for i in range(steps+1)]
            ramp=[val for val in ramp if val!=phase]
            for val in ramp:
                param_dict[dev]['phase']=val
                tmplist.append(sum([[val['device'],val['phase']] for key,val in param_dict.items() if val['selected']==True],['1']))
                param_dict[dev]['phase']=phase

        tmplist.append(sum([[val['device'],val['phase']] for key,val in param_dict.items() if val['selected']==True],['1']))
        ramplist=[]
        for l in tmplist:
            for i in range(numevents):
                ramplist.append(l.copy())
        ramplist[0][0]='0'
        return ramplist
    
    def make_loop_ramp_list(self,param_dict,numevents):
        limits = []
        [limits.append( [val['device'],val['phase'],val['delta'],val['steps']]) for key,val in param_dict.items() if val['selected']==True]
        print(limits)

        ramplist = []
        ramp = [None]*len(limits)
        self.do_loop(len(limits),limits,numevents,ramp,ramplist)

        ramplist.append(sum([[val['device'],val['phase']] for key,val in param_dict.items() if val['selected']==True],['1']))
        ramplist[0][0]='0'
        return ramplist
        
    def do_loop(self,N,limits,numevents,ramp,ramplist):

        if N==0:
            return
        else:
            steps = 0 if limits[N-1][2]==0 else limits[N-1][3]
            for i in range(int(steps+1)):
                ramp[N-1] = limits[N-1][1] - limits[N-1][2] + i*(2*limits[N-1][2]/limits[N-1][3])
                self.do_loop(N-1,limits,numevents,ramp,ramplist)

                line = ['1']
                if (N==1):
                    for j in range(len(ramp)):
                        line.append(limits[N-1+j][0])
                        line.append(ramp[j])

                    for k in range(numevents):
                        ramplist.append(line.copy())

