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

def getToken(source):
	session = requests.Session()
	session.headers.update({'referer': REFERRER})
	req = session.post(URL.format('getlookup'),data={'source':source})
	start = time.time()
	data = req.json()
	lookup = data['lookup']
	lookup_disp = lookup[0:4] + '-' + lookup[-4:]
	md5 = data['md5']
	xbmcgui.Dialog().ok('Authorize','Go to: {0}'.format(USER_URL), 'and enter the code: {0}'.format(lookup_disp),'Press OK when finished.')
	prog = xbmcgui.DialogProgress()
	prog.create('Getting Token','Code: {0}'.format(lookup_disp),'','Waiting for response...')
	try:
		while not prog.iscanceled() and not xbmc.abortRequested:
			req = session.post(URL.format('gettoken'),data={'lookup':lookup,'md5':md5})
			data = req.json()
			status = data.get('status') or 'error'
			if status == 'error':
				prog.close()
				xbmcgui.Dialog().ok('ERROR','There was an error authorizing.','','Please try again.')
				break
			elif status == 'ready':
				prog.close()
				xbmcgui.Dialog().ok('Done','','Authorization complete!')
				return data.get('token')
			xbmc.sleep(1000)
			now = time.time()
			interval = now - start
			pct = int((interval/300.0)*100)
			left = 300 - interval
			mins = int(left/60)
			secs = int(left%60)
			mins = mins and '{0}m '.format(mins) or ''
			secs = secs and '{0}s'.format(secs) or ''
			if mins or secs: left = mins + secs + ' left'
			prog.update(pct,'Code: {0}'.format(lookup_disp),'','Waiting for response... ' + left)
	finally:
		prog.close()