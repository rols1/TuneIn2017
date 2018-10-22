import httplib			# headers -> dictionary
import urllib			# urllib.quote()
import urllib2			# urllib2.Request
import ssl				# HTTPS-Handshake

import os, subprocess 	# u.a. Behandlung von Pfadnamen
import shlex			# Parameter-Expansion
import signal			# für os.kill
import time				# Verzögerung
import random			# Zufallswerte für rating_key
import sys				# Plattformerkennung
import re				# u.a. Reguläre Ausdrücke, z.B. in CalculateDuration
import json				# json -> Textstrings
from urlparse import urlparse # Check Portnummer in Url

import updater


# +++++ TuneIn2017 - tunein.com-Plugin für den Plex Media Server +++++

VERSION =  '1.2.9'	
VDATE = '22.10.2018'

# 
#	

# (c) 2016 by Roland Scholz, rols1@gmx.de
# 
# 	Licensed under MIT License (MIT)
# 	(previously licensed under GPL 3.0)
# 	A copy of the License you find here:
#		https://github.com/rols1/TuneIn2017/blob/master/LICENSE.md
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR 
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE 
# FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR 
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER 
# DEALINGS IN THE SOFTWARE.

# Wikipedia:	https://de.wikipedia.org/wiki/TuneIn
#				https://de.wikipedia.org/wiki/Internetradio
#				https://de.wikipedia.org/wiki/Streaming-Format
#				https://de.wikipedia.org/wiki/Audioformat
#
# Wicki Ubuntu: https://wiki.ubuntuusers.de/Internetradio/Stationen/


ICON_OK 				= "icon-ok.png"
ICON_WARNING 			= "icon-warning.png"
ICON_NEXT 				= "icon-next.png"
ICON_CANCEL 			= "icon-error.png"
ICON_MEHR 				= "icon-mehr.png"
ICON_SEARCH 			= 'ard-suche.png'

ICON_RECORD				= 'icon-record.png'						
ICON_STOP				= 'icon-stop.png'
MENU_RECORDS			= 'menu-records.png'
MENU_CUSTOM				= 'menu-custom.png'
MENU_CUSTOM_ADD			= 'menu-custom-add.png'
MENU_CUSTOM_REMOVE		= 'menu-custom-remove.png'
ICON_FAV_ADD			= 'fav_add.png'
ICON_MYRADIO			= 'myradio.png'
ICON_FAV_REMOVE			= 'fav_remove.png'
ICON_FAV_MOVE			= 'fav_move.png'
ICON_FOLDER_ADD			= 'folder_add.png'
ICON_FOLDER_REMOVE		= 'folder_remove.png'
ICON_MYLOCATION			= 'mylocation.png'
ICON_MYLOCATION_REMOVE	= 'mylocation-remove.png'
						

ICON_MAIN_UPDATER 		= 'plugin-update.png'		
ICON_UPDATER_NEW 		= 'plugin-update-new.png'


ART    		= 'art-default.jpg'
ICON   		= 'icon-default.jpg'
NAME		= 'TuneIn2017'
MENU_ICON 	=  	{'menu-lokale.png', 'menu-musik.png', 'menu-sport.png', 'menu-news.png',
					 'menu-talk.png', 'menu-audiobook.png', 'menu-pod.png', 
				}

# ab 18.04.2018, Version 1.1.9: Inhalte von Webseite statt opml-Browse-Call,
#	zusätzliche API-Calls: api.tunein.com/categories, api.tunein.com/profiles.
#	opml-Calls weiter verwendet für Fav's, Folders, audience_url, Account-Queries.
# ROOT_URL 	= 'https://opml.radiotime.com/Browse.ashx?formats=%s'
ROOT_URL 	= 'https://tunein.com/radio/home/'						
USER_URL 	= 'https://opml.radiotime.com/Browse.ashx?c=presets&partnerId=RadioTime&username=%s'
RECENTS_URL	= 'https://api.tunein.com/categories/recents?formats=%s&serial=%s&partnerId=RadioTime&version=2.22'

PREFIX 		= '/music/tunein2017'

REPO_NAME		 	= NAME
GITHUB_REPOSITORY 	= 'rols1/' + REPO_NAME
REPO_URL 			= 'https://github.com/{0}/releases/latest'.format(GITHUB_REPOSITORY)


# Globale Variablen für Tunein:
partnerId		= 'RadioTime'


####################################################################################################
def Start():
	# Phänomen bei Verzicht auf HTTP.CacheTime:
	# mit dieser url ruft das Framework beim 2. Durchlauf von CreateTrackObject  Main() auf (aber nicht, wenn sie hier direkt zugeordnet wird):	
	# 	url='http://absolut.hoerradar.de/absolutradio.mp3?sABC=59r8r97q#0#2s45pq59pr6699onn0qq321942141r80#gharva&amsparams=playerid:tunein;skey:1508436349'
	# Framework-Call auf Main() dazu (statt PlayAudio):
	#	GET /music/tunein2017?includeConcerts=1&includeExtras=1&includeOnDeck=1&includePopularLeaves=1&includeChapters=1&checkFiles=1
	
	ObjectContainer.title1 = NAME
	HTTP.CacheTime = 300		# = 5 min
	ObjectContainer.art = R(ART)
	DirectoryObject.art = R(ART)
	DirectoryObject.thumb = R(ICON)
	global MyContents
	global UrlopenTimeout 		
	UrlopenTimeout = 3			# Timeout sec, 18.10.2017 von 6 auf 3
	global SearchWeb			# Search: auf tunein.com / via opml-Call
	SearchWeb = True
	
	# Dict.Reset()				# Prozessliste Record: kein Reset wg. Record-Prozessliste. 
	if Dict['PID']:				# Dicts überleben auch PMS-Restart 
		pass
	else:
		Dict['PID'] = []		
	MyContents = Core.storage.join_path(Core.bundle_path, 'Contents')

	ValidatePrefs()
	
	
# Locale-Probleme 	s. https://forums.plex.tv/discussion/126807/another-localization-question,
#					https://forums.plex.tv/discussion/143342/non-ascii-characters-in-translations
#					Die Lösung von czukowski (eigene L-Funktion) funktioniert + wird hier verwendet:
#						https://forums.plex.tv/discussion/comment/838061/#Comment_838061
#						Bsp. de.json-String: "Durchstoebern": "Durchstöbern" (Umlaute nur im 2. Teil!)
#					Alternative (def LF(key, args)): 
#						https://github.com/fuzeman/Spotify2.bundle/blob/master/Contents/Code/utils.py
def ValidatePrefs():	
	try:
		lang = Prefs['language'].split('/') # Format Bsp.: "Danish/da/da-DA/Author Tommy Mikkelsen"
		loc 		= str(lang[1])		# de
		loc_browser = loc
		if len(lang) > 2:
			loc_browser = str(lang[2])	# de-DE - Konkretisierung, falls vorhanden
	except:
		loc 		= 'en-us'			# Fallback 
		loc_browser = 'en-US'
		
	loc_file = Core.storage.abs_path(Core.storage.join_path(MyContents, 'Strings', '%s.json' % loc))
	Log(loc_file)		
	if os.path.exists(loc_file):
		Locale.DefaultLocale = loc
	else:
		Locale.DefaultLocale = 'en-us'	# Fallback
		
	Dict['loc'] 		= loc
	Dict['loc_file'] 	= loc_file
	Dict['loc_browser'] = loc_browser
	Log('loc: %s' % loc)
	Log('loc_file: %s' % loc_file)
	Log('loc_browser: %s' % loc_browser)

####################################################################################################
@handler(PREFIX, NAME,  art = ART, thumb = ICON)
@route(PREFIX)
def Main():
	Log('Main')
	
	# nützliche Debugging-Variablen:
	Log('Plugin-Version: ' + VERSION); Log('Plugin-Datum: ' + VDATE)	
	client_platform = str(Client.Platform)								# Client.Platform: None möglich
	client_product = str(Client.Product)								# Client.Product: None möglich
	Log('Client-Platform: ' + client_platform)							
	Log('Client-Product: ' + client_product)							    
	Log('Plattform: ' + sys.platform)									# Server-Infos
	Log('Platform.OSVersion: ' + Platform.OSVersion)					# dto.
	Log('Platform.CPU: '+ Platform.CPU)									# dto.
	Log('Platform.ServerVersion: ' + Platform.ServerVersion)			# dto.
	
	title = 'Durchstoebern'
	title = L(title)
			
	oc = ObjectContainer(title2=title, art=ObjectContainer.art, no_cache=True)

	oc.add(InputDirectoryObject(key=Callback(Search), title=u'%s' % L('Suche'), prompt=u'%s' % L('Suche Station / Titel'), 
		thumb=R(ICON_SEARCH)))
		
	MyRadioStations = Prefs['MyRadioStations']							# eigene Liste mit Radiostationen, 
	Log('MyRadioStations: ' + str(MyRadioStations))							# (Muster in Resources)
	if  MyRadioStations:
		MyRadioStations = MyRadioStations.strip()	
		if os.path.exists(r'%s' % MyRadioStations):
				title = L("Meine Radiostationen")
				summ = MyRadioStations
				oc.add(DirectoryObject(key = Callback(ListMRS, path=MyRadioStations), 
					title=title, summary=summ, thumb = R(ICON_MYRADIO))) 
					 
				if Prefs['StartWithMyRadioStations']:					# MyRadioStations + SearchUpdate direkt anzeigen 								
					oc = SearchUpdate(title=NAME, start='true', oc=oc)	# Updater-Modul einbinden
					return oc				
		else:
			title = L("Meine Radiostationen") + ': ' + L("Datei nicht gefunden")
			summ = L("nicht gefunden") + ': ' +  MyRadioStations
			tag = L('Bitte den Eintrag in Einstellungen ueberpruefen!')
			oc.add(DirectoryObject(key=Callback(Main),title=title, summary=summ, tagline=tag, thumb=R(ICON_WARNING)))
				
		
	username = Prefs['username']										# Privat - nicht loggen
	passwort = Prefs['passwort']										# dto.
	if Dict['serial'] == None:
		Dict['serial'] = serial_random()								# eindeutige serial-ID für Tunein für Favoriten u.ä.
		Log('serial-ID erzeugt')										# 	wird nach Löschen Plugin-Cache neu erzeugt				
	Log('serial-ID: ' + Dict['serial'])												
	                  		
	if username:
		my_title = u'%s' % L('Meine Favoriten')
		my_url = USER_URL % username									# nicht serial-ID! Verknüpfung mit Account kann fehlen
		if Prefs['StartWithFavourits']:									# Favoriten + SearchUpdate direkt anzeigen 
			oc = GetContent( url=my_url, title=my_title, offset=0)
			oc = SearchUpdate(title=NAME, start='true', oc=oc)			# Updater-Modul einbinden
			return oc
		else:															# Standard-Menü
			oc.add(DirectoryObject(
				key = Callback(GetContent, url=my_url, title=my_title, offset=0),
				title = my_title, thumb = R(ICON) 
			))  
		
	formats = 'mp3,aac'	
	Log(Prefs['PlusAAC'])								
	if  Prefs['PlusAAC'] == False:										# Performance, aac nicht bei allen Sendern 
		formats = 'mp3'
	Dict['formats'] = formats											# Verwendung: Trend, opml- und api-Calls
	
	if Prefs['SystemCertifikat']:		# Vorabtest - in RequestTunein problematisch für return ObjectContainer	
		cafile = Prefs['SystemCertifikat']	
		Log(cafile)
		if os.path.exists(cafile) == False:
			msg = 'System-Certifikate ' + L("nicht gefunden") + ': ' + cafile
			Log(msg)
			return ObjectContainer(header=L('Fehler'), message=msg)		
	
	
	page, msg = RequestTunein(FunctionName='Main', url=ROOT_URL)		# Hauptmenü von Webseite
	Log(len(page))
	page = stringextract('"homeMenuItem"', 'leftSide__authContainer', page)
	items = blockextract('common__link', page)
	if len(items) > 0:													# kein Abbruch, weiter mit MyRadioStations + Fav's
		del items[0]			# Home löschen
	Log(len(items))
	for item in items:
		# Log('item: ' + item)
		url = 'https://tunein.com' + stringextract('href="', '"', item)	#  Bsp. href="/radio/local/"
		key = url[:-1].split('/')[-1]
		thumb = getMenuIcon(key)
		Log(url);	# Log(key);	Log(thumb);	
		try:	
			title = re.search('">(.*)</a>', item).group(1)				# Bsp. data-reactid="64">Local Radio</a>
			Log("title: " + title)
		except:
			title = key.title()
		title = title.replace('\u002F', '/')
		title = title.decode(encoding="utf-8")
		categories = 'Category'
		if key == 'recents':											# Recents: Url-Anpassung erforderlich
			categories = None
			url = RECENTS_URL  											# % (formats, serial) in GetContent
		oc.add(DirectoryObject(key = Callback(GetContent, url=url, title=title, offset=0),	
			title = title, thumb=thumb)) 
		
	
#-----------------------------	
	Log(Prefs['UseRecording'])
	Log(Dict['PID'])
	if Prefs['UseRecording'] == True:			# Recording-Option: Aufnahme-Menu bei aktiven Aufnahmen einbinden
		if len(Dict['PID']) > 0:						
			title = L("Laufende Aufnahmen")
			oc.add(DirectoryObject(key=Callback(RecordsList,title=title,), title=title,thumb=R(MENU_RECORDS)))			       
#-----------------------------	
	oc = SearchUpdate(title=NAME, start='true', oc=oc)	# Updater-Modul einbinden:
			
	# Lang_Test=True									# Menü-Test Plugin-Sprachdatei
	Lang_Test=False		
	if Lang_Test:
		oc.add(DirectoryObject(key=Callback(LangTest),title='LangTest', summary='LangTest', thumb=R('lang_gnome.png')))			
			
	return oc
						
####################################################################################################
# LangTest testet aktuelle Plugin-Sprachdatei, z.B. en.json (Lang_Test=True).
#	Ausgabe von Buttons: Titel = Deutsch, summary = gewählte Sprache
@route(PREFIX + '/LangTest')
def LangTest():										
	Log('LangTest')	
	title = 'LangTest: %s' % Dict['loc'] 
	oc = ObjectContainer(title2=title, art=ObjectContainer.art)
	verz = Core.storage.abs_path(Core.storage.join_path(MyContents, 'Strings', 'de.json')) # Basis German de
	de_strings = Core.storage.load(verz)		
	
	de_strings = de_strings.split('\n')
	for string in de_strings:
		string = string.split(':')[0]				# 1. Paar-Teil
		string = string.replace('"', '')
		string = string.replace('}', '')
		string = string.replace('{', '')
		string = string.strip()
		Log(string)
		if string:
			title = string
			summ = L(title)							# czukowski-Lösung	
			# summ = myL(title)						# Hardcore-Lösung
			oc.add(DirectoryObject(key=Callback(dummy),title=title, summary=summ, thumb=R('lang_gnome.png')))
	return oc
	
@route(PREFIX + '/dummy')
def dummy():
	return ObjectContainer(header=L('Hinweis'), message='dummy-Funktion OK')
	
#----------------------------------------------------------------
def home(oc):										# Home-Button
	Log('home')	
	title = 'Home' 	
	oc.add(DirectoryObject(key=Callback(Main),title=title, summary=title, tagline=NAME, thumb=R('home.png')))
	return oc
#-----------------------------	
def getMenuIcon(key):	# gibt zum key passendes Icon aus MENU_ICON zurück
	icon = ICON			# Fallback
	for icon in MENU_ICON:
		if key == 'local':
			icon = R('menu-lokale.png')
		if key == 'recents':
			icon = R('menu-kuerzlich.png')
		if key == 'trending':
			icon = R('menu-trend.png')
		elif key == 'music':
			icon = R('menu-musik.png')
		elif key == 'sports':
			icon = R('menu-sport.png')
		elif key == 'News-c57922':
			icon = R('menu-news.png')
		elif key == 'talk':
			icon = R('menu-talk.png')
		elif key == 'podcasts':
			icon = R('menu-pod.png')
		elif key == 'regions':
			icon = R('menu-orte.png')
		elif key == 'languages':
			icon = R('menu-sprachen.png')
	return icon	
#-----------------------------
@route(PREFIX + '/Search')
def Search(query=None):
	Log('Search: ' + str(query))
	oc_title2 = L('Suche nach')
	oc_title2 = oc_title2 + ' ' + query.decode(encoding="utf-8", errors="ignore")
	oc = ObjectContainer(title2=oc_title2, art=ObjectContainer.art)
	oc = home(oc)
	
	query = query.strip()
	Log(SearchWeb)
	if SearchWeb == True:
		query = urllib2.quote(query, "utf-8")								# Web-Variante
		url = 'https://tunein.com/search/?query=%s' % query		
		Log('url: ' + url)
		oc = GetContent(url=url, title=oc_title2, offset=0)
	else:		
		query = query.replace(' ', '+')										# opml-Variante
		url = 'http://opml.radiotime.com/Search.ashx?query=%s&formats=%s' % (query,Dict['formats'])	
		query = urllib2.quote(query, "utf-8")
		Log('url: ' + url)
		oc = GetContentOPML(url=url, title=oc_title2, offset=0)	
			
	
	if len(oc) == 1:
		title = 'Keine Suchergebnisse zu'
		title = title.decode(encoding="utf-8", errors="ignore")
		title = L(title) + ' >%s<' % query
		oc.add(DirectoryObject(key=Callback(Main),title=title, summary='Home', tagline=NAME, thumb=R(ICON_CANCEL)))
	return oc
#-----------------------------
def get_presetUrls(oc, outline):						# Auswertung presetUrls für GetContent
	Log('get_presetUrls')
	rubriken = blockextract('<outline type', outline)	# restliche outlines 
	for rubrik in rubriken:	 # presetUrls ohne bitrate + subtext, type=link. Behandeln wie typ == 'audio'
		typ,local_url,text,image,key,subtext,bitrate,preset_id = get_details(line=rubrik)	# xml extrahieren
		subtext = 'CustomURL'
		bitrate = 'unknown'		# dummy für PHT -> Blank in StationList
		typ = 'unknown'			# dummy für PHT
		oc.add(DirectoryObject(
			key = Callback(StationList, url=local_url, title=text, summ=subtext, image=image, typ=typ, bitrate=bitrate,
			preset_id=preset_id),
			title = text, summary=subtext,  tagline=local_url, thumb = image 
		))  
	Log(len(oc))	
	return oc					
	
#-----------------------------
# SetLocation (Aufruf GetContent): Region für Lokales Radiomanuell setzen/entfernen
@route(PREFIX + '/SetLocation')		
def SetLocation(url, title, region, myLocationRemove):	
	Log('SetLocation')
	Log('myLocationRemove: ' + myLocationRemove)

	if myLocationRemove == 'True':
		Dict['myLocation'] = None
		msg = L('Lokales Radio entfernt') + ' | '	 + L('neu setzen im Menue Orte')
		Dict.Save()
	else:
		Dict['myLocation'] = url
		msg = L('Lokales Radio gesetzt auf') + ': %s' % region
	return ObjectContainer(header=L('Info'), message=msg)

#-----------------------------
# GetContentOPML: aufgerufen via Browser-Url, nicht via Browser-Url (s. GetContent)
#	Inhalt im xml-Format
@route(PREFIX + '/GetContentOPML')		
def GetContentOPML(title, url, offset=0):
	Log('GetContentOPML'); Log(offset)
	offset = int(offset)
	title_org = title
	oc_title2 = title
	
	if offset:
		oc_title2 = title_org + ' | %s...' % offset			
	
	max_count = 0									# Default: keine Begrenzung
	if Prefs['maxPageContent']:
		max_count = int(Prefs['maxPageContent'])	# max. Anzahl Einträge ab offset

	page, msg = RequestTunein(FunctionName='GetContentOPML', url=url)	
	if page == '':
		error_txt = msg.decode(encoding="utf-8", errors="ignore")
		Log(error_txt)
		return ObjectContainer(header=L('Fehler'), message=error_txt)
	Log(len(page))
	Log(page[:100])
	
	title	= stringextract('<title>', '</title>', page)
	oc = ObjectContainer(no_cache=True, title2=oc_title2, art=ObjectContainer.art)	
	oc = home(oc)

	items = blockextract('outline type', page)
	Log(len(items))
	page_cnt = len(items)
	Log('items: ' + str(page_cnt))
	if 	max_count:									# '' = 'Mehr..'-Option ausgeschaltet?
		page_cnt = page_cnt 
		delnr = min(page_cnt, offset)
		del items[:delnr]
		Log(delnr)				
	Log(page_cnt); Log(len(items))
	
	for item in items:
		# Log('item: ' + items)	
		typ,local_url,text,image,key,subtext,bitrate,preset_id,guide_id,playing,is_preset = get_details(line=item)				
		# Log('%s | %s | %s | %s | %s | %s' % (typ,text,preset_id,guide_id,local_url,is_preset))
		if preset_id.startswith('u'):				# Custom-Url -> Station, is_preset=true
			typ = 'audio'
			image = R(MENU_CUSTOM)
			subtext = 'CustomURL'
		if typ == 'link':							# Ordner
			image = R(ICON)			
			oc.add(DirectoryObject(
				key = Callback(FolderMenuList, url=local_url, title=text),
				title = text, thumb=image
			)) 
		if typ == 'audio':							# Station
			oc.add(DirectoryObject(
				key = Callback(StationList, url=local_url, title=text, summ=subtext, image=image, typ='Station', bitrate=bitrate,
				preset_id=preset_id),
				title=text, summary=subtext, tagline=playing, thumb=image)) 	
				
		if max_count:
			# Mehr Seiten anzeigen:		
			cnt = len(oc) + offset		# 
			# Log('Mehr-Test: %s | %s | %s' % (len(oc), cnt, page_cnt) )
			if cnt > page_cnt:			# Gesamtzahl erreicht - Abbruch
				offset=0
				break					# Schleife beenden
			elif len(oc) >= max_count:	# Mehr, wenn max_count erreicht
				offset = offset + max_count +2	
				title = L('Mehr...') + title_org
				summ_mehr = L('Mehr...') + '(max.: %s)' % page_cnt
				oc.add(DirectoryObject(
					key = Callback(GetContentOPML, url=url, title=title_org, offset=offset),
					title = title, summary=summ_mehr, tagline=L('Mehr...'), thumb=R(ICON_MEHR) 
				)) 
				break					# Schleife beenden
						
	return oc
	
#-----------------------------

# GetContent aufgerufen via Browser-Url, nicht via opml-Request (s. GetContentOPML)
# 	Die Auswertung erfolgt mittels Stringfunktionen, da die Ausgabe weder im xml- noch im json-Format
#		erzwungen werden kann.
#	Bei Recents wird statt des opm-Calls ein api-Call verwendet. Der Output unterscheidet sich in den
#		Anfangsbuchstaben der Parameter - s. uppercase / lowercase.
#	Unterscheidung Link / Station mittels mytype ("type")
#
@route(PREFIX + '/GetContent')		
def GetContent(url, title, offset=0):
	Log('GetContent:'); Log(url); Log(offset); 
	offset = int(offset)
	title_org = title
	oc_title2 = title
	url_org = url
	
	if url == None or url == '':
		msg = 'GetContent: Url ' + L("nicht gefunden")	
		Log(msg)
		return ObjectContainer(header=L('Fehler'), message=msg)
	if offset:
		oc_title2 = title_org + ' | %s...' % offset			

	serial = Dict['serial']
	username = Prefs['username']
	local_url=''; callNoOPML=False
	base_url = 'https://tunein.com'				

	max_count = 0									# Default: keine Begrenzung
	if Prefs['maxPageContent']:
		max_count = int(Prefs['maxPageContent'])	# max. Anzahl Einträge ab offset

	# ------------------------------------------------------------------	
	# Favoriten-Ordner,  Custom Url											Favoriten-Ordner
	# ------------------------------------------------------------------
	if "c=presets" in url:
		Log("c=presets: " + url)
		oc = FolderMenuList(url=url, title=title)
		
		if Prefs['UseFavourites']:
			Log('Folder + Custom Menues')
			title = L('Neuer Ordner fuer Favoriten') 
			foldername = str(Prefs['folder'])
			if foldername != 'None':
				summ = L('Name des neuen Ordners') + ': ' + foldername
				oc.add(DirectoryObject(
					key = Callback(Folder, ID='addFolder', title=title, foldername=foldername, folderId='dummy'),
					title = title, summary=summ, thumb=R(ICON_FOLDER_ADD) 
				)) 
		
			title = L('Ordner entfernen') 
			summ = L('Ordner zum Entfernen auswaehlen')
			oc.add(DirectoryObject(
				key = Callback(FolderMenu, title=title, ID='removeFolder', preset_id='dummy'), 
				title = title, summary=summ, thumb=R(ICON_FOLDER_REMOVE) 
			))

	# ------------------------------------------------------------------	 Custom Url	
			# Button für Custom Url 
			# Einstellungen:  Felder Custom Url/Name müssen ausgefüllt sein, Custom Url mit http starten
			#	Custom Url wird hier nur hinzugefügt - Verschieben + Löschen erfolgt als Favorit in
			#		StationList 
			if Prefs['custom_url'] or Prefs['custom_name']: 		# Custom Url/Name - ausgefüllt 
				custom_url 	= str(Prefs['custom_url']).strip()
				custom_name = str(Prefs['custom_name']).strip()			# ungeprüft!
				sidExist,foldername,guide_id,foldercnt = SearchInFolders(preset_id=custom_url, ID=custom_url) 
				Log(sidExist)
				Log('custom_url: ' + custom_url); Log(custom_name)
				if custom_url == '' or custom_name == '':
					error_txt = L("Custom Url") + ': ' + L("Eintrag fehlt fuer Url oder Name")
					error_txt = error_txt.decode(encoding="utf-8", errors="ignore")
					return ObjectContainer(header=L('Fehler'), message=error_txt)		
				
				if custom_url.startswith('http') == False: 
					error_txt = L('Custom Url muss mit http beginnen')
					error_txt = error_txt.decode(encoding="utf-8", errors="ignore")
					return ObjectContainer(header=L('Fehler'), message=error_txt)	
						
				if sidExist == False:									# schon vorhanden?
					title = L('Custom Url') + ' ' + L('hinzufuegen')	# hinzufuegen immer in Ordner General	
					summ = custom_name + ' | ' + custom_url
					oc.add(DirectoryObject(key=Callback(Favourit, ID='addcustom', preset_id=custom_url, folderId=custom_name), 
						title=title,summary=summ,thumb=R(MENU_CUSTOM_ADD)))
		return oc

	# ------------------------------------------------------------------	
	# Anpassung RECENTS_URL an Formate (Einstellungen) und serial-ID		RECENTS_URL
	# ------------------------------------------------------------------
	if 'categories/recents' in url:
		formats = Dict['formats']; serial = Dict['serial']
		# Log(formats); Log(serial);
		url = url % (formats, serial)
	# ------------------------------------------------------------------	
	# Anpassung Url Local Radio: Title2 oc, Url setzen, Remove-Button		Local Radio
	# ------------------------------------------------------------------
	skip_SetLocation = False; myLocationRemove = False
	if url.endswith('/radio/local/'):			# Local Radio
		if Prefs['UseMyLocation']:	
			if Dict['myLocation']:				# Region gesetzt - Url anpassen
				url = Dict['myLocation']		
				skip_SetLocation = True
				myLocationRemove = True
				region = stringextract('/radio/', '-r', Dict['myLocation'])
				Log(region)
				oc_title2 = oc_title2 + ' (%s)' % region
	
	
	oc_title2 = oc_title2.decode(encoding="utf-8")
	oc = ObjectContainer(no_cache=True, title2=oc_title2, art=ObjectContainer.art)
	oc = home(oc)
	
	if myLocationRemove:							# Local Radio: Remove-Button
		if Prefs['UseMyLocation']:	
			if Dict['myLocation']:				# Region gesetzt
				summ = L('neu setzen im Menue Orte')
				thumb=R(ICON_MYLOCATION_REMOVE)
				info_title = L('entferne Lokales Radio') + ': >%s<' % region
				oc.add(DirectoryObject(
					key = Callback(SetLocation, url=url, title=info_title, region=region, 
					myLocationRemove='True'), title=info_title, summary=summ, thumb=thumb 	
				)) 			
	# ------------------------------------------------------------------
	# Anpassungen für UseMyLocation: Set-Button								UseMyLocation
	# ------------------------------------------------------------------	
	if Prefs['UseMyLocation'] and skip_SetLocation == False:					
		url_split = url.split('-')[-1]				# Bsp. ../radio/Africa-r101215/
		try:
			url_id = re.search('(\d+)', url_split).group(1)
		except:
			url_id = None
		Log("UseMyLocation: " + url_split); Log(url_id)	
		if  url_id and url_split.startswith('r'):	# show myLocation-button to set region manually
			# summ = L('neu setzen im Menue Orte')
			summ = ''
			thumb=R(ICON_MYLOCATION) 
			region = stringextract('/radio/', '-r', url)
			info_title = L('setze Lokales Radio auf') + ': >%s<' % region
			oc.add(DirectoryObject(
				key = Callback(SetLocation, url=url, title=info_title, region=region, 
				myLocationRemove='False'), title=info_title, summary=summ, thumb=thumb 	
			)) 			
	
	# ------------------------------------------------------------------	
	# 																		Get Content
	# ------------------------------------------------------------------	
	Log('url: ' + url)	
	page, msg = RequestTunein(FunctionName='GetContent', url=url)
	if page == '':	
		return ObjectContainer(header=L('Info'), message=msg)

	# Hinw.: Seite nicht ab initialStateEl begrenzen - fehlt bei api-Ausgaben (Bsp. Recents) 
	#if '"users":' in page:
	#	page = page [:page.find('"users":')]
	Log('page len: ' + str(len(page)))	
	Log(page[:80])
	# Data.Save('xplex',page)		# Debug: Save Content	
	# Log(page)
	link_list = blockextract('guide-item__guideItemLink', page) # Link-List außerhalb json-Bereich
	
	if 'doctypehtml' not in page:								# api-call: Uppercase für Parameter im json-Inhalt
		page = (page.replace('"Title"','"title"').replace('"Image"','"image"').replace('"Category"','"category"')
			.replace('"FollowText"','"followText"').replace('"ShareText"','"shareText"').replace('"Id"','"id"')
			.replace('Type','type').replace('ContainerType','containerType').replace('Token','token')
			.replace('Subtitle','subtitle').replace('Index','index').replace('GuideId','guideId').replace('"Url"','"url"'))			

	indices = blockextract('"index":', page)
	page_cnt = len(indices)
	Log('indices: %s, max_count: %s' % (str(page_cnt), str(max_count)))
	if 	max_count:									# '' = 'Mehr..'-Option ausgeschaltet?
		page_cnt = page_cnt 
		delnr = min(page_cnt, offset)
		del indices[:delnr]
		Log(delnr)				
	Log(len(indices))
		
	for index in indices:		
		# Log('index: ' + index)		
		# einleitenden Container überspringen, dto. hasButtonStrip":true / "hasIconInSubtitle":false /
		#	"expandableDescription" / "initialLinesCount" / "hasExpander":true
		#	Bsp. Bill Burr's Monday Morning Podcast
		if "children" in index:									# ohne eigenen Inhalt, children folgen
			Log('skip: "children" in index')
			continue
		if	'"hasProgressBar":true' in index:					
			Log('skip: "hasProgressBar":true in index')
			continue
			
		index = index.replace('\\"', '*')							# Bsp. Die \"beste\" Erfindung..
		title		= stringextract('"title":', '",', index)		# Sonderbhdl. wg. "\"Sticky Fingers\" ...
		title		= title[1:].replace('\\"', '"')	
		title		= title.replace('\u002F', '/')
		subtitle	= stringextract('"subtitle":"', '"', index)		# Datum lokal
		subtitle	= (subtitle.replace('\u002F', '/').replace('\u003E', '').replace('\u003C', ''))
		publishTime	= stringextract('"publishTime":"', '"', index)	# Format 2017-10-26T16:50:58
		seoName		= stringextract('"seoName":"', '"', index)		# -> url-Abgleich
		if '"description"' in index:
			descr		= stringextract('"description":"', '"', index)	
		else:
			descr		= stringextract('"text":"', '"', index)		# description
		descr	= (descr.replace('\u002F', '/').replace('\u003E', '').replace('\u003C', '')
			.replace('\\r\\n', ' '))

		#if 'Religious Music' in index:									# Debug: Datensatz
		#	Log(index)
		
		myindex	= stringextract('"index":"', '"', index)	
		mytype	= stringextract('"type":"', '"', index)	
		image	= stringextract('"image":"', '"', index)		# Javascript Unicode escape \u002F
		image	= image.replace('\u002F', '/')					# Standard-Icon für Kategorie
		if image == '':
			image=R(ICON)
		FollowText	= stringextract('"followText":"', '"', index)
		ShareText	= stringextract('"shareText":"', '"', index)
		preset_id 	= stringextract('"id":"', '"', index)		# dto. targetItemId, scope, guideId -> url
		guideId 	= stringextract('"guideId":"', '"', index)	# Bsp. t121001218 -> opml-url zum mp3-Quelle
		path 		= stringextract('"path":"', '"', index)		# -> url_title - url-Abgleich
		linkfilter 	= stringextract('"filter":"', '"', index)	# dto.
		linkfilter	= 'filter%3D' + linkfilter
		
		play_part	= stringextract('"play"', '}', index)		# Check auf abspielbaren Inhalt in Programm
		# Log(play_part)
		sec_gId		=  stringextract('"guideId":"', '"', play_part)# macht ev. Programm/Category zur Station		
		if sec_gId.startswith('t') or  sec_gId.startswith('s'):
			 guideId = sec_gId
			 
			
		# bei Bedarf: 	
		Log("%s | %s | %s | %s | %s | %s | %s"	% (myindex,mytype,title,subtitle,publishTime,seoName,FollowText))
		Log("%s | %s | %s | %s | %s | %s"		% (ShareText,descr,linkfilter,preset_id,guideId,path))
			
		if title in ShareText or subtitle in ShareText:		# Ergänzung: Höre .. auf TuneIn
			ShareText = ''			
		if seoName in title:				# seoName = Titel
			seoName = ''
											
		mytype = mytype.title()
	# ------------------------------------------------------------------	
	# 																	Callback Link
	# ------------------------------------------------------------------	
		if mytype == 'Link' or mytype == 'Category' or mytype == 'Program':		# Callback Link
			# die Url im Datensatz ist im Plugin nicht verwendbar ( api-Call -> profiles)
			# 	daher verwenden wir die fertigen Links aus dem linken Menü der Webseite ('guide-item__guideItemLink
			#	Die Links mixt Tunein mit preset_id, guideId, linkfilter. 
			#	Zusätzl. Problem: die Link-Sätze enthalten Verweis auf Folgesatz mit preset_id 
			#	(Bsp. data-nextGuideItem="c100000625")
			# Bisher sicherste Identifizierung (vorher über den Titel = title): Abgleich mit preset_id am
			#	Ende des Links. Bei Sprachen verwendet Tunein (außer bei Bashkirisch) nur linkfilter im Link.
			# Sätze überspringen (url == local_url) - Link zu Station zwar möglich (dann in guideId), aber 
			#	Stream häufig nicht verfügbar (künftige od. zeitlich begrenzte Sendung). 
			# 				
			url_found = False
			if preset_id == 'languages':		# nur mit linkfilter suchen (bei Tunein nur bei Languages)
				url_title = linkfilter
			else:
				url_title = "-%s/" % preset_id
																	
			# Log('url_title: ' + url_title)	# Bei Bedarf
			for link in link_list:
				local_url = base_url + stringextract('href="', '"', link)
				if url_title in local_url:			
					# Log('url_found: ' + local_url)
					url_found = True
					link_list.remove(link)								# Sätze mit ident. linkfilter möglich
					break
					
			if not url_found:
				msg = ('skip: no preset_id in link for: %s | %s' % (title,preset_id)) # selten: Link zu Main Menu, Bsp. Podcast
				Log(msg); Log(preset_id); Log(local_url)
				# return ObjectContainer(header=L('Info'), message=msg)	# nur Debug
				continue
											
			#Log('Link_url: ' + local_url); # Log(image);	# Bei Bedarf
			if url == local_url:
				Log('skip: url=local_url')
				continue
			if local_url == '':					# bei Programmcontainern möglich 
				Log('skip: empty local_url')
				continue			
			
			summ 	= 	subtitle			# summary -> subtitle od. FollowText
			title		= title.decode(encoding="utf-8")
			summ		= summ.decode(encoding="utf-8")
			summ_mehr = L('Mehr...')
			oc.add(DirectoryObject(key = Callback(GetContent, url=local_url, title=title, offset=offset),	
				title=title, summary=summ_mehr, thumb=R(ICON))) 
				
	# ------------------------------------------------------------------	
	# 																	Callback Station
	# ------------------------------------------------------------------	
		if mytype == 'Station' or mytype == 'Topic':					
			if preset_id.startswith('p'):
				preset_id = guideId				# mp3-Quelle in guideId., Bsp. t109814382
			local_url = 'http://opml.radiotime.com/Tune.ashx?id=%s&formats=%s' % (preset_id, Dict['formats'])
			#Log('Station_url: ' + local_url);	# Log(image);	# Bei Bedarf
			
			summ 	= 	subtitle			# summary -> subtitle od. FollowText
			if len(summ) < 11 and descr:	# summary: falls Datum mit description ergänzen
				summ = summ + ' | %s' % descr
			tagline	= FollowText			# Bsp. 377,5K Favoriten od. 16:23 (Topic)
			if tagline == '':				# PHT: leere Parameter absichern 
				tagline = ' '
			title		= title.decode(encoding="utf-8")
			summ		= summ.decode(encoding="utf-8")
			tagline		= tagline.decode(encoding="utf-8")
								
			# bitrate: PHT-dummy -> Blank in StationList		
			oc.add(DirectoryObject(
				key = Callback(StationList, url=local_url, title=title, summ=summ, image=image, typ='Station', bitrate='unknown',
				preset_id=preset_id),
				title=title, summary=summ, tagline=tagline, thumb=image))		
				
		if max_count:
			# Mehr Seiten anzeigen:		
			cnt = len(oc) + offset		# 
			# Log('Mehr-Test: %s | %s | %s' % (len(oc), cnt, page_cnt) )
			if cnt >= page_cnt:			# Gesamtzahl erreicht - Abbruch
				offset=0
				break					# Schleife beenden
			elif len(oc) > max_count:	# Mehr, wenn max_count erreicht
				offset = offset + max_count 	
				title = L('Mehr...') + title_org
				summ_mehr = L('Mehr...') + '(max.: %s)' % page_cnt
				oc.add(DirectoryObject(
					key = Callback(GetContent, url=url, title=title_org, offset=offset),
					title = title, summary=summ_mehr, tagline=L('Mehr...'), thumb=R(ICON_MEHR) 
				)) 
				break					# Schleife beenden		
								
		# break	# Debug Stop
		
	Log('oc: ' + str(len(oc)))	
	if len(oc) == 1:
		if subtitle:					# ev. Hinweis auf künftige Sendung
			title_org = title_org + " | %s" % subtitle	
		msg = L('keine Eintraege gefunden: ' + title_org) 
		Log(msg)
		return ObjectContainer(header=L('Info'), message=msg)
	return oc
	
#-----------------------------
# RequestTunein: die sprachliche Zuordnung steuern wir über die Header Accept-Language und 
#	CONSENT (Header-Auswertung Chrome).
#		
# 2-stufiger Ablauf: 1. HTTP.Request. bei Fehlschlag 2. urllib2.Request
#	notwendig, da trotz identischer URL-Basis die SSL-Kommunikation ablaufen kann.
# Das Problem "Moved Temporarily" im Location“-Header-Feld wird hier nicht behandelt (bisher nicht notwendig),
#	s. get_pls -> Zertifikate-Problem.
# 13.04.2018 Umstellung urllib2.Request auf HTTP.Request wg Nutzerproblem (SLV3_ALERT_BAD_RECORD_MAC), siehe
#	https://forums.plex.tv/discussion/comment/1652108/#Comment_1652108.
#
#	Ab 29.04.2018: 3. Stufe - mit Zertifikatecheck (linux-Zertifikat, s. get_pls)
#		Alternative: user-definiertes Zertifikat (Einstellungen) - z.B. fullchain.pem von Let's Encrypt 
#
#
def RequestTunein(FunctionName, url, GetOnlyHeader=None):
	msg=''
	loc_browser = str(Dict['loc_browser'])			# ergibt ohne str: u'de
	loc = loc_browser.split('_')[0]					# fr_FR -> fr

	try:																# Step 1: HTTP.Request
		Log("RequestTunein, step 1, called from %s" % FunctionName)
		HTTP.Headers['Accept-Language'] = "%s, en;q=0.8" % loc
		HTTP.Headers['CONSENT'] 	= loc_browser
		HEADERS = {'Accept-Language': "%s,en;q=0.8"  % loc, 'CONSENT': loc_browser}
		
		Log(loc_browser); Log(loc); Log(HEADERS)
		if GetOnlyHeader:
			page = HTTP.Request(url).headers	# Dict
			# Log(page)  # Bei Bedarf, nicht kürzen
		else:
			if url.startswith('https://tunein.com/'):							
				page = HTML.ElementFromURL(url, headers=HEADERS, cacheTime=1)
				page = HTML.StringFromElement(page)
			else:													# HTML-Output vermeiden,
				page = HTTP.Request(url, cacheTime=1).content		# bei Podcasts (Web) unvollständige Seiten
	except Exception as exception:
		error_txt = "RequestTunein: %s-1: " % FunctionName  + repr(exception) 
		error_txt = error_txt + ' | ' + url				 			 	 
		Log(error_txt)
		page=''	


	if page == '':	
		msg=''			
		try:																# Step 2: urllib2.Request
			Log("RequestTunein, step 2, called from %s" % FunctionName)
			req = urllib2.Request(url)			
			req.add_header('Accept-Language',  '%s, en;q=0.8' % loc_browser) 	# Quelle Language-Werte: Chrome-HAR
			req.add_header('CONSENT', loc_browser)
			gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)  
			gcontext.check_hostname = False
			gcontext.verify_mode = ssl.CERT_NONE
			# ret = urllib2.urlopen(req, context=gcontext, timeout=UrlopenTimeout)
			ret = urllib2.urlopen(req, context=gcontext)
			if GetOnlyHeader:
				page = getHeaders(ret)		# Dict
				# Log(page)  # Bei Bedarf, nicht kürzen
			else:
				page = ret.read()
		except Exception as exception:
			error_txt = "RequestTunein: %s-2: " % FunctionName  + repr(exception) 
			error_txt = error_txt + ' | ' + url				 			 	 
			msgH = L('Fehler'); msg = error_txt				
			msg =  msg.decode(encoding="utf-8", errors="ignore")
			Log(msg)
			msg = L('keine Eintraege gefunden') + " | %s" % msg	
			page=''
		
	if page == '':	
		msg=''			
		try:																# Step 3: urllib2.Request mit Zertifikat
			Log("RequestTunein, step 3, called from %s" % FunctionName)
			cafile = Core.storage.abs_path(Core.storage.join_path(MyContents, 'Resources', 'ca-bundle.pem'))
			if Prefs['SystemCertifikat']:			# Bsp. "/etc/certbot/live/rols1.dd-dns.de/fullchain.pem"	
				cafile = Prefs['SystemCertifikat']	# Test path.exists in Main
			Log(cafile)
			req = urllib2.Request(url)			
			req.add_header('Accept-Language',  '%s, en;q=0.8' % loc_browser) 	# Quelle Language-Werte: Chrome-HAR
			req.add_header('CONSENT', loc_browser)
			# ret = urllib2.urlopen(req, cafile=cafile, timeout=UrlopenTimeout)
			ret = urllib2.urlopen(req, cafile=cafile)
			if GetOnlyHeader:
				page = getHeaders(ret)		# Dict
				# Log(page)  # Bei Bedarf, nicht kürzen
			else:
				page = ret.read()
		except Exception as exception:
			error_txt = "RequestTunein: %s-3: " % FunctionName  + repr(exception) 
			error_txt = error_txt + ' | ' + url				 			 	 
			msgH = L('Fehler'); msg = error_txt				
			msg =  msg.decode(encoding="utf-8", errors="ignore")
			Log(msg)
			msg = L('keine Eintraege gefunden') + " | %s" % msg	
			page=''	
					
	# Log(page[:600])								# bei Bedarf
	return page, msg
	
#-----------------------------
# Auswertung der Streamlinks. Aufrufe ohne Playliste starten mit Ziffer 4:
#	1. opml-Info laden, Bsp. http://opml.radiotime.com/Tune.ashx?id=s24878
#	2. Test Inhalt von Tune.ashx auf Playlist-Datei (.pls) -
#		2.1. Playlist (.pls oder/und .m3u) laden, bei Problemen mittels urllib2 + Zertifikat
#		2.2. Streamlinks aus Playlist extrahieren -> in url-Liste
#		2.3. Doppler entfernen
#	3. Test Inhalt von Tune.ashx auf .m3u-Datei (Ergebnis überschreibt url-Liste, falls vorh.)
#		Ablauf wie .pls-Url, aber ohne urllib2 (nicht erforderl. bisher)
#	4. Behandlung der url-Liste:
#		4.1. .mp3-Links markieren (ohne Metaprüfung)
#		4.2. Prüfung der Metadaten (getStreamMeta - zeitaufwendig) 
#			4.2.1 Ermittlung Bitrate, Song - falls leer, mit tunein-Daten ergänzen
#			4.2.2 Prüfung auf angehängte Portnummer - url-Ergänzung mit ';' oder '/;'
#			4.2.3 Prüfung auf Endung '.fm/' - url-Ergänzung mit ';' 
#		4.3. letzte Doppler in der url-Liste entfernen
#	5. Aufbau des TrackObjects mit den einzelnen Url's der Liste
#	5.1. Bei Option UseRecording: Erstellung Recording- und Stop-Button
#
@route(PREFIX + '/StationList')
def StationList(url, title, image, summ, typ, bitrate, preset_id):
	Log('StationList: ' + url)
	summ = unescape(summ)
	Log(title);Log(image);Log(summ);Log(typ);Log(bitrate);Log(preset_id)
	title = title.decode(encoding="utf-8", errors="ignore")
	title_org=title; summ_org=summ; bitrate_org=bitrate; typ_org=typ		# sichern
	bitrate = bitrate.replace('unknown', '')	#							# PHT-dummy entf. 
	oc = ObjectContainer(no_cache=True, title2=title, art=ObjectContainer.art)
	
	Log(Client.Platform)				# Home-Button macht bei PHT die Trackliste unbrauchbar 
	client = Client.Platform
	if client == None:
		client = ''
	if client.find ('Plex Home Theater'): # PHT verweigert TrackObject bei vorh. DirectoryObject
		oc = home(oc)					
		
	if summ:
		if 'No compatible stream' in summ or 'Does not stream' in summ: 	# Kennzeichnung + mp3 von TuneIn 
			if 'Tune.ashx?' in url == False:								# "trozdem"-Streams überspringen - s. GetContent
				url = R('notcompatible.enUS.mp3') # Bsp. 106.7 | Z106.7 Jackson
				oc.add(CreateTrackObject(url=url, title=title, summary=summ, fmt='mp3', thumb=image, sid='0'))
				return oc

	if 'Tune.ashx?' in url:						# normaler TuneIn-Link zur Playlist o.ä.
		cont, msg = RequestTunein(FunctionName='StationList, Tune.ashx-Call', url=url)
		if cont == '':
			error_txt = msg.decode(encoding="utf-8", errors="ignore")
			return ObjectContainer(header=L('Fehler'), message=msg)		
		if ': 400' in cont:				# passiert (manchmal) bei 'neuer Versuch' (mit preset_id)
			error_txt = L("keinen Stream gefunden zu")  + '\r\n' + url  + '\r\n' + 'Tunein: %s' % cont
			error_txt = error_txt.decode(encoding="utf-8", errors="ignore")
			Log(error_txt)
			return ObjectContainer(header=L('Fehler'), message=error_txt)	
		Log('Tune.ashx_content: ' + cont)
	else:										# ev. CustomUrl - key="presetUrls"> (direkter Link zur Streamquelle),
		cont = url								# sowie url's aus GetContent- 
		Log('custom_content: ' + cont)
		
	# .pls-Auswertung ziehen wir vor, auch wenn (vereinzelt) .m3u-Links enthalten sein können
	if '.pls' in cont:					# Tune.ashx enthält häufig Links zu Playlist (.pls, .m3u)				
		cont = get_pls(cont)
		if cont.startswith('get_pls-error'): 						# Bsp. Rolling Stones by Radio UNO Digital, pls-Url: 
			cont = cont.decode(encoding="utf-8", errors="ignore")	# http://radiounodigital.com/Players-Tunein/rollingstones.pls
			return ObjectContainer(header=L('Fehler'), message=cont)
	
	# if line.endswith('.m3u'):				# ein oder mehrere .m3u-Links, Bsp. "Absolut relax (Easy Listening Music)"
	if '.m3u' in cont:						# auch das: ..playlist/newsouth-wusjfmmp3-ibc3.m3u?c_yob=1970&c_gender..
		cont = get_m3u(cont)
		Log('m3u-cont: ' + cont)
		if cont == '':
			msg=L('keinen Stream gefunden zu') 
			message="%s %s" % (msg, title)
			return ObjectContainer(header=L('Fehler'), message=message)			

	#	StreamTests ausgelagert zur Mehrfachnutzung (ListMRS)
	url_list, err_flag = StreamTests(cont,summ_org)		
	if len(url_list) == 0:
		if err_flag == True:					# detaillierte Fehlerausgabe vorziehen, aber nur bei leerer Liste
			msg=L('keinen Stream gefunden zu') 
			message="%s %s" % (msg, title)
			return ObjectContainer(header=L('Fehler'), message=message)

	i=1; 
	for line in url_list:
		Log(line)
		url   = line.split('|||')[0]
		summ  = line.split('|||')[1]
		server = url[:80] + '...'
		summ  = '%s | %s' % (summ, server)
		summ = summ.decode('utf-8')
		if summ.strip().startswith('|'):
			summ = summ[2:]
		
		fmt='mp3'								# Format nicht immer  sichtbar - Bsp. http://addrad.io/4WRMHX. Ermittlung
		if 'aac' in url:						#	 in getStreamMeta (contenttype) hier bisher nicht genutzt
			fmt='aac'
		title = title_org + ' | Stream %s | %s'  % (str(i), fmt)
		i=i+1
		Log(url)
		oc.add(CreateTrackObject(url=url, title=title, summary=summ, fmt=fmt, thumb=image, sid=preset_id))
		
	if Prefs['UseRecording'] == True:			# Aufnahme- und Stop-Button
		title = L("Aufnahme") + ' ' + L("starten")		
		oc.add(DirectoryObject(key=Callback(RecordStart,url=url,title=title,title_org=title_org,image=image,
			summ=summ_org,typ=typ_org,bitrate=bitrate_org), title=title,summary=summ,thumb=R(ICON_RECORD)))
		title = L("Aufnahme") + ' ' + L("beenden")		
		oc.add(DirectoryObject(key=Callback(RecordStop,url=url,title=title,summ=summ_org), 
			title=title,summary=summ,thumb=R(ICON_STOP)))
			
	if Prefs['UseFavourites'] == True:	# Favorit hinzufügen/Löschen
		if preset_id != None:			# None möglich - keine Einzelstation, Verweis auf Folgen, Bsp.:
										# # http://opml.radiotime.com/Tune.ashx?c=pbrowse&id=p680102 (stream_type=download)
			sidExist,foldername,guide_id,foldercnt = SearchInFolders(preset_id, ID='preset_id') # vorhanden, Ordner?
			Log('sidExist: ' + str(sidExist))
			Log('foldername: ' + foldername)
			Log('foldercnt: ' + foldercnt)
			Log(summ)
			if sidExist == False:		
				title = L("Favorit") + ' ' + L("hinzufuegen")	# hinzufuegen immer in Ordner General	
				oc.add(DirectoryObject(key=Callback(Favourit, ID='add', preset_id=preset_id, folderId='dummy'), 
					title=title,summary=summ,thumb=R(ICON_FAV_ADD)))
			if sidExist == True:	
				summ =title_org	+ ' | ' + L('Ordner') + ': ' + 	foldername	# hier nur Station + Ordner angeben,
				title = L("Favorit") + ' ' + L("entfernen")					#  Server + Song entfallen
				oc.add(DirectoryObject(key=Callback(Favourit, ID='remove', preset_id=preset_id, folderId='dummy'), 
					title=title,summary=summ,thumb=R(ICON_FAV_REMOVE)))

				title = L("Favorit") + ' ' + L("verschieben")	# preset_number ist Position im Ordner
				summ = L('Ordner zum Verschieben auswaehlen')				
				oc.add(DirectoryObject(key=Callback(FolderMenu, title=title, ID='moveto', preset_id=preset_id), 
					title = title, summary=summ, thumb=R(ICON_FAV_MOVE) 
				)) 	
											
	Log(len(url_list))		
	url_list = repl_dop(url_list)				# Doppler entfernen	
	Log(len(url_list))		
		
	return oc
#-----------------------------
# Wrapper für getStreamMeta. Nutzung durch StationList + ListMRS
#	Für jede Url erfolgt in getStreamMeta eine Headerauswertung; falls erforderlich wird die Url angepasst 
#		(Anhängen von ";" oder "/;"), falls vorhanden werden bitrate + song für summary gespeichert. 
#	Rückgabe: Liste der aktualisierten Url mit summary-Infos.
#	url_list = Liste von Streamlinks aus Einzel-Url, .m3u- oder .pls-Dateien.
#	
def StreamTests(url_list,summ_org):
	Log('StreamTests');
	summ = ''
	
	max_streams = 0								# Default: keine Begrenzung
	if Prefs['maxStreamsPerStation']:
		max_streams = int(Prefs['maxStreamsPerStation'])	# max. Anzahl Einträge ab offset
	Log('max_streams: ' + str(max_streams))
	
	lines = url_list.splitlines()
	err_flag = False; err=''					# Auswertung nach Schleife	
	url_list = []
	line_cnt = 0								# Einzelzählung
	max_streams = int(max_streams)
	for line in lines:
		line_cnt = line_cnt + 1			
		Log('line %s (max. %s): %s' % (line_cnt, str(max_streams), line))
		url = line

		if url.startswith('http'):				# rtpm u.ä. ignorieren
			if url.endswith('.mp3'):			# .mp3 bei getStreamMeta durchwinken
				st=1; ret={}
			else:
				ret = getStreamMeta(url)		# Sonderfälle: Shoutcast, Icecast usw. Bsp. http://rs1.radiostreamer.com:8020,
				Log(ret)						# 	http://217.198.148.101:80/
				st = ret.get('status')	
			Log('ret.get.status: ' + str(st))
			
			if st == 0:							# nicht erreichbar, verwerfen. Bsp. http://server-uk4.radioseninternetuy.com:9528
				err = ret.get('error')			# Bsp.  City FM 92.9 (Taichung, Taiwan):
				err = err + '\r\n' + url		#	URLError: timed out, http://124.219.41.230:8000/929.mp3
				err_flag = True
				Log(err)
				# return ObjectContainer(header=L('Fehler'), message=err) # erst nach Durchlauf der Liste, s.u.
				continue							
			else:
				if ret.get('metadata'):					# Status 1: Stream ist up, Metadaten aktualisieren (nicht .mp3)
					metadata = ret.get('metadata')
					Log('metadata:'); Log(metadata)						
					bitrate = metadata.get('bitrate')	# bitrate aktualisieren, falls in Metadaten vorh.
					Log(bitrate)
					try:
						song = metadata.get('song')		# mögl.: UnicodeDecodeError: 'utf8' codec can't decode..., Bsp.
						song = song.decode('utf-8')		# 	'song': 'R\r3\x90\x86\x11\xd7[\x14\xa6\xe1k...
						song = unescape(song)
					except:
						song=''
						
					Log('song: ' + str(song)); Log('bitrate: ' + str(bitrate))	# mind. bei bitrate None möglich
					if song.find('adw_ad=') == -1:		# ID3-Tags (Indiz: adw_ad=) verwerfen
						if bitrate and song:							
							summ = 'Song: %s | Bitrate: %sKB' % (song, bitrate) # neues summary
						if bitrate and song == '':	
							summ = '%s | Bitrate: %sKB' % (summ_org, bitrate)		# altes summary ergänzen
					Log('summ: ' + summ)		
				if  ret.get('hasPortNumber') == 'true': # auch SHOUTcast ohne Metadaten möglich, Bsp. Holland FM Gran Canaria,
					if url.endswith('/'):				#	http://stream01.streamhier.nl:9010
						url = '%s;' % url
					else:
						url = '%s/;' % url
				else:	
					if url.endswith('.fm/'):			# Bsp. http://mp3.dinamo.fm/ (SHOUTcast-Stream)
						url = '%s;' % url
					else:								# ohne Portnummer, ohne Pfad: letzter Test auf Shoutcast-Status 
						#p = urlparse(url)				# Test auf url-Parameter nicht verlässlich
						#if 	p.params == '':	
						url_split = url.split('/')		
						Log(len(url_split))
						if len(url_split) <= 4:			# Bsp. http://station.io, http://sl64.hnux.com/
							if url.endswith('/'):
								url = url[:len(url)-1]	# letztes / entfernen 
							# 27.09.2018 Verzicht auf "Stream is up"-Test. Falls keine Shoutcast-Seite, würde der
							#	Stream geladen, was hier zum Timeout führt. Falls erforderlich, hier Test auf 
							#  	ret.get('shoutcast') voranstellen.
							#cont = HTTP.Request(url).content# Bsp. Radio Soma -> http://live.radiosoma.com
							#if 	'<b>Stream is up' in cont:			# 26.09.2018 früheres '.. up at' manchmal zu lang
							#Log('Shoutcast ohne Portnummer: <b>Stream is up at')
							shoutcast = str(ret.get('shoutcast'))
							Log(ret.get('shoutcast'))
							if 'shoutcast' in shoutcast.lower(): # an Shoutcast-url /; anhängen
								url = '%s/;' % url	
																		
			Log('append: ' + url)	
			url_list.append(url + '|||' + summ)			# Liste für CreateTrackObject				
			if max_streams:							# Limit gesetzt?
				if line_cnt >= max_streams:
					break 
	return url_list, err_flag
#-----------------------------
def get_pls(url):               # Playlist extrahieren
	Log('get_pls: ' + url)
	
	# erlaubte Playlist-Formate - Endungen oder Fragmente der Url:
	#	Bsp. http://www.asfradio.com/launch.asp?p=pls
	format_list = ['.pls', '.m3u', '=pls', '=m3u', '=ram', '=asx']
	
	urls =url.splitlines()	# mehrere möglich, auch SHOUTcast- und m3u-Links, Bsp. http://64.150.176.192:8043/

	pls_cont = []
	for url in urls:
		# Log(url)
		cont = url.strip()
		if url.startswith('http') == False:		# Sicherung, falls Zeile keine Url enthält (bisher aber nicht gesehen)
			continue
		isInFormatList = False	
		for pat in format_list:				# Url mit Playlists
			if pat in url:	
				isInFormatList = True		
				break
													# 1. Versuch (2-step)
		if 	isInFormatList:	# .pls auch im Pfad möglich, Bsp. AFN: ../AFNE_WBN.pls?DIST=TuneIn&TGT=..
			cont, msg = RequestTunein(FunctionName='get_pls - isInFormatList', url=url)
		cont = cont.strip()
		Log('cont1: ' + cont)

		# Zertifikate-Problem (vorwiegend unter Windows):
		# Falls die Url im „Location“-Header-Feld eine neue HTTPS-Adresse enthält (Moved Temporarily), ist ein Zertifikat erforderlich.
		# 	Performance: das große Mozilla-Zertifikat cacert.pem tauschen wir gegen /etc/ssl/ca-bundle.pem von linux (ca. halbe Größe).
		#	Ab 29.04.2018: alternativ user-definiertes Zertifikat (Einstellungen) - wie RequestTunein
		#	Aber: falls ssl.SSLContext verwendet wird, schlägt der Request fehl.
		#	Hinw.: 	gcontext nicht mit	cafile verwenden (ValueError)
		#	Bsp.: KSJZ.db SmoothLounge, Playlist http://smoothlounge.com/streams/smoothlounge_128.pls
		# Ansatz, falls dies unter Windows fehlschlägt: in der url-Liste nach einzelner HTP-Adresse (ohne .pls) suchen
		
		if cont == '':								# 2. Versuch
			try:
				req = urllib2.Request(url)
				cafile = Core.storage.abs_path(Core.storage.join_path(MyContents, 'Resources', 'ca-bundle.pem'))
				if Prefs['SystemCertifikat']:		# Bsp. "/etc/certbot/live/rols1.dd-dns.de/fullchain.pem"	
					cafile = Prefs['SystemCertifikat']	
				Log(cafile)
				req = urllib2.urlopen(req, cafile=cafile, timeout=UrlopenTimeout) 
				# headers = getHeaders(req)			# bei Bedarf
				# Log(headers)
				cont = req.read()
			except Exception as exception:	
				error_txt = 'get_pls-error: ' + str(exception)	# hier nicht repr() verwenden
				# Rettungsversuch - hilft bei SomaFM-Stationen:
				# HTTP Error 302: Found - Redirection to url 'itunes://somafm.com/xmasrocks130.pls?bugfix=safari7' is not allowed
				if 'itunes://' in error_txt:	# Bsp. http://api.somafm.com/xmasrocks130.pls
					Log(url)
					Log(str(exception))
					url=stringextract('\'', '\'', str(exception))
					url=url.replace('itunes://', 'http://')
					Log('neue itunes-url: ' + url)
					req = urllib2.Request(url)		# 3. Versuch
					req = urllib2.urlopen(req, cafile=cafile, timeout=UrlopenTimeout) 
					cont = req.read()					
					Log(cont)
					if '[playlist]' in cont:		# nochmal gut gegangen
						pass
					else:
						error_txt = 'get_pls-error: itunes-Url not supported by this plugin.' + ' | ' + str(exception)
						return error_txt
				else:	
					error_txt = error_txt + ' | ' + url
					error_txt = error_txt.decode(encoding="utf-8")
					Log(error_txt)
					return error_txt
												
		if cont:									# Streamlinks aus Playlist extrahieren 
			lines =cont.splitlines()	
			for line in lines:						# Bsp. [playlist] NumberOfEntries=1 File1=http://s8.pop-stream.de:8650/
				line = line.strip()
				if line.startswith('http'):
					pls_cont.append(line)
				if '=http' in line:					# Bsp. File1=http://195.150.20.9:8000/..
					line_url = line.split('=')[1]
					pls_cont.append(line_url)						
		 			 	 		   
	pls = pls_cont
	if pls == '':
		Log('pls leer')
		return pls
	lines = repl_dop(pls)
	pls = '\n'.join(lines)
	pls = pls.strip()
	Log(pls[:100])
	return pls
    
#-----------------------------
def get_m3u(url):               # m3u extrahieren - Inhalte mehrerer Links werden zusammengelegt,
	Log('get_m3u: ' + url)		#	Details/Verfügbarkeit holt getStreamMeta
	urls =url.splitlines()	
	
	m3u_cont = []
	for url in urls:	
		# Bsp. http://icy3.abacast.com/progvoices-progvoicesmp3-32.m3u?source=TuneIn
		#	oder Radio Soma http://www.radiosoma.com/RadioSoma_107.9_MHz.m3u
		if url.startswith('http') and '.m3u' in url:	
			try:									
				req, msg = RequestTunein(FunctionName='get_m3u', url=url)
				req = urllib2.unquote(req).strip()	
				# Log(req)	
			except: 	
				req=''
			lines =req.splitlines()				# Einzelzeilen oder kompl. m3u-Datei
			for line in lines:
				if line.startswith('http'):			# skip #EXTM3U, #EXTINF
					m3u_cont.append(line)			# m3u-Inhalt anhängen
		
	pls = m3u_cont	
	lines = repl_dop(pls)					# möglich: identische Links in verschiedenen m3u8-Inhalten, 
	pls = '\n'.join(lines) # 				# Coolradio Jazz: coolradio1-48.m3u, coolradio1-128.m3u, coolradio1-hq.m3u
	pls = pls.strip()
	Log(pls[:100])
	return pls
    
#-----------------------------
def get_details(line):		# line=opml-Ergebnis im xml-Format, mittels Stringfunktionen extrahieren 
	# Log('get_details')	# 
	typ='';local_url='';text='';image='';key='';subtext='';bitrate='';preset_id='';guide_id='';playing=''
	
	typ 		= stringextract('type="', '"', line)
	if typ == '':
		typ = '?'
	local_url 	= stringextract('URL="', '"', line)
	text 		= stringextract('text="', '"', line)
	image 		= stringextract('image="', '"', line)
	if image == '':
		image = R(ICON) 
	key	 		= stringextract('key="', '"', line)
	subtext 	= stringextract('subtext="', '"', line)		# PHT: leere Parameter absichern 
	if subtext == '':
		subtext = 'unknown'
	bitrate 	= stringextract('bitrate="', '"', line)		# PHT: leere Parameter absichern 
	if bitrate == '':
		bitrate = 'unknown'
	preset_id  = stringextract('preset_id="', '"', line)	# Test auf 'u..' in FolderMenuList,
	if preset_id == '':										# daher Blank für PHT
		preset_id = ' '
	guide_id 	= stringextract('guide_id="', '"', line)	# Bsp. "f3"
	playing 	= stringextract('playing="', '"', line)
	if 	playing == subtext:									# Doppel summ. + tagline vermeiden
		playing = ''
	is_preset  = stringextract('is_preset="', '"', line)	# true = Custom-Url
	
	local_url 	= unescape(local_url)
	text 		= unescape(text)
	subtext 	= unescape(subtext)
	playing 	= unescape(playing)
	if playing == '':
		playing = 'unknown'
		
	text		= text.decode(encoding="utf-8")
	subtext		= subtext.decode(encoding="utf-8")
	playing		= playing.decode(encoding="utf-8")
	
	return typ,local_url,text,image,key,subtext,bitrate,preset_id,guide_id,playing,is_preset
	
#-----------------------------
# Codecs, Protocols ... s. Framework/api/constkit.py
#	DirectPlayProfiles s. Archiv/TuneIn2017/00_Hinweis.txt
#	sid = Station-ID (für opml-Call in PlayAudio)
@route(PREFIX + '/CreateTrackObject')
def CreateTrackObject(url, title, summary, fmt, thumb, sid, include_container=False, location=None, 
		includeBandwidths=None, autoAdjustQuality=None, hasMDE=None, **kwargs):
	Log('CreateTrackObject: ' + url); Log(include_container)
	Log(title);Log(summary);Log('fmt: ' + fmt);Log(thumb);

	if fmt == 'mp3' or fmt == 'ogg':
		container = Container.MP3
		# container = 'mp3'
		audio_codec = AudioCodec.MP3
	elif fmt == 'aac':
		container = Container.MP4
		# container = 'aac'
		audio_codec = AudioCodec.AAC
	elif fmt == 'hls':
		protocol = 'hls'
		container = 'mpegts'
		audio_codec = AudioCodec.AAC	
	elif fmt == 'asf':						# klappt nicht mit  http://mediau.yle.fi/liveklassinen?MSWMExt=.asf 
		container = 'asf'
		audio_codec = audioCodec = 'wmav2'

	title = title.decode(encoding="utf-8", errors="ignore")
	summary = summary.decode(encoding="utf-8", errors="ignore")

	random.seed()						
	rating_id = random.randint(1,10000)
	rating_key = 'rating_key-' + str(rating_id)
	Log(rating_key)

	track_object = TrackObject(
		key = Callback(CreateTrackObject, url=url, title=title, summary=summary, fmt=fmt, thumb=thumb, sid=sid,  
				include_container=True, location=None, includeBandwidths=None, autoAdjustQuality=None, hasMDE=None),
		rating_key = rating_key,	
		title = title,
		summary = summary,
		# art=thumb,					# Auflösung i.d.R. zu niedrig
		thumb=thumb,
		items = [
			MediaObject(
				parts = [
					PartObject(key=Callback(PlayAudio, url=url,ext=fmt,sid=sid)) # Bsp. runtime- Aufruf: PlayAudio.mp3 
				],
				container = container,
				audio_codec = audio_codec,
				# bitrate = 128,		# bitrate entbehrlich
				audio_channels = 2		# audio_channels entbehrlich
			)
		]
	)

	if include_container:
		return ObjectContainer(objects=[track_object])
	else:
		return track_object

#-----------------------------
@route(PREFIX + '/PlayAudio') 
#	Google-Translation-Url (lokalisiert) im Exception-Fall getestet - funktioniert mit PMS nicht
def PlayAudio(url, sid, **kwargs):
	Log('PlayAudio'); Log(url); Log(sid)

	if url is None or url == '':			# sollte hier nicht vorkommen
		Log('Url fehlt!')
		# return ObjectContainer(header='Error', message='Url fehlt!') # Web-Player: keine Meldung
		url=GetLocalUrl()					# lokale mp3-Nachricht,  s.u. GetLocalUrl
		
	if url:
		if url == "http://myradio/live/stream.mp3":	# Scherzkeks: Einstellungen-Beispiel kopiert
			return Redirect(R('tonleiter_harfe.mp3'))
						
		if 'notcompatible.enUS.mp3' in url:
			url = R('notcompatible.enUS.mp3')	# Kennzeichnung + mp3 von TuneIn 
			
		# Header-Check + audience-opml-Cal jweils 2-teilig (für Windows HTTP.Requests, 
		#	für Linux u.a. urllib2.Request)	
		page, msg = RequestTunein(FunctionName='PlayAudio, Header-Check', url=url,GetOnlyHeader=True)
		# Log(page)								# bei Bedarf, page hier Dict

		if 'text/html' in str(page):
			Log('Error: Textpage ' + url)
			return Redirect(R('textpage.mp3'))	# mp3: not a stream - this is a text page
		if 'HTTP Error' in msg:					# beliebiger HTTP-error
			url=GetLocalUrl()
			return Redirect(url)
		try:									# möglich: 'HTTPHeaderProxy' object has no attribute 'get'
			stype = page.get('content-type')
			if 	stype == 'video/x-ms-asf':
				url=GetLocalUrl()
				return Redirect(url)
		except Exception as exception:
			error_txt = "error get content-type: " + repr(exception) 
			Log(error_txt)
		 				
		if sid == None:							# Bsp. Der Feinmann-Translator http://www.dradio.de/wurf-tracks/112586.1420.mp3
			sid = '0'
		if sid.startswith('s') and len(sid) > 1:			# '0' = MyRadioStatios + notcompatible stations
			# audience-opml-Call dient der Aufnahme in Recents - nur stations (Bsp. s202726, p799140 nicht - kein Lifestream).
			#	aus Chrome-Analyse - siehe Chrome_1Live_Curl.txt - Wiedergabe des Streams allein reicht tunein nicht für Recent!
			#	Custom-Url ausschließen, Bsp. sid: "u21"
			#	
			audience_url='https://opml.radiotime.com/Tune.ashx?audience=Tunein2017&id=%s&render=json&formats=%s&type=station&serial=%s&partnerId=RadioTime&version=2.22'
			audience_url = audience_url % (sid, Dict['formats'], Dict['serial'])
			Log('audience_url: ' + audience_url)
			page, msg = RequestTunein(FunctionName='PlayAudio, audience_url', url=audience_url)
			Log(page[:30])									# falls OK: "status": "200"
			if page == '':
				url=GetLocalUrl()							
	else:		
		url=GetLocalUrl()					# lokale mp3-Nachricht,  s.u. GetLocalUrl	
		
	return Redirect(url)
	
#-----------------------------
def GetLocalUrl(): 						# lokale mp3-Nachricht, übersetzt,  - nur für PlayAudio
	loc = str(Dict['loc'])
	url=R('not_available_en.mp3')		# mp3: Sorry, this station is not available
	if loc == 'de':
		url=R('not_available_de.mp3')	# mp3: Dieser Sender ist leider nicht verfügbar	
	if loc == 'fr':
		url=R('not_available_fr.mp3')	# mp3: Désolé, cette station n'est pas disponible	
	if loc == 'da':
		url=R('not_available_da.mp3')	# mp3: Beklager, denne station er ikke tilgængelig	
	if loc == 'uk':
		url=R('not_available_uk.mp3')	# mp3: На жаль, ця станція недоступна	
	if loc == 'pl':
		url=R('not_available_pl.mp3')	# mp3: Przepraszamy, ta stacja nie jest dostępna	
	return url
	
####################################################################################################
#									Favoriten-/Ordner-Funktionen
####################################################################################################
#-----------------------------
# Rückgabe True, Ordnernamen, guide_id, foldercnt - True, falls ein Favorit mit preset_id existiert
#	
def SearchInFolders(preset_id, ID):	
	Log('SearchInFolders')
	preset_id = str(preset_id)			# None-Schutz (sollte hier nicht mehr vorkommen)
	Log('preset_id: ' + preset_id)
	Log('ID: ' + ID)
	serial = Dict['serial']	
	
	username = Prefs['username']
	url = 'http://opml.radiotime.com/Browse.ashx?c=presets&partnerId=RadioTime&serial=%s' % serial	
	page, msg = RequestTunein(FunctionName='SearchInFolders: Ordner-Liste laden', url=url)
	if page == '':
		error_txt = msg.decode(encoding="utf-8", errors="ignore")
		Log(error_txt)
		return ObjectContainer(header=L('Fehler'), message=error_txt)		
	Log(page[:10])
	
	foldercnt = page.count('guide_id="f')
	foldername = ''
	guide_id = ''
	if foldercnt == 0:			# Ordnerübersicht entw. ohne oder mind.2 (General + x)
		foldercnt = 1
		guide_id = 'f1'
		foldername = 'General'
		if ID == 'foldercnt':
			return True, foldername, guide_id, str(foldercnt)
		if ID == 'preset_id' or ID == 'custom_url':		# ID='custom_url': preset_id=custom_url			
			if preset_id in page:
				return True, foldername, guide_id, str(foldercnt)
			else:
				return False, foldername, guide_id, str(foldercnt)
	else:							# einz. Ordner abklappern
		if ID == 'foldercnt':
			return True, foldername, guide_id, str(foldercnt)
			
		if ID == 'preset_id' or ID == 'custom_url':		# 	Fav's preset_id od. custom_url in den Ordnern vorhanden?
			outlines = blockextract('outline type="link"', page)
			for outline in outlines:
				ordner_url = stringextract('URL="', '"', outline)
				ordner_url = unescape(ordner_url) 
				foldername = stringextract('title=', '&', ordner_url)
				guide_id = stringextract('guide_id=', '&', ordner_url)
				page, msg = RequestTunein(FunctionName='SearchInFolders: Ordner-Inhalt laden', url=ordner_url)
				if preset_id in page:
					return True, foldername, guide_id, str(foldercnt)				
		
	return False, foldername, guide_id, str(foldercnt)	
	
#-----------------------------
# ermittelt Inhalte aus den Profildaten
#	ID='favoriteId': Rückgabe der FavoriteId (kennzeichnet die Position des Fav mit preset_id im Profil),
#					Abgleich erfolgt mit "Id"
#					falls preset_id mit u startet (Bsp. u21), handelt es sich um eine Custom Url,
#					Abgleich erfolgt mit "FavoriteId" (preset_id ohne u)
#	
def SearchInProfile(ID, preset_id):	
	Log('SearchInProfile')
	Log('preset_id: ' + preset_id)
	custom = False
	if preset_id.startswith('u'):			# custom-url: u entfernen für Abgleich mit FavoriteId
		preset_id = preset_id[1:]
		custom = True
	
	Log('ID: ' + ID)
	serial = Dict['serial']	

	sidExist,foldername,guide_id,foldercnt = SearchInFolders(preset_id, ID='preset_id') # vorhanden, Ordner-ID?
	# url: Profil laden, Filter: Ordner favoriteId - nur json-Format möglich
	url = 'https://api.tunein.com/profiles/me/follows?folderId=%s&filter=favorites&formats=mp3,aac,ogg&serial=%s&partnerId=RadioTime' % (guide_id,serial)	
		
	favoriteId = guide_id
	if ID == 'favoriteId':
		page, msg = RequestTunein(FunctionName='SearchInProfile: favoriteId suchen', url=url)
		if page == '':
			error_txt = msg.decode(encoding="utf-8", errors="ignore")
			Log(error_txt)
			return ObjectContainer(header=L('Fehler'), message=error_txt)		
		Log(page[:10])				
		
		indices = blockextract('"Index"', page)
		for index in indices:
			# Log(index)	# bei Bedarf
			if  custom:			# custom-url
				Id = stringextract('FavoriteId":"', '"', index)
			else:
				Id = stringextract('"Id":"', '"', index)
			# Log(Id);Log(preset_id);
			if Id == preset_id:
				favoriteId = stringextract('"FavoriteId":"', '"', index)
				Log('Profil-Index: ' + favoriteId)
				return favoriteId
				
	return favoriteId	# leer - Fehlschlag
	
#-----------------------------
# Favorit hinzufügen/löschen/verschieben
#	Prefs['UseFavourites'] bereits in StationList geprüft
#	Tunein verhindert selbst mehrfaches Hinzufügen 
#	Hinzufügen ohne Ordnerauswahl wie in Tunein - Zielordner ist autom. General, 
#		anschl. Verschieben: Button in StationList -> SearchInFolders -> 
#		FolderMenu -> Favourit (hier zusätzl. SearchInProfile erforderlich)
@route(PREFIX + '/Favourit')		
def Favourit(ID, preset_id, folderId, includeOnDeck=None, **kwargs):		# unexpected keyword 'includeOnDeck'
	Log('Favourit')
	Log('ID: ' + ID); Log('preset_id: ' + preset_id); Log('folderId: ' + folderId);
	serial = Dict['serial']
	loc_browser = str(Dict['loc_browser'])
	username = str(Prefs['username'])	# ev. None
	password = str(Prefs['passwort'])
			
	headers = {'Accept-Language': "%s, en;q=0.8" % loc_browser}
	
	if not Prefs['username']  or not Prefs['passwort']:
		msg = L('Username und Passwort sind fuer diese Aktion erforderlich')
		return ObjectContainer(header=L('Fehler'), message=msg)

	# Query prüft, ob der Tunein-Account bereits mit der serial-ID verknüpft ist, Rückgabe username falls OK 
	#	verknüpfte Geräte: https://tunein.com/devices/
	query_url = 'https://opml.radiotime.com/Account.ashx?c=query&partnerId=%s&serial=%s' % (partnerId,serial)
	# Log(query_url)
	page, msg = RequestTunein(FunctionName='Favourit - association-test', url=query_url)	# 1. Query
	if page == '':	
		return ObjectContainer(header=L('Fehler'), message=msg)							

	Log('Fav-Query: ' + page[:10])				 
	tname  = stringextract('text="', '"', page)	# Bsp. <outline type="text" text="testuser"/>
	is_joined = False
	if tname == Prefs['username']:				
		is_joined = True						# Verknüpfung bereits erfolgt
	if "<fault>" in page:						# trotzdem weiter, Call zur Verknüpfung folgt
		fault =  stringextract('<fault>', '</fault>', page) # Bsp. "No associated account"
		Log(fault)
		
	Log('is_joined: ' + str(is_joined))	
	if is_joined == False:
		# Join verknüpft Account mit serial-ID. Vorhandene Presets werden eingebunden
		# 	Ersetzung: partnerId, username, password, serial
		join_url = ('https://opml.radiotime.com/Account.ashx?c=join&partnerId=%s&username=%s&password=%s&serial=%s' 
					% (partnerId,username,password,serial))

		page, msg = RequestTunein(FunctionName='Favourit - join', url=join_url)				# 2. Join (is_joined=False)
		if page == '':	
			return ObjectContainer(header=L('Fehler'), message=msg)							
		# Log('Fav-Join: ' + page)	# bei Bedarf
		
		status  = stringextract('<status>', '</status>', page)
		Log(status)
		if '200' != status:								# 
			title  = stringextract('<title>', '</title>', page)
			if title == '':
				title  = 'status ' + status
			msg = L('Problem mit Username / Passwort') + ' | Tunein: ' + title	
			Log(msg)
			return ObjectContainer(header=L('Fehler'), message=msg)
			
	# Favoriten hinzufügen/Löschen - ID steuert ('add', 'remove', moveto)
	#		 Custom  Url nur einfügen - danach Behandlung als Favorit 
	#	Angabe des Ordners (folderId) nur für  moveto erf. 
	# 	Ersetzung bei 'moveto': ID,favoriteId,folderId,serial,partnerId
	# 	Ersetzung bei 'add', 'remove': ID,preset_id,serial,partnerId
	#	Sonderbehandlung bei Custom  Url: url=preset_id=custom_url , name=folderId=custom_name -
	#		urllib.quote(folderId) für Leer- u.a. Zeichen in name
	
	if ID == 'addcustom':						# Custom  Url einfügen
		folderId = urllib.quote(folderId)
		fav_url = ('https://opml.radiotime.com/Preset.ashx?render=xml&c=add&name=%s&url=%s&render=xml&formats=mp3&serial=%s&partnerId=%s'
				% (folderId, preset_id, serial,partnerId))	

	if ID == 'moveto':
		folderId 	= folderId.split('f')[1]	# führendes 'f' entfernen, preset_number immer numerisch
		favoriteId 	= SearchInProfile(ID='favoriteId', preset_id=preset_id) # Wert ist bereits numerisch
		if favoriteId == '':					# 'Wahrscheinlichkeit gering			
			msg = L('verschieben') + ' ' + L('fehlgeschlagen')
			Log(msg)
			return ObjectContainer(header=L('Fehler'), message=msg)
		ID = 'move'		# Korrektur
		fav_url = ('https://opml.radiotime.com/favorites.ashx?render=xml&c=%s&favoriteId=%s&folderId=%s&formats=mp3,aac,ogg,flash,html&serial=%s&partnerId=%s'
				% (ID,favoriteId,folderId,serial,partnerId))
				
	if ID == 'add' or ID == 'remove':
		fav_url = ('https://opml.radiotime.com/favorites.ashx?render=xml&c=%s&id=%s&formats=mp3,aac,ogg,flash,html&serial=%s&partnerId=%s' 
				% (ID,preset_id,serial,partnerId))

	page, msg = RequestTunein(FunctionName="Favourit - ID=%s" % ID, url=fav_url)		# 3. Add / Remove
	if page == '':	
		return ObjectContainer(header=L('Fehler'), message=msg)							
	# Log('Fav add/remove: ' + page)
	
	status  = stringextract('<status>', '</status>', page)				# Ergebnisausgabe
	if '200' != status:	
		title  = stringextract('<title>', '</title>', page)
		if title == '':
			title  = 'status ' + status
		msg = L('fehlgeschlagen') + ' | Tunein: ' + title			
		return ObjectContainer(header=L('Fehler'), message=msg)
	else:
		if ID == 'add':											# 'add'
			msg = L("Favorit") + ' ' + L("hinzugefuegt")
		if ID == 'addcustom':									# 'addcustom'
			msg = L("Custom Url") + ' ' + L("hinzugefuegt")
		elif  ID == 'remove':	 								# 'remove'
			msg = L("Favorit") + ' ' + L("entfernt")	
		elif  ID == 'move':	 									# 'move'
			msg = L("Favorit") + ' ' + L("verschoben")
				
		return ObjectContainer(header=L('OK'), message=msg)		

#-----------------------------
@route(PREFIX + '/FolderMenuList')
# Direktaufruf von GetContent
# ID = folderId, url mit serial-id vorbelegt	
def FolderMenuList(url, title):	
	Log('FolderMenuList')
	
	page, msg = RequestTunein(FunctionName='FolderMenu: Liste laden', url=url)	
	if page == '':
		error_txt = msg.decode(encoding="utf-8", errors="ignore")
		Log(error_txt)
		return ObjectContainer(header=L('Fehler'), message=error_txt)
	Log(len(page))
	Log(page[:100])
	
	title	= stringextract('<title>', '</title>', page)
	title = unescape(title)
	title = title.decode(encoding="utf-8")
	oc = ObjectContainer(no_cache=True, title2=title, art=ObjectContainer.art)	
	oc = home(oc)

	items = blockextract('outline type', page)
	Log(len(items))
	for item in items:
		# Log('item: ' + items)	
		typ,local_url,text,image,key,subtext,bitrate,preset_id,guide_id,playing,is_preset = get_details(line=item)			
		Log('%s | %s | %s |%s | %s' % (typ,text,subtext,playing,bitrate))
		Log('%s | %s | %s |%s' % (preset_id,guide_id,local_url,image))
		if preset_id.startswith('u'):				# Custom-Url -> Station
			typ = 'audio'
		if typ == 'link':							# Ordner
			image = R(ICON)			
			oc.add(DirectoryObject(
				key = Callback(FolderMenuList, url=local_url, title=text),
				title = text, thumb=image
			)) 
		if typ == 'audio':							# Station
			subtext = subtext.replace('unknown', '  ')	# PHT-dummy 
			playing = playing.replace('unknown', '  ')	# PHT-dummy
			 
			text = text.decode(encoding="utf-8")
			subtext = subtext.decode(encoding="utf-8")
			
			oc.add(DirectoryObject(
				key = Callback(StationList, url=local_url, title=text, summ=subtext, image=image, typ='Station', bitrate=bitrate,
				preset_id=preset_id), title=text, summary=subtext, tagline=playing, thumb=image)) 			
	return oc
#-----------------------------
# Ordner hinzufügen/löschen
#	ID steuert: 'addFolder' / 'removeFolder' 
@route(PREFIX + '/Folder')		
def Folder(ID, title, foldername, folderId, **kwargs):
	Log('Folder')
	Log(ID); Log(title); Log(foldername); Log(folderId);
	serial = Dict['serial']
	oc = ObjectContainer(no_cache=True, title2=title, art=ObjectContainer.art)
	loc_browser = str(Dict['loc_browser'])			
	headers = {'Accept-Language': "%s, en;q=0.8" % loc_browser}
	
	if foldername == 'None' or foldername == '':
		msg=L('Ordnername fehlt') 
		return ObjectContainer(header=L('Fehler'), message=msg)			
	
	if foldername == 'General':
		msg=L('Ordner kann nicht entfernt werden')
		return ObjectContainer(header=L('Fehler'), message=msg)			
	
	# 	Ersetzung: c=ID, name=foldername, serial=serial, partnerId=partnerId
	#	
	if ID == 'addFolder':
		folder_url = ('https://opml.radiotime.com/favorites.ashx?render=xml&c=%s&name=%s&formats=mp3,aac,ogg,flash,html&serial=%s&partnerId=%s' 
					% (ID,foldername,serial,partnerId))	
	else:
		# bei 'removeFolder' wird name=foldername ersetzt durch folderId=folderId 
		#
		folderId = folderId.split('f')[1]	# führendes 'f' entfernen
		folder_url = ('https://opml.radiotime.com/favorites.ashx?render=xml&c=%s&folderId=%s&formats=mp3,aac,ogg,flash,html&serial=%s&partnerId=%s' 
					% (ID,folderId,serial,partnerId))	
						
	page, msg = RequestTunein(FunctionName='Folder: %s' % ID, url=folder_url)
	if page == '':
		error_txt = msg.decode(encoding="utf-8", errors="ignore")
		Log(error_txt)
		return ObjectContainer(header=L('Fehler'), message=error_txt)		
	# Log('Fav-Join: ' + page)

	status  = stringextract('<status>', '</status>', page)				# Ergebnisausgabe
	if '200' != status:	
		title  = stringextract('<title>', '</title>', page)
		msg = L('fehlgeschlagen') + ' | Tunein: ' + title			
		return ObjectContainer(header=L('Fehler'), message=msg)
	else:
		if ID == 'addFolder':							# 'add'
			msg = L("Ordner") + ' ' + L("hinzugefuegt")
		else:											# 'remove'
			msg = L("Ordner") + ' ' + L("entfernt")	
		return ObjectContainer(header=L('OK'), message=msg)			

	return
#-----------------------------
# Ordner auflisten - ID steuert Kennzeichnung:
#	ID='removeFolder' -> Ordner entfernen (Löschbutton in GetContent)
#	ID='moveto' -> Favorit in Ordner verschieben (UseFavourites in StationList)
#	preset_id nur für moveto erforderlich (Kennz. für Favoriten)
#
@route(PREFIX + '/FolderMenu')		
def FolderMenu(title, ID, preset_id, checkFiles=None, **kwargs):	#  unexpected keyword 'checkFiles'
	Log('FolderMenu')
	Log('ID: ' + ID)
	serial = Dict['serial']
	oc = ObjectContainer(no_cache=True, title2=title, art=ObjectContainer.art)
	oc = home(oc)					
	loc_browser = str(Dict['loc_browser'])			
	headers = {'Accept-Language': "%s, en;q=0.8" % loc_browser}
	
	preset_url = 'http://opml.radiotime.com/Browse.ashx?c=presets&partnerId=RadioTime&serial=%s' % serial
	page, msg = RequestTunein(FunctionName='FolderMenu: ID %s, Liste laden' % ID, url=preset_url)	
	if page == '':
		error_txt = msg.decode(encoding="utf-8", errors="ignore")
		Log(error_txt)
		return ObjectContainer(header=L('Fehler'), message=error_txt)
				
	rubriken = blockextract('<outline type="link"', page)		# Ordner-Übersicht
	Log(len(rubriken))	
	if len(rubriken) > 1:										# 1. Ordner (General) ohne Ordner-Urls
		for rubrik in rubriken:
				foldername 	= stringextract('text="', '"', rubrik)		# 1. Ordner immer General
				folderId 	= stringextract('guide_id="', '"', rubrik)	# Bsp. "f3"
				furl 		=  stringextract('URL="', '"', rubrik)
				furl		= unescape(furl)							# wie in SearchInFolders
				items_cnt 	= L('nicht gefunden')
				page, msg = RequestTunein(FunctionName='FolderMenu: %s, Inhalt laden' % foldername, url=furl)	
				items_cnt =  len(blockextract('URL=', page))		# outline unscharf
				
				if ID == 'removeFolder':	# -> Ordner entfernen, 
					title = foldername + ': ' + L('Ordner entfernen') + ' | ' + L('ohne Rueckfrage!')
					summ = L('Anzahl der Eintraege') + ': ' + str(items_cnt)
					thumb = R(ICON_FOLDER_REMOVE)
					if foldername == 'General':
						title = foldername + ': ' + L('Ordner kann nicht entfernt werden')
						thumb = R(ICON_FOLDER_ADD)	
					oc.add(DirectoryObject(
						key = Callback(Folder, ID='removeFolder', title=title, foldername=foldername, folderId=folderId),
						title = title, summary=summ, thumb=thumb
					)) 
				else:	         			# 'moveto' -> Favorit in Ordner verschieben, preset_id=preset_number	
					if 	preset_id in page:	# Fav enthalten - Ordner nicht listen	
						pass
					else:
						title = foldername + ': ' + L('hierhin verschieben') 
						summ = L('Anzahl der Eintraege') + ': ' + str(items_cnt)
						thumb = R(ICON_FAV_MOVE)
						oc.add(DirectoryObject(key=Callback(Favourit, ID='moveto', preset_id=preset_id, folderId=folderId), 
							title=title,summary=summ,thumb=thumb))
			
	return oc

####################################################################################################
#							   Funktionen für Meine Radiostationen
####################################################################################################
# ListMRS lädt eigene Datei "Meine Radiostationen" + listet die enthaltenen Stationen mit
#	Name + Url. Der Button führt zu SingleMRS (trackobject nach Auswertung in StreamTests).
#	path = lokale Textdatei
#	Test  os.path.exists  bereits in Main erfolgt.
# 
@route(PREFIX + '/ListMRS')						
def ListMRS(path):										
	Log('ListMRS'); Log(path) 
	title = L("Meine Radiostationen")
	
	oc = ObjectContainer(title2=title, art=ObjectContainer.art)
	oc = home(oc)					

	try:
		content = Resource.Load(path)
	except:
		content = ''
		
	if content == '' or content == None:
		msg = L("nicht gefunden") + ': ' +  path
		return ObjectContainer(header=L('Fehler'), message=msg)

	max_streams=0										# Limit default
	lines = content.splitlines()
	i=0
	for line in lines:
		i=i+1
		line = line.strip()
		if line.startswith('#') or line == '':			# skip comments
			continue
		try:
			if '#' in line:
				line = line.split('#')[0]				# Kommentar Zeilenende
			name,url = line.split('|')
			name = name.strip(); url = url.strip() 
			name =  name.decode('utf-8')
		except:
			name=''; url=''
		Log(name); Log(url); 
		
		if name=='' and url=='':
			msg = L("fehlerhafte Datei") + ': ' +  path + ' in line %s' % str(i)
			return ObjectContainer(header=L('Fehler'), message=msg)
		
		oc.add(DirectoryObject(key=Callback(SingleMRS, name=name, url=url, 
			max_streams=max_streams, image=R(ICON_MYRADIO)), 
			title=name, summary=url, thumb=R(ICON_MYRADIO)))  	
	
	return oc
#----------------------------------------------------------------
#	Einzelstation zu ListMRS - Meta-Auswertung hier - könnte in ListMRS zum Timeout führen
#	sid='0' für audience-opml-Call in PlayAudio: Einzelstationen ev. tunein-inkompatibel
@route(PREFIX + '/SingleMRS')						
def SingleMRS(name, url, max_streams, image):										
	Log('SingleMRS'); Log(url) 
	
	if url.startswith('http') == False: 
		error_txt = L('Custom Url muss mit http beginnen') + ':\n' + url
		error_txt = error_txt.decode(encoding="utf-8", errors="ignore")
		return ObjectContainer(header=L('Fehler'), message=error_txt)	
							
	name = name.decode('utf-8')	
	oc = ObjectContainer(title2=name, art=ObjectContainer.art)
	Log(Client.Platform)				# Home-Button macht bei PHT die Trackliste unbrauchbar 
	client = Client.Platform
	if client == None:
		client = ''
	if client.find ('Plex Home Theater'): # PHT verweigert TrackObject bei vorh. DirectoryObject
		oc = home(oc)					

	if 'Tune.ashx?' in url:						# TuneIn-Link ebenfalls ermöglichen, Inhalt laden
		try:
			url_list = HTTP.Request(url).content
		except Exception as exception:			
			url_list = ''
		if url_list == '' or 'error' in url_list:
			error_txt = 'My Radiostations - url error:' + '\r\n' + url
			error_txt = error_txt.decode(encoding="utf-8", errors="ignore")
			return ObjectContainer(header=L('Fehler'), message=error_txt)
		Log(url_list)	
		url_list = get_pls(url_list)		
	else:
		url_list = get_pls(url)				# Streamlinks extrahieren, ev. mit Zertifikat
		
	Log(url_list); 
	if url_list == '':
		msg=L('keinen Stream gefunden zu') 
		message="%s %s" % (msg, name)
		return ObjectContainer(header=L('Fehler'), message=message)
		
	if url_list.startswith('get_pls-error'): 					# z.B: Redirection to url ..  is not allowed, einschl.
		cont = url_list.decode(encoding="utf-8")				# itunes-Url not supported by this plugin	
		return ObjectContainer(header=L('Fehler'), message=cont)	
	
	url_list, err_flag =  StreamTests(url_list,summ_org='')
	if len(url_list) == 0:
		if err_flag == True:					# detaillierte Fehlerausgabe vorziehen, aber nur bei leerer Liste
			msg=L('keinen Stream gefunden zu') 
			message="%s %s" % (msg, name)
			return ObjectContainer(header=L('Fehler'), message=message)
	
	i=1;
	for line in url_list:
		Log(line)
		url   = line.split('|||')[0]
		server = url[:80] + '...'
		try:
			summ  = line.split('|||')[1]
		except:
			summ = url
		summ  = '%s | %s' % (summ, server)
		summ = summ.decode('utf-8')		# ev. für song erforderlich
		if summ.strip().startswith('|'):
			summ = summ[3:]
		
		fmt='mp3'								# Format nicht immer  sichtbar - Bsp. http://addrad.io/4WRMHX. Ermittlung
		if 'aac' in url:						#	 in getStreamMeta (contenttype) hier bisher nicht genutzt
			fmt='aac'
		if url.endswith('.asf') or '=asf' in url: # Achtung: www.asfradio.com
			fmt='asf'
		if url.endswith('.ogg') : 				# .ogg in http://mp3.radiox.ch:8000/standard.ogg.m3u
			fmt='ogg'
		title = name + ' | Stream %s | %s'  % (str(i), fmt)
		i=i+1
		oc.add(CreateTrackObject(url=url, title=title, summary=summ, fmt=fmt, thumb=image, sid='0'))
	return oc

####################################################################################################
#									Recording-Funktionen
####################################################################################################
# **kwargs erforderlich für unerwartete Parameter, z.B.  checkFiles (ext. Webplayer)
@route(PREFIX + '/RecordStart')
def RecordStart(url,title,title_org,image,summ,typ,bitrate, **kwargs):			# Aufnahme Start 
	Log('RecordStart')
	Log(sys.platform)
	oc = ObjectContainer(title2=title, art=ObjectContainer.art)
	
	p_prot, p_path = url.split('//')	# Url-Korrektur für streamripper bei Doppelpunkten in Url (aber nicht mit Port) 
	Log(p_path)							#	s. https://sourceforge.net/p/streamripper/discussion/19083/thread/300b7a0f/
										#	dagegen wird ; akzeptiert, Bsp. ..tunein;skey..
	p_path = (p_path.replace('id:', 'id%23').replace('secret:', 'secret%23').replace('key:', 'key%23'))	# ev.  ergänzen
	url_clean = '%s//%s'	% (p_prot, p_path)
	
	AppPath	= Prefs['StreamripperPath']
	Log('AppPath: ' + AppPath)	 
	AppExist = False
	if AppPath:										# Test: PRG existent?
		Log(os.path.exists(AppPath))
		if 'linux' in sys.platform:					# linux2, weitere linuxe?							
			if os.path.exists(AppPath):				
				AppExist = True
		else:										# für andere, spez. Windows kein Test (os.stat kann fehlschlagen)
			AppExist = True		
	else:
		AppExist = False
	if AppExist == False:
		msg= 'Streamripper' + ' ' + L("nicht gefunden")
		Log(msg)
		return ObjectContainer(header=L('Fehler'), message=msg)		
	
	DestDir = Prefs['DownloadDir']					# bei leerem Verz. speichert Streamripper ins Heimatverz.
	Log('DestDir: ' + DestDir)	 
	if DestDir:
		DestDir = DestDir.strip()
		if os.path.exists(DestDir) == False:
			msg= L('Download-Verzeichnis') + ' ' + L("nicht gefunden")
			Log(msg)
			return ObjectContainer(header=L('Fehler'), message=msg)		
					
	# cmd-Bsp.: streamripper http://addrad.io/4WRMHX --quiet -d /tmp -u Mozilla/5.0
	#	30.05.2018 UserAgent hinzugefügt (Error: Access Forbidden (try changing the UserAgent)) -
	#	einige Sender verweigern den Download beim Default Streamripper/1.x
	#	Konfig-Alternative:  /var/lib/plexmediaserver/.config/streamripper/streamripper.ini	
	#	MP3-Problem: streamripper speichert .mp3 im incomplet-Verz. und geht in Endlosschleife -
	#		Versuch mit Titel -> Dateiname plus Timestamp abgebrochen (Endlosschleife bleibt,
	#		streamripper verwendet weiter unterschiedl. Verz., abhängig  von Url) - Code
	#		s. __init__.py_v1.2.5_mp3-download
	UserAgent = "Mozilla/5.0"
	cmd = "%s %s --quiet -d %s -u %s"	% (AppPath, url_clean, DestDir, UserAgent)		
	Log('cmd: ' + cmd)
				
	Log(sys.platform)
	if sys.platform == 'win32':							
		args = cmd
	else:
		args = shlex.split(cmd)							# ValueError: No closing quotation (1 x, Ursache n.b.)
	Log(len(args))
	Log(args)

	for PID_line in Dict['PID']:						# Prüfung auf exist. Aufnahme, spez. für PHT
		Log(PID_line)									# Aufbau: Pid|Url|Sender|Info
		pid_url = PID_line.split('|')[1]
		if pid_url == url:	
			pid = PID_line.split('|')[0]		
			summ = PID_line.split('|')[3]	
			title_new = title_org + ': ' + L('Aufnahme') +  ' ' + L('gestartet')	# Info wg. PHT identisch mit call-Info
			msg =  '%s:\n%s | %s | PID: %s' % (title_new, url, summ, pid)	
			Log(Client.Platform)	
			Log('Test existing Record: ' + msg)
			return ObjectContainer(header=L('Info'), message=msg)

	# Popen-Objekt mit Pid außerhalb nicht mehr ansprechbar (call.pid). Daher speichern wir im Dict die Prozess-ID direkt.
	# PHT-Problem (Linux + Windows): return ObjectContainer nach Dict['PID'].append führt PHT direkt wieder hierher 
	# 	(vor append OK) - Problem der Stackverwaltung im Framwork? Den erneuten Durchlauf von PHT fangen wir oben in 
	#	Prüfung auf exist. Aufnahme ab.
	call=''
	try:
		Log(Client.Platform)	
		call = subprocess.Popen(args, shell=False)		# shell=False erfordert shlex-Nutzung	
		# output,error = call.communicate()				# klemmt hier (anders als im ARD-Plugin)
		Log('call: ' + str(call))						# Bsp. <subprocess.Popen object at 0x7f16fad2e290>
		if str(call).find('object at') > 0:  			# subprocess.Popen object OK
			PID_line = '%s|%s|%s|%s'	% (call.pid, url, title_org, summ) 	# Muster: 																
			Log(PID_line)	
			Dict['PID'].append(PID_line)				# PHT-Problem s.o.
			Log(Dict['PID'])
			Dict.Save()
			title_new = L('Aufnahme') + ' ' + L('gestartet')
			msg =  '%s: \n %s | %s | PID: %s' % (title_new, url, summ, call.pid)
			header = L('Info')
			Log(msg)
			return ObjectContainer(header=L('Info'), message=msg) 		# PHT-Problem s.o.
			return oc
							
	except Exception as exception:
		msgH = L('Fehler'); 
		summ_new = str(exception)
		summ_new = summ_new.decode(encoding="utf-8", errors="ignore")
		title_new = L('Aufnahme fehlgeschlagen')
		Log(summ_new)		
		oc.add(DirectoryObject(
			key = Callback(StationList, url=url, title=title, summ=summ, image=image, typ=typ, bitrate=bitrate,
			preset_id=preset_id),
			title=title_new, summary=summ_new,thumb =R(ICON_CANCEL)))						
		return oc
		
	msg = L('Aufnahme') + ' ' + L('fehlgeschlagen') + '\n' + L('Ursache unbekannt')
	header = L('Fehler')
	Log(msg)	
	return ObjectContainer(header=header, message=msg) 		# nicht mit Callback(StationList) zurück - erzeugt neuen Prozess
	 	
#-----------------------------
@route(PREFIX + '/RecordStop')
def RecordStop(url,title,summ, **kwargs):			# Aufnahme Stop
	Log('RecordStop')
	oc = ObjectContainer(title2=title, art=ObjectContainer.art)
	
	pid = ''
	Log(Dict['PID'])
	for PID_line in Dict['PID']:						# Prüfung auf exist. Aufnahme
		Log(PID_line)									# Aufbau: call|url|title_org|summ
		pid_url = PID_line.split('|')[1]
		if pid_url == url:
			pid = PID_line.split('|')[0]
			Log(pid)
			break
			
	if pid == '' or int(pid) == 0:
		if 	Client.Platform == 'Plex Home Theater':		# PHT-Problem s. RecordStart
			msg = L('Aufnahme') + ' ' + L('beendet')
			return ObjectContainer(header=L('Info'), message=msg)					
		msg = url + ': ' + L('keine laufende Aufnahme gefunden')
		return ObjectContainer(header=L('Fehler'), message=msg)					
			
	# Problem kill unter Linux: da wir hier Popen aus Sicherheitsgründen ohne shell ausführen, hinterlässt kill 
	#	einen Zombie. Dies ist aber zu vernachlässigen, da aktuelle Distr. Zombies nach wenigen Sekunden autom.
	#	entfernen. 
	#	Auch call.terminate() in einem Thread (Thread StreamripperStop wieder entfernt) hinterlässt Zombies.
	#	Alternative (für das Plugin Overkill) wäre die Verwendung von psutil (https://github.com/giampaolo/psutil) 
	pid = int(pid)
	try:
		os.kill(pid, signal.SIGTERM)	# Verzicht auf running-Abfrage os.kill(pid, 0)
		time.sleep(1)
		if 'linux' in sys.platform:		# Windows: 	object has no attribute 'SIGKILL'						
			os.kill(pid, signal.SIGKILL)	
		pidExist = True
	except OSError, err:
		pidExist = False
		error='Error: ' + str(err)
		Log(error)
						
	if pidExist == False:
		header=L('Fehler')
		title_new = str(err) 
		msg =  '%s:\n%s | %s | PID: %s' % (title_new, url, summ, pid)	
	else:
		header=L('Info')
		title_new = L('Aufnahme') + ' ' + L('beendet')
		msg =  '%s:\n%s | %s | PID: %s' % (title_new,url, summ, pid)
			
	Dict['PID'].remove(PID_line)	# Eintrag Prozessliste entfernen - unabhängig vom Erfolg
	Dict.Save()						# PHT springt vor Return wieder zum Anfang RecordStop, PID_line ist entfernt
	return ObjectContainer(header=header, message=msg)		
					
#-----------------------------
@route(PREFIX + '/RecordsList')	# Liste laufender Aufnahmen mit Stop-Button - Prozess wird nicht geprüft!
def RecordsList(title):			# title=L("laufende Aufnahmen")
	Log('RecordsList')
	oc = ObjectContainer(title2=title, art=ObjectContainer.art)
	oc = home(oc)					
	
	for PID_line in Dict['PID']:						# Prüfung auf exist. Aufnahme
		Log(PID_line)									# Aufbau: Pid|Url|Sender|Info
		pid 	= PID_line.split('|')[0]
		pid_url = PID_line.split('|')[1]
		pid_sender = PID_line.split('|')[2]
		pid_summ = PID_line.split('|')[3]
		pid_summ = pid_summ.decode(encoding="utf-8", errors="ignore")
		title_new = L('beenden') + ': ' + pid_sender 
		if not 'unknown' in pid_summ:
			title_new = title_new + ' | ' + pid_summ
		summ_new = pid_url + ' | ' + 'PID: ' + pid			
		oc.add(DirectoryObject(key=Callback(RecordStop,url=pid_url,title=pid_sender,summ=pid_summ), title=title_new,
			summary=summ_new, tagline=pid_url, thumb=R(ICON_STOP)))			       
	
	return oc

####################################################################################################
#									Hilfsfunktionen
####################################################################################################

@route(PREFIX + '/SearchUpdate')
def SearchUpdate(title, start, oc=None):		
	Log('SearchUpdate')
	
	if start=='true':									# Aufruf beim Pluginstart
		if Prefs['InfoUpdate'] == True:					# Hinweis auf neues Update beim Start des Plugins 
			oc,available = presentUpdate(oc,start)
			if available == 'no_connect':
				msgH = L('Fehler'); 
				msg = L('Github ist nicht errreichbar') +  ' - ' +  L('Bitte die Update-Anzeige abschalten')		
				# return ObjectContainer(header=msgH, message=msg)	# skip - das blockt das Startmenü
							
			if 	available == 'true':					# Update präsentieren
				return oc
		
		Log('InfoUpdate = False, no Check')				# Menü Plugin-Update zeigen														
		title = L('Plugin Update') + " | " + L('Plugin Version:') + VERSION + ' - ' + VDATE 	 
		summary=L('Suche nach neuen Updates starten')
		tagline=L('Bezugsquelle') + ': ' + REPO_URL			
		oc.add(DirectoryObject(key=Callback(SearchUpdate, title='Plugin-Update', start='false'), 
			title=title, summary=summary, tagline=tagline, thumb=R(ICON_MAIN_UPDATER)))
		return oc
		
	else:					# start=='false', Aufruf aus Menü Plugin-Update
		oc = ObjectContainer(title2=title, art=ObjectContainer.art)	
		oc,available = presentUpdate(oc,start)
		if available == 'no_connect':
			msgH = L('Fehler'); 
			msg = L('Github ist nicht errreichbar') 		
			return ObjectContainer(header=msgH, message=msg)
		else:
			return oc	
	
		
#-----------------------------
def presentUpdate(oc,start):
	Log('presentUpdate')
	ret = updater.update_available(VERSION)			# bei Github-Ausfall 3 x None
	Log(ret)
	int_lv = ret[0]			# Version Github
	int_lc = ret[1]			# Version aktuell
	latest_version = ret[2]	# Version Github, Format 1.4.1

	if ret[0] == None or ret[0] == False:
		return oc, 'no_connect'
		
	zip_url = ret[5]	# erst hier referenzieren, bei Github-Ausfall None
	url = zip_url
	summ = ret[3]			# History, replace ### + \r\n in get_latest_version, summ -> summary, 
	tag = summ.decode(encoding="utf-8", errors="ignore")  # History -> tag
	Log(latest_version); Log(int_lv); Log(int_lc); Log(tag); Log(zip_url); 
	
	if int_lv > int_lc:								# 2 Update-Button: "installieren" + "abbrechen"
		available = 'true'
		title = L('neues Update vorhanden') +  ' - ' + L('jetzt installieren')
		summary = L('Plugin Version:') + " " + VERSION + ', Github Version: ' + latest_version

		oc.add(DirectoryObject(key=Callback(updater.update, url=url , ver=latest_version), 
			title=title, summary=summary, tagline=tag, thumb=R(ICON_UPDATER_NEW)))
			
		if start == 'false':						# Option Abbrechen nicht beim Start zeigen
			oc.add(DirectoryObject(key = Callback(Main), title = L('Update abbrechen'),
				summary = L('weiter im aktuellen Plugin'), thumb = R(ICON_UPDATER_NEW)))
	else:											# Plugin aktuell -> Main
		available = 'false'
		if start == 'false':						# beim Start unterdrücken
			oc.add(DirectoryObject(key = Callback(Main), 	
				title = L('Plugin aktuell') + " | Home",
				summary = 'Plugin Version ' + VERSION + ' ' + L('ist die neueste Version'),
				tagline = tag, thumb = R(ICON_OK)))			

	return oc,available
#----------------------------------------------------------------  
def blockextract(blockmark, mString):  	# extrahiert Blöcke begrenzt durch blockmark aus mString
	#	blockmark bleibt Bestandteil der Rückgabe - im Unterschied zu split()
	#	Rückgabe in Liste. Letzter Block reicht bis Ende mString (undefinierte Länge!),
	#		Variante mit definierter Länge siehe Plex-Plugin-TagesschauXL (extra Parameter blockendmark)
	#	Verwendung, wenn xpath nicht funktioniert (Bsp. Tabelle EPG-Daten www.dw.com/de/media-center/live-tv/s-100817)
	rlist = []				
	if 	blockmark == '' or 	mString == '':
		Log('blockextract: blockmark or mString leer')
		return rlist
	
	pos = mString.find(blockmark)
	if 	mString.find(blockmark) == -1:
		Log('blockextract: blockmark nicht in mString')
		# Log(pos); Log(blockmark);Log(len(mString));Log(len(blockmark));
		return rlist
	pos2 = 1
	while pos2 > 0:
		pos1 = mString.find(blockmark)						
		ind = len(blockmark)
		pos2 = mString.find(blockmark, pos1 + ind)		
	
		block = mString[pos1:pos2]	# extrahieren einschl.  1. blockmark
		rlist.append(block)
		# reststring bilden:
		mString = mString[pos2:]	# Rest von mString, Block entfernt	
	return rlist  
#----------------------------------------------------------------  
def stringextract(mFirstChar, mSecondChar, mString):  	# extrahiert Zeichenkette zwischen 1. + 2. 
	pos1 = mString.find(mFirstChar)						# return '' bei Fehlschlag
	ind = len(mFirstChar)
	#pos2 = mString.find(mSecondChar, pos1 + ind+1)		
	pos2 = mString.find(mSecondChar, pos1 + ind)		# ind+1 beginnt bei Leerstring um 1 Pos. zu weit
	rString = ''

	if pos1 >= 0 and pos2 >= 0:
		rString = mString[pos1+ind:pos2]	# extrahieren 
		
	#Log(mString); Log(mFirstChar); Log(mSecondChar); 	# bei Bedarf
	#Log(pos1); Log(ind); Log(pos2);  Log(rString); 
	return rString
#----------------------------------------------------------------  	
def my_rfind(left_pattern, start_pattern, line):  # sucht ab start_pattern rückwärts + erweitert 
#	start_pattern nach links bis left_pattern.
#	Rückgabe: Position von left_pattern und String ab left_pattern bis einschl. start_pattern	
#	Mit Python's rfind-Funktion nicht möglich

	# Log(left_pattern); Log(start_pattern); 
	if left_pattern == '' or start_pattern == '' or line.find(start_pattern) == -1:
		return -1, ''
	startpos = line.find(start_pattern)
	# Log(startpos); Log(line[startpos-10:startpos+len(start_pattern)]); 
	i = 1; pos = startpos
	while pos >= 0:
		newline = line[pos-i:startpos+len(start_pattern)]	# newline um 1 Zeichen nach links erweitern
		# Log(newline)
		if newline.find(left_pattern) >= 0:
			leftpos = pos						# Position left_pattern in line
			leftstring = newline
			# Log(leftpos);Log(newline)
			return leftpos, leftstring
		i = i+1				
	return -1, ''								# Fehler, wenn Anfang line erreicht
#----------------------------------------------------------------  	
def unescape(line):	# HTML-Escapezeichen in Text entfernen, bei Bedarf erweitern. ARD auch &#039; statt richtig &#39;
#					# s.a.  ../Framework/api/utilkit.py
	if line == None:
		return line
	line_ret = (line.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
		.replace("&#39;", "'").replace("&#039;", "'").replace("&quot;", '"').replace("&#x27;", "'")
		.replace("&ouml;", "ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&szlig;", "ß")
		.replace("&Ouml;", "Ö").replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&apos;", "'"))
		
	# Log(line_ret)		# bei Bedarf
	return line_ret	
#----------------------------------------------------------------  	
def cleanhtml(line): 	# ersetzt alle HTML-Tags zwischen < und >  mit 1 Leerzeichen
	cleantext = line
	cleanre = re.compile('<.*?>')
	cleantext = re.sub(cleanre, ' ', line)
	return cleantext
#----------------------------------------------------------------  
def repl_dop(liste):	# Doppler entfernen, im Python-Script OK, Problem in Plex - s. PageControl
	mylist=liste
	myset=set(mylist)
	mylist=list(myset)
	mylist.sort()
	return mylist
#----------------------------------------------------------------  
def serial_random(): # serial-ID's für tunein erzeugen (keine Formatvorgabe bekannt)
	basis = ['b8cfa75d', '4589', '4fc19', '3a64', '2c2d24dfa1c2'] # 5 Würfelblöcke
	serial = []
	for block in basis:
		new_block = ''.join(random.choice(block) for i in range(len(block)))
		serial.append(new_block)
	serial = '-'.join(serial)
	return serial
#---------------------------------------------------------------- 
# s. Start(), Locale-Probleme, Lösung czukowski
def L(string):		
	local_string = Locale.LocalString(string)
	local_string = str(local_string).decode()
	# Log(string); Log(local_string)
	return local_string
#----------------------------------------------------------------
def myL(string):		# Erweiterung, falls L(string) von czukowski nicht funktioniert
	loc_file = Dict['loc_file']
	if os.path.exists(loc_file) == False:			# czukowski-Lösung
		local_string = Locale.LocalString(string)		
		return str(local_string).decode()
	
	lines = Resource.Load(loc_file)
	lines = lines.splitlines()
	lstring = ''	
	for line in lines:
		term1 = line.split(':')[0].strip()
		term1 = term1.strip()
		term1 = term1.replace('"', '')			# Hochkommata entfernen
		# Log(term1)
		if term1 == string:						# string stimmt mit Basis-String überein?
			lstring = line.split(':')[1]		# 	dann Ziel-String zurückgeben
			lstring = lstring.strip()
			lstring = lstring.replace('"', '') 	# Hochkommata + Komma entfernen
			lstring = lstring.replace(',', '')
			break
			
	Log(string); Log(lstring)		
	if lstring:
		return lstring.decode(encoding="utf-8", errors="ignore")
	else:
		return string						# Rückgabe Basis-String, falls kein Paar gefunden
#----------------------------------------------------------------
####################################################################################################
#									Streamtest-Funktionen
####################################################################################################
# getStreamMeta ist Teil von streamscrobbler-python (https://github.com/dirble/streamscrobbler-python),
#	angepasst für dieses Plugin (Wandlung Objekte -> Funktionen, Prüfung Portnummer, Rückgabe Error-Wert).
#	Originalfunktiom: getAllData(self, address).
#	
#	getStreamMeta wertet die Header der Stream-Typen und -Services Shoutcast, Icecast / Radionomy, 
#		Streammachine, tunein aus und ermittelt die Metadaten.
#		Zusätzlich wird die Url auf eine angehängte Portnummer geprüft.
# 	Rückgabe 	Bsp. 1. {'status': 1, 'hasPortNumber': 'false', 'shoutcast': 'false', 'metadata': false, error': error}
#				Bsp. 2.	{'status': 1, 'hasPortNumber': 'true',  'shoutcast': 'true', 'error': error, 
#						'metadata': {'contenttype': 'audio/mpeg', 'bitrate': '64', 
#						'song': 'Nasty Habits 41 - Senza Filtro 2017'}}
#		
def getStreamMeta(address):
	Log('getStreamMeta: ' + address)
	# import httplib			# bereits geladen
	# import httplib2 as http	# hier nicht genutzt
	# import pprint				# hier nicht genutzt
	# import re					# bereits geladen
	# import urllib2			# bereits geladen
	# from urlparse import urlparse # bereits geladen
				
	shoutcast = False
	status = 0

	# Test auf angehängte Portnummer = zusätzl. Indikator für Stream, Anhängen von ; in StationList
	#	aber nur, wenn Link direkt mit Portnummer oder Portnummer + / endet, Bsp. http://rs1.radiostreamer.com:8020/
	hasPortNumber='false'
	p = urlparse(address)
	if p.port and p.path == '':	
		hasPortNumber='true'		
	if p.port and p.path:
		if address.endswith('/'):		# als path nur / erlaubt
			hasPortNumber='true'
	Log('hasPortNumber: ' + hasPortNumber)	
	
	request = urllib2.Request(address)
	user_agent = 'iTunes/9.1.1'
	request.add_header('User-Agent', user_agent)
	request.add_header('icy-metadata', 1)
	gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1) 	# 08.10.2017 SSLContext für https://hr-youfm-live.sslcast.addradio.de
	gcontext.check_hostname = False
	gcontext.verify_mode = ssl.CERT_NONE
	
	try:
		response = urllib2.urlopen(request, context=gcontext, timeout=UrlopenTimeout)	
		headers = getHeaders(response)
		# Log(headers)
				   
		if "server" in headers:
			shoutcast = headers['server']
		elif "X-Powered-By" in headers:
			shoutcast = headers['X-Powered-By']
		elif "icy-notice1" in headers:
			shoutcast = headers['icy-notice2']
		else:
			shoutcast = bool(1)

		if isinstance(shoutcast, bool):
			if shoutcast is True:
				status = 1
			else:
				status = 0
			metadata = False;
		elif "SHOUTcast" in shoutcast:
			status = 1
			metadata = shoutcastCheck(response, headers, False)
		elif "Icecast" or "137" in shoutcast:
			status = 1
			metadata = shoutcastCheck(response, headers, True)
		elif "StreamMachine" in shoutcast:
			status = 1
			metadata = shoutcastCheck(response, headers, True)
		elif shoutcast is not None:
			status = 1
			metadata = shoutcastCheck(response, headers, True)
		else:
			metadata = False
		response.close()
		error=''
		return {"status": status, "metadata": metadata, "hasPortNumber": hasPortNumber, "shoutcast": shoutcast, "error": error}

	except urllib2.HTTPError, e:	
		error='Error, HTTP-Error = ' + str(e.code)
		Log(error)
		return {"status": status, "metadata": None, "hasPortNumber": hasPortNumber, "shoutcast": shoutcast, "error": error}

	except urllib2.URLError, e:						# Bsp. RANA FM 88.5 http://216.221.73.213:8000
		error='Error, URL-Error: ' + str(e.reason)
		Log(error)
		return {"status": status, "metadata": None, "hasPortNumber": hasPortNumber, "shoutcast": shoutcast, "error": error}

	except Exception, err:
		error='Error: ' + str(err)
		Log(error)
		return {"status": status, "metadata": None, "hasPortNumber": hasPortNumber, "shoutcast": shoutcast, "error": error}
#----------------------------------------------------------------  
#	Hilfsfunktionen für getStreamMeta
#----------------------------------------------------------------  
def parse_headers(response):
	headers = {}
	int = 0
	while True:
		line = response.readline()
		if line == '\r\n':
			break  # end of headers
		if ':' in line:
			key, value = line.split(':', 1)
			headers[key] = value.rstrip()
		if int == 12:
			break;
		int = int + 1
	return headers
#---------------------------------------------------
def getHeaders(response):
	if is_empty(response.headers.dict) is False:
		headers = response.headers.dict
	elif hasattr(response.info(),"item") and is_empty(response.info().item()) is False:
		headers = response.info().item()
	else:
		headers = parse_headers(response)
	return headers
#---------------------------------------------------
def is_empty(any_structure):
	if any_structure:
		return False
	else:
		return True       
#----------------------------------------------------------------  
def stripTags(text):
	finished = 0
	while not finished:
		finished = 1
		start = text.find("<")
		if start >= 0:
			stop = text[start:].find(">")
			if stop >= 0:
				text = text[:start] + text[start + stop + 1:]
				finished = 0
	return text
#----------------------------------------------------------------  
def shoutcastCheck(response, headers, itsOld):
	if itsOld is not True:
		if 'icy-br' in headers:
			bitrate = headers['icy-br']
			bitrate = bitrate.rstrip()
		else:
			bitrate = None

		if 'icy-metaint' in headers:
			icy_metaint_header = headers['icy-metaint']
		else:
			icy_metaint_header = None

		if "Content-Type" in headers:
			contenttype = headers['Content-Type']
		elif 'content-type' in headers:
			contenttype = headers['content-type']
			
	else:
		if 'icy-br' in headers:
			bitrate = headers['icy-br'].split(",")[0]
		else:
			bitrate = None
		if 'icy-metaint' in headers:
			icy_metaint_header = headers['icy-metaint']
		else:
			icy_metaint_header = None

	if headers.get('Content-Type') is not None:
		contenttype = headers.get('Content-Type')
	elif headers.get('content-type') is not None:
		contenttype = headers.get('content-type')
				

	if icy_metaint_header is not None:
		metaint = int(icy_metaint_header)
		Log("icy metaint: " + str(metaint))
		read_buffer = metaint + 255
		content = response.read(read_buffer)
		# Data.SaveObject("/tmp/icy_content",content)	# Debug

		start = "StreamTitle='"
		end = "';"

		try: 
			title = re.search('%s(.*)%s' % (start, end), content[metaint:]).group(1)
			title = re.sub("StreamUrl='.*?';", "", title).replace("';", "").replace("StreamUrl='", "")
			title = re.sub("&artist=.*", "", title)
			title = re.sub("http://.*", "", title)
			title.rstrip()
		except Exception, err:
			Log("songtitle error: " + str(err))
			title = content[metaint:].split("'")[1]

		return {'song': title, 'bitrate': bitrate, 'contenttype': contenttype.rstrip()}
	else:
		Log("No metaint")
		return False
#---------------------------------------------------

		
