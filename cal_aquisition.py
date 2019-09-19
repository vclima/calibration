class NoPower(Exception):
	pass

class IterationLimitReached(Exception):
	pass


import calibration_lib as cal
import numpy as np
import time
import epics as ep
from datetime import datetime

step_size=10 #mV
meas_avg=5
stab_time=20

if(not(cal.GEN_check_RF())):
	raise Exception ('Check RF Power and Loop')

starting_power=int(round(cal.PWR_read_LLRF('AmpSP')))
stop_power=20
error=0
line_index=0
pwr_vec=np.arange(starting_power,stop_power-step_size,-step_size)
print(pwr_vec)

while(abs(cal.PWR_read_LLRF('AmpSP')-cal.PWR_read_LLRF('AmpRef'))>0.1):
	print(abs(cal.PWR_read_LLRF('AmpSP')-cal.PWR_read_LLRF('AmpRef')))
	time.sleep(3)

results=np.zeros((len(pwr_vec),31))

j=0
PV_header='BR-RF-DLLRF-01:'
for pwr_lvl in pwr_vec:
	if(not(cal.GEN_check_RF())):
		error=1
		break
	cal.PWR_set_power_mv(pwr_lvl)
	print('Setting power to '+str(pwr_lvl)+' mV')
	time.sleep(1)
	while(abs(cal.PWR_read_LLRF('AmpSP')-cal.PWR_read_LLRF('AmpRef'))>0.1):
		print(abs(cal.PWR_read_LLRF('AmpSP')-cal.PWR_read_LLRF('AmpRef')))
		time.sleep(1)

	print('Waiting stabilization')
	time.sleep(stab_time)
	if(pwr_lvl>30):
		try:
			of=cal.TUN_find_offset()
			ep.caput(PV_header+'DTune-SP',float(of))
			ep.caput(PV_header+'TUNE:S',1)
		except :
			if(not(cal.GEN_check_RF())):
				error=1
				break
			print('Unable to tune, power too low')
	results[j,0]=cal.PWR_read_LLRF('AmpRef')
	for i in range(1,16):
		print('Aquiring CalSys channel RFIn'+str(i))
		results[j,2*(i-1)+1]=cal.PWR_read_LLRF('RFIn'+str(i),avg=meas_avg)
		print('Aquiring LLRF channel RFIn'+str(i))
		results[j,2*(i)]=cal.PWR_read_CalSys('RFIn'+str(i),avg=meas_avg)
	j=j+1


now=datetime.now()
date=now.strftime("%H%M_%d%m%y")
LoopStatus=cal.GEN_check_loop()
setup=['LoopStatus='+str(cal.GEN_check_loop()),'StepSize='+str(step_size),'StartmV='+str(starting_power),'DataSize='+str(len(pwr_vec)),'TimeStamp='+date,'LLRF measurements in mV CalSys in dBm']
header=['AmpRef_LLRF','INRF1_LLRF','INRF1_CalSys','INRF2_LLRF','INRF2_CalSys','INRF3_LLRF','INRF3_CalSys','INRF4_LLRF','INRF4_CalSys','INRF5_LLRF',
'INRF5_CalSys','INRF6_LLRF','INRF6_CalSys','INRF7_LLRF','INRF7_CalSys','INRF8_LLRF','INRF8_CalSys','INRF9_LLRF','INRF9_CalSys','INRF10_LLRF',
'INRF10_CalSys','INRF11_LLRF','INRF11_CalSys','INRF12_LLRF','INRF12_CalSys','INRF13_LLRF','INRF13_CalSys','INRF14_LLRF','INRF14_CalSys','INRF15_LLRF','INRF15_CalSys']


if(error):
	results=results[0:pwr_vec.find(pwr_lvl)-1,:]
	cal.GEN_write_csv(results,date+'_AQS_FAILED.csv',setup)
	raise Exception ('Check RF Power and Loop')

#Corrigir filename
cal.GEN_write_csv(results,date+'_AQS.csv',setup,header)
