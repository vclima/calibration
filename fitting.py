import csv
import numpy as np
import calibration_lib as cal
import matplotlib.pyplot as plt

csv_name='1533_170919.csv'

with open(csv_name) as csvfile:
	csvfile = csv.reader(csvfile, delimiter=',', quotechar='"')
	line_count=0
	for row in csvfile:
		if line_count==0:
			header=row
			DataSize=int(header[3][9:])
			LS=int(header[0][11:])
			data=np.zeros((DataSize,31))
			line_count+=1
		elif line_count==1:
			line_count+=1
		else:
			data[line_count-2,:]=row
			line_count+=1

coeff_Raw_U=np.zeros((5,15))
coeff_U_Raw=np.zeros((5,15))
olg_coeff=np.zeros((5,15))
if (LS==1):
	coeff[:,0]=np.nan
	print('Open loop gain can\'t be fitted with closed-loop run')
else:
	d1=data[:,0]
	for i in range(0,15):
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
		ans=input('Do you wish to replace the old coefficients? [Y/n]?')
		if(ans=='Y' or ans=='y'):
			olg_coeff[:,i-1]=olg_new
			print('Coefficients replaced')
			plt.close()
		else:
			olg_coeff[:,i-1]=olg_old
			print('Kept old Coefficients')
			plt.close()

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
	ans=input('Do you wish to replace the old coefficients? [Y/n]?')
	if(ans=='Y' or ans=='y'):
		coeff_Raw_U[:,i-1]=c_new
		print('Coefficients replaced')
		plt.close()
	else:
		coeff_Raw_U[:,i-1]=c_old
		print('Kept old Coefficients')
		plt.close()
for i in range(1,16):
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
	ans=input('Do you wish to replace the old coefficients? [Y/n]?')
	if(ans=='Y' or ans=='y'):
		coeff_U_Raw[:,i-1]=c_new
		print('Coefficients replaced')
		plt.close()
	else:
		coeff_U_Raw[:,i-1]=c_old
		print('Kept old Coefficients')
		plt.close()
