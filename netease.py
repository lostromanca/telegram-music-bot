#
# Copyright (C) 2021 Shell-Script
# (https://ctcgfw.eu.org)
#
# This is free software, licensed under the GNU General Public License v3.
# See /LICENSE for more information.

# import getpass
import json
import pyncm
import requests

from pyncm.apis import cloudsearch as ncmsearch
from pyncm.apis import track as ncmtrack
from urllib.parse import quote as urlencode
from urllib.parse import unquote as urldecode

# pyncm.login.LoginViaCellphone(input('Phone number: '), getpass.getpass('Password: '))
# open('ncm.session', 'w+').write(pyncm.DumpSessionAsString(pyncm.GetCurrentSession()))
pyncm.SetCurrentSession(pyncm.LoadSessionFromString(open("ncm.session", "r", encoding="utf-8").read()))

def search(keyword):
	# search_info = ncmsearch.GetSearchResult(keyword=urlencode(keyword), type=1, limit=1, offset=0)
	search_info = requests.get('https://music.163.com/api/search/get?s=%s&type=1&limit=1&offset=0' % urlencode(keyword))
	if (search_info.ok and search_info.text):
		search_info.encoding = 'utf-8'
		search_info = json.loads(json.loads(json.dumps(search_info.text)))
		if (search_info['code'] != 200) or (search_info['result']['songCount'] < 1):
			return False
		else:
			return search_info['result']['songs'][0]['id']
	else:
		return False

def initial(musicId, bitrate):
	global music_info, music_source
	music_info = ncmtrack.GetTrackDetail(int(musicId))
	music_source = ncmtrack.GetTrackAudio(int(musicId), bitrate=bitrate)
	if not (music_info.text and music_source.text):
		return False
	else:
		music_info.encoding = 'utf-8'
		music_source.encoding = 'utf-8'
		music_info = json.loads(json.loads(json.dumps(music_info.text)))
		music_source = json.loads(json.loads(json.dumps(music_source.text)))
		if (music_info['code'] != 200) or (music_source['code'] != 200):
			return False
		else:
			return True

def get_album_id():
	try:
		return music_info['songs'][0]['al']['pic']
	except IndexError:
		return False

def get_album_link(size):
	try:
		return '%s?param=%s' % (music_info['songs'][0]['al']['picUrl'], size)
	except IndexError:
		return False

def get_song_name():
	try:
		return music_info['songs'][0]['name']
	except IndexError:
		return False

def get_song_singer():
	try:
		return music_info['songs'][0]['ar'][0]['name']
	except IndexError:
		return False

def get_song_type():
	try:
		return music_source['data'][0]['type']
	except IndexError:
		return False

def get_song_link():
	try:
		return music_source['data'][0]['url']
	except IndexError:
		return False
