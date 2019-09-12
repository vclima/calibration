import epics as ep
import time
from math import isnan
import csv
import numpy as np

addr='BR-RF-DLLRF-01:'
pulses=1500
speed='2 kHz'
direction=['up','down']
ref_threshold=27
direction_sel=1
it_limit=11

def set_direction(dir):
    if(direction[dir]=='up'):
        ep.caput(addr+'TUNE:PLG1:DIR:S',1)
        ep.caput(addr+'TUNE:PLG2:DIR:S',1)
    elif(direction[dir]=='down'):
        ep.caput(addr+'TUNE:PLG1:DIR:S',0)
        ep.caput(addr+'TUNE:PLG2:DIR:S',0)
    return 0



def wait_plunger(dir):
    if(direction[dir]=='up'):
        if(ep.caget(addr+'PLG1:MANUAL:UP') or ep.caget(addr+'PLG1:MANUAL:UP')):
            return 1
        else:
            return 0
    elif(direction[dir]=='down'):
        if(ep.caget(addr+'PLG1:MANUAL:DN') or ep.caget(addr+'PLG1:MANUAL:DN')):
            return 1
        else:
            return 0

def move_plunger(dir):
    ep.caput(addr+'TUNE:PULSE:FREQ:S',speed)
    ep.caput(addr+'TUNE:PULSE:NUM:S',pulses)

    print('Moving plunger '+direction[dir]+' '+str(pulses)+' pulses')
    set_direction(dir)
    ep.caput(addr+'TUNE:RESET:S',1)
    time.sleep(0.5)
    ep.caput(addr+'TUNE:RESET:S',0)
    print('Waiting plunger')
    time.sleep(1.5)
    while(wait_plunger(dir)):
        time.sleep(1)
    print('Finished moving')
    return 0



def find_offset():
    iterations=0
    global direction_sel
    global pulses
    pulses=1500
    ep.caput(addr+'DTune-SP',0)
    ep.caput(addr+'TUNE:S',0)
    fwd_power=ep.caget('RA-RaBO01:RF-LLRFCalSys:PwrdBm14-Mon')
    rev_power=ep.caget('RA-RaBO01:RF-LLRFCalSys:PwrdBm15-Mon')
    diff=fwd_power-rev_power
    print('Ref ratio '+str(diff))
    if(isnan(diff)):
        print('Offset not found: no power \n')
        return 'error'
    while(diff<ref_threshold and iterations<=it_limit):
        move_plunger(direction_sel)
        diff_old=diff
        fwd_power=ep.caget('RA-RaBO01:RF-LLRFCalSys:PwrdBm14-Mon')
        rev_power=ep.caget('RA-RaBO01:RF-LLRFCalSys:PwrdBm15-Mon')
        diff=fwd_power-rev_power
        print('Ref ratio '+str(diff))
        if(isnan(diff)):
            print('Offset not found: no power \n')
            return 'error'
        if(diff<diff_old):
            direction_sel=not direction_sel
        iterations+=1
        pulses=1500+600*abs(ref_threshold-diff)
    dephase=ep.caget(addr+'TUNE:DEPHS')
    if(iterations>it_limit):
        print('Offset not found: too many interations \n')
        return 'error'
    else:
        print('Dephase: '+str(dephase)+'\n')
        return dephase

phase=np.arange(5,360,10)
result=np.zeros([phase.size,3])
success=0
ep.caput(addr+'PHSREF:INCRATE:S','2.0')
while(ep.caget(addr+'SL')==1 and ep.caget('RA-RaBO01:RF-LLRFPreAmp:PinSw-Mon')):
    for i in range(0,phase.size):
        ep.caput(addr+'PL:REF:S',phase[i])
        time.sleep(1)
        if(not(ep.caget(addr+'SL')==1 and ep.caget('RA-RaBO01:RF-LLRFPreAmp:PinSw-Mon'))):
            break
        pwr=round(ep.caget(addr+'AL:REF:dBm'))
        print('Phase: '+str(phase[i])+' Pwr: '+str(pwr))
        print('Waiting phase loop')
        while(abs(ep.caget(addr+'SL:INP:PHS')-ep.caget(addr+'PL:REF'))>0.1):
            time.sleep(1)
        tune_dephase=find_offset()
        if (type(tune_dephase)==float):
            result[i,0]=pwr
            result[i,1]=phase[i]
            result[i,2]=tune_dephase
        else:
            result[i,0]=pwr
            result[i,1]=phase[i]
            result[i,2]=np.nan

    with open ('out.csv',mode='w') as csv_file:
        writer=csv.writer(csv_file,delimiter=',',quotechar='"',quoting=csv.QUOTE_MINIMAL)
        for i in range(0,result.shape[0]):
            writer.writerow(result[i,:])
    success=1
    break

if(success==1):
    print('Scan ended')
else:
    print('Scan terminated: control loop not enabled')
