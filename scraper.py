import requests, os, time
from bs4 import BeautifulSoup
import mtranslate
from googletrans import Translator
import json,re


def translate_to_sinhala(value):
	translator = Translator()
	#sinhala_val = mtranslate.translate(value, 'si', 'en')
	sinhala_val = translator.translate(value, dest='si')
	return sinhala_val.text

def parse_lyrics(lyrics):
	space_set = set([' '])
	processed = ''
	regex = r"([A-z])+|[0-9]|\||-|∆|([.!?\\\/\(\)\+#&])+"
	lyric_lines = lyrics.split('\n')
	for line in lyric_lines:
		new = re.sub(regex, '', line)
		chars = set(new)
		if not ((chars == space_set) or (len(chars) is 0)):
			processed += new + '\n'
	return processed

def seperate_key_beat(key_beat):
	key_beat_list = key_beat.split("|")
	key = ""
	beat = ""
	if len(key_beat_list) == 2:
		key = key_beat_list[0]
		beat = key_beat_list[1]
		if beat[0] == " ":
			beat = beat[1:]	
	return key, beat


def key_val_split(key_val):
	key_val_list = key_val.split(":")
	if len(key_val_list) >= 2 :
		key = key_val_list[0]
		vals = key_val_list[1]
		if vals[0] == " ":
			vals = vals[1:]
		if "," in vals :
			vals = vals.split(",")
		return key, vals

def get_song_info(song_page):
	soup = BeautifulSoup(song_page, 'html.parser')

	song = soup.find('h1', {'class': 'entry-title'})
	artist = soup.find('span', {'class': 'entry-categories'})
	genre = soup.find('span', {'class': 'entry-tags'})
	lyricist = soup.find('span', {'class': 'lyrics'})
	music = soup.find('span', {'class': 'music'})
	movie = soup.find('span', {'class': 'movies'})
	author = soup.find('span', {'class': 'entry-author-name'})
	keys = soup.find('h3', {'class': None})
	views = soup.find('div',{'class':'tptn_counter'})
	lyrics = parse_lyrics(soup.find_all('pre')[0].get_text())
	if views :
		views = views.get_text().split()[1].split('Visits')[0]
	if keys :
		key, beat = seperate_key_beat(keys.get_text())
	song_meta_data = {}
	if song : 
		song_meta_data['title'] = song.get_text()

	song_list = [artist, genre, lyricist, author, music, movie, key, beat]
	for key_val in song_list:
		if key_val :
			if isinstance(key_val, str):
				key_vals = key_val_split(key_val)
			else :
				key_vals = key_val_split(key_val.get_text())
			if key_vals :
				key = key_vals[0]
				vals = key_vals[1]
				song_meta_data[key] = vals
	
	if views :
		song_meta_data['views'] = int(views.replace(',',''))
	if lyrics :
		song_meta_data['song_lyrics'] = lyrics

	return song_meta_data

def translate_meta_data(dict_meta_data):
	sinhala_meta_data = {}
	for eng_key in dict_meta_data :
		if isinstance(dict_meta_data[eng_key], int) or eng_key == "lyrics" or eng_key == "Beat":
			key = translate_to_sinhala(eng_key)
			value = dict_meta_data[eng_key]
		elif eng_key == "Genre":
			key = translate_to_sinhala(eng_key)
			value = []
			for i in dict_meta_data[eng_key] :
				value.append(translate_to_sinhala(i))
		else :
			key = translate_to_sinhala(eng_key)
			value = translate_to_sinhala(dict_meta_data[eng_key])
		sinhala_meta_data[key] = value

def translate_values(dict_meta_data):
	sinhala_meta_data = {}
	for key in dict_meta_data:
		if isinstance(dict_meta_data[key], int) or key == "Beat" or key == "song_lyrics" or key == "Key" or key == "title":
			sinhala_meta_data[key] = dict_meta_data[key]
		elif type(dict_meta_data[key]) == list :
			value_list = []
			for i in dict_meta_data[key]:
				value_list.append(translate_to_sinhala(i))
			sinhala_meta_data['{}_en'.format(key)] = dict_meta_data[key]
			sinhala_meta_data['{}_si'.format(key)] = value_list
		else :
			sinhala_meta_data['{}_en'.format(key)] = dict_meta_data[key]
			sinhala_meta_data['{}_si'.format(key)] = translate_to_sinhala(dict_meta_data[key])
	return sinhala_meta_data

def scrape_page(url):
	headers = requests.utils.default_headers()
	res = requests.get(url, headers)
	soup = BeautifulSoup(res.text, 'html.parser')	
	song_links = soup.find_all('a', {'class': '_blank'})
	song_list_english = []
	song_list_sinhala = []
	for i in song_links :
		song_url = i.get("href")
		song_meta_data = get_song_info(song_url)
		song_meta_sinhala = translate_meta_data(song_meta_data)
		song_list_english.append(song_meta_data)
		song_list_sinhala.append(song_meta_sinhala)
		time.sleep(10)
	return song_list_english, song_list_sinhala

def parse_html(html_pg):
	links = []
	soup = BeautifulSoup(html_pg, 'html.parser')
	song_links = soup.find_all("a", {"class": "_blank"})
	for tag in song_links:
		link = tag.get('href')
		links.append(link)
	return links

def write_res(links_array):
	with open('song-corpus/song_links.csv','a') as f:
		for link in links_array:
			f.write(link + os.linesep)

def scrape_links():
	for i in range(1, 22):
		url = 'https://sinhalasongbook.com/all-sinhala-song-lyrics-and-chords/?_page={}/'.format(i)
		headers = requests.utils.default_headers()
		res = requests.get(url, headers)
		links_array = parse_html(res.text)
		write_res(links_array)

def add_element(song, key, list_elements):
	if key not in song:
		return list_elements
	else :
		element = song[key]
		if element == None :
			return list_elements
		elif element in list_elements :
			return list_elements
		elif element not in list_elements :
			if type(element) == list :
				for i in element :
					if i not in list_elements:
						list_elements.append(i)
			else :
				list_elements.append(element)
			return list_elements


def get_songs_list():
	with open('song-corpus/song_links.csv', 'r') as f:
		lines = f.readlines()
	list_songs = []
	for i in range(1000):
		headers = requests.utils.default_headers()
		res = requests.get(lines[i], headers)
		print('Scraping songs', i)
		song = get_song_info(res.text)
		song_sinhala = translate_values(song)
		list_songs.append(song_sinhala)
	return list_songs


def translate_list(list_val):
	list_si = []
	for i in list_val :
		list_si.append(translate_to_sinhala(i))
	return list_si

def get_songs_data():
	list_songs = get_songs_list()
	with open ('song-corpus/songs.json','w+') as f:
		f.write(json.dumps(list_songs))


def clean_spaces(data_point):
	for key in data_point:
		if type(data_point[key]) == int :
			pass
		elif type(data_point[key]) == list:
			for i in range(len(data_point[key])):
				if type(data_point[key][i]) == str :
					c = 0
					for j in data_point[key][i]:
						if j == " ":
							c += 1
						else :
							break
					data_point[key][i] = data_point[key][i][c:]
		else :
			c = 0
			for i in data_point[key]:
				if i == " ":
					c += 1
				else :
					break
			data_point[key] = data_point[key][c:]
	#print(data_point)
	return data_point

def combine_songs():
	song_list = []
	for i in range(1,11):
		with open('song-corpus/songs_0{}.json'.format(i)) as f:
			data = json.loads(f.read())
		for j in data:
			song_list.append(clean_spaces(j))
	print(len(song_list))
	with open ('song-corpus/songs.json','w+') as f:
		f.write(json.dumps(song_list))

def create_meta_all():
	dict_all_meta = {}
	list_keys = ['Artist_en', 'Artist_si', 'Genre_en', 'Genre_si', 'Music_en', 'Music_si', 'Lyrics_en', 'Lyrics_si']
	for i in list_keys :
		dict_all_meta[i] = []

	with open('song-corpus/songs.json') as f:
		data = json.loads(f.read())

	for items in data:
		for key in items:
			if key in list_keys:
				if type(items[key]) == list:
					for val in items[key]:
						if val not in dict_all_meta[key]:
							dict_all_meta[key].append(val)
				else :
					if items[key] not in dict_all_meta[key]:
						dict_all_meta[key].append(items[key])
	
	with open ('song-corpus/songs_meta_all.json','w+') as f:
		f.write(json.dumps(dict_all_meta))


#combine_songs()
#get_songs_data()
#print(mtranslate.translate('Coffee', 'si', 'en'))
if __name__ == "__main__":
	scrape_links()
	get_songs_data()
	create_meta_all()

    