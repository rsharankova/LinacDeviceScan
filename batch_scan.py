from phasescan import phasescan
import argparse
import os
#import pandas as pd

def parse_args():

    parser = argparse.ArgumentParser(description="usage: %prog [options] \n")
    parser.add_argument ('--r',  dest='readfile', default='Reading_devices.csv',
                         help="Reading devices list file name. (default: Reading_devices.csv")
    parser.add_argument ('--N', dest='Nmeas', type=float, default=1,
                         help="Number of measurements to record")
    parser.add_argument ('--e',  dest='event', default='',
                         help="DAQ event")
    parser.add_argument ('--o',  dest='outfile', default='devicescan.csv',
                         help="Name of scan output file. (default: devicescan.csv)")

    options = parser.parse_args()
    readfile= options.readfile
    Nmeas   = options.Nmeas
    event   = options.event
    outfile = options.outfile

    return readfile,Nmeas,event,outfile


def main():

    ps = phasescan()
    pwd = os.getcwd()
    readfile,Nmeas,event,outfile = parse_args()

    readfile  =   os.path.join(pwd,readfile)
    outfile   =   os.path.join(pwd,outfile)
    
    read_list = ps.readList(readfile)

    drf_list = ['%s@%s'%(l,event) for l in read_list if len(read_list)!=0]
    
    ramplist = []
    thread = 'scanner'

    timeout = 3540 #59 min
    
    try:
        ps.start_thread('%s'%thread,timeout,drf_list,ramplist,ps.role,Nmeas)
        
    except Exception as e:
        print('Scan failed',e)


    scanresults = []
    while len(ps.get_list_of_threads())>0:
        scanresults.extend(ps.get_thread_data('%s'%thread))
    try:
        ps.fill_write_dataframe_oneTS(scanresults,read_list,outfile)
    except Exception as e:
        print('Something went wrong',e)


if __name__ == "__main__":
    main()

        
