import acsys.dpm
import threading
import asyncio

async def set_once(con,drf_list,value_list,settings_role):
    settings = [None]*len(drf_list)
    async with acsys.dpm.DPMContext(con) as dpm:
        await dpm.enable_settings(role=settings_role)
        for i, dev in enumerate(drf_list):
            await dpm.add_entry(i, dev+'@i')
        await dpm.start()
        async for reply in dpm.replies():
            if reply.isReadingFor(*list(range(0, len(drf_list)))):
                settings[reply.tag]= reply.data + value_list[reply.tag]
            if settings.count(None)==0:
                break

        setpairs = list(enumerate(settings))
        print(setpairs)
        await dpm.apply_settings(setpairs)
        print('settings applied')

    return None


async def set_many(con,ramp_list,evt,settings_role):
    async with acsys.dpm.DPMContext(con) as dpm:
        await dpm.enable_settings(role=settings_role)

        drf_list = [s for s in ramp_list[0] if str(s).find(':')!=-1]

        drf_list=['%s%s'%(l,evt) for l in drf_list]
        for i, dev in enumerate(drf_list):
            await dpm.add_entry(i, dev)

        await dpm.start()
        ii=0
        async for evt_res in dpm:
            if evt_res.isReadingFor(0):
                print('0 ',evt_res)
                vals = [n for n in ramp_list[ii] if isinstance(n,float)]
                setpairs = list(enumerate(vals))
                await dpm.apply_settings(setpairs[1:])
                ii = ii+1

            elif evt_res.isReadingFor(*list(range(0, len(drf_list)))):
                print('other ',evt_res)
            if ii>=min(5,len(ramp_list)):
                break
                
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

async def read_many(con,dict):
    async with acsys.dpm.DPMContext(con) as dpm:
        await dpm.add_entries(list(enumerate(dict['paramlist'])))

        await dpm.start()

        async for evt_res in dpm:
            if isinstance(evt_res,acsys.dpm.ItemData):
                dict['data'][evt_res.tag]=evt_res.data
                if not dict['run_daq']:
                        break
            else:
                print(f'Status: {evt_res}')

        print("Ending read_many loop")

'''
async def read_many(con, thread_context):
    """Read many values from the DPM."""
    async with acsys.dpm.DPMContext(con) as dpm:
        # Add our async context to the thread context.
        # This allows us to close the DPM context when
        # the thread exits without a flag.
        thread_context['daq_task'] = dpm

        await dpm.add_entries(list(enumerate(thread_context['paramlist'])))

        await dpm.start()

        async for evt_res in dpm:
            #if evt_res.isReading:
            if isinstance(evt_res,acsys.dpm.ItemData):
                # We must have a lock before we can write data, otherwise the
                # data could be read at the same time.
                with thread_context['lock']:
                    thread_context['data'][evt_res.tag] = evt_res.data
            #elif evt_res.isStatus:
            elif isinstance(evt_res,acsys.dpm.ItemStatus):
                print(f'Status: {evt_res}')
            else:
                print(f'Unknown response: {evt_res}')

        print('Ending read_many loop')
'''

class phasescan:
    def __init__(self):
        self.thread_dict = {}
        self.thread_lock=threading.Lock()

        self.main_dict = {'RFQ':{'device':'L:RFQPAH','idx':1,'selected':False,'phase':0,'delta':0,'steps':2},
                           'RFB':{'device':'L:RFBPAH','idx':2,'selected':False,'phase':0,'delta':0,'steps':2},
                           'Tank 1':{'device':'L:V1QSET','idx':3,'selected':False,'phase':0,'delta':0,'steps':2},
                           'Tank 2':{'device':'L:V2QSET','idx':4,'selected':False,'phase':0,'delta':0,'steps':2},
                           'Tank 3':{'device':'L:V3QSET','idx':5,'selected':False,'phase':0,'delta':0,'steps':2},
                           'Tank 4':{'device':'L:V4QSET','idx':6,'selected':False,'phase':0,'delta':0,'steps':2},
                           'Tank 5':{'device':'L:V5QSET','idx':7,'selected':False,'phase':0,'delta':0,'steps':2}}
        self.debug_dict={'Z:CUBE_X':{'device':'Z:CUBE_X','idx':1,'selected':False,'phase':0,'delta':0,'steps':2},
                         'Z:CUBE_Y':{'device':'Z:CUBE_Y','idx':2,'selected':False,'phase':0,'delta':0,'steps':2},
                         'Z:CUBE_Z':{'device':'Z:CUBE_Z','idx':3,'selected':False,'phase':0,'delta':0,'steps':2}}

        self.param_dict=self.main_dict
        
    def swap_dict(self):
        if self.param_dict==self.main_dict:
            self.param_dict=self.debug_dict
        else:
            self.param_dict=self.main_dict

    '''
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
            return self.thread_dict[thread_name]['data'].copy()

    def start_thread(self, thread_name, param_list):
        """Start the thread."""
        print('Starting thread', thread_name)
        daq_thread = threading.Thread(
            target=self._acnet_daq,
            args=(thread_name,)
        )

        self.thread_dict[thread_name] = {
            'thread': daq_thread,
            'lock': threading.Lock(),
            'data': [None]*len(param_list),
            'paramlist': param_list
        }

        daq_thread.start()

    def stop_thread(self, thread_name):
        """Stop the thread."""
        print('Stopping thread', thread_name)

        # Close the DPM context.
        #self.thread_dict[thread_name]['daq_task'].cancel()
        # Clean up the thread.
        self.thread_dict[thread_name]['thread'].join()
    '''

            
    def acnet_daq(self,thread_name):
        thread_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(thread_loop)

        acsys.run_client(read_many, dict=self.thread_dict[thread_name])

        thread_loop.close()
        print("Stopping thread ",thread_name)
        
    def get_thread_data(self,thread_name):
        with self.thread_lock:
            return self.thread_dict[thread_name]['data']


    def start_thread(self,thread_name,paramlist):
        print('Starting thread', thread_name)
        daqthread = threading.Thread(target=self.acnet_daq, args=(thread_name,))
        self.thread_dict[thread_name]={'run_daq':True, 'thread': daqthread, 'data':[None]*len(paramlist), 'paramlist':paramlist}
        daqthread.start()
    
    def stop_thread(self,thread_name):
        self.thread_dict[thread_name]['run_daq']=False
        self.thread_dict[thread_name]['thread'].join()
    
    def stop_all_threads(self):
        for t in self.thread_dict:
            self.stop_thread(t)

    def get_list_of_threads(self):
        return self.thread_dict.keys()
    
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

    def apply_settings(self,ramplist,evt):
        acsys.run_client(set_many, ramp_list=ramplist,evt=evt,settings_role='testing') 

    
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
                
        ramplist=[]
        for l in tmplist:
            for i in range(numevents):
                ramplist.append(l.copy())
        ramplist[0][0]='0'
        return ramplist
    
    def make_loop_ramp_list(self,param_dict,numevents):
        limits = []
        for dev in param_dict:
            if param_dict[dev]['selected']==True:
                limits.append([param_dict[dev]['device'],param_dict[dev]['phase'],param_dict[dev]['delta'],param_dict[dev]['steps']])
        print(limits)

        ramplist = []
        ramp = [None]*len(limits)
        self.do_loop(len(limits),limits,numevents,ramp,ramplist)

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

