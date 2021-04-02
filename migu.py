#
# Copyright (C) 2021 Shell-Script
# (https://ctcgfw.eu.org)
#
# This is free software, licensed under the GNU General Public License v3.
# See /LICENSE for more information.

import json
import requests
import mgAES
import re

from urllib.parse import quote_plus as urlencode
from urllib.parse import unquote_plus as urldecode

MiguHeaders = {'origin': 'http://music.migu.cn/', 'referer': 'http://m.music.migu.cn/v3/',
	'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:77.0) Gecko/20190101 Firefox/77.0'}
MiguCookies = { 'migu_music_sid': '' }

def search(keyword):
	search_info = requests.get('http://m.music.migu.cn/migu/remoting/scr_search_tag?keyword=%s&&type=2&rows=1&pgc=1' \
		% urlencode(keyword), headers=MiguHeaders)
	if (search_info.ok and search_info.text):
		search_info.encoding = 'utf-8'
		search_info = json.loads(json.loads(json.dumps(search_info.text)))
		try:
			if (not search_info['success']) or (search_info['pgt'] < 1):
				return False
			else:
				return search_info['musics'][0]['copyrightId']
		except KeyError:
			return False
	else:
		return False

def initial(musicId, quality):
	global music_info, music_source
	music_id = musicId
	music_info = requests.get('https://m.music.migu.cn/migu/remoting/cms_detail_tag?cpid=%s' % music_id, headers = MiguHeaders)
	if not (music_info.ok and music_info.text):
		return False
	else:
		music_info.encoding = 'utf-8'
		music_info = json.loads(json.loads(json.dumps(music_info.text)))
	request_data = { 'copyrightId': music_id, 'type': int(quality) }
	encrypted_request_data = mgAES.encrypt(json.dumps(request_data))
	encrypted_data = urlencode(encrypted_request_data[0])
	encrypted_secKey = urlencode(encrypted_request_data[1])
	music_source = requests.get('https://music.migu.cn/v3/api/music/audioPlayer/getPlayInfo?dataType=2&data=%s&secKey=%s' \
		% (encrypted_data, encrypted_secKey), headers = MiguHeaders, cookies=MiguCookies)
	if (music_source.status_code != 200) or (not music_source.text):
		return False
	else:
		music_source = json.loads(json.loads(json.dumps(music_source.text)))
		if music_source['returnCode'] != '000000':
			return False
		else:
			return True

def get_album_link(type):
	try:
		return music_info['data'][type]
	except KeyError:
		return False

def get_song_name():
	try:
		return music_info['data']['songName']
	except KeyError:
		return False

def get_song_singer():
	try:
		singers = str()
		for singer in music_info['data']['singerName']:
			singers += ' / ' + singer if singers else singer
		return singers
	except KeyError:
		return False

def get_song_type():
	try:
		return re.findall('flac|mp3', music_source['data']['playUrl'])[0]
	except KeyError:
		return False

def get_song_link():
	try:
		return 'http:%s' % music_source['data']['playUrl']
	except KeyError:
		return False
