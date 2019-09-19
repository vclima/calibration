import epics as ep
import time
import numpy as np
from math import isnan
import csv

direction_sel=1
''' Custom exceptions'''
class NoPower(Exception):
	pass

class IterationLimitReached(Exception):
	pass

'''General functions'''
def GEN_check_loop():
	LS=ep.caget('BR-RF-DLLRF-01:SL')
	return LS

def GEN_check_RF():
	PS=ep.caget('RA-RaBO01:RF-LLRFPreAmp:PinSw-Mon')
	return PS

def GEN_write_csv(list,file,setup=None,header=None):
	if (file.find('.csv')>0):
		with open (file,mode='w') as csv_file:
			writer=csv.writer(csv_file,delimiter=',',quotechar='"',quoting=csv.QUOTE_MINIMAL)
			if(setup):
				writer.writerow(setup)
			if(header):
				writer.writerow(header)
			for i in range(0,list.shape[0]):
				writer.writerow(list[i,:])
	else:
		raise ValueError('Invalid file extension')
	return

def GEN_PV_average(pvname=None,value=None,**kws):
	global val
	global measurements
	val.append(value)
	measurements+=1

def GEN_dBmtoVrms(dbm_value):
	V_value=np.sqrt(10**(dbm_value/10)*0.05)
	return V_value


'''Tunning functions'''

def TUN_set_direction(dir):
	direction=['up','down']
	PLG1='BR-RF-DLLRF-01:TUNE:PLG1:DIR:S'
	PLG2='BR-RF-DLLRF-01:TUNE:PLG2:DIR:S'
	if(direction[dir]=='up'):
		ep.caput(PLG1,1)
		ep.caput(PLG2,1)
	elif(direction[dir]=='down'):
		ep.caput(PLG1,0)
		ep.caput(PLG2,0)
	return 0

def TUN_wait_plunger(dir):
	direction=['up','down']
	PLG1='BR-RF-DLLRF-01:PLG1:MANUAL:'
	PLG2='BR-RF-DLLRF-01:PLG2:MANUAL:'

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
	PV_header='BR-RF-DLLRF-01:TUNE:'
	direction=['up','down']

	ep.caput(PV_header+'PULSE:FREQ:S',speed)
	ep.caput(PV_header+'PULSE:NUM:S',pulses)
	print('Moving plunger '+direction[dir]+' '+str(pulses)+' pulses')

	TUN_set_direction(dir)
	ep.caput(PV_header+'RESET:S',1)
	time.sleep(0.5)
	ep.caput(PV_header+'RESET:S',0)
	print('Waiting plunger')
	time.sleep(1.5)
	while(TUN_wait_plunger(dir)):
		time.sleep(1)
	return 0

def TUN_find_offset():
	iterations=0
	pulses=1500
	PV_header='BR-RF-DLLRF-01:'
	ref_threshold=20
	global direction_sel
	it_limit=11

	ep.caput(PV_header+'DTune-SP',0)
	ep.caput(PV_header+'TUNE:S',0)
	fwd_power=PWR_read_CalSys('RFIn14',ofs_flag='ofs')
	rev_power=PWR_read_CalSys('RFIn15',ofs_flag='ofs')
	diff=fwd_power-rev_power
	print('Ref ratio '+str(diff))
	if(isnan(diff)):
		raise NoPower('No RF power detected')
	while(diff<ref_threshold and iterations<=it_limit):
		TUN_move_plunger(direction_sel,pulses)
		diff_old=diff
		fwd_power=PWR_read_CalSys('RFIn14',ofs_flag='ofs')
		rev_power=PWR_read_CalSys('RFIn15',ofs_flag='ofs')
		diff=fwd_power-rev_power
		print('Ref ratio '+str(diff))
		if(isnan(diff)):
			raise NoPower('No RF power detected')
		if(diff<diff_old):
			direction_sel=not direction_sel
		iterations+=1
		pulses=1500+1000*abs(ref_threshold-diff)
	dephase=ep.caget(PV_header+'TUNE:DEPHS')
	if(iterations>it_limit):
		raise IterationLimitReached('Too many iterations')
	print('Dephase: '+str(dephase)+'\n')
	return dephase


'''Power functions'''

def PWR_read_CalSys(var,inf_flag='inf',ofs_flag='noofs',avg='noavg'):
	if(var.startswith('RFIn')):
		RFIn=int(var[4:])
		if(RFIn<1 or RFIn>15):
			raise ValueError('Channel '+str(RFIn)+' does not exist')
	else:
		raise ValueError('Channel '+var+' does not exist')

	PV_header='RA-RaBO01:RF-LLRFCalSys:PwrdBm'
	pwr_pv=ep.PV(PV_header+str(RFIn)+'_CALC')
	if(avg=='noavg'):
		pwr=pwr_pv.get()
		if (pwr<-42 and inf_flag!='noinf'):
			return -np.inf
		if(ofs_flag=='ofs'):
			ofs=ep.caget('RA-RaBO01:RF-LLRFCalSys:OFSdB'+str(RFIn)+'-Mon')
			return pwr+ofs
		return pwr
	else:
		try:
			avg_size=int(avg)
		except ValueError:
			raise ValueError('Avg parameter is not an integer')
		global val
		global measurements
		val=[]
		measurements=0
		pwr_pv.add_callback(GEN_PV_average)
		while measurements<avg_size:
			pass
		pwr_pv.clear_callbacks()
		avg=sum(val)/avg_size
		if(avg<-42 and inf_flag!='noinf'):
			return -np.inf
		if(ofs_flag=='ofs'):
			ofs=ep.caget('RA-RaBO01:RF-LLRFCalSys:OFSdB'+str(RFIn)+'-Mon')
			return avg+ofs
		return avg

def PWR_read_LLRF(var,avg='noavg'):

	if(var.startswith('RFIn')):
		RFIn=int(var[4:])
		if(RFIn<1 or RFIn>15):
			raise ValueError('Channel '+str(RFIn)+' does not exist')
	elif(var=='AmpRef'):
		RFIn=16
	elif(var=='AmpSP'):
		RFIn=17
	else:
		raise ValueError('Channel '+var+' does not exist')

	BO_LLRF_label=['CAV:AMP','FWDCAV:AMP','REVCAV:AMP','MO:AMP','FWDSSA1:AMP','REVSSA1:AMP','CELL2:AMP','CELL4:AMP','CELL1:AMP','CELL5:AMP','INPRE:AMP','FWDPRE:AMP','REVPRE:AMP','FWDCIRC:AMP','REVCIRC:AMP','SL:REF:AMP','mV:AL:REF','SL:INP:AMP']
	PV_header='BR-RF-DLLRF-01:'

	pwr_pv=ep.PV(PV_header+BO_LLRF_label[RFIn-1])
	if(avg=='noavg'):
		pwr=pwr_pv.get()
		return pwr
	else:
		try:
			avg_size=int(avg)
		except ValueError:
			raise ValueError('Avg parameter is not an integer')
		global val
		global measurements
		val=[]
		measurements=0
		pwr_pv.add_callback(GEN_PV_average)
		while measurements<avg_size:
			pass
		pwr_pv.clear_callbacks()
		avg=sum(val)/avg_size
		return avg

def PWR_read_LLRF_coeff(var,type):
	BO_LLRF_label=['CAV','FWDCAV','REVCAV','MO','FWDSSA1','REVSSA1','CELL2','CELL4','CELL1','CELL5','INPRE','FWDPRE','REVPRE','FWDCIRC','REVCIRC']
	coeff=np.zeros(5)
	if(var.startswith('RFIn')):
		RFIn=int(var[4:])
		if(RFIn<1 or RFIn>15):
			raise ValueError('Channel '+str(RFIn)+' does not exist')
	else:
		raise ValueError('Channel '+var+' does not exist')
	PV_header='BR-RF-DLLRF-01:'
	if(type=='Raw-U'):
		PV_name=PV_header+BO_LLRF_label[RFIn-1]+':Const:Raw-U:'
	elif(type=='U-Raw'):
		PV_name=PV_header+BO_LLRF_label[RFIn-1]+':Const:U-Raw:'
	elif(type=='OLG'):
		PV_name=PV_header+'OLG:'+BO_LLRF_label[RFIn-1]+':Const:'
	else:
		raise ValueError('Type does not exist')
	coeff[0]=ep.caget(PV_name+'C4')
	coeff[1]=ep.caget(PV_name+'C3')
	coeff[2]=ep.caget(PV_name+'C2')
	coeff[3]=ep.caget(PV_name+'C1')
	coeff[4]=ep.caget(PV_name+'C0')
	return coeff

def PWR_read_LLRF_ofs(var):
	BO_LLRF_label=['CAV','FWDCAV','REVCAV','MO','FWDSSA1','REVSSA1','CELL2','CELL4','CELL1','CELL5','INPRE','FWDPRE','REVPRE','FWDCIRC','REVCIRC']
	if(var.startswith('RFIn')):
		RFIn=int(var[4:])
		if(RFIn<1 or RFIn>15):
			raise ValueError('Channel '+str(RFIn)+' does not exist')
	else:
		raise ValueError('Channel '+var+' does not exist')
	PV_header='BR-RF-DLLRF-01:'
	PV_name=PV_header+BO_LLRF_label[RFIn-1]+':Const:'
	ofs=ep.caget(PV_name+'OFS')
	return ofs

def PWR_set_power_mv(lvl,incrate='1.0'):
	PV_header='BR-RF-DLLRF-01:'
	values=['0.01','0.03','0.1','0.25','0.5','1.0','2.0','Immediately']
	if incrate in values:
		ep.caput(PV_header+'AMPREF:INCRATE:S',incrate)
	else:
		raise ValueError('Invalid increase rate')
	if lvl<=ep.caget(PV_header+'mV:AL:REF:S.DRVH'):
		ep.caput(PV_header+'mV:AL:REF:S',lvl)
	else:
		raise ValueError('mV value above maximum')
	return 0


'''Phase functions'''

def PHS_read(var):
	if(var=='PhsIn'):
		phs=ep.caget('BR-RF-DLLRF-01:SL:INP:PHS')
	elif(var=='PhsSP'):
		phs=ep.caget('BR-RF-DLLRF-01:PL:REF')
	else:
		raise ValueError('Invalid parameter: '+var)

def PHS_set_phase(lvl):

	ep.caput('BR-RF-DLLRF-01:PHSREF:INCRATE:S','2.0')
	if(lvl>=-180 and lvl<=180):
		ep.caput('BR-RF-DLLRF-01:PL:REF:S',lvl)
		return 0
	else:
		raise ValueError('Phase out of range')
