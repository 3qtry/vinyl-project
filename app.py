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

def get_popular_tracks(limit=15):
    """Получаем популярные треки"""
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
        if 'tracks' in data and 'track' in data['tracks']:
            for track in data['tracks']['track']:
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

def get_new_releases(limit=15):
    """Получаем новые релизы"""
    try:
        params = {
            'method': 'chart.gettoptracks',
            'api_key': LASTFM_API_KEY,
            'format': 'json',
            'limit': limit
        }
        
        response = requests.get(LASTFM_BASE_URL, params=params, timeout=10)
        data = response.json()
        
        tracks = []
        if 'tracks' in data and 'track' in data['tracks']:
            for track in data['tracks']['track']:
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

def search_tracks(query, limit=20):
    """Поиск треков"""
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

def search_artists(query, limit=10):
    """Поиск артистов"""
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

def search_albums(query, limit=10):
    """Поиск альбомов"""
    params = {
        'method': 'album.search',
        'api_key': LASTFM_API_KEY,
        'album': query,
        'format': 'json',
        'limit': limit
    }
    
    try:
        response = requests.get(LASTFM_BASE_URL, params=params, timeout=10)
        data = response.json()
        
        albums = []
        if 'results' in data and 'albummatches' in data['results']:
            for album in data['results']['albummatches']['album']:
                albums.append({
                    'name': album['name'],
                    'artist': album['artist'],
                    'url': album.get('url', '#'),
                    'image': album.get('image', [{}])[-1].get('#text', 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=300'),
                    'type': 'album'
                })
        return albums
    except Exception as e:
        print(f"Error searching albums: {e}")
        return []

def get_recent_tracks(artist, limit=10):
    """Получаем последние треки артиста"""
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
        print(f"Error fetching recent tracks: {e}")
        return []

def get_artist_albums(artist, limit=10):
    """Получаем альбомы артиста"""
    params = {
        'method': 'artist.gettopalbums',
        'artist': artist,
        'api_key': LASTFM_API_KEY,
        'format': 'json',
        'limit': limit
    }
    
    try:
        response = requests.get(LASTFM_BASE_URL, params=params, timeout=10)
        data = response.json()
        
        albums = []
        if 'topalbums' in data and 'album' in data['topalbums']:
            for album in data['topalbums']['album']:
                albums.append({
                    'name': album['name'],
                    'artist': artist,
                    'url': album.get('url', '#'),
                    'image': album.get('image', [{}])[-1].get('#text', 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=300'),
                    'playcount': album.get('playcount', '0'),
                    'type': 'album'
                })
        return albums
    except Exception as e:
        print(f"Error fetching artist albums: {e}")
        return []

def get_artist_info(artist):
    """Получаем информацию об артисте"""
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
            artist_data = data['artist']
            return {
                'name': artist_data.get('name', ''),
                'listeners': artist_data.get('stats', {}).get('listeners', '0'),
                'playcount': artist_data.get('stats', {}).get('playcount', '0'),
                'bio': artist_data.get('bio', {}).get('summary', ''),
                'image': artist_data.get('image', [{}])[-1].get('#text', 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=300'),
                'tags': [tag['name'] for tag in artist_data.get('tags', {}).get('tag', [])][:5]
            }
    except Exception as e:
        print(f"Error fetching artist info for {artist}: {e}")
    
    return {
        'name': artist,
        'listeners': '0',
        'playcount': '0',
        'bio': '',
        'image': 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=300',
        'tags': []
    }

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
    tracks = get_popular_tracks()
    return jsonify(tracks)

@app.route('/api/tracks/new')
def get_new_releases_route():
    tracks = get_new_releases()
    return jsonify(tracks)

@app.route('/api/search')
def search_route():
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'tracks')
    
    if not query:
        return jsonify([])
    
    if search_type == 'tracks':
        results = search_tracks(query)
    elif search_type == 'artists':
        results = search_artists(query)
    elif search_type == 'albums':
        results = search_albums(query)
    elif search_type == 'recent':
        results = get_recent_tracks(query)
    else:
        results = []
    
    return jsonify(results)

@app.route('/api/artist/<artist>/info')
def get_artist_info_route(artist):
    info = get_artist_info(artist)
    return jsonify(info)

@app.route('/api/artist/<artist>/tracks')
def get_artist_tracks_route(artist):
    tracks = get_recent_tracks(artist)
    return jsonify(tracks)

@app.route('/api/artist/<artist>/albums')
def get_artist_albums_route(artist):
    albums = get_artist_albums(artist)
    return jsonify(albums)

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