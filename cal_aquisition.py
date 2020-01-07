class NoPower(Exception):
	pass

class IterationLimitReached(Exception):
	pass


import calibration_lib as cal
import numpy as np
import time
import epics as ep
from datetime import datetime
import logging

now=datetime.now()
date=now.strftime("%H%M_%d%m%y")
logging.basicConfig(level=logging.DEBUG,filename=date+'.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')



meas_avg=10
stab_time=20

stop_power=int(input('Set stop power:'))
step_size=int(input('Set step size:'))
sint_flag=input('Enable auto-tunning during script?[Y/n]')

aqs_channels=list(range(1,16))

while (True):
	print('Channels being calibrated: '+str(aqs_channels))
	selection=input('Press A to add channel, R to remove channel, S to start\n')
	if (selection=='A'):
		selection=input('Press A to add all channels or type channel #:')
		if (selection=='A'):
			aqs_channels=list(range(1,17))
		else:
			try:
				selection=int(selection)
				if (selection<=16 and selection>0):
					if(not (selection in aqs_channels)):
						aqs_channels.append(selection)
						aqs_channels.sort()
				else:
					print('Undefined chanel')
			except:
				print('Undefined chanel')

	elif (selection=='R'):
		selection=input('Press A to remove all channels or type channel #:')
		if (selection=='A'):
			aqs_channels=[]
		else:
			try:
				selection=int(selection)
				if (selection<=16 and selection>0):
					if(selection in aqs_channels):
						aqs_channels.append(selection)
						aqs_channels.sort()
				else:
					print('Undefined chanel')
			except:
				print('Undefined chanel')
	elif (selection=='S'):
		break

if(not(cal.GEN_check_RF())):
	logging.error('No RF Power')
	raise Exception ('Check RF Power and Loop')

calsys_pv_set=cal.GEN_create_CalSys_PVset()
llrf_pv_set=cal.GEN_create_LLRF_PVset()

starting_power=int(round(cal.PWR_read_LLRF(llrf_pv_set,'AmpSP')))

error=0
line_index=0
pwr_vec=np.arange(starting_power,stop_power-step_size,-step_size)
logging.debug('PWR levels: '+str(pwr_vec))
logging.debug('Channels: '+str(aqs_channels))

while(abs(cal.PWR_read_LLRF(llrf_pv_set,'AmpSP')-cal.PWR_read_LLRF(llrf_pv_set,'AmpRef'))>0.1):
	print(abs(cal.PWR_read_LLRF(llrf_pv_set,'AmpSP')-cal.PWR_read_LLRF(llrf_pv_set,'AmpRef')))
	time.sleep(3)

results=np.zeros((len(pwr_vec),2*len(aqs_channels)+1))

j=0
PV_header='SR-RF-DLLRF-01:'

if(sint_flag=='Y'):
	of=cal.TUN_find_offset(13)
	ep.caput(PV_header+'DTune-SP',float(of))
	ep.caput(PV_header+'TUNE:S',1)



try:
	for pwr_lvl in pwr_vec:
		if(not(cal.GEN_check_RF())):
			error=1
			break
		cal.PWR_set_power_mv(pwr_lvl)
		print('Setting power to '+str(pwr_lvl)+' mV')
		logging.info('Setting power to '+str(pwr_lvl)+' mV')
		time.sleep(1)
		while(abs(cal.PWR_read_LLRF(llrf_pv_set,'AmpSP')-cal.PWR_read_LLRF(llrf_pv_set,'AmpRef'))>0.1):
			logging.debug('PWR diff: '+str(abs(cal.PWR_read_LLRF(llrf_pv_set,'AmpSP')-cal.PWR_read_LLRF(llrf_pv_set,'AmpRef'))))
			time.sleep(1)

		logging.debug('Reached power level')
		print('Waiting stabilization')
		time.sleep(stab_time)
		if(sint_flag=='Y'):
			if(pwr_lvl>35):
				try:
					of=cal.TUN_find_offset(27)
					ep.caput(PV_header+'DTune-SP',float(of))
					ep.caput(PV_header+'TUNE:S',1)
				except :
					logging.exception('Tunning exception')
					if(not(cal.GEN_check_RF())):
						error=1
						break
					print('Unable to tune, power too low')
					logging.warning('Unable to tune, power too low')
		results[j,0]=cal.PWR_read_LLRF(llrf_pv_set,'AmpRef')
		k=1
		for i in aqs_channels:
			print('Aquiring LLRF channel RFIn'+str(i))
			logging.info('Aquiring LLRF channel RFIn'+str(i))
			results[j,2*(k-1)+1]=cal.PWR_read_LLRF(llrf_pv_set,'RFIn'+str(i),avg=meas_avg)
			print('Aquiring CalSys channel RFIn'+str(i))
			logging.info('Aquiring CalSys channel RFIn'+str(i))
			results[j,2*(k)]=cal.PWR_read_CalSys(calsys_pv_set,'RFIn'+str(i),avg=meas_avg)
			k=k+1
		j=j+1
except:
	logging.exception('Unknown exception')
	error=2

ep.caput(PV_header+'TUNE:S',0)
LoopStatus=cal.GEN_check_loop()
setup=['LoopStatus='+str(cal.GEN_check_loop()),'StepSize='+str(step_size),'StartmV='+str(starting_power),'DataSize='+str(len(pwr_vec)),'TimeStamp='+date,'LLRF measurements in mV CalSys in dBm']

header_template=['AmpRef_LLRF','INRF1_LLRF','INRF1_CalSys','INRF2_LLRF','INRF2_CalSys','INRF3_LLRF','INRF3_CalSys','INRF4_LLRF','INRF4_CalSys','INRF5_LLRF',
'INRF5_CalSys','INRF6_LLRF','INRF6_CalSys','INRF7_LLRF','INRF7_CalSys','INRF8_LLRF','INRF8_CalSys','INRF9_LLRF','INRF9_CalSys','INRF10_LLRF',
'INRF10_CalSys','INRF11_LLRF','INRF11_CalSys','INRF12_LLRF','INRF12_CalSys','INRF13_LLRF','INRF13_CalSys','INRF14_LLRF','INRF14_CalSys','INRF15_LLRF','INRF15_CalSys','INRF16_LLRF','INRF16_CalSys']

header=[]
header.append(header_template[0])
for i in aqs_channels:
	header.append(header_template[2*(i-1)+1])
	header.append(header_template[2*i])

if(error):
	results=results[0:j,:]
	cal.GEN_write_csv(results,date+'_AQS_FAILED.csv',setup,header)
	if(error==1):
		logging.error('No RF Power')
		raise Exception ('Check RF Power and Loop')

	else:
		raise Exception ('Unknown exception')


cal.GEN_write_csv(results,date+'_AQS.csv',setup,header)
logging.info('Finised aquisition')
