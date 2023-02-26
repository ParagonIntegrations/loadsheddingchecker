import datetime
import logging

settings = {
	'filename': 'NorthWest_LS.csv',
	'blocknumber': 5,
	'loadsheddingduration': datetime.timedelta(hours=2),
	'predisconnecttime': datetime.timedelta(minutes=5),
	'lsvalupdatetime': datetime.timedelta(minutes=10),
	'timezoneoffset': datetime.timedelta(hours=2),
	'sleeptime': 5,
	'fileloglevel': logging.DEBUG,
	'streamloglevel': logging.DEBUG,
	'dbusservices':{
		'systemmode': {'Service': "com.victronenergy.vebus.ttyO1",
						  'Path': "/Mode",
						  'Proxy': object,
						  'Value': 3},
	}
}