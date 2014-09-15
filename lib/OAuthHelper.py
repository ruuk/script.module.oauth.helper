# -*- coding: utf-8 -*-
try:
	from reqests2 import requests
except:
	import requests
	
import xbmc, xbmcgui, xbmcaddon
import time

ADDON_ID = 'script.module.oauth.helper'


URL = 'https://auth-ruuk.rhcloud.com/auth/{0}'
USER_URL = 'auth.2ndmind.com'
REFERRER = 'https://auth-ruuk.rhcloud.com/'
WAIT_SECONDS = 300
POLL_INTERVAL_SECONDS = 5

'''#TODO:
	Handle timeout
'''

def LOG(msg):
	xbmc.log('{0}: {1}'.format(ADDON_ID,msg))

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

class GoogleOAuthorizer(object):
	auth1URL = 'https://accounts.google.com/o/oauth2/device/code'
	auth2URL = 'https://accounts.google.com/o/oauth2/token'
	grantType = 'http://oauth.net/grant_type/device/1.0'
	verificationURL = 'http://www.google.com/device'

	def __init__(self,addon_id=None,client_id=None,client_secret=None,auth_scope=None):
		assert addon_id != None, 'addon_id cannot be None'
		assert client_id != None, 'client_id cannot be None'
		assert client_secret != None, 'client_secret cannot be None'
		assert auth_scope != None, 'auth_scope cannot be None'
		
		self.addonID = addon_id
		self.clientID = client_id
		self.clientS = client_secret
		self.authScope = auth_scope
		self.authPollInterval = 5
		self.authExpires = int(time.time())
		self.deviceCode = ''
		self.session = requests.Session()
		self.loadToken()

	def _setSetting(self,key,value):
		setSetting('{0}.{1}'.format(self.addonID,key),value)

	def _getSetting(self,key,default=None):
		return getSetting('{0}.{1}'.format(self.addonID,key),default)

	def loadToken(self):
		self.token = self._getSetting('access_token')
		self.tokenExpires = self._getSetting('token_expiration',0)

	def getToken(self):
		if self.tokenExpires <= int(time.time()):
			return self.updateToken()
		return self.token

	def updateToken(self):
		LOG('REFRESHING TOKEN')
		data = {	
					'client_id':self.clientID,
					'client_secret':self.clientS,
					'refresh_token':self._getSetting('refresh_token'),
					'grant_type':'refresh_token'
		}

		json = self.session.post(self.auth2URL,data=data).json()
		if 'access_token' in json:
			self.saveData(json)
		else:
			LOG('Failed to update token')
		return self.token
	
	def authorized(self):
		return bool(self.token)
		
	def authorize(self):
		userCode = self.getDeviceUserCode()
		if not userCode: return
		d = xbmcgui.DialogProgress()
		d.create('Authorization','Go to: ' + self.verificationURL,'Enter code: ' + userCode,'Waiting for response...')
		try:
			ct=0
			while not d.iscanceled() and not xbmc.abortRequested:
				d.update(ct,'Go to: ' + self.verificationURL,'Enter code: ' + userCode,'Waiting for response...')
				json = self.pollAuthServer()
				if 'access_token' in json: break
				for x in range(0,self.authPollInterval):
					if d.iscanceled(): return
					xbmc.sleep(1000)
				ct+=1
			if d.iscanceled(): return
		finally:
			d.close()
			
		xbmcgui.Dialog().ok('Done','','Authorization complete!')
		return self.saveData(json)
		
	def saveData(self,json):
		self.token = json.get('access_token','')
		refreshToken = json.get('refresh_token')
		self.tokenExpires = json.get('expires_in',3600) + int(time.time())
		self._setSetting('access_token',self.token)
		if refreshToken: self._setSetting('refresh_token',refreshToken)
		self._setSetting('token_expiration',self.tokenExpires)
		return self.token and refreshToken

	def pollAuthServer(self):
		json = self.session.post(
			self.auth2URL, 
			data={
					'client_id':self.clientID,
					'client_secret':self.clientS,
					'code':self.deviceCode,
					'grant_type':self.grantType
			}
		).json()
		if 'error' in json:
			if json['error'] == 'slow_down':
				self.authPollInterval += 1
		return json
		
	def getDeviceUserCode(self):
		json = self.session.post(self.auth1URL,data={'client_id':self.clientID,'scope':self.authScope}).json()
		self.authPollInterval = json.get('interval',5)
		self.authExpires = json.get('expires_in',1800) + int(time.time())
		self.deviceCode = json.get('device_code','')
		self.verificationURL = json.get('verification_url',self.verificationURL)
		if 'error' in json:
			LOG('ERROR - getDeviceUserCode(): ' + json.get('error_description',''))
		return json.get('user_code','')


def getSetting(key,default=None):
	return xbmcaddon.Addon(ADDON_ID).getSetting(key) or default
	
def setSetting(key,value):
	xbmcaddon.Addon(ADDON_ID).setSetting(key,value)