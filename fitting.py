import csv
import numpy as np
import calibration_lib as cal
import matplotlib.pyplot as plt

csv_name='1547_250919_AQS.csv'

header_template=header=['AmpRef_LLRF','INRF1_LLRF','INRF1_CalSys','INRF2_LLRF','INRF2_CalSys','INRF3_LLRF','INRF3_CalSys','INRF4_LLRF','INRF4_CalSys','INRF5_LLRF',
'INRF5_CalSys','INRF6_LLRF','INRF6_CalSys','INRF7_LLRF','INRF7_CalSys','INRF8_LLRF','INRF8_CalSys','INRF9_LLRF','INRF9_CalSys','INRF10_LLRF',
'INRF10_CalSys','INRF11_LLRF','INRF11_CalSys','INRF12_LLRF','INRF12_CalSys','INRF13_LLRF','INRF13_CalSys','INRF14_LLRF','INRF14_CalSys','INRF15_LLRF','INRF15_CalSys']
BO_LLRF_label=['CAV:AMP','FWDCAV:AMP','REVCAV:AMP','MO:AMP','FWDSSA1:AMP','REVSSA1:AMP','CELL2:AMP','CELL4:AMP','CELL1:AMP','CELL5:AMP','INPRE:AMP','FWDPRE:AMP','REVPRE:AMP','FWDCIRC:AMP','REVCIRC:AMP','SL:REF:AMP','mV:AL:REF','SL:INP:AMP','mV:AMPREF:MIN']

with open(csv_name) as csvfile:
	csvfile = csv.reader(csvfile, delimiter=',', quotechar='"')
	line_count=0
	for row in csvfile:
		if line_count==0:
			setup=row
			DataSize=int(setup[3][9:])
			TimeStamp=setup[4][10:]
			LS=int(setup[0][11:])
			line_count+=1
		elif line_count==1:
			header=row
			ColsSize=len(header)
			data=np.zeros((DataSize,ColsSize))
			line_count+=1
		else:
			data[line_count-2,:]=row
			line_count+=1

coeff_Raw_U=np.zeros((5,15))
coeff_U_Raw=np.zeros((5,3))
olg_coeff=np.zeros((5,3))
range_length=int(ColsSize/2)+1

olg_cols=[0,1,4]
if (LS==1):
	print('Open loop gain can\'t be fitted with closed-loop run')
	j=0
	for k in olg_cols:
		olg_old=cal.PWR_read_LLRF_coeff('RFIn'+str(k+1),'OLG')
		olg_coeff[:,j]=olg_old
		j=j+1
else:
	d1=data[:,0]
	j=0
	for k in olg_cols:
		found=0
		for i in range(1,range_length):
			if(header[2*(i-1)+1]==header_template[2*k+1]):
				d2=data[:,2*(i-1)+1]
				olg_new,r,_,_,_=np.polyfit(d1,d2,4,full=True)
				olg_old=cal.PWR_read_LLRF_coeff('RFIn'+str(k+1),'OLG')
				d2_fit=np.polyval(olg_new,d1)
				d2_old_fit=np.polyval(olg_old,d1)
				plt.plot(d1,d2_fit,label='New')
				plt.plot(d1,d2_old_fit,label='Old')
				plt.plot(d1,d2,'bo')
				plt.title(BO_LLRF_label[k]+' OLG R='+str(r))
				plt.legend(loc='best')
				plt.show(block=False)
				ans=input('Do you wish to replace the '+BO_LLRF_label[k]+' OLG old coefficients? [Y/n]?')
				if(ans=='Y' or ans=='y'):
					olg_coeff[:,j]=olg_new
					print('Coefficients replaced')
					plt.close()
				else:
					olg_coeff[:,j]=olg_old
					print('Kept old Coefficients')
					plt.close()
				j=j+1
				found=1
				break
		if(not found):
			print(BO_LLRF_label[k]+' OLG not found, keeping old coefficients')
			olg_old=cal.PWR_read_LLRF_coeff('RFIn'+str(k+1),'OLG')
			olg_coeff[:,j]=olg_old
			j=j+1

for k in range(1,16):
	found=0
	for i in range(1,range_length):
		if(header[2*(i-1)+1]==header_template[2*(k-1)+1]):
			d1=data[:,2*(i-1)+1]
			d2=cal.GEN_dBmtoVrms(data[:,2*i])
			c_new,r,_,_,_=np.polyfit(d1,d2,4,full=True)
			c_old=cal.PWR_read_LLRF_coeff('RFIn'+str(k),'Raw-U')
			d2_fit=np.polyval(c_new,d1)
			d2_old_fit=np.polyval(c_old,d1)
			plt.plot(d1,d2_fit,label='New')
			plt.plot(d1,d2_old_fit,label='Old')
			plt.plot(d1,d2,'bo')
			plt.title(BO_LLRF_label[k-1]+' Raw-U R='+str(r))
			plt.legend(loc='best')
			plt.show(block=False)
			ans=input('Do you wish to replace the '+BO_LLRF_label[k-1]+' RAW-U old coefficients? [Y/n]?')
			if(ans=='Y' or ans=='y'):
				coeff_Raw_U[:,k-1]=c_new
				print('Coefficients replaced')
				plt.close()
			else:
				coeff_Raw_U[:,k-1]=c_old
				print('Kept old Coefficients')
				plt.close()
			found=1
			break
	if(not found):
		c_old=cal.PWR_read_LLRF_coeff('RFIn'+str(k),'Raw-U')
		coeff_Raw_U[:,k-1]=c_old

u_raw_inputs=[1,2,5]
j=0
for k in u_raw_inputs:
	found=0
	for i in range(1,range_length):
		if(header[2*(i-1)+1]==header_template[2*(k-1)+1]):
			d2=data[:,2*(i-1)+1]
			d1=cal.GEN_dBmtoVrms(data[:,2*i])
			c_new,r,_,_,_=np.polyfit(d1,d2,4,full=True)
			c_old=cal.PWR_read_LLRF_coeff('RFIn'+str(k),'U-Raw')
			d2_fit=np.polyval(c_new,d1)
			d2_old_fit=np.polyval(c_old,d1)
			plt.plot(d1,d2_fit,label='New')
			plt.plot(d1,d2_old_fit,label='Old')
			plt.plot(d1,d2,'bo')
			plt.title(BO_LLRF_label[k-1]+' U-Raw R='+str(r))
			plt.legend(loc='best')
			plt.show(block=False)
			ans=input('Do you wish to replace the '+BO_LLRF_label[k-1]+' U-Raw old coefficients? [Y/n]?')
			if(ans=='Y' or ans=='y'):
				coeff_U_Raw[:,j]=c_new
				print('Coefficients replaced')
				plt.close()
			else:
				coeff_U_Raw[:,j]=c_old
				print('Kept old Coefficients')
				plt.close()
			j=j+1
			found=1
			break
	if(not found):
		c_old=cal.PWR_read_LLRF_coeff('RFIn'+str(k),'U-Raw')
		coeff_U_Raw[:,j]=c_old
		j=j+1

out_header=['OLG_CAV:AMP','OLG_FWDCAV:AMP','OLG_FWDSSA1:AMP','RAW_U_CAV:AMP','RAW_U_FWDCAV:AMP','RAW_U_REVCAV:AMP','RAW_U_MO:AMP','RAW_U_FWDSSA1:AMP','RAW_U_REVSSA1:AMP','RAW_U_CELL2:AMP','RAW_U_CELL4:AMP','RAW_U_CELL1:AMP','RAW_U_CELL5:AMP','RAW_U_INPRE:AMP','RAW_U_FWDPRE:AMP','RAW_U_REVPRE:AMP','RAW_U_FWDCIRC:AMP','RAW_U_REVCIRC:AMP','U_RAW_CAV:AMP','U_RAW_FWDCAV:AMP','U_RAW_FWDSSA1:AMP']
out=np.concatenate((olg_coeff,coeff_Raw_U,coeff_U_Raw),axis=1)
cal.GEN_write_csv(out,TimeStamp+'_fit.csv',header=out_header)
