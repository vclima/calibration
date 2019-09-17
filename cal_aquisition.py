import calibration_lib as cal
import numpy as np
import time
from datetime import datetime

step_size=5 #mV
meas_avg=5

if(not(cal.GEN_check_RF())):
	raise Exception ('Check RF Power and Loop')

starting_power=int(round(cal.PWR_read_LLRF('AmpSP')))
stop_power=0
error=0
line_index=0
pwr_vec=range(starting_power,stop_power,-step_size)

while(cal.PWR_read_LLRF('AmpSP')-cal.PWR_read_LLRF('AmpRef')>0.5):
	time.sleep(1)

results=np.zeros((len(pwr_vec),31))

for pwr_lvl in pwr_vec:
	if(not(cal.GEN_check_RF())):
		error=1
		break
	cal.PWR_set_power_mv(pwr_lvl)
	print('Setting power to '+str(pwr_lvl)+' mV')

	while(cal.PWR_read_LLRF('AmpSP')-cal.PWR_read_LLRF('AmpRef')>0.5):
		time.sleep(1)

	print('Waiting stabilization')
	time.sleep(25)
	try:
		of=cal.TUN_find_offset()
	except NoPower:
		if(not(cal.GEN_check_RF())):
			error=1
			break
		print('Unable to tune, power too low')
	except IterationLimitReached:
		if(not(cal.GEN_check_RF())):
			error=1
			break
		print('Unable to tune, power too low')
	results[pwr_vec.find(pwr_lvl),0]=cal.PWR_read_LLRF('AmpRef')
	for i in range(1,16):
		results[pwr_vec.find(pwr_lvl),2*(i-1)+1]=cal.PWR_read_LLRF('RFIn'+str(i),avg=meas_avg])
		results[pwr_vec.find(pwr_lvl),2*(i)]=cal.PWR_read_CalSys('RFIn'+str(i),avg=meas_avg)

now=datetime.now()
date=now.strftime("%H%M_%d%m%y")
LoopStatus=cal.GEN_check_loop()
setup=['LoopStatus='+str(cal.GEN_check_loop()),'StepSize='+str(step_size),'StartmV='+str(starting_power),'DataSize='+str(len(pwr_vec)),'LLRF measurements in mV CalSys in dBm']


if(error):
	results=results[0:pwr_vec.find(pwr_lvl)-1,:]
	cal.GEN_write_csv(results,date+'_FAILED.csv',setup)
	raise Exception ('Check RF Power and Loop')

#Corrigir filename
cal.GEN_write_csv(results,date+'.csv',setup,header)
