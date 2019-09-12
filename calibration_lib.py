import epics as ep
import time
import numpy as np

'''Tunning functions'''

def TUN_set_direction(dir):

	PLG1='BR-RF-DLLRF-01:TUNE:PLG1:DIR:S'
	PLG2='BR-RF-DLLRF-01:TUNE:PLG1:DIR:S'

    if(direction[dir]=='up'):
        ep.caput(PLG1,1)
        ep.caput(PLG2,1)
    elif(direction[dir]=='down'):
        ep.caput(PLG1,0)
        ep.caput(PLG2,0)
    return 0

def TUN_wait_plunger(dir):
	direction=['up','down']
	PLG1='BR-RF-DLLRF-01:TUNE:PLG1:MANUAL:'
	PLG2='BR-RF-DLLRF-01:TUNE:PLG1:MANUAL:'

    if(direction[dir]=='up'):
        if(ep.caget(PLG1+'UP') or ep.caget(PLG2+'UP')):
            return 1
        else:
            return 0
    elif(direction[dir]=='down'):
        if(ep.caget(PLG1+'DN') or ep.caget(PLG2+'DN')):
            return 1
        else:
            return 0

def TUN_move_plunger(dir,pulses):
	speed='2 kHz'
	PV_header='BR-RF-DLLRF-01:TUNE:PULSE:'

    ep.caput(PV_header+'FREQ:S',speed)
    ep.caput(PV_header+'NUM:S',pulses)
	print('Moving plunger '+direction[dir]+' '+str(pulses)+' pulses')

    TUN_set_direction(dir)
    ep.caput(PV_header+'RESET:S',1)
    time.sleep(0.5)
    ep.caput(PV_header+'RESET:S',0)
    print('Waiting plunger')
    time.sleep(1.5)
    while(TUN_wait_plunger(dir)):
        time.sleep(1)
    print('Finished moving')
    return 0

def TUN_find_offset():
    iterations=0
    pulses=1500
	PV_header='BR-RF-DLLRF-01:'
	ref_threshold=27
	direction_sel=1
	it_limit=11

    ep.caput(PV_header+'DTune-SP',0)
    ep.caput(PV_header+'TUNE:S',0)
    fwd_power=PWR_read_calsys(14)
    rev_power=PWR_read_calsys(15)
    diff=fwd_power-rev_power
    print('Ref ratio '+str(diff))
    if(isnan(diff)): #Mudar para exception
        print('Offset not found: no power \n')
        return 'error'
    while(diff<ref_threshold and iterations<=it_limit):
        move_plunger(direction_sel,pulses)
        diff_old=diff
        fwd_power=ep.caget('RA-RaBO01:RF-LLRFCalSys:PwrdBm14-Mon')
	    fwd_power=PWR_read_calsys(14)
	    rev_power=PWR_read_calsys(15)
        diff=fwd_power-rev_power
        print('Ref ratio '+str(diff))
        if(isnan(diff)): #Mudar para exception
            print('Offset not found: no power \n')
            return 'error'
        if(diff<diff_old):
            direction_sel=not direction_sel
        iterations+=1
        pulses=1500+600*abs(ref_threshold-diff)
    dephase=ep.caget(addr+'TUNE:DEPHS')
    if(iterations>it_limit): #Mudar para exception
        print('Offset not found: too many interations \n')
        return 'error'
    else:
        print('Dephase: '+str(dephase)+'\n')
        return dephase


'''Power functions'''

def PWR_read_calsys(RFIn):

	if(RFIn>15 or RFIn<0):
		raise ValueError('Channel '+str(RFIn)+' does not exist')

	PV_header='RA-RaBO01:RF-LLRFCalSys:PwrdBm'
	pwr=ep.caget(PV_header+str(RFIn)+'_CALC')
	if pwr<-42:
		return -np.inf
	return pwr

def PWR_read_LLRF(RFIn):

	if(RFIn>15 or RFIn<0):
		raise ValueError('Channel '+str(RFIn)+' does not exist')

	BO_LLRF_label=['CAV','FWDCAV','REVCAV','MO','FWDSSA1','REVSSA1','CELL2','CELL4','CELL1','CELL5','INPRE','FWDPRE','REVPRE','FWDCIRC','REVCIRC']
	PV_header='BR-RF-DLLRF-01:'

	pwr=ep.caget(PV_header+BO_LLRF_label[RFIn-1]+':AMP')
	return pwr
