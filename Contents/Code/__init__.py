import urllib			# urllib.quote(), 
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

VERSION =  '0.7.3'		
VDATE = '21.11.2017'

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

ICON_OK 				= "icon-ok.png"
ICON_WARNING 			= "icon-warning.png"
ICON_NEXT 				= "icon-next.png"
ICON_CANCEL 			= "icon-error.png"
ICON_MEHR 				= "icon-mehr.png"
ICON_SEARCH 			= 'ard-suche.png'

ICON_RECORD				= 'icon-record.png'						
ICON_STOP				= 'icon-stop.png'
MENU_RECORDS			= 'menu-records.png'
ICON_FAV_ADD			= 'fav_add.png'
ICON_FAV_REMOVE			= 'fav_remove.png'
ICON_FAV_MOVE			= 'fav_move.png'
ICON_FOLDER_ADD			= 'folder_add.png'
ICON_FOLDER_REMOVE		= 'folder_remove.png'
						

ICON_MAIN_UPDATER 		= 'plugin-update.png'		
ICON_UPDATER_NEW 		= 'plugin-update-new.png'


ART    		= 'art-default.jpg'
ICON   		= 'icon-default.jpg'
NAME		= 'TuneIn2017'
MENU_ICON 	=  	{'menu-lokale.png', 'menu_kuerzlich.png', 'menu-trend.png', 'menu-musik.png', 
					'menu-sport.png', 'menu-news.png', 'menu-talk.png', 'menu-audiobook.png', 'menu-pod.png', 
				}

ROOT_URL 	= 'http://opml.radiotime.com/Browse.ashx?formats=%s'
USER_URL 	= 'http://opml.radiotime.com/Browse.ashx?c=presets&partnerId=RadioTime&username=%s'
NEWS_URL	= 'http://opml.radiotime.com/Browse.ashx?id=c57922&formats=%s'

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
	# Framework-Call uaf Main() dazu (statt PlayAudio):
	#	GET /music/tunein2017?includeConcerts=1&includeExtras=1&includeOnDeck=1&includePopularLeaves=1&includeChapters=1&checkFiles=1
	
	ObjectContainer.title1 = NAME
	HTTP.CacheTime = 300			
	ObjectContainer.art = R(ART)
	DirectoryObject.art = R(ART)
	DirectoryObject.thumb = R(ICON)
	global MyContents
	global UrlopenTimeout 		
	UrlopenTimeout = 3			# Timeout sec, 18.10.2017 von 6 auf 3
	
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
def ValidatePrefs():	
	lang = Prefs['language'].split('/') # Format Bsp.: "Danish/da/da-DA/Author Tommy Mikkelsen"
	try:
		loc 		= str(lang[1])		# de
		loc_browser = loc
		if len(lang) > 2:
			loc_browser = str(lang[2])	# de-DE - Konkretisierung, falls vorhanden
	except:
		loc 		= 'en-us'
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
	title = title.decode(encoding="utf-8", errors="ignore")
	title = myL(title)
			
	oc = ObjectContainer(title2=title, art=ObjectContainer.art)

	oc.add(InputDirectoryObject(key=Callback(Search), title=u'%s' % L('Suche'), prompt=u'%s' % L('Suche Station / Titel'), 
		thumb=R(ICON_SEARCH)))
		
	username = Prefs['username']										# Privat - nicht loggen
	passwort = Prefs['passwort']										# dto.
	if Dict['serial'] == None:
		Dict['serial'] = serial_random()								# eindeutige serial-ID für Tunein für Favoriten u.ä.
		Log('serial-ID erzeugt')										# 	wird nach Löschen Plugin-Cache neu erzeugt
	Log('serial-ID: ' + Dict['serial'])												

	if username:
		my_title = u'%s' % L('Meine Favoriten')
		my_url = USER_URL % username									# serial hier auch statt username möglich
		oc.add(DirectoryObject(
			key = Callback(Rubriken, url=my_url, title=my_title, image=ICON),
			title = my_title, thumb = R(ICON) 
		))                    
		
	formats = 'mp3,aac'	
	Log(Prefs['PlusAAC'])								
	if  Prefs['PlusAAC'] == False:					# Performance, aac ist bei manchen Sendern nicht erreichbar
		formats = 'mp3'
	
	loc_browser = str(Dict['loc_browser'])			# ergibt ohne str: u'de
	# Achtung: mit HTTP.Request wirkt sich headers nicht auf TuneIn aus - daher urllib2.Request
	req = urllib2.Request(ROOT_URL % formats)					# xml-Übersicht Rubriken
	req.add_header('Accept-Language',  '%s, en;q=0.8' % loc_browser) # Quelle Language-Werte: Chrome-HAR
	# req.add_header('Accept-Encoding',  'gzip, deflate, br')			# Performance, klappt nicht in Plex
	ret = urllib2.urlopen(req)
	page = ret.read()
	
	Log(page[:30])									# wg. Umlauten UnicodeDecodeError möglich bei größeren Werten
	rubriken = blockextract('<outline', page)
	for rubrik in rubriken:							# bitrate hier n.b.
		typ,local_url,text,image,key,subtext,bitrate,preset_id = get_details(line=rubrik)	# xml extrahieren
		text = text.decode(encoding="utf-8", errors="ignore")
		subtext = subtext.decode(encoding="utf-8", errors="ignore")	
		thumb = getMenuIcon(key)
		oc.add(DirectoryObject(
			key = Callback(Rubriken, url=local_url, title=text, image=image),
			title = text, summary=subtext, thumb = R(thumb) 
		))
													# Nachrichten anhängen
	oc.add(DirectoryObject(key = Callback(Rubriken, url=NEWS_URL % formats, title='NEWS', image=R('menu-news.png')),	
		title = 'NEWS', summary='NEWS', thumb = R('menu-news.png'))) 
	 
#-----------------------------	
	Log(Prefs['UseRecording'])
	Log(Dict['PID'])
	if Prefs['UseRecording'] == True:			# Recording-Option: Aufnahme-Menu bei aktiven Aufnahmen einbinden
		if len(Dict['PID']) > 0:						
			title = L("laufende Aufnahmen")
			oc.add(DirectoryObject(key=Callback(RecordsList,title=title,), title=title,thumb=R(MENU_RECORDS)))			       
#-----------------------------	
	oc = SearchUpdate(title=NAME, start='true', oc=oc)	# Updater-Modul einbinden:
			
	# Lang_Test=True									# Menü-Test Plugin-Sprachdatei
	Lang_Test=False		
	if Lang_Test:
		oc.add(DirectoryObject(key=Callback(LangTest),title='LangTest', summary='LangTest', thumb=R('lang_gnome.png')))			
			
	return oc
						
#----------------------------------------------------------------
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
			icon = 'menu-lokale.png'
		elif key == 'music':
			icon = 'menu-musik.png'
		elif key == 'talk':
			icon = 'menu-talk.png'
		elif key == 'sports':
			icon = 'menu-sport.png'
		elif key == 'location':
			icon = 'menu-orte.png'
		elif key == 'language':
			icon = 'menu-sprachen.png'
		elif key == 'podcast':
			icon = 'menu-talk.png'
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
	query = query.replace(' ', '+')
	query = urllib2.quote(query, "utf-8")
	url = 'http://opml.radiotime.com/Search.ashx?query=%s' % query
	oc = Rubriken(url=url, title=oc_title2, image=R(ICON_SEARCH))
	
	if len(oc) == 1:
		title = 'Keine Suchergebnisse zu'
		title = title.decode(encoding="utf-8", errors="ignore")
		title = L(title) + ' >%s<' % query
		oc.add(DirectoryObject(key=Callback(Main),title=title, summary='Home', tagline=NAME, thumb=R(ICON_CANCEL)))
	return oc
#-----------------------------
@route(PREFIX + '/Rubriken')
def Rubriken(url, title, image, offset=0):
	Log('Rubriken: ' + url)
	Log(offset)
	offset = int(offset)
	url_org 	= url	# sichern
	title_org 	= title	# sichern

	max_count = ''									# Default: keine Begrenzung
	if Prefs['maxPageContent']:
		max_count = int(Prefs['maxPageContent'])	# max. Anzahl Einträge ab offset
	loc_browser = str(Dict['loc_browser'])			# ergibt ohne str: u'de
	# Achtung: mit HTTP.Request wirkt sich headers nicht auf TuneIn aus - daher urllib2.Request
	req = urllib2.Request(url)					# xml-Übersicht Rubriken
	req.add_header('Accept-Language',  '%s, en;q=0.8' % loc_browser) 	# Quelle Language-Werte: Chrome-HAR
	ret = urllib2.urlopen(req)
	
	#headers = getHeaders(ret)						# Headeres bei Bedarf
	#headers = ret.headers.dict						
	#Log(headers)
		
	page = ret.read()
	Log(page[:30])									# wg. Umlauten UnicodeDecodeError möglich bei größeren Werten
		
	status  = stringextract('<status>', '</status>', page)
	if status == '400':								# Test auf Status 400 - ev. falscher Username
		oc = ObjectContainer(title2=title, art=ObjectContainer.art)
		title = title.decode(encoding="utf-8", errors="ignore")
		title = L('Fehler') + ' | ' + 'tuneIn-Status: 400'
		summary = 'Username ueberpruefen'		
		summary = L(summary)
		oc.add(DirectoryObject(key=Callback(Main),title=title, summary=summary, thumb=R(ICON_CANCEL)))
		return oc	
	
	if status == '200' and 'URL=' not in page:		# leerer Inhalt, Bsp. neuer Ordner
		msg = L('keine Eintraege gefunden') 		
		return ObjectContainer(header=L('Info'), message=msg)			
		
	oc_title2 = stringextract('<title>', '</title>', page)	# Bsp. <title>Frankfurt am Main</title>
	oc_title2 = unescape(oc_title2)
	oc_title2 = oc_title2.decode(encoding="utf-8", errors="ignore")
	oc_title2_org = oc_title2	# sichern
	if offset:
		oc_title2 = oc_title2 + ' | %s...' % offset		# Bsp.: 
	
	oc = ObjectContainer(title2=oc_title2, art=ObjectContainer.art)
	oc = home(oc)

	outline_text = stringextract('<outline text', '>', page)# Bsp. <outline text="Stations (2)" key="stations">
	Log('outline_text: ' + outline_text)			
	outlines = blockextract('<outline text', page)
	Log(len(outlines))
	
	if len(outlines) == 0:								# Normalausgabe ohne Gliederung, Bsp. alle type="link" 
		outlines = blockextract('<body>', page)
		Log('switch_no_blocks')
	Log(len(outlines))		
		
	for outline in outlines:
		key = stringextract('key="', '"', outline)		# Bsp. key="stations"
		# Log(outline); 
		Log('outline_key: ' + key)	
		if key == 'presetUrls':							# CustomUrl's getrennt + komplett behandeln
			oc = get_presetUrls(oc, outline)
			continue
			
		# if key == 'stations'							# z.Z. nicht nötig, Rest typ=link od. typ=audio
		rubriken = blockextract('<outline type', outline)	# restliche outlines
		page_cnt = len(rubriken)
		
		if 	max_count:									# '' = 'Mehr..'-Option ausgeschaltet
			delnr = min(page_cnt, offset)
			del rubriken[:delnr]
			Log(delnr)				
		Log(page_cnt); Log(len(rubriken))
		
		for rubrik in rubriken:			
			typ,local_url,text,image,key,subtext,bitrate,preset_id = get_details(line=rubrik)	# xml extrahieren
			# Log(local_url)		# bei Bedarf
			# Log("typ: " +typ); Log("local_url: " +local_url); Log("text: " +text);
			# Log("image: " +image); Log("key: " +key); Log("subtext: " +subtext); 

			text = text.decode(encoding="utf-8", errors="ignore")
			subtext = subtext.decode(encoding="utf-8", errors="ignore")
						
			if typ == 'link':									# bitrate hier n.b.
				oc.add(DirectoryObject(
					key = Callback(Rubriken, url=local_url, title=text, image=image, offset=0),
					title = text, summary=subtext, tagline=L('Mehr...'), thumb = image 
				)) 
								 
			if typ == 'audio':
				tagline = ''
				if bitrate:											# möglich: keine Angabe (stream_type="download")
					tagline = 'Station | Bitrate: %s KB' % bitrate
				else:
					bitrate = '?'									# PHT verträgt '' nicht
					
				# Sonderfall: Station wird als nicht unterstützt ausgegeben, aber im Web/App gespielt. Hier
				#	versuchen wir den Zugriff auf die Playlist via preset_id (Analyse Chrome-HAR).
				if key == "unavailable":							# Bsp. Buddha Hits mit url -> notcompatible.enUS.mp3
					new_text 	= text + ' | ' + L("neuer Versuch")
					new_subtext = subtext + ' | ' + L("neuer Versuch")
					new_url = 'http://opml.radiotime.com/Tune.ashx?id=%s&formats=mp3,aac' % preset_id
					oc.add(DirectoryObject(
						key = Callback(StationList, url=new_url, title=new_text, summ=new_subtext, image=image, typ=typ, bitrate=bitrate,
						preset_id=preset_id),
						title = new_text, summary=new_subtext,  tagline=tagline, thumb = image 
					))  				
					
				# Log(local_url)		# bei Bedarf
				oc.add(DirectoryObject(
					key = Callback(StationList, url=local_url, title=text, summ=subtext, image=image, typ=typ, bitrate=bitrate,
					preset_id=preset_id),
					title=text, summary=subtext, tagline=tagline, thumb=image 	
				)) 
				 
			if max_count:
				# Mehr Seiten anzeigen:		
				cnt = len(oc) + offset		# 
				# Log('Mehr-Test'); Log(len(oc)); Log(cnt); Log(page_cnt)
				if cnt > page_cnt:			# Gesamtzahl erreicht - Abbruch
					offset=0
					break					# Schleife beenden
				elif len(oc) >= max_count:	# Mehr, wenn max_count erreicht
					offset = offset + max_count-1
					title = L('Mehr...') + oc_title2_org
					summ_mehr = L('Mehr...') + '(max.: %s)' % page_cnt
					oc.add(DirectoryObject(
						key = Callback(Rubriken, url=url_org, title=title, image=image, offset=offset),
						title = title, summary=summ_mehr, tagline=L('Mehr...'), thumb=R(ICON_MEHR) 
					)) 
					break					# Schleife beenden
					
		if 'c=presets' in url_org:			# Ordner-Funktionen in Favoriten anhängen
			if Prefs['UseFavourites']:
				title = L('Neuer Ordner fuer Favoriten') 
				foldername = str(Prefs['folder'])
				summ = L('Name des neuen Ordners') + ': ' + foldername
				oc.add(DirectoryObject(
					key = Callback(Folder, ID='addFolder', title=title, foldername=foldername, folderId='dummy'),
					title = title, summary=summ, thumb=R(ICON_FOLDER_ADD) 
				)) 
				
				sidExist,foldername,guide_id,foldercnt = SearchInFolders(preset_id, ID='foldercnt')
				Log('foldercnt: ' + foldercnt)
				if foldercnt > '1':			# Löschbutton -> Liste - 1. Ordner General nicht löschen
					title = L('Ordner entfernen') 
					summ = L('Ordner zum Entfernen auswaehlen')
					oc.add(DirectoryObject(
						key = Callback(FolderMenu, title=title, ID='removeFolder', preset_id='dummy'), 
						title = title, summary=summ, thumb=R(ICON_FOLDER_REMOVE) 
					)) 								

	return oc
#-----------------------------
def get_presetUrls(oc, outline):						# Auswertung presetUrls für Rubriken
	Log('get_presetUrls')
	rubriken = blockextract('<outline type', outline)	# restliche outlines 
	for rubrik in rubriken:	 # presetUrls ohne bitrate + subtext, type=link. Behandeln wie typ == 'audio'
		typ,local_url,text,image,key,subtext,bitrate,preset_id = get_details(line=rubrik)	# xml extrahieren
		subtext = 'CustomURL'
		bitrate = 'unknown'		# dummy für PHT
		typ = 'unknown'			# dummy für PHT
		oc.add(DirectoryObject(
			key = Callback(StationList, url=local_url, title=text, summ=subtext, image=image, typ=typ, bitrate=bitrate,
			preset_id=preset_id),
			title = text, summary=subtext,  tagline=local_url, thumb = image 
		))  
	Log(len(oc))	
	return oc					
	
#-----------------------------
# Auswertung der Streamlinks:
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
	oc = ObjectContainer(no_cache=True, title2=title, art=ObjectContainer.art)
	
	Log(Client.Platform)				# Home-Button macht bei PHT die Trackliste unbrauchbar 
	client = Client.Platform
	if client == None:
		client = ''
	if client.find ('Plex Home Theater'): # PHT verweigert TrackObject bei vorh. DirectoryObject
		oc = home(oc)					
		
	if 'No compatible stream' in summ or 'Does not stream' in summ: 	# Kennzeichnung + mp3 von TuneIn 
		if 'Tune.ashx?' in url == False:								# "trozdem"-Streams überspringen - s. Rubriken
			url = R('notcompatible.enUS.mp3') # Bsp. 106.7 | Z106.7 Jackson
			oc.add(CreateTrackObject(url=url, title=title, summary=summ, fmt='mp3', thumb=image))
			return oc
		
	if 'Tune.ashx?' in url:						# normaler TuneIn-Link zur Playlist o.ä.
		try:
			cont = HTTP.Request(url).content	# Bsp. http://opml.radiotime.com/Tune.ashx?id=s24878
			# Log(cont)							# hier schon UnicodeDecodeError möglich (selten)
		except Exception as exception:			
				error_txt = 'Servermessage1: ' + str(exception) 
				error_txt = error_txt + '\r\n' + url
				cont = ''
		if cont == '':
			error_txt = error_txt.decode(encoding="utf-8", errors="ignore")
			return ObjectContainer(header=L('Fehler'), message=error_txt)		
		Log('Tune.ashx_content: ' + cont)
	else:										# ev. CustomUrl - key="presetUrls"> - direkter Link zur Streamquelle
		cont = url
		Log('custom_content: ' + cont)
		
	# .pls-Auswertung ziehen wir vor, auch wenn (vereinzelt) .m3u-Links enthalten sein können
	if '.pls' in cont:					# Tune.ashx enthält häufig Links zu Playlist (.pls, .m3u)				
		cont = get_pls(cont)
		if cont.startswith('Servermessage3'): 						# Bsp. Rolling Stones by Radio UNO Digital, pls-Url: 
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

	lines = cont.splitlines()
	err_flag = False; err=''					# Auswertung nach Schleife	
	url_list = []
	line_cnt = 0								# Einzelzählung
	for line in lines:
		line_cnt = line_cnt + 1
		Log('line %s: %s' % (line_cnt, line))
		url = line

		if '=http' in line:						# Playlist-Eintrag, Bsp. File1=http://195.150.20.9:8000/..
			url = line.split('=')[1]
			Log(url)

		if url.startswith('http'):				# rtpm u.ä. ignorieren
			if url.endswith('.mp3'):			# .mp3 bei getStreamMeta durchwinken
				st=1; ret={}
			else:
				ret = getStreamMeta(url)		# Sonderfälle: Shoutcast, Icecast usw. Bsp. http://rs1.radiostreamer.com:8020,
				st = ret.get('status')			# 	http://217.198.148.101:80/
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
											
			Log('append: ' + url)	
			url_list.append(url + '|||' + summ)			# Liste für CreateTrackObject				
		
	Log(len(url_list))		
	url_list = repl_dop(url_list)				# Doppler entfernen	
	Log(len(url_list))		
	if len(url_list) == 0:
		if err_flag == True:					# detaillierte Fehlerausgabe vorziehen, aber nur bei leerer Liste
			return ObjectContainer(header=L('Fehler'), message=err)
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
		
		fmt='mp3'								# Format nicht immer  sichtbar - Bsp. http://addrad.io/4WRMHX. Ermittlung
		if 'aac' in url:						#	 in getStreamMeta (contenttype) hier bisher nicht genutzt
			fmt='aac'
		title = title_org + ' | Stream %s | %s'  % (str(i), fmt)
		i=i+1
		Log(url)
		oc.add(CreateTrackObject(url=url, title=title, summary=summ, fmt=fmt, thumb=image))
		
	if Prefs['UseRecording'] == True:			# Aufnahme- und Stop-Button
		title = L("Aufnahme") + ' ' + L("starten")		
		oc.add(DirectoryObject(key=Callback(RecordStart,url=url,title=title,title_org=title_org,image=image,
			summ=summ_org,typ=typ_org,bitrate=bitrate_org), title=title,summary=summ,thumb=R(ICON_RECORD)))
		title = L("Aufnahme") + ' ' + L("beenden")		
		oc.add(DirectoryObject(key=Callback(RecordStop,url=url,title=title,summ=summ_org), 
			title=title,summary=summ,thumb=R(ICON_STOP)))
			
	if Prefs['UseFavourites'] == True:			# Favorit hinzufügen/Löschen
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
		
	return oc
#-----------------------------
def get_pls(url):               # Playlist holen
	Log('get_pls: ' + url)
	urls =url.splitlines()	# mehrere möglich, auch SHOUTcast- und m3u-Links, Bsp. http://64.150.176.192:8043/, 

	pls_cont = []
	for url in urls:
		# Log(url)
		cont = url
		if url.startswith('http') == False:		# Sicherung, falls Zeile keine Url enthält (bisher aber nicht gesehen)
			continue
		if 	'.pls' in url or url.endswith('.m3u'):	# .pls auch im Pfad möglich, Bsp. AFN: ../AFNE_WBN.pls?DIST=TuneIn&TGT=..
			try:									# 1. Versuch (klappt mit KSJZ.db unter Linux, nicht unter Windows)
				cont = HTTP.Request(url).content 	# Framework-Problem möglich: URLError: <urlopen error unknown url type: itunes>	
			except: 	
				cont=''
		cont = cont.strip()
		Log(cont)

		# Zertifikate-Problem (vorwiegend unter Windows):
		# Falls die Url im „Location“-Header-Feld eine neue HTTPS-Adresse enthält (Moved Temporarily), ist ein Zertifikat erforderlich.
		# 	Performance: das große Mozilla-Zertifikat cacert.pem tauschen wir gegen /etc/ssl/ca-bundle.pem von linux (ca. halbe Größe).
		#	Aber: falls ssl.SSLContext verwendet wird, schlägt der Request fehl.
		#	Hinw.: 	gcontext nicht mit	cafile verwenden (ValueError)
		#	Bsp.: KSJZ.db SmoothLounge, Playlist http://smoothlounge.com/streams/smoothlounge_128.pls
		# Ansatz, falls dies unter Windows fehlschlägt: in der url-Liste nach einzelner HTP-Adresse (ohne .pls) suchen
		
		if cont == '':							# 2. Versuch
			try:
				req = urllib2.Request(url)
				cafile = Core.storage.abs_path(Core.storage.join_path(MyContents, 'Resources', 'ca-bundle.pem'))		
				Log(cafile)
				req = urllib2.urlopen(req, cafile=cafile, timeout=UrlopenTimeout) 
				# headers = getHeaders(req)		# bei Bedarf
				# Log(headers)
				cont = req.read()
				Log(cont)
			except Exception as exception:	
				error_txt = 'Servermessage2: ' + str(exception)
				error_txt = error_txt + '\r\n' + url
				Log(error_txt)
												# 3. Versuch
		Log(cont)
		if '[playlist]' in cont:	# Streamlinks aus Playlist extrahieren 
			lines =cont.splitlines()
			for line in lines:	
				if 'http' in line:	# Bsp. File1=http://195.150.20.9:8000/.., split in Verlauf StationList
					pls_cont.append(cont)	
		else:
			if cont.startswith('http'):
				pls_cont.append(cont)
				 			 	 		   
	pls = pls_cont
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
		if url.startswith('http') and url.endswith('.m3u'):		
			try:									
				req = HTTP.Request(url).content 
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
def get_details(line):		# xml mittels Stringfunktionen extrahieren 
	# Log('get_details')
	typ='';local_url='';text='';image='';key='';subtext='';
	
	typ 		= stringextract('type="', '"', line)
	local_url 	= stringextract('URL="', '"', line)
	text 		= stringextract('text="', '"', line)
	image 		= stringextract('image="', '"', line)
	if image == '':
		image = R(ICON) 
	key	 		= stringextract('key="', '"', line)
	subtext 	= stringextract('subtext="', '"', line)
	bitrate 	= stringextract('bitrate="', '"', line)
	preset_id  = stringextract('preset_id="', '"', line)
	# itemAttr	= stringextract('itemAttr="', '"', line)	# n.b.
	
	local_url 	= unescape(local_url)
	text 		= unescape(text)
	subtext 	= unescape(subtext)	
	
	#Log("typ: " +typ); Log("local_url: " +local_url); Log("text: " +text); Log("image: " +image); 
	#Log("key: " +key); Log("subtext: " +subtext);
	#Log("text: " +text)

	return typ,local_url,text,image,key,subtext,bitrate,preset_id
	
#-----------------------------
@route(PREFIX + '/CreateTrackObject')
def CreateTrackObject(url, title, summary, fmt, thumb, include_container=False, location=None, 
		includeBandwidths=None, autoAdjustQuality=None, hasMDE=None, **kwargs):
	Log('CreateTrackObject: ' + url); Log(include_container)
	Log(title);Log(summary);Log('fmt: ' + fmt);Log(thumb);

	if fmt == 'mp3':
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

	title = title.decode(encoding="utf-8", errors="ignore")
	summary = summary.decode(encoding="utf-8", errors="ignore")

	random.seed()						
	rating_id = random.randint(1,10000)
	rating_key = 'rating_key-' + str(rating_id)
	Log(rating_key)

	track_object = TrackObject(
		key = Callback(CreateTrackObject, url=url, title=title, summary=summary, fmt=fmt, thumb=thumb,  
				include_container=True, location=None, includeBandwidths=None, autoAdjustQuality=None, hasMDE=None),
		rating_key = rating_key,	
		title = title,
		summary = summary,
		# art=thumb,					# Auflösung i.d.R. zu niedrig
		thumb=thumb,
		items = [
			MediaObject(
				parts = [
					PartObject(key=Callback(PlayAudio, url=url, ext=fmt)) # Bsp. runtime- Aufruf: PlayAudio.mp3 
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
def PlayAudio(url, location=None, includeBandwidths=None, autoAdjustQuality=None, hasMDE=None, **kwargs):
	Log('PlayAudio')
		
	if url is None or url == '':			# sollte hier nicht vorkommen
		Log('Url fehlt!')
		return ObjectContainer(header='Error', message='Url fehlt!') # Web-Player: keine Meldung
	try:
		req = urllib2.Request(url)			# Test auf Existenz, SSLContext für HTTPS erforderlich,
		gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)  	#	Bsp.: SWR3 https://pdodswr-a.akamaihd.net/swr3
		ret = urllib2.urlopen(req, context=gcontext)
		Log('PlayAudio: %s | %s' % (str(ret.code), url))
	except Exception as exception:			# selten, da StationList leere Url-Listen abfängt, Bsp.: 
		error_txt = 'Servermessage4: ' + str(exception) # La Red21.FM Rolling Stones Radio, url:
		error_txt = error_txt + '\r\n' + url			# http://server-uk4.radioseninternetuy.com:9528/;	 			 	 
		msgH = L('Fehler'); msg = error_txt				# Textausgabe: 	This station is suspended, if...
		msg =  msg.decode(encoding="utf-8", errors="ignore")
		Log(msg)
		# return ObjectContainer(header=msgH, message=msg) # Framework fängt ab - keine Ausgabe
		if 'notcompatible.enUS.mp3' in url:
			url = R('notcompatible.enUS.mp3')	# Kennzeichnung + mp3 von TuneIn 
		else:
			url=GetLocalUrl()					# lokale mp3-Nachricht,  s.u. GetLocalUrl	
		
	return Redirect(url)
	
#-----------------------------
def GetLocalUrl(): 						# lokale mp3-Nachricht, engl./deutsch - nur für PlayAudio
	loc = str(Dict['loc'])
	url=R('not_available_en.mp3')		# mp3: Sorry, this station is not available
	if loc == 'de':
		url=R('not_available_de.mp3')	# mp3: Dieser Sender ist leider nicht verfügbar	
	return url
	
####################################################################################################
#									Favoriten-/Ordner-Funktionen
####################################################################################################
#-----------------------------
# Rückgabe True, Ordnernamen, guide_id, foldercnt - True, falls ein Favorit mit preset_id existiert
#	
def SearchInFolders(preset_id, ID):	
	Log('SearchInFolders')
	Log('preset_id: ' + preset_id)
	Log('ID: ' + ID)
	serial = Dict['serial']	
	
	username = Prefs['username']
	url = 'http://opml.radiotime.com/Browse.ashx?c=presets&partnerId=RadioTime&serial=%s' % serial	
	try:
		page = HTTP.Request(url, cacheTime=1).content						# Ordner-Übersicht laden
	except Exception as exception:			
			error_txt = 'Servermessage8: ' + str(exception) 
			error_txt = error_txt + '\r\n' + url
			page = ''
	if page == '':
		error_txt = error_txt.decode(encoding="utf-8", errors="ignore")
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
		if ID == 'preset_id':		
			if preset_id in page:
				return True, foldername, guide_id, str(foldercnt)
			else:
				return False, foldername, guide_id, str(foldercnt)
	else:							# einz. Ordner abklappern
		if ID == 'foldercnt':
			return True, foldername, guide_id, str(foldercnt)
			
		if ID == 'preset_id':		# 	Fav's preset_id  in den Ordnern vorhanden?
			outlines = blockextract('outline type="link"', page)
			for outline in outlines:
				ordner_url = stringextract('URL="', '"', outline)
				ordner_url = unescape(ordner_url) 
				foldername = stringextract('title=', '&', ordner_url)
				guide_id = stringextract('guide_id=', '&', ordner_url)
				page = HTTP.Request(ordner_url, cacheTime=1).content		# Ordner-Inhalt laden	
				if preset_id in page:
					return True, foldername, guide_id, str(foldercnt)				
		
	return False, foldername, guide_id, str(foldercnt)	
	
#-----------------------------
# ermittelt Inhalte aus den Profildaten
#	ID='favoriteId' - eindeutige Kennz. des Ordners für Fav mit preset_id
#	
def SearchInProfile(ID, preset_id):	
	Log('SearchInProfile')
	Log('ID: ' + ID)
	serial = Dict['serial']	

	sidExist,foldername,guide_id,foldercnt = SearchInFolders(preset_id, ID='preset_id') # vorhanden, Ordner-ID?
	url = 'https://api.tunein.com/profiles/me/follows?folderId=%s&filter=favorites&formats=mp3,aac,ogg&serial=%s&partnerId=RadioTime' % (guide_id,serial)	
		
	favoriteId = guide_id
	if ID == 'favoriteId':
		try:	
			page = HTTP.Request(url, cacheTime=1).content		# Profil laden, Filter: Ordner favoriteId	
		except Exception as exception:			
				error_txt = 'Servermessage11: ' + str(exception) 
				error_txt = error_txt + '\r\n' + url
				page = ''
		if page == '':
			error_txt = error_txt.decode(encoding="utf-8", errors="ignore")
			Log(error_txt)
			return ObjectContainer(header=L('Fehler'), message=error_txt)		
		Log(page[:10])				
		
		indices = blockextract('"Index"', page)
		for index in indices:
			# Log(index)	# bei Bedarf
			Id = stringextract('"Id":"', '"', index)
			Log(Id)
			if Id ==  preset_id:
				favoriteId = stringextract('"FavoriteId":"', '"', index)
				Log(favoriteId)
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
def Favourit(ID, preset_id, folderId):
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
		
	# Query prüft, ob der Tunein-Account bereits mit der serial-ID verknüpft ist
	query_url = 'https://opml.radiotime.com/Account.ashx?c=query&partnerId=%s&serial=%s' % (partnerId,serial)
	# Log(queqry_url)
	try:
		page = HTTP.Request(query_url, headers=headers, cacheTime=1).content				# 1. Query
	except Exception as exception:			
			error_txt = 'Servermessage5: ' + str(exception) 
			error_txt = error_txt + '\r\n' + url
			page = ''
	if page == '':
		error_txt = error_txt.decode(encoding="utf-8", errors="ignore")
		Log(error_txt)
		return ObjectContainer(header=L('Fehler'), message=error_txt)		
	Log('Fav-Query: ' + page[:10])
	tname  = stringextract('text="', '"', page)	# Bsp. <outline type="text" text="testuser"/>
	is_joined = False
	if tname == Prefs['username']:				
		is_joined = True						# Verknüpfung bereits erfolgt
	Log('is_joined: ' + str(is_joined))
		
	if is_joined == False:
		# Join verknüpft Account mit serial-ID. Vorhandene Presets werden eingebunden
		# 	Ersetzung: partnerId, username, password, serial
		join_url = ('https://opml.radiotime.com/Account.ashx?c=join&partnerId=%s&username=%s&password=%s&serial=%s' 
					% (partnerId,username,password,serial))
		try:
			page = HTTP.Request(join_url, headers=headers, cacheTime=1).content			# 2. Join
		except Exception as exception:			
				error_txt = 'Servermessage6: ' + str(exception) 		# Bsp. 403 - Forbidden..
				error_txt = error_txt + '\r\n' + url
				page = ''
		if page == '':
			error_txt = error_txt.decode(encoding="utf-8", errors="ignore")
			Log(error_txt)
			return ObjectContainer(header=L('Fehler'), message=error_txt)		
		# Log('Fav-Join: ' + page)	# bei Bedarf
		
		status  = stringextract('<status>', '</status>', page)
		if '200' != status:								# 
			title  = stringextract('<title>', '</title>', page)
			msg = L('Problem mit Username / Passwort') + ' | Tunein: ' + title	
			Log(msg)
			return ObjectContainer(header=L('Fehler'), message=msg)
			
	# Favoriten hinzufügen/Löschen - ID steuert ('add', 'remove', moveto)
	#	Angabe des Ordners (folderId) nur für  moveto erf. 
	# 	Ersetzung bei 'moveto': ID,favoriteId,folderId,serial,partnerId
	# 	Ersetzung bei 'add', 'remove': ID,preset_id,serial,partnerId
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
	else:
		fav_url = ('https://opml.radiotime.com/favorites.ashx?render=xml&c=%s&id=%s&formats=mp3,aac,ogg,flash,html&serial=%s&partnerId=%s' 
				% (ID,preset_id,serial,partnerId))
	try:
		req = HTTP.Request(fav_url, headers=headers, cacheTime=1)		# 3. Add / Remove
		page = req.content
		# h = req.headers; Log(h)	# nichts Relevantes	
		
	except Exception as exception:			
			error_txt = 'Servermessage7: ' + str(exception) 
			error_txt = error_txt + '\r\n' + fav_url
			page = ''
	if page == '':
		error_txt = error_txt.decode(encoding="utf-8", errors="ignore")
		Log(error_txt)
		return ObjectContainer(header=L('Fehler'), message=error_txt)		
	# Log('Fav add/remove: ' + page)
	
	status  = stringextract('<status>', '</status>', page)				# Ergebnisausgabe
	if '200' != status:	
		title  = stringextract('<title>', '</title>', page)
		msg = L('fehlgeschlagen') + ' | Tunein: ' + title			
		return ObjectContainer(header=L('Fehler'), message=msg)
	else:
		if ID == 'add':									# 'add'
			msg = L("Favorit") + ' ' + L("hinzugefuegt")
		elif  ID == 'remove':	 										# 'remove'
			msg = L("Favorit") + ' ' + L("entfernt")	
		elif  ID == 'move':	 
			msg = L("Favorit") + ' ' + L("verschoben")
				
		return ObjectContainer(header=L('OK'), message=msg)		

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
						
	try:
		page = HTTP.Request(folder_url, headers=headers, cacheTime=1).content		
	except Exception as exception:			
			error_txt = 'Servermessage9: ' + str(exception) 		# Bsp. 403 - Forbidden..
			error_txt = error_txt + '\r\n' + url
			page = ''
	if page == '':
		error_txt = error_txt.decode(encoding="utf-8", errors="ignore")
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
#	ID='removeFolder' -> Ordner entfernen (Löschbutton in Rubriken)
#	ID='moveto' -> Favorit in Ordner verschieben (UseFavourites in StationList)
#	preset_id nur für moveto erforderlich (Kennz. für Favoriten)
#
@route(PREFIX + '/FolderMenu')		
def FolderMenu(title, ID, preset_id):
	Log('FolderMenu')
	Log('ID: ' + ID)
	serial = Dict['serial']
	oc = ObjectContainer(no_cache=True, title2=title, art=ObjectContainer.art)
	oc = home(oc)					
	loc_browser = str(Dict['loc_browser'])			
	headers = {'Accept-Language': "%s, en;q=0.8" % loc_browser}
	
	preset_url = 'http://opml.radiotime.com/Browse.ashx?c=presets&partnerId=RadioTime&serial=%s' % serial	
	try:
		page = HTTP.Request(preset_url, headers=headers, cacheTime=1).content		
	except Exception as exception:			
			error_txt = 'Servermessage10: ' + str(exception) 		
			error_txt = error_txt + '\r\n' + url
			page = ''
	if page == '':
		error_txt = error_txt.decode(encoding="utf-8", errors="ignore")
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
				try:
					page = 		HTTP.Request(furl, headers=headers, cacheTime=1).content	# Inhalte abfragen
					items_cnt =  len(blockextract('URL=', page))		# outline unscharf
				except:
					pass
				
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

#-----------------------------
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
					
	# cmd-Bsp.: streamripper http://addrad.io/4WRMHX --quiet -d /tmp 		
	cmd = "%s %s --quiet -d %s"	% (AppPath, url_clean, DestDir)		
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
		title_new = pid_sender + ' | ' + pid_summ
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
														# Menü Plugin-Update zeigen														
		title = 'Plugin-Update | Version: ' + VERSION + ' - ' + VDATE 	 
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
		summary = 'Plugin Version: ' + VERSION + ', Github Version: ' + latest_version

		oc.add(DirectoryObject(key=Callback(updater.update, url=url , ver=latest_version), 
			title=title, summary=summary, tagline=tag, thumb=R(ICON_UPDATER_NEW)))
			
		if start == 'false':						# Option Abbrechen nicht beim Start zeigen
			oc.add(DirectoryObject(key = Callback(Main), title = L('Update abbrechen'),
				summary = L('weiter im aktuellen Plugin'), thumb = R(ICON_UPDATER_NEW)))
	else:											# Plugin aktuell -> Main
		available = 'false'
		if start == 'false':						# beim Start unterdrücken
			oc.add(DirectoryObject(key = Callback(Main), 	
				title = 'Plugin up to date | Home',
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
def stringextract(mFirstChar, mSecondChar, mString):  	# extrahiert Zeichenkette zwischen 1. + 2. Zeichenkette
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
# 	Rückgabe 	Bsp. 1. {'status': 1, 'hasPortNumber': 'false', 'metadata': False, 'error': error}
#				Bsp. 2.	{'status': 1, 'hasPortNumber': 'true', 'error': error, 
#						'metadata': {'contenttype': 'audio/mpeg', 'bitrate': '64', 
#						'song': 'Nasty Habits 41 - Senza Filtro 2017'}}
#		
def getStreamMeta(address):
	Log('getStreamMeta: ' + address)
	import httplib
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
		return {"status": status, "metadata": metadata, "hasPortNumber": hasPortNumber, "error": error}

	except urllib2.HTTPError, e:	
		error='Error, HTTPError = ' + str(e.code)
		Log(error)
		return {"status": status, "metadata": None, "hasPortNumber": hasPortNumber, "error": error}

	except urllib2.URLError, e:						# Bsp. RANA FM 88.5 http://216.221.73.213:8000
		error='Error, URLError: ' + str(e.reason)
		Log(error)
		return {"status": status, "metadata": None, "hasPortNumber": hasPortNumber, "error": error}

	except Exception, err:
		error='Error: ' + str(err)
		Log(error)
		return {"status": status, "metadata": None, "hasPortNumber": hasPortNumber, "error": error}
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

		
