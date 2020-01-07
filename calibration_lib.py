import epics as ep
import time
import numpy as np
from math import isnan
import csv
import logging
import threading

direction_sel=1
''' Custom exceptions'''
class NoPower(Exception):
	pass

class IterationLimitReached(Exception):
	pass

g_lock = threading.RLock()
measurements = 0
val = 0

'''General functions'''
def GEN_check_loop():
	LS=ep.caget('SR-RF-DLLRF-01:SL')
	return LS

def GEN_check_RF():
	PS=ep.caget('RA-RaBO01:RF-LLRFPreAmp:PinSw-Mon') #NÃO ACHEI
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
	with g_lock:
		global val
		global measurements
		val.append(value)
		print(pvname, value, measurements)
		measurements += 1

def GEN_dBmtomVp(dbm_value):
	V_value=np.sqrt(10**(dbm_value/10)*0.1)*1000
	return V_value

def GEN_create_LLRF_PVset():
	SR_LLRF_label=['CAV:AMP','FWDCAV:AMP','REVCAV:AMP','MO:AMP','FWDSSA1:AMP','REVSSA1:AMP','CELL2:AMP','CELL6:AMP','FWDSSA2:AMP','REVSSA2:AMP','INPRE1:AMP','FWDPRE1:AMP','INPRE2:AMP','FWDPRE2:AMP','FWDCIRC:AMP','REVCIRC:AMP','SL:REF:AMP','mV:AL:REF','SL:INP:AMP','mV:AMPREF:MIN']
	PV_header='SR-RF-DLLRF-01:'
	pv_names=[PV_header]*len(SR_LLRF_label)
	for i in range(len(SR_LLRF_label)):
		pv_names[i]=pv_names[i]+SR_LLRF_label[i]
	pv_set=[ep.PV(name) for name in pv_names]
	return pv_set

def GEN_create_CalSys_PVset():
	PV_header='RA-RaSIA01:RF-LLRFCalSys:PwrdBm' #CONFERIR
	
	pv_names=[PV_header]*16
	for i in range(16):
		pv_names[i]=pv_names[i]+str(i+1)+'_CALC'
	pv_set=[ep.PV(name) for name in pv_names]
	return pv_set


'''Tunning functions'''

def TUN_set_direction(dir):
	direction=['up','down']
	PLG1='SR-RF-DLLRF-01:TUNE:PLG1:DIR:S'
	PLG2='SR-RF-DLLRF-01:TUNE:PLG2:DIR:S'
	if(direction[dir]=='up'):
		ep.caput(PLG1,1)
		ep.caput(PLG2,1)
	elif(direction[dir]=='down'):
		ep.caput(PLG1,0)
		ep.caput(PLG2,0)
	return 0

def TUN_wait_plunger(dir):
	direction=['up','down']
	PLG1='SR-RF-DLLRF-01:PLG1:MANUAL:'
	PLG2='SR-RF-DLLRF-01:PLG2:MANUAL:'

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
	PV_header='SR-RF-DLLRF-01:TUNE:'
	direction=['up','down']

	ep.caput(PV_header+'PULSE:FREQ:S',speed)
	ep.caput(PV_header+'PULSE:NUM:S',pulses)
	logging.debug('Moving plunger '+direction[dir]+' '+str(pulses)+' pulses')

	TUN_set_direction(dir)
	ep.caput(PV_header+'RESET:S',1)
	time.sleep(0.5)
	ep.caput(PV_header+'RESET:S',0)
	logging.debug('Waiting plunger')
	time.sleep(1.5)
	while(TUN_wait_plunger(dir)):
		time.sleep(1)
	return 0

def TUN_find_offset(ref_threshold=13):
	iterations=0
	pulses=1500
	PV_header='SR-RF-DLLRF-01:'
	global direction_sel
	it_limit=11
	fwd_power=ep.caget('RA-RaSIA01:RF-LLRFCalSys:PwrdBm15-Mon')
	rev_power=ep.caget('RA-RaSIA01:RF-LLRFCalSys:PwrdBm16-Mon')
	diff=fwd_power-rev_power
	print('Ref ratio '+str(diff))
	if(isnan(diff)):
		raise NoPower('No RF power detected')
	print('Tunning...')
	if(diff>ref_threshold):
		offset=ep.caget(PV_header+'DTune-SP')
		dephase=ep.caget(PV_header+'TUNE:DEPHS')
		return dephase+offset

	ep.caput(PV_header+'DTune-SP',0)
	ep.caput(PV_header+'TUNE:S',0)
	while(diff<ref_threshold and iterations<=it_limit):
		TUN_move_plunger(direction_sel,pulses)
		diff_old=diff
		fwd_power=ep.caget('RA-RaSIA01:RF-LLRFCalSys:PwrdBm15-Mon')
		rev_power=ep.caget('RA-RaSIA01:RF-LLRFCalSys:PwrdBm16-Mon')
		diff=fwd_power-rev_power
		print('Ref ratio '+str(diff))
		if(isnan(diff)):
			raise NoPower('No RF power detected')
		if(diff<diff_old):
			direction_sel=not direction_sel
		iterations+=1
		pulses=int(1500+1000*abs(ref_threshold-diff))
	dephase=ep.caget(PV_header+'TUNE:DEPHS')
	if(iterations>it_limit):
		raise IterationLimitReached('Too many iterations')
	print('Dephase: '+str(dephase)+'\n')
	logging.debug('Dephase: '+str(dephase))
	return dephase


'''Power functions'''

def clean_val():
	global val
	with g_lock:
		val=[]

def PWR_read_CalSys(pv_set,var,inf_flag='inf',ofs_flag='noofs',avg='noavg'):
	if(var.startswith('RFIn')):
		RFIn=int(var[4:])
		if(RFIn<1 or RFIn>16):
			raise ValueError('Channel '+str(RFIn)+' does not exist')
	else:
		raise ValueError('Channel '+var+' does not exist')


	pwr_pv=pv_set[RFIn-1]
	if(avg=='noavg'):
		pwr=pwr_pv.get()
		if (pwr<-42 and inf_flag!='noinf'):
			return -np.inf
		if(ofs_flag=='ofs'):
			ofs=ep.caget('RA-RaSIA01:RF-LLRFCalSys:OFSdB'+str(RFIn)+'-Mon')
			return pwr+ofs
		return pwr
	else:
		try:
			avg_size=int(avg)
		except ValueError:
			raise ValueError('Avg parameter is not an integer')
		global val
		global measurements
		clean_val()
		val.append(pwr_pv.get())
		measurements=1
		timeout=1.5*avg_size
		pwr_pv.add_callback(GEN_PV_average)
		start_time=time.perf_counter()
		while measurements<avg_size and time.perf_counter()-start_time<timeout:
			pass
		pwr_pv.clear_callbacks()
		if(measurements<avg_size):
			logging.warning(var+' PWR read timeout:'+str(measurements)+' measurements taken')
		avg=sum(val)/len(val)
		if(avg<-42 and inf_flag!='noinf'):
			return -np.inf
		if(ofs_flag=='ofs'):
			ofs=ep.caget('RA-RaSIA01:RF-LLRFCalSys:OFSdB'+str(RFIn)+'-Mon')
			return avg+ofs
		return avg

def PWR_read_LLRF(pv_set,var,avg='noavg'):

	if(var.startswith('RFIn')):
		RFIn=int(var[4:])
		if(RFIn<1 or RFIn>16):
			raise ValueError('Channel '+str(RFIn)+' does not exist')
	elif(var=='AmpRef'):
		RFIn=17
	elif(var=='AmpSP'):
		RFIn=18
	elif(var=='tst'):
		RFIn=20
	else:
		raise ValueError('Channel '+var+' does not exist')

	pwr_pv=pv_set[RFIn-1]
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
		clean_val()
		val.append(pwr_pv.get())
		measurements=1
		timeout=1.5*avg_size
		pwr_pv.add_callback(GEN_PV_average)
		start_time=time.perf_counter()
		while measurements<avg_size and time.perf_counter()-start_time<timeout:
			pass
		pwr_pv.clear_callbacks()
		if(measurements<avg_size):
			logging.warning(var+' PWR read timeout:'+str(measurements)+' measurements taken')
		avg=sum(val)/len(val)
		return avg

def PWR_read_LLRF_coeff(var,type):
	SR_LLRF_label=['CAV','FWDCAV','REVCAV','MO','FWDSSA1','REVSSA1','CELL2','CELL6','FWDSSA2','REVSSA2','INPRE1','FWDPRE1','INPRE2','FWDPRE2','FWDCIRC','REVCIRC']
	coeff=np.zeros(5)
	if(var.startswith('RFIn')):
		RFIn=int(var[4:])
		if(RFIn<1 or RFIn>16):
			raise ValueError('Channel '+str(RFIn)+' does not exist')
	else:
		raise ValueError('Channel '+var+' does not exist')
	PV_header='SR-RF-DLLRF-01:'
	if(type=='Raw-U'):
		PV_name=PV_header+SR_LLRF_label[RFIn-1]+':Const:Raw-U:'
	elif(type=='U-Raw'):
		PV_name=PV_header+SR_LLRF_label[RFIn-1]+':Const:U-Raw:'
	elif(type=='OLG'):
		PV_name=PV_header+'OLG:'+SR_LLRF_label[RFIn-1]+':Const:'
	else:
		raise ValueError('Type does not exist')
	coeff[0]=ep.caget(PV_name+'C4')
	coeff[1]=ep.caget(PV_name+'C3')
	coeff[2]=ep.caget(PV_name+'C2')
	coeff[3]=ep.caget(PV_name+'C1')
	coeff[4]=ep.caget(PV_name+'C0')
	return coeff

def PWR_set_LLRF_coeff(coef):
	if(not coef.shape==(6,24)):
		raise ValueError ('Wrong coefficient array size')
	PV_header='SR-RF-DLLRF-01:'
	SR_LLRF_label=['CAV','FWDCAV','FWDSSA1','FWDSSA2','CAV','FWDCAV','REVCAV','MO','FWDSSA1','REVSSA1','CELL2','CELL6','FWDSSA2','REVSSA2','INPRE1','FWDPRE1','INPRE2','FWDPRE2','FWDCIRC','REVCIRC','CAV','FWDCAV','FWDSSA1','FWDSSA2']
	j=0
	for i in range(0,24):
		if i<4:
			logging.info('Setting '+SR_LLRF_label[i]+' OLG Coefficients')
			print('Setting '+SR_LLRF_label[i]+' OLG Coefficients')
			PV_name=PV_header+'OLG:'+SR_LLRF_label[i]+':Const:'
			ep.caput(PV_name+'C4:S',coef[0,i])
			ep.caput(PV_name+'C3:S',coef[1,i])
			ep.caput(PV_name+'C2:S',coef[2,i])
			ep.caput(PV_name+'C1:S',coef[3,i])
			ep.caput(PV_name+'C0:S',coef[4,i])
		elif i<20:
			logging.info('Setting '+SR_LLRF_label[i]+' RAW-U Coefficients')
			print('Setting '+SR_LLRF_label[i]+' RAW-U Coefficients')
			PV_name=PV_header+SR_LLRF_label[i]+':Const:Raw-U:'
			ep.caput(PV_name+'C4:S',coef[0,i])
			ep.caput(PV_name+'C3:S',coef[1,i])
			ep.caput(PV_name+'C2:S',coef[2,i])
			ep.caput(PV_name+'C1:S',coef[3,i])
			ep.caput(PV_name+'C0:S',coef[4,i])
			ep.caput(PV_header+SR_LLRF_label[i]+':Const:OFS:S',coef[5,i])
		else:
			logging.info('Setting '+SR_LLRF_label[i]+' U-RAW Coefficients')
			print('Setting '+SR_LLRF_label[i]+' U-RAW Coefficients')
			PV_name=PV_header+SR_LLRF_label[i]+':Const:U-Raw:'
			ep.caput(PV_name+'C4:S',coef[0,i])
			ep.caput(PV_name+'C3:S',coef[1,i])
			ep.caput(PV_name+'C2:S',coef[2,i])
			ep.caput(PV_name+'C1:S',coef[3,i])
			ep.caput(PV_name+'C0:S',coef[4,i])

def PWR_read_LLRF_ofs(var):
	SR_LLRF_label=['CAV','FWDCAV','REVCAV','MO','FWDSSA1','REVSSA1','CELL2','CELL6','FWDSSA2','REVSSA2','INPRE1','FWDPRE1','INPRE2','FWDPRE2','FWDCIRC','REVCIRC']
	if(var.startswith('RFIn')):
		RFIn=int(var[4:])
		if(RFIn<1 or RFIn>16):
			raise ValueError('Channel '+str(RFIn)+' does not exist')
	else:
		raise ValueError('Channel '+var+' does not exist')
	PV_header='BR-RF-DLLRF-01:'
	PV_name=PV_header+SR_LLRF_label[RFIn-1]+':Const:'
	ofs=ep.caget(PV_name+'OFS')
	return ofs

def PWR_set_power_mv(lvl,incrate='1.0'):
	PV_header='SR-RF-DLLRF-01:'
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
		phs=ep.caget('SR-RF-DLLRF-01:SL:INP:PHS')
	elif(var=='PhsSP'):
		phs=ep.caget('SR-RF-DLLRF-01:PL:REF')
	else:
		raise ValueError('Invalid parameter: '+var)

def PHS_set_phase(lvl):

	ep.caput('SR-RF-DLLRF-01:PHSREF:INCRATE:S','2.0')
	if(lvl>=-180 and lvl<=180):
		ep.caput('SR-RF-DLLRF-01:PL:REF:S',lvl)
		return 0
	else:
		raise ValueError('Phase out of range')
