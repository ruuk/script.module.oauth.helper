# -*- coding: utf-8 -*-
try:
	from reqests2 import requests
except:
	import requests
	
import xbmc, xbmcgui
import time

URL = 'https://auth-ruuk.rhcloud.com/auth/{0}'
USER_URL = 'auth.2ndmind.com'
REFERRER = 'https://auth-ruuk.rhcloud.com/'
WAIT_SECONDS = 300
POLL_INTERVAL_SECONDS = 5

'''#TODO:
	Handle timeout
'''

def getToken(source):
	session = requests.Session()
	session.headers.update({'referer': REFERRER})
	req = session.post(URL.format('getlookup'),data={'source':source})
	start = time.time()
	data = req.json()
	lookup = data['lookup']
	lookup_disp = lookup[0:4] + '-' + lookup[-4:]
	md5 = data['md5']
	prog = xbmcgui.DialogProgress()
	prog.create('Authorize','Go to: {0}'.format(USER_URL),'and enter the code: {0}'.format(lookup_disp),'Waiting for response...')
	prog.update(0,'Go to: {0}'.format(USER_URL),'and enter the code: {0}'.format(lookup_disp),'Waiting for response... ')
	try:
		while not prog.iscanceled() and not xbmc.abortRequested:
			req = session.post(URL.format('gettoken'),data={'lookup':lookup,'md5':md5})
			data = req.json()
			status = data.get('status') or 'error'
			if status == 'error':
				prog.close()
				xbmcgui.Dialog().ok('ERROR','There was an error authorizing.','','Please try again.')
				break
			elif status == 'waiting':
				secs_left = data.get('secs_left')
			elif status == 'ready':
				prog.close()
				xbmcgui.Dialog().ok('Done','','Authorization complete!')
				return data.get('token')
				
			for x in range(0,POLL_INTERVAL_SECONDS): #Update display every second, but only poll every POLL_INTERVAL_SECONDS
				if prog.iscanceled(): return
				pct, left_disp, start = timeLeft(start,WAIT_SECONDS,secs_left=secs_left)
				secs_left = None
				prog.update(pct,'Go to: {0}'.format(USER_URL),'and enter the code: {0}'.format(lookup_disp),'Waiting for response... ' + left_disp)
				xbmc.sleep(1000)
	finally:
		prog.close()

def timeLeft(start,total,secs_left=None):
	left_disp = ''
	
	now = time.time()
	if secs_left:
		left = secs_left
		sofar = total - left
		start = now - sofar
	else:
		sofar = now - start
		left = total - sofar
		
	pct = int((sofar/float(total))*100)
	mins = int(left/60)
	secs = int(left%60)
	mins = mins and '{0}m '.format(mins) or ''
	secs = secs and '{0}s'.format(secs) or ''
	if mins or secs: left_disp = mins + secs + ' left'
	return pct, left_disp, start