from elasticsearch import Elasticsearch, helpers
import json
import re
from googletrans import Translator
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

es = Elasticsearch([{'host': 'localhost', 'port':9200}])

def translate_to_english(value):
	translator = Translator()
	english_term = translator.translate(value, dest='en')
	return english_term.text

def post_processing_text(results):
    list_songs = []
    for i in range(len(results['hits']['hits'])) :
        lyrics = json.dumps(results['hits']['hits'][i]['_source']["song_lyrics"], ensure_ascii=False)
        lyrics = lyrics.replace('"', '')
        lyrics = lyrics.replace("'", '')       
        lyrics = lyrics.replace('\\', '')
        lyrics = lyrics.replace('t', '')
        lyrics = lyrics.replace('\xa0', '')
        lyrics = "<br>".join(lyrics.split("n"))
        lyrics =  re.sub(r'(<br> )+', r'\1', lyrics)
        j = 0
        while True :
            if lyrics[j] == '<' or lyrics[j] == '>' or lyrics[j] == 'b' or lyrics[j] == 'r' or lyrics[j] == ' ':
                j += 1
            else :
                break
        lyrics = lyrics[j:]
        results['hits']['hits'][i]['_source']["song_lyrics"] = lyrics
        list_songs.append(results['hits']['hits'][i]['_source'])
    aggregations = results['aggregations']
    artists = aggregations['artist']['buckets']
    genres = aggregations['genre']['buckets']
    music = aggregations['music']['buckets']
    lyrics = aggregations['lyrics']['buckets']

    return list_songs, artists, genres, music, lyrics


def search_text(search_term):
    results = es.search(index='index-songs',doc_type = 'sinhala-songs',body={
        "size" : 500,
        "query" :{
            "multi_match": {
                "query" : search_term,
                "type" : "best_fields",
                "fields" : [
                    "title", "Artist_si", "Artist_en","Genre_si","Genre_en", 
                    "Lyrics_si", "Lyrics_en","Music_si","Music_en", "song_lyrics"]
                    
            }
        },
        "aggs": {
            "genre": {
                "terms": {
                    "field": "Genre_si.keyword",
                    "size" : 15    
                }        
            },
            "artist": {
                "terms": {
                    "field":"Artist_si.keyword",
                    "size" : 15
                }             
            },
            "music": {
                "terms": {
                    "field":"Music_si.keyword",
                    "size" : 15
                }             
            },
            "lyrics": {
                "terms": {
                    "field":"Lyrics_si.keyword",
                    "size" : 15
                }             
            },

        }

    })

    list_songs, artists, genres, music, lyrics = post_processing_text(results)
    return list_songs, artists, genres, music, lyrics

def search_filter_text(search_term, artist_filter, genre_filter, music_filter, lyrics_filter):
    must_list = [{
                    "multi_match": {
                        "query" : search_term,
                        "type" : "best_fields",
                        "fields" : [
                            "title", "Artist_si", "Artist_en","Genre_si","Genre_en", 
                            "Lyrics_si", "Lyrics_en","Music_si","Music_en", "song_lyrics"]
                            
                    }
                }]
    if len(artist_filter) != 0 :
        for i in artist_filter :
            must_list.append({"match" : {"Artist_si": i}})
    if len(genre_filter) != 0 :
        for i in genre_filter :
            must_list.append({"match" : {"Genre_si": i}})
    if len(music_filter) != 0 :
        for i in music_filter :
            must_list.append({"match" : {"Music_si": i}})
    if len(lyrics_filter) != 0 :
        for i in lyrics_filter :
            must_list.append({"match" : {"Lyrics_si": i}})
    results = es.search(index='index-songs',doc_type = 'sinhala-songs',body={
        "size" : 500,
        "query" :{
            "bool": {
                "must": must_list
            }
        },
        "aggs": {
            "genre": {
                "terms": {
                    "field": "Genre_si.keyword",
                    "size" : 15    
                }        
            },
            "artist": {
                "terms": {
                    "field":"Artist_si.keyword",
                    "size" : 15
                }             
            },
            "music": {
                "terms": {
                    "field":"Music_si.keyword",
                    "size" : 15
                }             
            },
            "lyrics": {
                "terms": {
                    "field":"Lyrics_si.keyword",
                    "size" : 15
                }             
            },

        }
    })
    list_songs, artists, genres, music, lyrics = post_processing_text(results)
    return list_songs, artists, genres, music, lyrics





def intent_classifier(search_term):

    select_type = False
    resultword = ''

    keyword_top = ["top", "best", "popular", "good", "great"]
    keyword_song = ["song", "sing", "sang", "songs", "sings"]
    search_term_list = search_term.split()
    for j in search_term_list : 
        documents = [j]
        documents.extend(keyword_top)
        documents.extend(keyword_song)
        tfidf_vectorizer = TfidfVectorizer(analyzer="char", token_pattern=u'(?u)\\b\w+\\b')
        tfidf_matrix = tfidf_vectorizer.fit_transform(documents)

        cs = cosine_similarity(tfidf_matrix[0:1],tfidf_matrix)
        similarity_list = cs[0][1:]

        for i in similarity_list :
            if i > 0.8 :
                select_type  = True
    if select_type :
        querywords = search_term.split()
        querywords  = [word for word in querywords if word.lower() not in keyword_top]
        querywords  = [word for word in querywords if word.lower() not in keyword_song]
        resultword = ' '.join(querywords)

    
    return select_type,  resultword


def top_most_text(search_term):

    with open('song-corpus/songs_meta_all.json') as f:
        meta_data = json.loads(f.read())

    artist_list = meta_data["Artist_en"]
    genre_list = meta_data["Genre_en"]
    music_list = meta_data["Music_en"]
    lyrics_list = meta_data["Lyrics_en"]

    documents_artist = [search_term]
    documents_artist.extend(artist_list)
    documents_genre = [search_term]
    documents_genre.extend(genre_list)
    documents_music = [search_term]
    documents_music.extend(music_list)
    documents_lyrics = [search_term]
    documents_lyrics.extend(lyrics_list)
    query = []
    select_type = False

    size = 100
    term_list = search_term.split()
    print(term_list)
    for i in term_list:
        if i.isnumeric():
            size = int(i)

    tfidf_vectorizer = TfidfVectorizer(analyzer="char", token_pattern=u'(?u)\\b\w+\\b')
    tfidf_matrix = tfidf_vectorizer.fit_transform(documents_artist)

    cs = cosine_similarity(tfidf_matrix[0:1],tfidf_matrix)

    similarity_list = cs[0][1:]

    max_val = max(similarity_list)
    other_select = False
    if max_val >  0.85 :
        loc = np.where(similarity_list==max_val)
        i = loc[0][0]
        query.append({"match" : {"Artist_en": artist_list[i]}})
        select_type = True
        other_select = True

    tfidf_vectorizer = TfidfVectorizer(analyzer="char", token_pattern=u'(?u)\\b\w+\\b')
    tfidf_matrix = tfidf_vectorizer.fit_transform(documents_genre)

    cs = cosine_similarity(tfidf_matrix[0:1],tfidf_matrix)

    similarity_list = cs[0][1:]

    max_val = max(similarity_list)
    if max_val >  0.85 :
        loc = np.where(similarity_list==max_val)
        i = loc[0][0]
        query.append({"match" : {"Genre_en": genre_list[i]}})
        select_type = True

    tfidf_vectorizer = TfidfVectorizer(analyzer="char", token_pattern=u'(?u)\\b\w+\\b')
    tfidf_matrix = tfidf_vectorizer.fit_transform(documents_music)

    cs = cosine_similarity(tfidf_matrix[0:1],tfidf_matrix)

    similarity_list = cs[0][1:]
    max_val = max(similarity_list)
    if max_val >  0.85 and other_select == False:
        loc = np.where(similarity_list==max_val)
        i = loc[0][0]
        query.append({"match" : {"Music_en": music_list[i]}})
        select_type = True
        other_select = True

    tfidf_vectorizer = TfidfVectorizer(analyzer="char", token_pattern=u'(?u)\\b\w+\\b')
    tfidf_matrix = tfidf_vectorizer.fit_transform(documents_lyrics)

    cs = cosine_similarity(tfidf_matrix[0:1],tfidf_matrix)

    similarity_list = cs[0][1:]
    max_val = max(similarity_list)
    if max_val >  0.85 and other_select == False:
        loc = np.where(similarity_list==max_val)
        i = loc[0][0]
        query.append({"match" : {"Lyrics_en": lyrics_list[i]}})
        select_type = True
        other_select = True
    
    if select_type != True :
        query.append({"match_all" : {}})

    print(query)
    results = es.search(index='index-songs',doc_type = 'sinhala-songs',body={
        "size" : size,
        "query" :{
            "bool": {
                "must": query
            }
        },
        "sort" :{
            "views": {"order": "desc"}
        },
        "aggs": {
            "genre": {
                "terms": {
                    "field": "Genre_si.keyword",
                    "size" : 15    
                }        
            },
            "artist": {
                "terms": {
                    "field":"Artist_si.keyword",
                    "size" : 15
                }             
            },
            "music": {
                "terms": {
                    "field":"Music_si.keyword",
                    "size" : 15
                }             
            },
            "lyrics": {
                "terms": {
                    "field":"Lyrics_si.keyword",
                    "size" : 15
                }             
            },

        }
    })
    list_songs, artists, genres, music, lyrics = post_processing_text(results)
    return list_songs, artists, genres, music, lyrics

def top_most_filter_text(search_term, artist_filter, genre_filter, music_filter, lyrics_filter):

    with open('song-corpus/songs_meta_all.json') as f:
        meta_data = json.loads(f.read())

    artist_list = meta_data["Artist_en"]
    genre_list = meta_data["Genre_en"]
    music_list = meta_data["Music_en"]
    lyrics_list = meta_data["Lyrics_en"]

    documents_artist = [search_term]
    documents_artist.extend(artist_list)
    documents_genre = [search_term]
    documents_genre.extend(genre_list)
    documents_music = [search_term]
    documents_music.extend(music_list)
    documents_lyrics = [search_term]
    documents_lyrics.extend(lyrics_list)
    query = []
    select_type = False
    size = 100
    term_list = search_term.split()
    for i in term_list:
        if i.isnumeric():
            size = i

    if len(artist_filter) != 0 :
        for i in artist_filter :
            query.append({"match" : {"Artist_si": i}})
    if len(genre_filter) != 0 :
        for i in genre_filter :
            query.append({"match" : {"Genre_si": i}})
    if len(music_filter) != 0 :
        for i in music_filter :
            query.append({"match" : {"Music_si": i}})
    if len(lyrics_filter) != 0 :
        for i in lyrics_filter :
            query.append({"match" : {"Lyrics_si": i}})


    tfidf_vectorizer = TfidfVectorizer(analyzer="char", token_pattern=u'(?u)\\b\w+\\b')
    tfidf_matrix = tfidf_vectorizer.fit_transform(documents_artist)

    cs = cosine_similarity(tfidf_matrix[0:1],tfidf_matrix)

    similarity_list = cs[0][1:]
    other_select = False
    max_val = max(similarity_list)
    if max_val >  0.85 and other_select == False:
        loc = np.where(similarity_list==max_val)
        i = loc[0][0]
        query.append({"match" : {"Artist_en": artist_list[i]}})
        select_type = True
        other_select = True

    tfidf_vectorizer = TfidfVectorizer(analyzer="char", token_pattern=u'(?u)\\b\w+\\b')
    tfidf_matrix = tfidf_vectorizer.fit_transform(documents_genre)

    cs = cosine_similarity(tfidf_matrix[0:1],tfidf_matrix)

    similarity_list = cs[0][1:]

    max_val = max(similarity_list)
    if max_val >  0.85 and other_select == False:
        loc = np.where(similarity_list==max_val)
        i = loc[0][0]
        query.append({"match" : {"Genre_en": genre_list[i]}})
        select_type = True

    tfidf_vectorizer = TfidfVectorizer(analyzer="char", token_pattern=u'(?u)\\b\w+\\b')
    tfidf_matrix = tfidf_vectorizer.fit_transform(documents_music)

    cs = cosine_similarity(tfidf_matrix[0:1],tfidf_matrix)

    similarity_list = cs[0][1:]
    max_val = max(similarity_list)
    if max_val >  0.85 and other_select == False:
        loc = np.where(similarity_list==max_val)
        i = loc[0][0]
        query.append({"match" : {"Music_en": music_list[i]}})
        select_type = True
        other_select = True

    tfidf_vectorizer = TfidfVectorizer(analyzer="char", token_pattern=u'(?u)\\b\w+\\b')
    tfidf_matrix = tfidf_vectorizer.fit_transform(documents_lyrics)

    cs = cosine_similarity(tfidf_matrix[0:1],tfidf_matrix)

    similarity_list = cs[0][1:]
    max_val = max(similarity_list)
    if max_val >  0.85 and other_select == False :
        loc = np.where(similarity_list==max_val)
        i = loc[0][0]
        query.append({"match" : {"Lyrics_en": lyrics_list[i]}})
        select_type = True
        other_select = True
    
    if select_type != True :
        query.append({"match_all" : {}})

    print(query)
    results = es.search(index='index-songs',doc_type = 'sinhala-songs',body={
        "size" : 500,
        "query" :{
            "bool": {
                "must": query
            }
        },
        "sort" :{
            "views": {"order": "desc"}
        },
        "aggs": {
            "genre": {
                "terms": {
                    "field": "Genre_si.keyword",
                    "size" : 15    
                }        
            },
            "artist": {
                "terms": {
                    "field":"Artist_si.keyword",
                    "size" : 15
                }             
            },
            "music": {
                "terms": {
                    "field":"Music_si.keyword",
                    "size" : 15
                }             
            },
            "lyrics": {
                "terms": {
                    "field":"Lyrics_si.keyword",
                    "size" : 15
                }             
            },

        }
    })
    list_songs, artists, genres, music, lyrics = post_processing_text(results)
    return list_songs, artists, genres, music, lyrics


def search_query(search_term):
    english_term = translate_to_english(search_term)
    select_type, strip_term = intent_classifier(english_term)  
    if select_type :
        list_songs, artists, genres, music, lyrics = top_most_text(strip_term)
    else :
        list_songs, artists, genres, music, lyrics = search_text(search_term)

    return list_songs, artists, genres, music, lyrics


def search_query_filtered(search_term, artist_filter, genre_filter, music_filter, lyrics_filter):
    english_term = translate_to_english(search_term)
    select_type, strip_term = intent_classifier(english_term)  
    if select_type :
        list_songs, artists, genres, music, lyrics = top_most_filter_text(strip_term, artist_filter, genre_filter, music_filter, lyrics_filter)
    else :
        list_songs, artists, genres, music, lyrics = search_filter_text(search_term, artist_filter, genre_filter, music_filter, lyrics_filter)

    return list_songs, artists, genres, music, lyrics
    
    
            







    
