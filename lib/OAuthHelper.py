# -*- coding: utf-8 -*-
try:
	from reqests2 import requests
except:
	import requests
import xbmc, xbmcgui
import time

URL = 'http://auth.2ndmind.com/cgi-bin/oauth.py'
USER_URL = 'auth.2ndmind.com'

def getToken(source):
	req = requests.post(URL,data={'request':'getlookup','source':source})
	data = req.json()
	lookup = data['lookup']
	lookup_disp = lookup[0:4] + '-' + lookup[-4:]
	md5 = data['md5']
	xbmcgui.Dialog().ok('Authorize','Go to: {0}'.format(USER_URL), 'and enter the code: {0}'.format(lookup_disp),'Press OK when finished.')
	prog = xbmcgui.DialogProgress()
	prog.create('Getting Token','Code: {0}'.format(lookup_disp),'','Waiting for response...')
	try:
		start = time.time()
		while not prog.iscanceled() and not xbmc.abortRequested:
			req = requests.post(URL,data={'request':'gettoken','lookup':lookup,'md5':md5})
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
			prog.update(pct,'Code: {0}'.format(lookup_disp),'','Waiting for response...')
	finally:
		prog.close()