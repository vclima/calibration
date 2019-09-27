import csv
import numpy as np
import calibration_lib as cal
import matplotlib.pyplot as plt

csv_name='1547_250919_AQS.csv'

with open(csv_name) as csvfile:
	csvfile = csv.reader(csvfile, delimiter=',', quotechar='"')
	line_count=0
	for row in csvfile:
		if line_count==0:
			header=row
			DataSize=int(header[3][9:])
			TimeStamp=header[4][10:]
			LS=int(header[0][11:])
			data=np.zeros((DataSize,31))
			line_count+=1
		elif line_count==1:
			line_count+=1
		else:
			data[line_count-2,:]=row
			line_count+=1

coeff_Raw_U=np.zeros((5,15))
coeff_U_Raw=np.zeros((5,3))
olg_coeff=np.zeros((5,3))
if (LS==1):
	print('Open loop gain can\'t be fitted with closed-loop run')
else:
	d1=data[:,0]
	olg_cols=[0,1,4]
	j=0
	for i in olg_cols:
		d2=data[:,2*i+1]
		olg_new,r,_,_,_=np.polyfit(d1,d2,4,full=True)
		olg_old=cal.PWR_read_LLRF_coeff('RFIn'+str(i+1),'OLG')
		d2_fit=np.polyval(olg_new,d1)
		d2_old_fit=np.polyval(olg_old,d1)
		plt.plot(d1,d2_fit,label='New')
		plt.plot(d1,d2_old_fit,label='Old')
		plt.plot(d1,d2,'bo')
		plt.title('RFIn'+str(i+1)+' OLG R='+str(r))
		plt.legend(loc='best')
		plt.show(block=False)
		ans=input('Do you wish to replace the RFIn'+str(i+1)+' OLG old coefficients? [Y/n]?')
		if(ans=='Y' or ans=='y'):
			olg_coeff[:,j]=olg_new
			print('Coefficients replaced')
			plt.close()
		else:
			olg_coeff[:,j]=olg_old
			print('Kept old Coefficients')
			plt.close()
		j=j+1

for i in range(1,16):
	d1=data[:,2*(i-1)+1]
	d2=cal.GEN_dBmtoVrms(data[:,2*i])
	c_new,r,_,_,_=np.polyfit(d1,d2,4,full=True)
	c_old=cal.PWR_read_LLRF_coeff('RFIn'+str(i),'Raw-U')
	d2_fit=np.polyval(c_new,d1)
	d2_old_fit=np.polyval(c_old,d1)
	plt.plot(d1,d2_fit,label='New')
	plt.plot(d1,d2_old_fit,label='Old')
	plt.plot(d1,d2,'bo')
	plt.title('RFIn'+str(i)+' Raw-U R='+str(r))
	plt.legend(loc='best')
	plt.show(block=False)
	ans=input('Do you wish to replace the RFIn'+str(i)+' RAW-U old coefficients? [Y/n]?')
	if(ans=='Y' or ans=='y'):
		coeff_Raw_U[:,i-1]=c_new
		print('Coefficients replaced')
		plt.close()
	else:
		coeff_Raw_U[:,i-1]=c_old
		print('Kept old Coefficients')
		plt.close()
u_raw_inputs=[1,2,5]
j=0
for i in u_raw_inputs:
	d2=data[:,2*(i-1)+1]
	d1=cal.GEN_dBmtoVrms(data[:,2*i])
	c_new,r,_,_,_=np.polyfit(d1,d2,4,full=True)
	c_old=cal.PWR_read_LLRF_coeff('RFIn'+str(i),'U-Raw')
	d2_fit=np.polyval(c_new,d1)
	d2_old_fit=np.polyval(c_old,d1)
	plt.plot(d1,d2_fit,label='New')
	plt.plot(d1,d2_old_fit,label='Old')
	plt.plot(d1,d2,'bo')
	plt.title('RFIn'+str(i)+' U-Raw R='+str(r))
	plt.legend(loc='best')
	plt.show(block=False)
	ans=input('Do you wish to replace the RFIn'+str(i),'U-Raw old coefficients? [Y/n]?')
	if(ans=='Y' or ans=='y'):
		coeff_U_Raw[:,j]=c_new
		print('Coefficients replaced')
		plt.close()
	else:
		coeff_U_Raw[:,j]=c_old
		print('Kept old Coefficients')
		plt.close()
	j=j+1
