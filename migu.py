#
# Copyright (C) 2021 Shell-Script
# (https://ctcgfw.eu.org)
#
# This is free software, licensed under the GNU General Public License v3.
# See /LICENSE for more information.

import json
# import mgAES
import random
import re
import requests
import string

from urllib.parse import quote as urlencode
from urllib.parse import unquote as urldecode

MiguHeaders = {'origin': 'http://music.migu.cn/', 'referer': 'http://m.music.migu.cn/v3/',
	'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:77.0) Gecko/20190101 Firefox/77.0', 'channel': '0',
	'aversionid': ''}
# MiguCookies = { 'migu_music_sid': '' }
MiguProxies = {'http': '',
	'https': ''}

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
	music_info = requests.get('https://m.music.migu.cn/migu/remoting/cms_detail_tag?cpid=%s' % music_id, headers=MiguHeaders)
	if not (music_info.ok and music_info.text):
		return False
	else:
		music_info.encoding = 'utf-8'
		music_info = json.loads(json.loads(json.dumps(music_info.text)))
		try:
			song_id = music_info['data']['songId']
		except:
			return False
	''' Deprecated, as it requires login, and the cookie expires quickly.
	# Acceptable quality: 1=PQ, 2=HQ, 3=SQ
	request_data = { 'copyrightId': music_id, 'type': int(quality) }
	encrypted_request_data = mgAES.encrypt(json.dumps(request_data))
	encrypted_data = urlencode(encrypted_request_data[0])
	encrypted_secKey = urlencode(encrypted_request_data[1])
	music_source = requests.get('https://music.migu.cn/v3/api/music/audioPlayer/getPlayInfo?dataType=2&data=%s&secKey=%s' \
		% (encrypted_data, encrypted_secKey), headers=MiguHeaders, cookies=MiguCookies)
	'''
	random_str = ''.join(random.sample(string.digits + string.digits, 18))
	# Acceptable quality: PQ, HQ, SQ, ZQ | unimplemented: LQ, Z3D, ZQ24, ZQ32
	music_source = requests.get('https://app.c.nf.migu.cn/MIGUM2.0/strategy/listen-url/v2.2?lowerQualityContentId=%s' \
		% random_str + '&netType=01&resourceType=E&songId=%s&toneFlag=%s' % (song_id, quality), headers=MiguHeaders,
		proxies=MiguProxies)
	if (music_source.status_code != 200) or (not music_source.text):
		return False
	else:
		music_source = json.loads(json.loads(json.dumps(music_source.text)))
		# if music_source['returnCode'] != '000000':
		if (music_source.get('code') != '000000') or (music_source.get('formatType') != quality):
			return False
		else:
			return True

def get_album_link(type):
	# Acceptable type: picS, picM, picL
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
		# return re.findall('flac|mp3', music_source['data']['playUrl'])[0]
		return re.findall('flac|mp3', music_source['data']['url'])[0]
	except KeyError:
		return False

def get_song_link():
	try:
		# return 'http:%s' % urlencode(music_source['data']['playUrl'])
		return music_source['data']['url']
	except KeyError:
		return False
