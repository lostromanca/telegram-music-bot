#!/usr/bin/env python3
#-*-coding:utf-8-*-
# SPDX-License-Identifier: AGPL-3.0-only
#
# Copyright (C) 2021 Shell-Script
# (https://ctcgfw.eu.org)

import base64
import cv2
import fcntl
# import getpass
import logging
import json
import kwDES
# import mgAES
import os
import pickledb
import pyncm
import random, re, requests
import socket, string
# import subprocess
import time
import wget

from lxml import etree
from pyncm.apis import cloudsearch as ncmsearch
from pyncm.apis import track as ncmtrack
from pyncm.apis import video as ncmmvtrack
from pyrogram import filters, Client
from pyrogram.errors.exceptions.bad_request_400 import MessageIdInvalid
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from socket import getaddrinfo, AF_INET, AF_INET6
from tinytag import TinyTag as tinytag
from unittest.mock import patch as ipvxpatch
from urllib.parse import quote as urlencode
from urllib.parse import unquote as urldecode

# pyncm.login.LoginViaCellphone(input('Phone number: '), getpass.getpass('Password: '))
# open('ncm.session', 'w+').write(pyncm.DumpSessionAsString(pyncm.GetCurrentSession()))
pyncm.SetCurrentSession(pyncm.LoadSessionFromString(open('ncm.session', 'r', encoding='utf-8').read()))

app = Client('musicbot', bot_token='',
	api_id='', api_hash='')

allow_chat_id = [ ]
cache_chat_id = 

MUSIC_CACHE_DB = 'db/mcache.db'
MV_CACHE_DB = 'db/mcache.db'
PROCESS_LOCK = 'locks/process.lock'

# MiguCookies = { 'migu_music_sid': '' }
MiguHeaders = {'origin': 'http://music.migu.cn/', 'referer': 'http://m.music.migu.cn/v3/',
	'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:77.0) Gecko/20190101 Firefox/77.0', 'channel': '0',
	'aversionid': ''}

GlobalProxies = {'http': '',
	'https': 'socks5://'}

def format_size(B):
	try:
		B = float(B)
		KiB = B / 1024
	except:
		return False
	if KiB >= 1024:
		MiB = KiB / 1024
		if MiB >= 1024:
			GiB = MiB / 1024
			return '%.2f GiB' % GiB
		else:
			return '%.2f MiB' % MiB
	else:
		return '%.2f KiB' % KiB

def getaddrinfoIPv4(host, port, family=0, type=0, proto=0, flags=0):
	return getaddrinfo(host=host, port=port, family=AF_INET, type=type, proto=proto, flags=flags)

def getaddrinfoIPv6(host, port, family=0, type=0, proto=0, flags=0):
	return getaddrinfo(host=host, port=port, family=AF_INET6, type=type, proto=proto, flags=flags)

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

def set_lock(FILE):
	file = open(FILE, 'a')
	fcntl.flock(file.fileno(), fcntl.LOCK_EX)
	return file

def set_multi_lock(FILE):
	thread = str(random.randint(1,4))
	file = open(FILE + thread, 'a')
	fcntl.flock(file.fileno(), fcntl.LOCK_EX)
	return file

def download_file(url, file, msg, msg_id, chat_id):
	headers = { 'Proxy-Connection': 'keep-alive' }
	request_data = requests.get(url, stream=True, headers=headers)
	file_size = float(request_data.headers.get('content-length') or 0)
	app.edit_message_text(chat_id, msg_id, '%s\n\n0%% of total %s, speed: 0/s' % (msg, format_size(file_size)))

	save_file = open(file, 'wb')
	count = 0
	count_tmp = 0
	start_time = time.time()
	try:
		for chunk in request_data.iter_content(chunk_size=1024):
			if chunk:
				save_file.write(chunk)
				count += len(chunk)
				if time.time() - start_time > 4:
					progress = count / file_size * 100
					down_speed = (count - count_tmp) / 5
					count_tmp = count
					app.edit_message_text(chat_id, msg_id, '%s\n\n%.2f%% of total %s, speed: %s/s' % (msg, progress, format_size(file_size),
						format_size(down_speed)))
					start_time = time.time()
		save_file.close()
	except:
		return False
	return True

def upload_music(info, msg_id, orig_msg_id, chat_id):
	'''
	Info:
	0. Platform
	1. Song ID
	2. Song name
	3. Song alias name
	4. Singer(s)
	5. Album ID
	6. Album name
	7. Album picURL
	8. Song type
	9. Song playURL
	10. Song detail URL
	11. Album detail URL
	'''
	platform = info[0]
	song_id = info[1]
	song_name = info[2]
	song_alias = info[3]
	song_singers = info[4]
	album_id = info[5]
	album_name = info[6]
	album_url = info[7]
	song_type = info[8]
	song_url = info[9]
	song_link = info[10]
	album_link = info[11]
	song_reply_markup = InlineKeyboardMarkup(
		[
			[
				InlineKeyboardButton(
					'Song: ' + song_name,
					url=song_link
				)
			],
			[
				InlineKeyboardButton(
					'Album: ' + album_name,
					url=album_link
				)
			]
		]
	)

	app.edit_message_text(chat_id, msg_id, 'Wait download lock...')
	album_lock = 'locks/%s.lock' % album_id
	lock = set_lock(album_lock)

	cache_db = pickledb.load(MUSIC_CACHE_DB, True)
	cached_msgid = cache_db.get('%s_%s' % (platform, song_id))
	if cached_msgid:
		try:
			app.copy_message(chat_id, cache_chat_id, cached_msgid, reply_markup=song_reply_markup)
			try: app.delete_messages(chat_id, msg_id)
			except: None
			lock.close()
			os.remove(album_lock)
			return
		except:
			None

	downloading_album_message = 'Start downloading album...\n\nAlbum information:\n'
	downloading_album_message += 'Album ID: %s\n' % album_id
	downloading_album_message += 'Album name: %s' % album_name
	album_file = 'songs/%s-%s.jpg' % (platform, album_id)
	if not download_file(album_url, album_file, downloading_album_message, msg_id, chat_id):
		app.edit_message_text(chat_id, msg_id, 'Failed to download album.\n\nAlbum URL: ' + album_url)
		return

	downloading_song_message = 'Start downloading music...\n\nMusic information:\n'
	downloading_song_message += 'Song ID: %s\n' % song_id
	downloading_song_message += 'Song name: %s\n' % song_name
	downloading_song_message += 'Song singer(s): %s' % song_singers
	song_file = 'songs/%s-%s.%s' % (platform, song_id, song_type)
	if not download_file(urldecode(song_url), song_file, downloading_song_message, msg_id, chat_id):
		app.edit_message_text(chat_id, msg_id, 'Failed to download music.\n\nSong URL: ' + song_url)
		return

	song_info = tinytag.get(song_file)
	song_bitrate = song_info.bitrate
	song_duration = int(song_info.duration)
	song_size = song_info.filesize
	song_caption = 'Platform: %s\n' % platform
	song_caption += 'Song ID: %s\n' % song_id
	song_caption += 'Song name: %s\n' % song_name
	if song_alias: song_caption += 'Song alias name: %s\n' % song_alias
	song_caption += 'Song singer(s): %s\n' % song_singers
	song_caption += 'Album name: %s\n' % album_name
	song_caption += 'Bitrate: %.f Kbps' % song_bitrate
	app.edit_message_text(chat_id, msg_id, 'Uploading music...\n\nSong size: %s' % format_size(song_size))
	try:
		song_msg_id = app.send_audio(cache_chat_id, audio=song_file, reply_to_message_id=orig_msg_id, caption=song_caption,
			duration=song_duration, performer=song_singers, title=song_name, thumb=album_file,
				file_name='%s - %s.%s' % (song_singers, song_name, song_type), reply_markup=song_reply_markup).message_id
		app.copy_message(chat_id, cache_chat_id, song_msg_id, reply_markup=song_reply_markup)
	except:
		app.edit_message_text(chat_id, msg_id, 'Failed to upload music.\n\nAlbum URL: %s\nSong URL: %s' %
			(album_url, song_url))

	cache_db.set('%s_%s' % (platform, song_id), song_msg_id)

	try: app.delete_messages(chat_id, msg_id)
	except: None
	try: os.remove(album_file)
	except: None
	try: os.remove(song_file)
	except: None

	lock.close()
	os.remove(album_lock)

def upload_mv(info, msg_id, orig_msg_id, chat_id):
	'''
	Info:
	0. Platform
	1. MV ID
	2. MV name
	3. Artist(s)
	4. Cover ID
	5. Cover picURL
	6. MV playURL
	7. MV detail URL
	'''
	platform = info[0]
	mv_id = info[1]
	mv_name = info[2]
	mv_artists = info[3]
	cover_id = info[4]
	cover_url = info[5]
	mv_url = info[6]
	mv_link = info[7]
	mv_reply_markup = InlineKeyboardMarkup(
		[
			[
				InlineKeyboardButton(
					'MV: ' + mv_name,
					url=mv_link
				)
			]
		]
	)

	app.edit_message_text(chat_id, msg_id, 'Wait download lock...')
	mv_lock = 'locks/%s.lock' % mv_id
	lock = set_lock(mv_lock)

	cache_db = pickledb.load(MV_CACHE_DB, True)
	cached_msgid = cache_db.get('%s_%s' % (platform, mv_id))
	if cached_msgid:
		try:
			app.copy_message(chat_id, cache_chat_id, cached_msgid, reply_markup=mv_reply_markup)
			try: app.delete_messages(chat_id, msg_id)
			except: None
			return
		except:
			None

	downloading_cover_message = 'Start downloading cover...\n\nCover information:\n'
	downloading_cover_message += 'Platform: %s\n' % platform
	downloading_cover_message += 'Cover ID: %s' % cover_id
	cover_file = 'mvs/%s-%s.jpg' % (platform, cover_id)
	if not download_file(cover_url, cover_file, downloading_cover_message, msg_id, chat_id):
		app.edit_message_text(chat_id, msg_id, 'Failed to download cover.\n\nCover URL: ' + cover_url)
		return

	downloading_mv_message = 'Start downloading MV...\n\nMV information:\n'
	downloading_mv_message += 'MV ID: %s\n' % mv_id
	downloading_mv_message += 'MV name: %s\n' % mv_name
	downloading_mv_message += 'MV artist(s): %s' % mv_artists
	mv_file = 'mvs/%s-%s.mp4' % (platform, mv_id)
	if not download_file(mv_url, mv_file, downloading_mv_message, msg_id, chat_id):
		app.edit_message_text(chat_id, msg_id, 'Failed to download MV.\n\nMV URL: ' + mv_url)
		return

	mv_info = cv2.VideoCapture(mv_file)
	mv_duration = int(mv_info.get(cv2.CAP_PROP_FRAME_COUNT) / mv_info.get(cv2.CAP_PROP_FPS))
	mv_height = int(mv_info.get(cv2.CAP_PROP_FRAME_HEIGHT))
	mv_width = int(mv_info.get(cv2.CAP_PROP_FRAME_WIDTH))
	mv_size = os.path.getsize(mv_file)
	mv_caption = 'Platform: %s\n' % platform
	mv_caption += 'MV ID: %s\n' % mv_id
	mv_caption += 'MV name: %s\n' % mv_name
	mv_caption += 'MV artist(s): %s' % mv_artists
	app.edit_message_text(chat_id, msg_id, 'Uploading MV...\n\nVideo size: %s' % format_size(mv_size))
	try:
		mv_msg_id = app.send_video(cache_chat_id, video=mv_file, reply_to_message_id=orig_msg_id, caption=mv_caption,
		duration=mv_duration, height=mv_height, width=mv_width, thumb=cover_file, file_name='%s - %s.mp4' % (mv_artists, mv_name),
			supports_streaming=True, reply_markup=mv_reply_markup).message_id
		app.copy_message(chat_id, cache_chat_id, mv_msg_id, reply_markup=mv_reply_markup)
	except:
		app.edit_message_text(chat_id, msg_id, 'Failed to upload MV.\n\nCover URL: %s\nMV URL: %s' %
			(cover_url, mv_url))

	cache_db.set('%s_%s' % (platform, mv_id), mv_msg_id)

	try: app.delete_messages(chat_id, msg_id)
	except: None
	try: os.remove(cover_file)
	except: None
	try: os.remove(mv_file)
	except: None

	lock.close()
	os.remove(mv_lock)

def get_kuwo_music(musicId, msg_id, chat_id):
	''' Cannot get albumID
	try:
		music_info = requests.get('http://player.kuwo.cn/webmusic/st/getNewMuiseByRid?rid=MUSIC_%s' % musicId)
		if not music_info.text != '<Song>\n</Song>\n':
			return False
		else:
			music_info.encoding = 'utf-8'
			music_info = music_info.text
	except:
		return False
	'''
	# Require mainland China IPs
	try:
		with ipvxpatch('socket.getaddrinfo', side_effect=getaddrinfoIPv4):
			music_info = requests.get('http://m.kuwo.cn/newh5/singles/songinfoandlrc?musicId=%s' % musicId, proxies=GlobalProxies)
		music_info.encoding = 'utf-8'
		music_info = json.loads(json.loads(json.dumps(music_info.text)))
		if music_info.get('status') != 200:
			app.edit_message_text(chat_id, msg_id, 'Failed to get music metadata.')
			return False
	except:
		app.edit_message_text(chat_id, msg_id, '[NET ERR] Failed to get music metadata.')
		return False

	try:
		music_source = requests.get('http://mobi.kuwo.cn/mobi.s?f=kuwo&q=%s' % kwDES.base64_encrypt('corp=kuwo&p2p=1&' +
			'type=convert_url2&sig=0&format=flac|mp3&rid=%s' % musicId)).text
		if not music_source:
			app.edit_message_text(chat_id, msg_id, 'Failed to get music playurl.')
			return False
	except:
		app.edit_message_text(chat_id, msg_id, '[NET ERR] Failed to get music playurl.')
		return False

	music_default_img = 'https://h5static.kuwo.cn/upload/image/4f768883f75b17a426c95b93692d98bec7d3ee9240f77f5ea68fc63870fdb050.png'
	music_pack_info = [ ]
	music_pack_info.append('kuwo')
	music_pack_info.append(musicId)
	# music_pack_info.append(GetMiddleStr(music_info, '<name>', '</name>'))
	music_pack_info.append(music_info.get('data').get('songinfo').get('songName'))
	music_pack_info.append(None)
	# music_pack_info.append(GetMiddleStr(music_info, '<singer>', '</singer>'))
	music_pack_info.append(music_info.get('data').get('songinfo').get('artist'))
	music_pack_info.append(str(music_info.get('data').get('songinfo').get('albumId')))
	music_pack_info.append(music_info.get('data').get('songinfo').get('album') or 'None')
	'''
	try:
		music_album_url = requests.get('http://artistpicserver.kuwo.cn/pic.web?corp=kuwo&type=rid_pic&pictype=url&' +
			'content=list&size=320x320&rid=%s' % musicId).text
		if (not music_album_url) or (music_album_url == 'NO_PIC'):
			music_pack_info.append(music_default_img)
		else:
			music_pack_info.append(music_album_url)
	except:
		music_pack_info.append(music_default_img)
	'''
	music_pack_info.append(music_info.get('data').get('songinfo').get('pic') or music_default_img)
	music_pack_info.append(re.findall('flac|mp3', music_source)[0])
	music_pack_info.append(re.findall('http[^\s$"]+', music_source)[0])
	music_pack_info.append('https://www.kuwo.cn/play_detail/' + musicId)
	music_pack_info.append('https://www.kuwo.cn/album_detail/' + str(music_pack_info[5]))
	return music_pack_info

def get_migu_music(musicId, msg_id, chat_id):
	try:
		music_info = requests.get('https://m.music.migu.cn/migu/remoting/cms_detail_tag?cpid=%s' % musicId, headers=MiguHeaders)
		music_info.encoding = 'utf-8'
		music_info = json.loads(json.loads(json.dumps(music_info.text)))
		music_song_id = music_info.get('data').get('songId')
		if not music_song_id:
			app.edit_message_text(chat_id, msg_id, 'Failed to get music metadata.')
			return False
	except:
		app.edit_message_text(chat_id, msg_id, '[NET ERR] Failed to get music metadata.')
		return False

	try:
		music_details = requests.get('https://music.migu.cn/v3/music/song/%s' % musicId, headers=MiguHeaders)
		music_details.encoding = 'utf-8'
		music_details = etree.HTML(music_details.text)
	except:
		app.edit_message_text(chat_id, msg_id, '[NET ERR] Failed to get music details.')
		return False

	''' Deprecated, as it requires login, and the cookie expires quickly.
	# Acceptable quality: 1=PQ, 2=HQ, 3=SQ
	request_data = { 'copyrightId': musicId, 'type': int(quality) }
	encrypted_request_data = mgAES.encrypt(json.dumps(request_data))
	encrypted_data = urlencode(encrypted_request_data[0])
	encrypted_secKey = urlencode(encrypted_request_data[1])
	try:
		music_source = requests.get('https://music.migu.cn/v3/api/music/audioPlayer/getPlayInfo?dataType=2&data=%s&secKey=%s' \
			% (encrypted_data, encrypted_secKey), headers=MiguHeaders, cookies=MiguCookies)
	except:
		app.edit_message_text(chat_id, msg_id, '[NET ERR] Failed to get music playurl.')
		return False
	'''

	random_str = ''.join(random.sample(string.digits + string.digits, 18))
	# Acceptable quality: PQ, HQ, SQ, ZQ | unimplemented: LQ, Z3D, ZQ24, ZQ32
	for quality in ['PQ', 'HQ', 'SQ', 'ZQ']:
		try:
			with ipvxpatch('socket.getaddrinfo', side_effect=getaddrinfoIPv4):
				music_source = requests.get('https://app.c.nf.migu.cn/MIGUM2.0/strategy/listen-url/v2.2?lowerQualityContentId=%s' \
					% random_str + '&netType=01&resourceType=E&songId=%s&toneFlag=%s' % (music_song_id, quality), headers=MiguHeaders,
						proxies=GlobalProxies)
			music_source = json.loads(json.loads(json.dumps(music_source.text)))
			# if music_source.get('returnCode') != '000000':
			if (music_source.get('code') != '000000'):
				app.edit_message_text(chat_id, msg_id, 'Failed to get music playurl.')
				return False
				break
			elif music_source.get('formatType') != quality:
				continue
			else:
				break
		except:
			continue
	if not music_source:
		app.edit_message_text(chat_id, msg_id, '[NET ERR] Failed to get music playurl.')
		return False

	music_pack_info = [ ]
	music_pack_info.append('migu')
	music_pack_info.append(musicId)
	music_pack_info.append(music_info.get('data').get('songName'))
	music_pack_info.append(None)
	music_pack_info.append(' / '.join(music_info.get('data').get('singerName')))
	music_pack_info.append(music_details.xpath('//div[@class="songInfo"]/input[@id="albumid"]/@value')[0] or '0')
	music_pack_info.append(music_details.xpath('//div[@class="info_about"]/p')[3].xpath('//span/a/text()')[0] or 'None')
	music_pack_info.append(music_info.get('data').get('picS'))
	music_pack_info.append(re.findall('flac|mp3', music_source.get('data').get('url'))[0])
	music_pack_info.append(music_source.get('data').get('url'))
	music_pack_info.append('https://music.migu.cn/v3/music/song/' + musicId)
	music_pack_info.append('https://music.migu.cn/v3/music/album/' + str(music_pack_info[5]))
	return music_pack_info

def get_netease_music(musicId, msg_id, chat_id):
	try:
		music_info = ncmtrack.GetTrackDetail(musicId)
		if music_info.get('code') != 200:
			app.edit_message_text(chat_id, msg_id, 'Failed to get music metadata.')
			return False
	except:
		app.edit_message_text(chat_id, msg_id, '[NET ERR] Failed to get music metadata.')
		return False

	try:
		music_source = ncmtrack.GetTrackAudio(musicId, bitrate=999000)
		if (music_source.get('code') != 200) or (music_source.get('data')[0].get('code') != 200):
			app.edit_message_text(chat_id, msg_id, 'Failed to get music playurl.')
			return False
	except:
		app.edit_message_text(chat_id, msg_id, '[NET ERR] Failed to get music playurl.')
		return False

	num = int()
	music_singers = str()
	music_pack_info = [ ]
	music_pack_info.append('netease')
	music_pack_info.append(musicId)
	music_pack_info.append(music_info.get('songs')[0].get('name'))
	if len(music_info.get('songs')[0].get('alia')) > 0:
		music_pack_info.append(' / '.join(music_info.get('songs')[0].get('alia')))
	else:
		music_pack_info.append(None)
	while num < len(music_info.get('songs')[0].get('ar')):
		if not music_singers:
			music_singers = music_info.get('songs')[0].get('ar')[num].get('name')
		else:
			music_singers += ' / ' + music_info.get('songs')[0].get('ar')[num].get('name')
		num += 1
	music_pack_info.append(music_singers)
	music_pack_info.append(str(music_info.get('songs')[0].get('al').get('id')))
	music_pack_info.append(music_info.get('songs')[0].get('al').get('name'))
	music_pack_info.append(music_info.get('songs')[0].get('al').get('picUrl') + '?param=320x320')
	music_pack_info.append(music_source.get('data')[0].get('type'))
	music_pack_info.append(music_source.get('data')[0].get('url'))
	music_pack_info.append('https://music.163.com/#/song?id=' + musicId)
	music_pack_info.append('https://music.163.com/#/album?id=' + str(music_pack_info[5]))
	return music_pack_info

def get_netease_mv(mvId, msg_id, chat_id):
	try:
		mv_info = ncmmvtrack.GetMVDetail(mvId)
		if mv_info.get('code') != 200:
			app.edit_message_text(chat_id, msg_id, 'Failed to get MV metadata.')
			return False
	except:
		app.edit_message_text(chat_id, msg_id, '[NET ERR] Failed to get MV metadata.')
		return False

	try:
		mv_source = ncmmvtrack.GetMVResource(mvId, res=1080)
		if (mv_source.get('code') != 200):
			app.edit_message_text(chat_id, msg_id, 'Failed to get MV playurl.')
			return False
	except:
		app.edit_message_text(chat_id, msg_id, '[NET ERR] Failed to get MV playurl.')
		return False

	num = int()
	mv_artists = str()
	mv_pack_info = [ ]
	mv_pack_info.append('netease')
	mv_pack_info.append(mvId)
	mv_pack_info.append(mv_info.get('data').get('name'))
	while num < len(mv_info.get('data').get('artists')):
		if not mv_artists:
			mv_artists = mv_info.get('data').get('artists')[num].get('name')
		else:
			mv_artists += ' / ' + mv_info.get('data').get('artists')[num].get('name')
		num += 1
	mv_pack_info.append(mv_artists)
	mv_pack_info.append(str(mv_info.get('data').get('coverId')))
	mv_pack_info.append(mv_info.get('data').get('cover'))
	mv_pack_info.append(mv_source.get('data').get('url'))
	mv_pack_info.append('https://music.163.com/#/mv?id=' + mvId)
	return mv_pack_info

@app.on_message(filters.command(['kuwo', 'kuwo@ctcgfw_musicpusher_bot'], case_sensitive=True) & filters.chat(allow_chat_id) & ~filters.edited)
def kuwo_command(client, message):
	kuwo_musicinfo = ' '.join(message.text.split(' ')[1:])
	if not kuwo_musicinfo:
		message.reply_text('Usage: /kuwo musicrId|keyword', quote=True)
		return

	original_message_id = message.message_id
	update_message_id = message.reply_text('Wait process lock...', quote=True).message_id
	lock = set_multi_lock(PROCESS_LOCK)

	if not str.isdigit(kuwo_musicinfo):
		app.edit_message_text(message.chat.id, update_message_id, 'Searching music information...')

		keyword = urlencode(kuwo_musicinfo)
		try:
			# search_info = requests.get('http://search.kuwo.cn/r.s?SONGNAME=%s&ft=music&rformat=json&encoding=utf8&rn=1')
			# Get CSRF token, required by search api
			search_request = requests.get('http://kuwo.cn/search/list?key=%s' % keyword)
			search_cookies = search_request.cookies
			search_token = search_request.cookies.get('kw_token')
			search_headers = {'referer': 'http://kuwo.cn/search/list?key=%s' % keyword, 'csrf': search_token}
			search_info = requests.get('http://www.kuwo.cn/api/www/search/searchMusicBykeyWord?key=%s&pn=1&rn=1' % keyword,
				cookies=search_cookies, headers=search_headers)
			search_info.encoding = 'utf-8'
			search_info = json.loads(json.loads(json.dumps(search_info.text)))
			# if (int(GetKuwoJsonItem(search_info, 'HIT') == 0) or (int(GetKuwoJsonItem(search_info, 'TOTAL')) < 1):
			if (search_info.get('code') != 200) or (int(search_info.get('data').get('total')) < 1):
				app.edit_message_text(message.chat.id, update_message_id, 'Failed to search music information.')
			else:
				app.edit_message_text(message.chat.id, update_message_id, 'Getting music information...')

				# kuwo_musicid = GetKuwoJsonItem(search_info, 'MUSICRID').replace('MUSIC_', '')
			kuwo_musicid = search_info.get('data').get('list')[0].get('musicrid').replace('MUSIC_', '')
			kuwo_info = get_kuwo_music(kuwo_musicid, update_message_id, message.chat.id)
			if kuwo_info: upload_music(kuwo_info, update_message_id, original_message_id, message.chat.id)
		except:
			app.edit_message_text(message.chat.id, update_message_id, '[NET ERR] Failed to search music information.')
	else:
		app.edit_message_text(message.chat.id, update_message_id, 'Getting music information...')

		kuwo_info = get_kuwo_music(kuwo_musicinfo, update_message_id, message.chat.id)
		if kuwo_info: upload_music(kuwo_info, update_message_id, original_message_id, message.chat.id)

	lock.close()

@app.on_message(filters.command(['migu', 'migu@ctcgfw_musicpusher_bot'], case_sensitive=True) & filters.chat(allow_chat_id) & ~filters.edited)
def migu_command(client, message):
	migu_musicinfo = ' '.join(message.text.split(' ')[1:])
	if not migu_musicinfo:
		message.reply_text('Usage: /migu copyrightId|keyword', quote=True)
		return

	original_message_id = message.message_id
	update_message_id = message.reply_text('Wait process lock...', quote=True).message_id
	lock = set_multi_lock(PROCESS_LOCK)

	if not str.isdigit(migu_musicinfo):
		app.edit_message_text(message.chat.id, update_message_id, 'Searching music information...')

		try:
			search_info = requests.get('http://m.music.migu.cn/migu/remoting/scr_search_tag?keyword=%s&type=2&rows=1&pgc=1' \
				% urlencode(migu_musicinfo), headers=MiguHeaders)
			search_info.encoding = 'utf-8'
			search_info = json.loads(json.loads(json.dumps(search_info.text)))
			if (not search_info.get('success')) or (not search_info.get('pgt')):
				app.edit_message_text(message.chat.id, update_message_id, 'Failed to search music information.')
			else:
				app.edit_message_text(message.chat.id, update_message_id, 'Getting music information...')

				migu_musicid = str(search_info.get('musics')[0].get('copyrightId'))
				migu_info = get_migu_music(migu_musicid, update_message_id, message.chat.id)
				if migu_info: upload_music(migu_info, update_message_id, original_message_id, message.chat.id)
		except:
			app.edit_message_text(message.chat.id, update_message_id, '[NET ERR] Failed to search music information.')
	else:
		app.edit_message_text(message.chat.id, update_message_id, 'Getting music information...')

		migu_info = get_migu_music(migu_musicinfo, update_message_id, message.chat.id)
		if migu_info: upload_music(migu_info, update_message_id, original_message_id, message.chat.id)

	lock.close()

@app.on_message(filters.command(['netease', 'netease@ctcgfw_musicpusher_bot'], case_sensitive=True) & filters.chat(allow_chat_id) & ~filters.edited)
def netease_command(client, message):
	netease_musicinfo = ' '.join(message.text.split(' ')[1:])
	if not netease_musicinfo:
		message.reply_text('Usage: /netease songId|keyword', quote=True)
		return

	original_message_id = message.message_id
	update_message_id = message.reply_text('Wait process lock...', quote=True).message_id
	lock = set_multi_lock(PROCESS_LOCK)

	if not str.isdigit(netease_musicinfo):
		app.edit_message_text(message.chat.id, update_message_id, 'Searching music information...')

		try:
			# search_info = ncmsearch.GetSearchResult(keyword=urlencode(netease_musicinfo), type=ncmsearch.TYPE_SONG, limit=1, offset=0)
			search_info = requests.get('https://music.163.com/api/search/get?s=%s&type=1&limit=1&offset=0' % urlencode(netease_musicinfo))
			search_info.encoding = 'utf-8'
			search_info = json.loads(json.loads(json.dumps(search_info.text)))
			if (search_info.get('code') != 200) or (search_info.get('result').get('songCount') < 1):
				app.edit_message_text(message.chat.id, update_message_id, 'Failed to search music information.')
			else:
				app.edit_message_text(message.chat.id, update_message_id, 'Getting music information...')

				netease_musicid = str(search_info.get('result').get('songs')[0].get('id'))
				netease_info = get_netease_music(netease_musicid, update_message_id, message.chat.id)
				if netease_info: upload_music(netease_info, update_message_id, original_message_id, message.chat.id)
		except:
			app.edit_message_text(message.chat.id, update_message_id, '[NET ERR] Failed to search music information.')
	else:
		app.edit_message_text(message.chat.id, update_message_id, 'Getting music information...')

		netease_info = get_netease_music(netease_musicinfo, update_message_id, message.chat.id)
		if netease_info: upload_music(netease_info, update_message_id, original_message_id, message.chat.id)

	lock.close()

@app.on_message(filters.command(['neteasemv', 'neteasemv@ctcgfw_musicpusher_bot'], case_sensitive=True) & filters.chat(allow_chat_id) & ~filters.edited)
def neteasemv_command(client, message):
	netease_mvinfo = ' '.join(message.text.split(' ')[1:])
	if not netease_mvinfo:
		message.reply_text('Usage: /neteasemv mvId|keyword', quote=True)
		return

	original_message_id = message.message_id
	update_message_id = message.reply_text('Wait process lock...', quote=True).message_id
	lock = set_multi_lock(PROCESS_LOCK)

	if not str.isdigit(netease_mvinfo):
		app.edit_message_text(message.chat.id, update_message_id, 'Searching MV information...')

		try:
			# search_info = ncmsearch.GetSearchResult(keyword=urlencode(netease_mvinfo), type=ncmsearch.TYPE_MV, limit=1, offset=0)
			search_info = requests.get('https://music.163.com/api/search/get?s=%s&type=1004&limit=1&offset=0' % urlencode(netease_mvinfo))
			search_info.encoding = 'utf-8'
			search_info = json.loads(json.loads(json.dumps(search_info.text)))
			if (search_info.get('code') != 200) or (search_info.get('result').get('mvCount') < 1):
				app.edit_message_text(message.chat.id, update_message_id, 'Failed to search MV information.')
			else:
				app.edit_message_text(message.chat.id, update_message_id, 'Getting MV information...')

				netease_mvid = str(search_info.get('result').get('mvs')[0].get('id'))
				netease_info = get_netease_mv(netease_mvid, update_message_id, message.chat.id)
				if netease_info: upload_mv(netease_info, update_message_id, original_message_id, message.chat.id)
		except:
			app.edit_message_text(message.chat.id, update_message_id, '[NET ERR] Failed to search MV information.')
	else:
		app.edit_message_text(message.chat.id, update_message_id, 'Getting MV information...')

		netease_info = get_netease_mv(netease_mvinfo, update_message_id, message.chat.id)
		if netease_info: upload_mv(netease_info, update_message_id, original_message_id, message.chat.id)

	lock.close()

app.run()
