import urllib			# urllib.quote(), 
import urllib2			# urllib2.Request
import ssl				# HTTPS-Handshake
import random			# Zufallswerte für rating_key
import sys				# Plattformerkennung
import re				# u.a. Reguläre Ausdrücke, z.B. in CalculateDuration
import json				# json -> Textstrings
from urlparse import urlparse
import updater



# +++++ TuneIn2017 - tunein.com-Plugin für den Plex Media Server +++++

VERSION =  '0.3.2'		
VDATE = '05.10.2017'

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

ICON_MAIN_UPDATER 		= 'plugin-update.png'		
ICON_UPDATER_NEW 		= 'plugin-update-new.png'


ART    		= 'art-default.jpg'
ICON   		= 'icon-default.jpg'
NAME		= 'TuneIn2017'
MENU_ICON 	=  	{'menu-lokale.png', 'menu_kuerzlich.png', 'menu-trend.png', 'menu-musik.png', 
					'menu-sport.png', 'menu-news.png', 'menu-talk.png', 'menu-audiobook.png', 'menu-pod.png', 
				}

ROOT_URL 	= 'http://opml.radiotime.com/Browse.ashx?formats=mp3,aac'
USER_URL 	= 'http://opml.radiotime.com/Browse.ashx?c=presets&partnerId=RadioTime&username=%s'
PREFIX 		= '/music/tunein2017'

REPO_NAME		 	= NAME
GITHUB_REPOSITORY 	= 'rols1/' + REPO_NAME

####################################################################################################
def Start():

	ObjectContainer.title1 = NAME
	HTTP.CacheTime = 300
	ObjectContainer.art = R(ART)
	DirectoryObject.art = R(ART)
	DirectoryObject.thumb = R(ICON)
	
	ValidatePrefs()
	
# Locale-Probleme 	s. https://forums.plex.tv/discussion/126807/another-localization-question,
#					https://forums.plex.tv/discussion/143342/non-ascii-characters-in-translations
#	Bis zur praktikablen Lösung vermeide ich deutsche Sonderzeichen (Bsp. Durchstoebern)
def ValidatePrefs():	
	lang = Prefs['language'].split('/')
	try:
		loc 		= str(lang[1])		# de
		loc_browser = loc
		if len(lang) == 3:
			loc_browser = str(lang[2])	# de-DE - Konkretisierung, falls vorhanden
	except:
		loc 		= 'en-us'
		loc_browser = 'en-US'
	if Core.storage.file_exists(Core.storage.abs_path(
		Core.storage.join_path(
			Core.bundle_path,
			'Contents',
			'Strings',
			'%s.json' % loc
		)
	)):
		Locale.DefaultLocale = loc
	else:
		Locale.DefaultLocale = 'en-us'
	Dict['loc'] 		= loc
	Dict['loc_browser'] = loc_browser
	Log('loc: %s' % loc)
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
	
	Dict.Reset()														# Speicherobjekte des Plugins löschen

	title = 'Durchstoebern'
	title = title.decode(encoding="utf-8", errors="ignore")
	title = L(title)
			
	oc = ObjectContainer(title2=title, art=ObjectContainer.art)

	oc.add(InputDirectoryObject(key=Callback(Search), title=u'%s' % L('Suche'), prompt=u'%s' % L('Suche Station / Titel'), 
		thumb=R(ICON_SEARCH)))
		
	username = Prefs['username']	
	# Log(username)														# privat! nur für lokale Tests

	if username:
		my_title = u'%s' % L('Meine Favoriten')
		my_url = USER_URL % username
		oc.add(DirectoryObject(
			key = Callback(Rubriken, url=my_url, title=my_title, image=ICON),
			title = my_title, thumb = R(ICON) 
		))                    
		
	loc_browser = str(Dict['loc_browser'])			# ergibt ohne str: u'de
	# Achtung: mit HTTP.Request wirkt sich headers nicht auf TuneIn aus - daher urllib2.Request
	req = urllib2.Request(ROOT_URL)					# xml-Übersicht Rubriken
	req.add_header('Accept-Language',  '%s, en;q=0.8' % loc_browser) # Quelle Language-Werte: Chrome-HAR
	ret = urllib2.urlopen(req)
	page = ret.read()
	
	Log(page[:30])									# wg. Umlauten UnicodeDecodeError möglich bei größeren Werten
	rubriken = blockextract('<outline', page)
	for rubrik in rubriken:							# bitrate hier n.b.
		typ,local_url,text,image,key,subtext,bitrate= get_details(line=rubrik)	# xml extrahieren
		text = text.decode(encoding="utf-8", errors="ignore")
		subtext = subtext.decode(encoding="utf-8", errors="ignore")	
		thumb = getMenuIcon(key)
		oc.add(DirectoryObject(
			key = Callback(Rubriken, url=local_url, title=text, image=image),
			title = text, summary=subtext, thumb = R(thumb) 
		))   
		       
#-----------------------------	# Updater-Modul einbinden:
	
	repo_url = 'https://github.com/{0}/releases/'.format(GITHUB_REPOSITORY)
	call_update = False
	if Prefs['InfoUpdate'] == True:					# Hinweis auf neues Update beim Start des Plugins 
		ret = updater.update_available(VERSION)
		int_lv = ret[0]			# Version Github
		int_lc = ret[1]			# Version aktuell
		latest_version = ret[2]	# Version Github, Format 1.4.1

		if ret[0] == False:
			msgH = L('Fehler'); 
			msg = L('Github ist nicht errreichbar') +  ' - ' +  L('Bitte die Update-Anzeige abschalten')		
			return ObjectContainer(header=msgH, message=msg)
	
		if int_lv > int_lc:								# Update-Button "installieren" zeigen
			call_update = True
			title = L('neues Update vorhanden') +  ' - ' + L('jetzt installieren')
			summary = 'Plugin Version: ' + VERSION + ', Github Version: ' + latest_version
			url = 'https://github.com/{0}/releases/download/{1}/{2}.bundle.zip'.format(GITHUB_REPOSITORY, latest_version, REPO_NAME)
			oc.add(DirectoryObject(key=Callback(updater.update, url=url , ver=latest_version), 
				title=title, summary=summary, tagline=cleanhtml(summary), thumb=R(ICON_UPDATER_NEW)))
	if call_update == False:							# Update-Button "Suche" zeigen	
		title = 'Plugin-Update | Version: ' + VERSION + ' - ' + VDATE	
		summary=L('Suche nach neuen Updates starten')
		tagline=L('Bezugsquelle: ') + repo_url			
		oc.add(DirectoryObject(key=Callback(SearchUpdate, title='Plugin-Update'), 
			title=title, summary=summary, tagline=tagline, thumb=R(ICON_MAIN_UPDATER)))
	return oc
						
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
	oc_title2 = L('Suche nach: ')
	oc_title2 = oc_title2 + query.decode(encoding="utf-8", errors="ignore")
	oc = ObjectContainer(title2=oc_title2, art=ObjectContainer.art)
	oc = home(oc)
	
	query = query.replace(' ', '+')
	query = urllib2.quote(query, "utf-8")
	url = 'http://opml.radiotime.com/Search.ashx?query=%s' % query
	oc = Rubriken(url=url, title=oc_title2, image=R(ICON_SEARCH))
	
	if len(oc) == 1:
		title = 'Keine Suchergebnisse zu '
		title = title.decode(encoding="utf-8", errors="ignore")
		title = L(title) + '>%s<' % query
		oc.add(DirectoryObject(key=Callback(Main),title=title, summary='Home', tagline=NAME, thumb=R(ICON_CANCEL)))
	return oc
#-----------------------------
@route(PREFIX + '/Rubriken')
def Rubriken(url, title, image):
	Log('Rubriken: ' + url)

	loc_browser = str(Dict['loc_browser'])			# ergibt ohne str: u'de
	# Achtung: mit HTTP.Request wirkt sich headers nicht auf TuneIn aus - daher urllib2.Request
	req = urllib2.Request(url)					# xml-Übersicht Rubriken
	req.add_header('Accept-Language',  '%s, en;q=0.8' % loc_browser) # Quelle Language-Werte: Chrome-HAR
	ret = urllib2.urlopen(req)
	page = ret.read()	
	Log(page[:30])									# wg. Umlauten UnicodeDecodeError möglich bei größeren Werten
		
	status  = stringextract('<status>', '</status>', page)
	if status == '400':								# Test auf Status 400 - ev. falscher Username
		oc = ObjectContainer(title2=title, art=ObjectContainer.art)
		title = title.decode(encoding="utf-8", errors="ignore")
		title = L('Fehler') + ' | ' + 'tuneIn-Status: 400'
		summary = 'Problem mit username'		
		summary = L(summary)
		oc.add(DirectoryObject(key=Callback(Main),title=title, summary=summary, thumb=R(ICON_CANCEL)))
		return oc			
	
	rubriken = blockextract('<outline type', page)
	
	oc_title2 = stringextract('<title>', '</title>', page)	# Bsp. <title>Frankfurt am Main</title>
	oc_title2 = unescape(oc_title2)
	oc_title2 = oc_title2.decode(encoding="utf-8", errors="ignore")
	
	key 	= stringextract('key="', '"', page)				# Bsp. key="stations">
	oc = ObjectContainer(title2=oc_title2, art=ObjectContainer.art)
	oc = home(oc)
	
	for rubrik in rubriken:
		# Log(rubrik)
		typ,local_url,text,image,key,subtext,bitrate = get_details(line=rubrik)	# xml extrahieren
		# Log(local_url)
		# Log("typ: " +typ); Log("local_url: " +local_url); Log("text: " +text);
		# Log("image: " +image); Log("key: " +key); Log("subtext: " +subtext); 

		text = text.decode(encoding="utf-8", errors="ignore")
		subtext = subtext.decode(encoding="utf-8", errors="ignore")
		
		if typ == 'link':									# bitrate hier n.b.
			oc.add(DirectoryObject(
				key = Callback(Rubriken, url=local_url, title=text, image=image),
				title = text, summary=subtext, tagline=L('Mehr...'), thumb = image 
			)) 
                 
		if typ == 'audio':
			tagline = ''
			if bitrate:											# möglich: keine Angabe (stream_type="download")
				tagline = 'Station | Bitrate: %s KB' % bitrate
			else:
				bitrate = '?'									# PHT verträgt '' nicht 
			oc.add(DirectoryObject(
				key = Callback(StationList, url=local_url, title=text, summ=subtext, image=image, typ=typ, bitrate=bitrate),
				title = text, summary=subtext,  tagline=tagline, thumb = image 
			))  

	return oc

#-----------------------------
# Auswertung der Streamlinks:
#	1. opml-Info laden, Bsp. http://opml.radiotime.com/Tune.ashx?id=s24878
#	2. Test Inhalt von Tune.ashx auf Playlist-Datei (.pls) - Details siehe get_pls
#	3. Behandlung der url-Liste:
#		3.1. falls .m3u8-Datei: Inhalte laden, verketten, Doppler entfernen
#		3.2. Streamlinks der einzelnen Playlist-Einträge extrahieren
#		3.3. Behandlung von Sonderfällen, Metaden div. Streamingdienste (getStreamMeta - zeitaufwendig) 
#	4. letzte Doppler in der url-Liste entfernen
#	5. Aufbau des TrackObjects mit den einzelnen Url's der Liste
#
@route(PREFIX + '/StationList')
def StationList(url, title, image, summ, typ, bitrate):
	Log('StationList: ' + url)
	summ = unescape(summ)
	Log(title);Log(image);Log(summ);Log(typ);Log(bitrate)
	title = title.decode(encoding="utf-8", errors="ignore")
	summ_org=summ; bitrate_org=bitrate	# sichern
	oc = ObjectContainer(title2=title, art=ObjectContainer.art)
	
	Log(Client.Platform)				# Home-Button macht bei PHT die Trackliste unbrauchbar 
	client = Client.Platform
	if client == None:
		client = ''
	if client.find ('Plex Home Theater'): # PHT verweigert TrackObject bei vorh. DirectoryObject
		oc = home(oc)					
		
	if 'No compatible stream' in summ or 'Does not stream' in summ: 	 # Kennzeichnung + mp3 von TuneIn 
		url = R('notcompatible.enUS.mp3') # Bsp. 106.7 | Z106.7 Jackson
		oc.add(CreateTrackObject(url=url, title=title, summary=summ, fmt='mp3', thumb=image))
		return oc
		
	try:
		cont = HTTP.Request(url).content	# Bsp. http://opml.radiotime.com/Tune.ashx?id=s24878
		Log(cont)							# hier schon UnicodeDecodeError möglich (selten)
	except Exception as exception:			
			error_txt = 'Servermessage1: ' + str(exception) 
			error_txt = error_txt + '\r\n' + url
			cont = ''
	if cont == '':
		error_txt = error_txt.decode(encoding="utf-8", errors="ignore")
		return ObjectContainer(header=L('Fehler'), message=error_txt)
		
	Log('Tune.ashx_content: ' + cont)
		
	if '.pls' in cont:					# Tune.ashx enthält häufig Links zu Playlist (.pls, .m3u)				
		cont = get_pls(cont)
		if cont.startswith('Servermessage'): 						# Bsp. Rolling Stones by Radio UNO Digital, pls-Url: 
			cont = cont.decode(encoding="utf-8", errors="ignore")	# http://radiounodigital.com/Players-Tunein/rollingstones.pls
			return ObjectContainer(header=L('Fehler'), message=cont)
	
	# if line.endswith('.m3u'):				# ein oder mehrere .m3u-Links
	if '.m3u' in cont:						# auch das: ..playlist/newsouth-wusjfmmp3-ibc3.m3u?c_yob=1970&c_gender..
		cont = get_m3u(cont)
		Log('m3u-cont: ' + cont)
		if cont == '':
			msg=L('keinen Stream gefunden zu: ') 
			message="%s %s" % (msg, title)
			return ObjectContainer(header=L('Fehler'), message=message)

	lines = cont.splitlines()
	err_flag = False; err=''					# Auswertung nach Schleife	
	url_list = []
	for line in lines:
		Log('line: ' + line)
		url = line

		if '=http' in line:						# Playlist-Eintrag, Bsp. File1=http://195.150.20.9:8000/..
			url = line.split('=')[1]
			Log(url)

		if url.startswith('http'):			
			ret = getStreamMeta(url)			# Sonderfälle: Shoutcast, Icecast usw. Bsp. http://rs1.radiostreamer.com:8020,
			st = ret.get('status')				# 	http://217.198.148.101:80/
			Log('ret.get.status: ' + str(st))
						
			if st == 0:							# nicht erreichbar, verwerfen. Bsp. http://server-uk4.radioseninternetuy.com:9528
				err = ret.get('error')			# Bsp.  City FM 92.9 (Taichung, Taiwan):
				err = err + '\r\n' + url		#	URLError: timed out, http://124.219.41.230:8000/929.mp3
				err_flag = True
				Log(err)
				# return ObjectContainer(header=L('Fehler'), message=err) # erst nach Schleife, s.u.
				continue							
			else:
				if ret.get('metadata'):					# Status 1: Stream ist up, Metadaten aktualisieren
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
											
			Log('append:')	
			url_list.append(url + '|||' + summ)			# Liste für CreateTrackObject
		
	Log(len(url_list))		
	url_list = repl_dop(url_list)				# Doppler entfernen	
	Log(len(url_list))		
	if len(url_list) == 0:
		if err_flag == True:					# detaillierte Fehlerausgabe vorziehen, aber nur bei leerer Liste
			return ObjectContainer(header=L('Fehler'), message=err)
		msg=L('keinen Stream gefunden zu: ') 
		message="%s %s" % (msg, title)
		return ObjectContainer(header=L('Fehler'), message=message)

	i=1; org_title=title
	for line in url_list:
		Log(line)
		url   = line.split('|||')[0]
		summ  = line.split('|||')[1]
		server = url[:80] + '...'
		summ  = '%s | %s' % (summ, server)
		
		fmt='mp3'
		if 'aac' in url:						# nicht immer  sichtbar - Bsp. http://addrad.io/4WRMHX
			fmt='aac'
		title = org_title + ' | Stream %s | %s'  % (str(i), fmt)
		i=i+1
		oc.add(CreateTrackObject(url=url, title=title, summary=summ, fmt=fmt, thumb=image))
		
	return oc

#-----------------------------
def get_pls(url):               # Playlist holen
	Log('get_pls: ' + url)
	urls =url.splitlines()	# manchmal mehrere enthalten, auch SHOUTcast.Links, Bsp. http://64.150.176.192:8043/, 
	for url in urls:		# wir verwenden aber nur den ersten pls-Link 
		if url.endswith('.pls'):
			break

	try:									# 1. Versuch 
		pls = HTTP.Request(url).content 	# Framework-Problem möglich: URLError: <urlopen error unknown url type: itunes>		
	except: 	
		pls=''
		
	if pls == '':							# 2. Versuch
		try:
			req = urllib2.Request(url)
			ret = urllib2.urlopen(req)
			pls = ret.read()	
			Log(pls[:10])
		except Exception as exception:	
			error_txt = 'Servermessage2: ' + str(exception)
			error_txt = error_txt + '\r\n' + url
			pls=error_txt
			return pls	
		
	if '[playlist]' in pls == False:	# Playlist erst mit der gefundenen url verfügbar 
		try:
			pls = HTTP.Request(pls).content # Bsp. [playlist] File1=http://195.150.20.9:8000/rmf_baby
		except Exception as exception:	
			error_txt = 'Servermessage3: ' + str(exception)
			error_txt = error_txt + '\r\n' + url
			pls=error_txt
				 			 	 		   
	Log(pls[:100])
	return pls
    
#-----------------------------
def get_m3u(url):               # m3u extrahieren - Inhalte mehrerer Links werden zusammengelegt,
	Log('get_m3u: ' + url)		#	Details holt getStreamMeta
	urls =url.splitlines()	
	
	m3u_cont = ''
	for url in urls:	
		if url.startswith('http') and url.endswith('.m3u'):		
			try:									
				req = HTTP.Request(url).content 	
			except: 	
				req=''
			m3u_cont = m3u_cont + req			# m3u-Inhalt anhängen
		
	pls=''; 
	lines =m3u_cont.splitlines()	
	for line in lines:
		# Log(line)
		if line.startswith('http'):			# skip #EXTM3U, #EXTINF, .. / Links sammeln
			pls = pls + line + '|'	
				 	
	pls =pls.split('|')	
	lines = repl_dop(pls)					# häufig identische Links in verschiedenen m3u8-Inhalten, 
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
	# itemAttr	= stringextract('itemAttr="', '"', line)	# n.b.
	
	local_url 	= unescape(local_url)
	text 		= unescape(text)
	subtext 	= unescape(subtext)	
	
	#Log("typ: " +typ); Log("local_url: " +local_url); Log("text: " +text); Log("image: " +image); 
	#Log("key: " +key); Log("subtext: " +subtext);
	#Log("text: " +text)

	return typ,local_url,text,image,key,subtext,bitrate
	
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
#	Google-Translation-Url (lokalisiert) im Exception-Fall getestet - funktionert mit PMS nicht
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
#									Hilfsfunktionen
####################################################################################################

@route(PREFIX + '/SearchUpdate')
def SearchUpdate(title):		#
	oc = ObjectContainer(title2=title, art=ObjectContainer.art)	

	ret = updater.update_available(VERSION)
	int_lv = ret[0]			# Version Github
	int_lc = ret[1]			# Version aktuell
	latest_version = ret[2]	# Version Github, Format 1.4.1
	summ = ret[3]			# Plugin-Name
	tag = ret[4]			# History (last change)

	url = 'https://github.com/{0}/releases/download/{1}/{2}.bundle.zip'.format(GITHUB_REPOSITORY, latest_version, REPO_NAME)
	Log(latest_version); Log(int_lv); Log(int_lc); Log(url); 
	
	if int_lv > int_lc:		# zum Testen drehen (akt. Plugin vorher sichern!)
		oc.add(DirectoryObject(
			key = Callback(updater.update, url=url , ver=latest_version), 
			title = L('neues Update vorhanden - jetzt installieren'),
			summary = 'Plugin Version: ' + VERSION + ', Github Version ' + latest_version,
			tagline = cleanhtml(summ),
			thumb = R(ICON_UPDATER_NEW)))
			
		oc.add(DirectoryObject(
			key = Callback(Main), 
			title = L('Update abbrechen'),
			summary = L('weiter im aktuellen Plugin'),
			thumb = R(ICON_UPDATER_NEW)))
	else:	
		oc.add(DirectoryObject(
			#key = Callback(updater.menu, title='Update Plugin'), 
			key = Callback(Main), 
			title = 'Plugin up to date | Home',
			summary = 'Plugin Version ' + VERSION + L(' ist die neueste Version'),
			tagline = cleanhtml(summ),
			thumb = R(ICON_OK)))
			
	return oc	
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
		Log('blockextract: blockmark nicht in mString enthalten')
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
def cleanhtml(line): # ersetzt alle HTML-Tags zwischen < und >  mit 1 Leerzeichen
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

	# Test auf angehängte Portnummer (zusätzl. Indikator für Stream)
	port = address.split(':')[-1]	# http://live.radiosbn.com:9400/
	port = port.replace('/', '')	# angeh. Slash entf.
	try:
		number = int(port)
		hasPortNumber='true'
	except:
		hasPortNumber='false'
	
	
	request = urllib2.Request(address)
	user_agent = 'iTunes/9.1.1'
	request.add_header('User-Agent', user_agent)
	request.add_header('icy-metadata', 1)
	try:
		response = urllib2.urlopen(request, timeout=6)
		headers = getHeaders(response)
		   
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

	except urllib2.URLError, e:
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

		
