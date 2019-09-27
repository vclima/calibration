import calibration_lib as cal
import time
import epics as ep
from datetime import datetime
import logging

def GEN_PV_average(pvname=None,value=None,**kws):
	global val
	global measurements
	val.append(value)
	measurements+=1

def create_LLRF_PVset():
	BO_LLRF_label=['CAV:AMP','FWDCAV:AMP','REVCAV:AMP','MO:AMP','FWDSSA1:AMP','REVSSA1:AMP','CELL2:AMP','CELL4:AMP','CELL1:AMP','CELL5:AMP','INPRE:AMP','FWDPRE:AMP','REVPRE:AMP','FWDCIRC:AMP','REVCIRC:AMP','SL:REF:AMP','mV:AL:REF','SL:INP:AMP','mV:AMPREF:MIN']
	PV_header='BR-RF-DLLRF-01:'
	pv_names=[PV_header]*len(BO_LLRF_label)
	for i in range(len(BO_LLRF_label)):
		pv_names[i]=pv_names[i]+BO_LLRF_label[i]
	pv_set=[ep.PV(name) for name in pv_names]
	return pv_set

def create_CalSys_PVset():
	PV_header='RA-RaBO01:RF-LLRFCalSys:PwrdBm'
	
	pv_names=[PV_header]*15
	for i in range(15):
		pv_names[i]=pv_names[i]+str(i+1)+'_CALC'
	pv_set=[ep.PV(name) for name in pv_names]
	return pv_set



def alt_read_LLRF(pv_set,var,avg='noavg'):

	if(var.startswith('RFIn')):
		RFIn=int(var[4:])
		if(RFIn<1 or RFIn>15):
			raise ValueError('Channel '+str(RFIn)+' does not exist')
	elif(var=='AmpRef'):
		RFIn=16
	elif(var=='AmpSP'):
		RFIn=17
	elif(var=='tst'):
		RFIn=19
	else:
		raise ValueError('Channel '+var+' does not exist')

	pwr_pv=pv_set[RFIn-1]
	logging.debug('Reading pv'+str(pwr_pv))
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

def alt_read_CalSys(pv_set,var,inf_flag='inf',ofs_flag='noofs',avg='noavg'):
	if(var.startswith('RFIn')):
		RFIn=int(var[4:])
		if(RFIn<1 or RFIn>15):
			raise ValueError('Channel '+str(RFIn)+' does not exist')
	else:
		raise ValueError('Channel '+var+' does not exist')

	
	pwr_pv=pv_set[RFIn-1]
	logging.debug('Reading pv'+str(pwr_pv))
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
			ofs=ep.caget('RA-RaBO01:RF-LLRFCalSys:OFSdB'+str(RFIn)+'-Mon')
			return avg+ofs
		return avg


meas_avg=10

now=datetime.now()
date=now.strftime("%H%M_%d%m%y")
logging.basicConfig(level=logging.DEBUG,filename=date+'_test.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')

while(1):
	test_type=input('Test type:')
	while(1):
		if(test_type==1):
			for i in range(1,16):
				print('Aquiring LLRF channel RFIn'+str(i))
				logging.info('Aquiring LLRF channel RFIn'+str(i))
				cal.PWR_read_LLRF('RFIn'+str(i),avg=meas_avg)
				print('Aquiring CalSys channel RFIn'+str(i))
				logging.info('Aquiring CalSys channel RFIn'+str(i))
				cal.PWR_read_CalSys('RFIn'+str(i),avg=meas_avg)
		else:
			calsys_pv_set=create_CalSys_PVset()
			llrf_pv_set=create_LLRF_PVset()
			for i in range(1,16):
				print('Aquiring LLRF channel RFIn'+str(i))
				logging.info('Aquiring LLRF channel RFIn'+str(i))
				alt_read_LLRF(llrf_pv_set,'RFIn'+str(i),avg=meas_avg)
				print('Aquiring CalSys channel RFIn'+str(i))
				logging.info('Aquiring CalSys channel RFIn'+str(i))
				alt_read_CalSys(calsys_pv_set,'RFIn'+str(i),avg=meas_avg)



