from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import requests
import lyricsgenius
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

LASTFM_API_KEY = "5058e4076992e4688bb4104b252aaed7"
DISCOGS_API_KEY = "lYJnxXhQJsIwBDOmIeAATXrJogYjXikuRUYsJIhR"
GENIUS_API_KEY = "a5ox7Baa789j7qMf5JP8zBRs5qdT5WjkzOL_NRj07Qt8aEr7UZww-NKNZo-lhu-G"
LASTFM_BASE_URL = 'http://ws.audioscrobbler.com/2.0/'

# Инициализация Genius API
genius = lyricsgenius.Genius(GENIUS_API_KEY, timeout=15, retries=3)

# Список жанров для поиска
GENRES = [
    'electronic', 'rock', 'hip-hop', 'indie', 'jazz', 'reggae', 
    'british', 'punk', 'acoustic', 'rnb', 'metal', 'country', 
    'hardcore', 'blues', 'alternative', 'classical', 'rap'
]

def get_popular_tracks(genre=None, limit=15):
    """Получаем популярные треки, с возможностью фильтрации по жанру"""
    if genre:
        params = {
            'method': 'tag.gettoptracks',
            'tag': genre,
            'api_key': LASTFM_API_KEY,
            'format': 'json',
            'limit': limit
        }
    else:
        params = {
            'method': 'chart.gettoptracks',
            'api_key': LASTFM_API_KEY,
            'format': 'json',
            'limit': limit
        }
    
    try:
        response = requests.get(LASTFM_BASE_URL, params=params, timeout=10)
        data = response.json()
        
        tracks = []
        if genre and 'tracks' in data:
            track_data = data['tracks']['track']
        elif not genre and 'tracks' in data:
            track_data = data['tracks']['track']
        else:
            return []
        
        for track in track_data:
            cover_url = get_track_cover(track['artist']['name'], track['name'])
            track_info = get_track_info(track['artist']['name'], track['name'])
            
            tracks.append({
                'id': f"{track['artist']['name']}-{track['name']}",
                'name': track['name'],
                'artist': track['artist']['name'],
                'image': cover_url or track.get('image', [{}])[-1].get('#text', 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=300'),
                'duration': track_info.get('duration', '3:45'),
                'url': track_info.get('url', '#'),
                'listeners': track.get('listeners', '0'),
                'type': 'track'
            })
        return tracks
    except Exception as e:
        print(f"Error fetching popular tracks: {e}")
        return []

def get_new_releases(genre=None, limit=15):
    """Получаем новые релизы (треки) с использованием различных методов Last.fm"""
    try:
        # Пробуем разные методы для получения новых треков
        if genre:
            # Используем метод для получения топ треков по жанру как приближение новых релизов
            params = {
                'method': 'tag.gettoptracks',
                'tag': genre,
                'api_key': LASTFM_API_KEY,
                'format': 'json',
                'limit': limit
            }
        else:
            # Используем глобальные чарты как новые релизы
            params = {
                'method': 'chart.gettoptracks',
                'api_key': LASTFM_API_KEY,
                'format': 'json',
                'limit': limit
            }
        
        response = requests.get(LASTFM_BASE_URL, params=params, timeout=10)
        data = response.json()
        
        tracks = []
        if genre and 'tracks' in data:
            track_data = data['tracks']['track']
        elif not genre and 'tracks' in data:
            track_data = data['tracks']['track']
        else:
            return []
        
        for track in track_data:
            cover_url = get_track_cover(track['artist']['name'], track['name'])
            track_info = get_track_info(track['artist']['name'], track['name'])
            
            tracks.append({
                'id': f"{track['artist']['name']}-{track['name']}",
                'name': track['name'],
                'artist': track['artist']['name'],
                'image': cover_url or track.get('image', [{}])[-1].get('#text', 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=300'),
                'duration': track_info.get('duration', '3:45'),
                'url': track_info.get('url', '#'),
                'listeners': track.get('listeners', '0'),
                'type': 'track'
            })
        return tracks
    except Exception as e:
        print(f"Error fetching new releases: {e}")
        return []

def search_tracks(query, genre=None, limit=20):
    """Поиск треков с фильтрацией по жанру"""
    params = {
        'method': 'track.search',
        'api_key': LASTFM_API_KEY,
        'track': query,
        'format': 'json',
        'limit': limit
    }
    
    try:
        response = requests.get(LASTFM_BASE_URL, params=params, timeout=10)
        data = response.json()
        
        tracks = []
        if 'results' in data and 'trackmatches' in data['results']:
            for track in data['results']['trackmatches']['track']:
                # Если указан жанр, проверяем принадлежность артиста к жанру
                if genre and not has_genre(track['artist'], genre):
                    continue
                    
                cover_url = get_track_cover(track['artist'], track['name'])
                track_info = get_track_info(track['artist'], track['name'])
                
                tracks.append({
                    'id': f"{track['artist']}-{track['name']}",
                    'name': track['name'],
                    'artist': track['artist'],
                    'image': cover_url or track.get('image', [{}])[-1].get('#text', 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=300'),
                    'duration': track_info.get('duration', '3:45'),
                    'url': track.get('url', '#'),
                    'listeners': track.get('listeners', '0'),
                    'type': 'track'
                })
        return tracks
    except Exception as e:
        print(f"Error searching tracks: {e}")
        return []

def search_artists(query, genre=None, limit=10):
    """Поиск артистов с фильтрацией по жанру"""
    params = {
        'method': 'artist.search',
        'api_key': LASTFM_API_KEY,
        'artist': query,
        'format': 'json',
        'limit': limit
    }
    
    try:
        response = requests.get(LASTFM_BASE_URL, params=params, timeout=10)
        data = response.json()
        
        artists = []
        if 'results' in data and 'artistmatches' in data['results']:
            for artist in data['results']['artistmatches']['artist']:
                # Если указан жанр, проверяем принадлежность артиста к жанру
                if genre and not has_genre(artist['name'], genre):
                    continue
                    
                # Получаем дополнительную информацию об артисте для количества слушателей
                artist_info = get_artist_info(artist['name'])
                
                artists.append({
                    'name': artist['name'],
                    'listeners': artist_info.get('listeners', '0'),
                    'url': artist.get('url', '#'),
                    'image': artist.get('image', [{}])[-1].get('#text', 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=300'),
                    'type': 'artist'
                })
        return artists
    except Exception as e:
        print(f"Error searching artists: {e}")
        return []

def search_all(query, genre=None, limit=20):
    """Объединенный поиск артистов и треков"""
    artists = search_artists(query, genre, limit=5)
    tracks = search_tracks(query, genre, limit=15)
    
    return {
        'artists': artists,
        'tracks': tracks
    }

def get_artist_info(artist):
    """Получаем информацию об артисте, включая количество слушателей"""
    params = {
        'method': 'artist.getInfo',
        'api_key': LASTFM_API_KEY,
        'artist': artist,
        'format': 'json'
    }
    
    try:
        response = requests.get(LASTFM_BASE_URL, params=params, timeout=5)
        data = response.json()
        
        if 'artist' in data and data['artist']:
            return {
                'listeners': data['artist'].get('stats', {}).get('listeners', '0'),
                'playcount': data['artist'].get('stats', {}).get('playcount', '0')
            }
    except Exception as e:
        print(f"Error fetching artist info for {artist}: {e}")
    
    return {'listeners': '0', 'playcount': '0'}

def has_genre(artist, genre):
    """Проверяем, относится ли артист к указанному жанру"""
    try:
        params = {
            'method': 'artist.gettoptags',
            'artist': artist,
            'api_key': LASTFM_API_KEY,
            'format': 'json'
        }
        response = requests.get(LASTFM_BASE_URL, params=params, timeout=5)
        data = response.json()
        
        if 'toptags' in data and 'tag' in data['toptags']:
            tags = [tag['name'].lower() for tag in data['toptags']['tag']]
            return genre.lower() in tags
        return False
    except:
        return False

def get_artists_by_genre(genre, limit=20):
    """Получаем список артистов по жанру"""
    params = {
        'method': 'tag.gettopartists',
        'tag': genre,
        'api_key': LASTFM_API_KEY,
        'format': 'json',
        'limit': limit
    }
    
    try:
        response = requests.get(LASTFM_BASE_URL, params=params, timeout=10)
        data = response.json()
        
        artists = []
        if 'topartists' in data and 'artist' in data['topartists']:
            for artist in data['topartists']['artist']:
                artists.append({
                    'name': artist['name'],
                    'listeners': artist.get('listeners', '0'),
                    'url': artist.get('url', '#'),
                    'image': artist.get('image', [{}])[-1].get('#text', 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=300'),
                    'type': 'artist'
                })
        return artists
    except Exception as e:
        print(f"Error fetching artists by genre: {e}")
        return []

def get_artist_tracks(artist, limit=15):
    """Получаем треки артиста"""
    params = {
        'method': 'artist.gettoptracks',
        'artist': artist,
        'api_key': LASTFM_API_KEY,
        'format': 'json',
        'limit': limit
    }
    
    try:
        response = requests.get(LASTFM_BASE_URL, params=params, timeout=10)
        data = response.json()
        
        tracks = []
        if 'toptracks' in data and 'track' in data['toptracks']:
            for track in data['toptracks']['track']:
                cover_url = get_track_cover(artist, track['name'])
                track_info = get_track_info(artist, track['name'])
                
                tracks.append({
                    'id': f"{artist}-{track['name']}",
                    'name': track['name'],
                    'artist': artist,
                    'image': cover_url or track.get('image', [{}])[-1].get('#text', 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=300'),
                    'duration': track_info.get('duration', '3:45'),
                    'url': track.get('url', '#'),
                    'listeners': track.get('listeners', '0'),
                    'type': 'track'
                })
        return tracks
    except Exception as e:
        print(f"Error fetching artist tracks: {e}")
        return []

def get_track_cover(artist, track_name):
    """Получаем обложку из Discogs"""
    try:
        headers = {
            'Authorization': f'Discogs token={DISCOGS_API_KEY}',
            'User-Agent': 'VinylPlayer/1.0'
        }
        params = {
            'q': f'{artist} {track_name}',
            'type': 'release',
            'per_page': 1
        }
        response = requests.get(
            'https://api.discogs.com/database/search',
            headers=headers,
            params=params,
            timeout=5
        )
        data = response.json()
        
        if data.get('results') and data['results'][0].get('cover_image'):
            return data['results'][0]['cover_image']
    except Exception as e:
        print(f"Discogs error: {e}")
    
    return None

def get_track_info(artist, track):
    """Получаем информацию о треке, включая длительность"""
    params = {
        'method': 'track.getInfo',
        'api_key': LASTFM_API_KEY,
        'artist': artist,
        'track': track,
        'format': 'json'
    }
    
    try:
        response = requests.get(LASTFM_BASE_URL, params=params, timeout=5)
        data = response.json()
        
        if 'track' in data and data['track']:
            duration = data['track'].get('duration', '-')
            if duration != '-':
                # Конвертируем миллисекунды в минуты:секунды
                minutes = int(int(duration) // 60000)
                seconds = int((int(duration) % 60000) // 1000)
                duration = f"{minutes}:{seconds:02d}"
            return {
                'duration': duration,
                'url': data['track'].get('url', '#')
            }
    except Exception as e:
        print(f"Error fetching track info for {artist} - {track}: {e}")
    
    return {'duration': '3:45', 'url': '#'}

def get_lyrics(artist, title):
    """Получаем текст песни с Genius API"""
    if GENIUS_API_KEY == "YOUR_GENIUS_API_KEY":
        return None
    
    try:
        # Поиск песни
        song = genius.search_song(title, artist)
        if song:
            return song.lyrics
        return None
    except Exception as e:
        print(f"Error fetching lyrics: {e}")
        return None

# API Endpoints
@app.route('/api/tracks/popular')
def get_popular_tracks_route():
    genre = request.args.get('genre', '')
    tracks = get_popular_tracks(genre if genre != 'all' else None)
    return jsonify(tracks)

@app.route('/api/tracks/new')
def get_new_releases_route():
    genre = request.args.get('genre', '')
    tracks = get_new_releases(genre if genre != 'all' else None)
    return jsonify(tracks)

@app.route('/api/search')
def search_tracks_route():
    query = request.args.get('q', '')
    genre = request.args.get('genre', '')
    
    if not query:
        return jsonify({'artists': [], 'tracks': []})
    
    results = search_all(query, genre if genre != 'all' else None)
    return jsonify(results)

@app.route('/api/artists/<genre>')
def get_artists_by_genre_route(genre):
    artists = get_artists_by_genre(genre)
    return jsonify(artists)

@app.route('/api/artist/<artist>/tracks')
def get_artist_tracks_route(artist):
    tracks = get_artist_tracks(artist)
    return jsonify(tracks)

@app.route('/api/genres')
def get_genres_route():
    return jsonify(GENRES)

@app.route('/api/lyrics')
def get_lyrics_route():
    artist = request.args.get('artist', '')
    title = request.args.get('title', '')
    
    if not artist or not title:
        return jsonify({'lyrics': None})
    
    lyrics = get_lyrics(artist, title)
    return jsonify({'lyrics': lyrics})

# Основной маршрут для отдачи HTML
@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'test.html')

# Маршрут для отдачи статических файлов
@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

if __name__ == '__main__':
    app.run(debug=True, port=5500)