import csv
import numpy as np
import calibration_lib as cal

csv_name=input('File name: ')

with open(csv_name) as csvfile:
	csvfile = csv.reader(csvfile, delimiter=',', quotechar='"')
	line_count=0
	for row in csvfile:
		if line_count==0:
			header=row
			ColsSize=len(header)
			data=np.zeros((6,ColsSize))
			line_count+=1
		else:
			data[line_count-1,:]=row
			line_count+=1
cal.PWR_set_LLRF_coeff(data)
