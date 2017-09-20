import urllib			# urllib.quote(), 
import urllib2			# urllib2.Request
import ssl				# HTTPS-Handshake
import random			# Zufallswerte für rating_key


ART    	= 'art-default.jpg'
ICON   	= 'icon-default.jpg'
NAME	= 'TuneIn2017'

ROOT_URL = 'http://opml.radiotime.com/Browse.ashx?formats=mp3,aac'
USER_URL = 'http://opml.radiotime.com/Browse.ashx?c=presets&partnerId=RadioTime&username=%s'
PREFIX = '/music/tunein2017'

####################################################################################################
def Start():

	ObjectContainer.title1 = NAME
	HTTP.CacheTime = 300
	ObjectContainer.art = R(ART)
	DirectoryObject.art = R(ART)
	DirectoryObject.thumb = R(ICON)

####################################################################################################
@handler(PREFIX, NAME,  art = ART, thumb = ICON)
@route(PREFIX)
def Main():
	Log('Main')
	title = 'Durchstöbern'
	title = title.decode(encoding="utf-8", errors="ignore")
	oc = ObjectContainer(title2=title)

	username = Prefs['username']
	Log(username)

	if username:
		my_title = 'Meine Favoriten'
		my_url = USER_URL % username
		my_stations = L('My Stations')
		oc.add(DirectoryObject(
			key = Callback(Rubriken, url=my_url, title=my_title, image=ICON),
			title = my_title, thumb = R(ICON) 
		))                    
		
	page = HTTP.Request(ROOT_URL).content	# xml-Übersicht Rubriken
	Log(page[:60])
	rubriken = blockextract('<outline', page)
	for rubrik in rubriken:
		typ,local_url,text,image,key,subtext= get_details(line=rubrik)	# xml extrahieren
		oc.add(DirectoryObject(
			key = Callback(Rubriken, url=local_url, title=text, image=image),
			title = text, thumb = R(ICON) 
		))   
		                 
	return oc
						
#----------------------------------------------------------------
def home(oc):											# Home-Button
	Log('home')	
	title = 'Start' 	
	oc.add(DirectoryObject(key=Callback(Main),title=title, summary=title, tagline=NAME, thumb=R('home.png')))
	return oc
#-----------------------------
@route(PREFIX + '/Rubriken')
def Rubriken(url, title, image):
	Log('Rubriken: ' + url)

	page = HTTP.Request(url).content	# xml-Übersicht Rubriken
	Log(page[:100])
	rubriken = blockextract('<outline type', page)
	
	oc_title2 = stringextract('<title>', '</title>', page)	# Bsp. <title>Frankfurt am Main</title>
	oc_title2 = unescape(oc_title2)
	oc_title2 = oc_title2.decode(encoding="utf-8", errors="ignore")
	
	key 	= stringextract('key="', '"', page)				# Bsp. key="stations">
	oc = ObjectContainer(title2=oc_title2)
	oc = home(oc)
	
	for rubrik in rubriken:
		#Log(rubrik)
		typ,local_url,text,image,key,subtext = get_details(line=rubrik)	# xml extrahieren
		Log(local_url)
		Log("typ: " +typ); Log("local_url: " +local_url); Log("text: " +text);
		Log("image: " +image); Log("key: " +key); Log("subtext: " +subtext); 
		text = text.decode(encoding="utf-8", errors="ignore")
		subtext = subtext.decode(encoding="utf-8", errors="ignore")
		
		if typ == 'link':
			oc.add(DirectoryObject(
				key = Callback(Rubriken, url=local_url, title=text, image=image),
				title = text, summary=subtext, thumb = image 
			)) 
                 
		if typ == 'audio':
			oc.add(DirectoryObject(
				key = Callback(StationList, url=local_url, title=text, summ=subtext, image=image, typ=typ),
				title = text, summary=subtext, thumb = image 
			))                    

	return oc

#-----------------------------
@route(PREFIX + '/StationList')
def StationList(url, title, image, summ, typ):
	Log('StationList: ' + url)
	summ = unescape(summ)
	Log(image);Log(summ);Log(typ)
	title = title.decode(encoding="utf-8", errors="ignore")
	oc = ObjectContainer(title2=title)
	
	Log(Client.Platform)				# Home-Button macht bei PHT die Trackliste unbrauchbar 
	client = Client.Platform
	if client == None:
		client = ''
	if client.find ('Plex Home Theater'): 
		oc = home(oc)					
			
	cont = HTTP.Request(url).content	# Bsp. http://opml.radiotime.com/Tune.ashx?id=s24878
	Log(cont[:100])
	if '.pls' in cont:					# Tune.ashx enthält häufig Links zu Playlist				
		cont = get_pls(cont)
		
	Log(cont)
			
	url_list = []						# Url-Liste 
	lines = cont.splitlines()	
	for line in lines:
		Log(line)
		url = line
		# if line.endswith('.m3u'):				# ein oder mehrere .m3u-Links
		if '.m3u' in line:						# auch das: ..playlist/newsouth-wusjfmmp3-ibc3.m3u?c_yob=1970&c_gender..
			url = HTTP.Request(line).content	# i.d.R. nur ein Direktlink, Bsp. http://absolut.hoerradar.de/..
			Log(url)
		if '=http' in line:						# Playlist-Eintrag, Bsp. File1=http://195.150.20.9:8000/..
			url = line.split('=')[1]
			Log(url)	
												# Sonderfälle:
		if 	'radiostreamer.com' in url:			# Streamhoster http://www.radiostreamer.com/: rs1.radiostreamer.com .. rs9..
			url = url + '/;stream/1'			#	 Div. Ports, Bsp. 'http://rs1.radiostreamer.com:8020'

				
		if 	url.startswith('http'):				# in Url-Liste 
			url_list.append(url)
			
	Log(url_list)
	url_list = repl_dop(url_list)				# Doppler entfernen	
	Log(url_list)
	for url in url_list:
		oc.add(CreateTrackObject(url=url, title=title, summary=summ, fmt='mp3', thumb=image))
		
	if len(oc) == 0:
		return ObjectContainer(header='Error', message='keinen Stream zu %s gefunden' % title)					
	return oc

#-----------------------------
def get_pls(url):               # Playlist holen
	Log('get_pls: ' + url)
	url =url.splitlines()[0]	# manchmal mehrere enthalten, wir verwenden nur den ersten Link 
	try:
		pls = HTTP.Request(url).content 	# Bsp. http://rmfon.pl/n/rmfswieta.pls
		Log(pls)
		if '[playlist]' in pls == False:	# erst pls_url führt zur Playlist
			pls = HTTP.Request(pls).content # Bsp. [playlist] File1=http://195.150.20.9:8000/rmf_baby
	except:
		pls = '' 
		   
	Log(pls)
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
	# itemAttr	= stringextract('itemAttr="', '"', line)	# n.b.
	
	local_url 	= unescape(local_url)
	text 		= unescape(text)
	subtext 	= unescape(subtext)	
	
	#Log("typ: " +typ); Log("local_url: " +local_url); Log("text: " +text); Log("image: " +image); 
	#Log("key: " +key); Log("subtext: " +subtext);

	return typ,local_url,text,image,key,subtext
	
#-----------------------------
@route(PREFIX + '/CreateTrackObject')
def CreateTrackObject(url, title, summary, fmt, thumb, include_container=False, location=None, includeBandwidths=None, autoAdjustQuality=None, hasMDE=None, **kwargs):
	Log('CreateTrackObject: ' + url); Log(include_container)
	Log(summary);Log(fmt);Log(thumb);

	if fmt == 'mp3':
		container = Container.MP3
		# container = 'mp3'
		audio_codec = AudioCodec.MP3

	title = title.decode(encoding="utf-8", errors="ignore")
	summary = summary.decode(encoding="utf-8", errors="ignore")

	random.seed()						
	rating_id = random.randint(1,10000)
	rating_key = 'rating_key-' + str(rating_id)
	Log(rating_key)

	track_object = TrackObject(
		key = Callback(CreateTrackObject, url=url, title=title, summary=summary, fmt=fmt, thumb=thumb, include_container=True, 
				location=None, includeBandwidths=None, autoAdjustQuality=None, hasMDE=None),
		rating_key = rating_key,	
		title = title,
		summary = summary,
		thumb=thumb,
		items = [
			MediaObject(
				parts = [
					PartObject(key=Callback(PlayAudio, url=url, ext=fmt)) # runtime- Aufruf: PlayAudio.mp3
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
# def PlayAudio(url, location=None, includeBandwidths=None, autoAdjustQuality=None, hasMDE=None, includeConcerts=None, includeExtras=None, includeOnDeck=None, includePopularLeaves=None, includeChapters=None, checkFiles=None, **kwargs):	
def PlayAudio(url, location=None, includeBandwidths=None, autoAdjustQuality=None, hasMDE=None, **kwargs):	
	Log('PlayAudio: ' + url )	
		
	if url is None or url == '':		# sollte hier nicht vorkommen
		Log('Url fehlt!')
		return ObjectContainer(header='Error', message='Url fehlt!') # Web-Player: keine Meldung
	try:
		req = urllib2.Request(url)						# Test auf Existenz, SSLContext für HTTPS erforderlich,
		gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)  	#	Bsp.: SWR3 https://pdodswr-a.akamaihd.net/swr3
		ret = urllib2.urlopen(req, context=gcontext)
		Log('PlayAudio: ' + str(ret.code))
	except Exception as exception:	
		error_txt = 'Server meldet: ' + str(exception)
		error_txt = error_txt + '\r\n' + url			 			 	 
		msgH = 'Error'; msg = error_txt
		msg =  msg.decode(encoding="utf-8", errors="ignore")
		Log(msg)
		return ObjectContainer(header=msgH, message=msg) # Framework fängt ab - keine Ausgabe
			
	return Redirect(url)

####################################################################################################
#									Hilfsfunktionen
####################################################################################################
def blockextract(blockmark, mString):  	# extrahiert Blöcke begrenzt durch blockmark aus mString
	#	blockmark bleibt Bestandteil der Rückgabe - im Unterschied zu split()
	#	Rückgabe in Liste. Letzter Block reicht bis Ende mString (undefinierte Länge),
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
def repl_dop(liste):	# Doppler entfernen, im Python-Script OK, Problem in Plex - s. PageControl
	mylist=liste
	myset=set(mylist)
	mylist=list(myset)
	mylist.sort()
	return mylist
