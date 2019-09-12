import epics as ep
import time


def read_calsys(RFIn):
	PV_header='RA-RaBO01:RF-LLRFCalSys:PwrdBm'
	pwr=ep.caget(PV_header+string(RFIn)+'_CALC')
	return pwr

def read_LLRF(RFIn):
	PV_header=''