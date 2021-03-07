#
# Copyright (C) 2021 Shell-Script
# (https://ctcgfw.eu.org)
#
# This is free software, licensed under the GNU General Public License v3.
# See /LICENSE for more information.

import kwDES
import json
import re
import requests

from urllib.parse import quote as urlencode
from urllib.parse import unquote as urldecode

def GetMiddleStr(content, startStr, endStr):
	startIndex = content.index(startStr)
	if startIndex>=0:
		startIndex += len(startStr)
	endIndex = content.index(endStr)
	return content[startIndex:endIndex]

def GetKuwoJsonItem(content, item):
	dump_text = content.replace('\'', '').split(',')
	count = 0
	while count < len(dump_text):
		try:
			if dump_text[count].split(':')[0] == item:
				return dump_text[count].split(':')[1]
				break
			else:
				count += 1
		except IndexError:
			count += 1
	return False

def search(keyword):
	keyword = urlencode(keyword)
	# Get CSRF token, required by search api
	search_request = requests.get('http://kuwo.cn/search/list?key=%s' % keyword)
	search_cookies = search_request.cookies
	search_token = search_request.cookies.get('kw_token')
	search_headers = {'referer': 'http://kuwo.cn/search/list?key=%s' % keyword, 'csrf': search_token}
	search_info = requests.get('http://www.kuwo.cn/api/www/search/searchMusicBykeyWord?key=%s&pn=1&rn=1' % keyword,
		cookies=search_cookies, headers=search_headers)
	# search_info = requests.get('http://search.kuwo.cn/r.s?SONGNAME=%s&ft=music&rformat=json&encoding=utf8&rn=1')
	if (search_info.ok and search_info.text):
		search_info.encoding = 'utf-8'
		search_info = json.loads(json.loads(json.dumps(search_info.text)))
		if (int(search_info['code']) != 200) or (int(search_info['data']['total']) < 1):
		# if (int(GetKuwoJsonItem(search_info, 'HIT') == 0) or (int(GetKuwoJsonItem(search_info, 'TOTAL')) < 1):
			return False
		else:
			return search_info['data']['list'][0]['musicrid'].replace('MUSIC_', '')
			# return GetKuwoJsonItem(search_info, 'MUSICRID').replace('MUSIC_', '')
	else:
		return False

def initial(musicId, quality):
	global music_id, music_info, music_source
	music_id = musicId
	music_info = requests.get('http://player.kuwo.cn/webmusic/st/getNewMuiseByRid?rid=MUSIC_%s' % music_id)
	if not (music_info.ok and music_info.text != '<Song>\n</Song>\n'):
		return False
	else:
		music_info.encoding = 'utf-8'
		music_info = music_info.text
	music_source = requests.get('http://mobi.kuwo.cn/mobi.s?f=kuwo&q=%s' % kwDES.base64_encrypt('corp=kuwo&p2p=1&' +
		'type=convert_url2&sig=0&format=%s&rid=%s' % (quality, music_id))).text
	if not music_source:
		return False
	else:
		return True

def get_album_link(size):
	music_album_link = requests.get('http://artistpicserver.kuwo.cn/pic.web?corp=kuwo&type=rid_pic&pictype=url&' +
		'content=list&size=%s&rid=%s' % (size, music_id)).text
	if not music_album_link:
		return False
	elif music_album_link == "NO_PIC":
		# Return the default one if no song-specific picture found
		return 'https://h5static.kuwo.cn/upload/image/4f768883f75b17a426c95b93692d98bec7d3ee9240f77f5ea68fc63870fdb050.png'
	else:
		return music_album_link

def get_song_name():
	try:
		song_name = GetMiddleStr(music_info, '<name>', '</name>')
		if song_name:
			return song_name
		else:
			return False
	except ValueError:
		return False

def get_song_singer():
	try:
		song_singer = GetMiddleStr(music_info, '<singer>', '</singer>')
		if song_singer:
			return song_singer
		else:
			return False
	except ValueError:
		return False

def get_song_type():
	try:
		return re.findall('flac|mp3', music_source)[0]
	except IndexError:
		return False

def get_song_link():
	try:
		return re.findall('http[^\s$"]+', music_source)[0]
	except IndexError:
		return False
