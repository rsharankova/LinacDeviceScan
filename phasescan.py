import numpy as np
import acsys.dpm

async def apply_settings(con,device_list,value_list,settings_role):
    settings = [None]*len(device_list)
    async with acsys.dpm.DPMContext(con) as dpm:
        await dpm.enable_settings(role=settings_role)
        for i, value in enumerate(device_list):
            await dpm.add_entry(i, value+'@i')
        await dpm.start()
        async for reply in dpm.replies():
            settings[reply.tag]= reply.data + value_list[reply.tag]
            if settings.count(None)==0:
                break

        setpairs = list(enumerate(settings))
        print(setpairs)
        await dpm.apply_settings(setpairs)
        print('settings applied')
        async for reply in dpm.replies(tmo=0.25):
            print(reply)
            break
    return None

async def read_settings(con,drf_list):
    settings = [None]*len(drf_list)
    async with acsys.dpm.DPMContext(con) as dpm:
        for i in range(len(drf_list)):
            await dpm.add_entry(i, drf_list[i]+'@i')
        await dpm.start()
        async for reply in dpm:
            #print(reply)
            settings[reply.tag]=reply.data
            if settings.count(None) ==0:
                break
    return settings

class phasescan:
    def __init__(self):
        self.paramlist = ['Z:CUBE_X','Z:CUBE_Y','Z:CUBE_Z']
        
    def build_device_list(self,devlist):
        drf_list=[]
        for dev in devlist:
            drf = f'{dev}.SETTING'
            drf_list.append(drf)
            
        return drf_list

    def get_phases_once(self,paramlist):
        if paramlist and len(paramlist)!=0:
            drf_list = self.build_device_list(paramlist)
        else:
            print('Device list empty. Reading dummy devices')
            drf_list = self.build_device_list(self.paramlist)
        phases= acsys.run_client(read_settings, drf_list=drf_list) 
        return phases

    def make_ramp_list(self,param_dict,numevents):
        tmplist = []
        done_first_ref=False
        for scanned_dev in param_dict:
            if param_dict[scanned_dev]['selected']==True:
                phase=param_dict[scanned_dev]['phase']
                delta=param_dict[scanned_dev]['delta']
                for pset in list(dict.fromkeys([phase,phase-delta,phase+delta])):
                    if not done_first_ref or phase!=pset:
                        param_dict[scanned_dev]['phase']=pset
                        tmplist.append(sum([[val['device'],val['phase']] for key,val in param_dict.items() if val['selected']==True],['1']))
                        done_first_ref=True
                        param_dict[scanned_dev]['phase']=phase #put back phase to nominal
        ramplist=[]
        for l in tmplist:
            for i in range(numevents):
                ramplist.append(l.copy())
        ramplist[0][0]='0'
        return ramplist
