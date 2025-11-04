from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import requests
import lyricsgenius
import os

app = Flask(__name__)
CORS(app)

LASTFM_API_KEY = "5058e4076992e4688bb4104b252aaed7"
DISCOGS_API_KEY = "lYJnxXhQJsIwBDOmIeAATXrJogYjXikuRUYsJIhR"
GENIUS_API_KEY = "a5ox7Baa789j7qMf5JP8zBRs5qdT5WjkzOL_NRj07Qt8aEr7UZww-NKNZo-lhu-G"
LASTFM_BASE_URL = 'http://ws.audioscrobbler.com/2.0/'

# Инициализация Genius API
genius = lyricsgenius.Genius(GENIUS_API_KEY, timeout=15, retries=3)

def get_recent_tracks():
    params = {
        'method': 'chart.gettoptracks',
        'api_key': LASTFM_API_KEY,
        'format': 'json',
        'limit': 15
    }
    
    try:
        response = requests.get(LASTFM_BASE_URL, params=params, timeout=10)
        data = response.json()
        
        tracks = []
        for track in data['tracks']['track']:
            cover_url = get_track_cover(track['artist']['name'], track['name'])
            track_info = get_track_info(track['artist']['name'], track['name'])
            
            tracks.append({
                'id': f"{track['artist']['name']}-{track['name']}",
                'name': track['name'],
                'artist': track['artist']['name'],
                'image': cover_url or track['image'][-1]['#text'] if track['image'][-1]['#text'] else 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=300',
                'duration': track_info.get('duration', '3:45'),
                'url': track_info.get('url', '#')
            })
        return tracks
    except Exception as e:
        print(f"Error fetching tracks: {e}")
        return []

def search_tracks(query):
    params = {
        'method': 'track.search',
        'api_key': LASTFM_API_KEY,
        'track': query,
        'format': 'json',
        'limit': 20
    }
    
    try:
        response = requests.get(LASTFM_BASE_URL, params=params, timeout=10)
        data = response.json()
        
        tracks = []
        if 'results' in data and 'trackmatches' in data['results']:
            for track in data['results']['trackmatches']['track']:
                cover_url = get_track_cover(track['artist'], track['name'])
                # Получаем информацию о треке для правильной длительности
                track_info = get_track_info(track['artist'], track['name'])
                
                tracks.append({
                    'id': f"{track['artist']}-{track['name']}",
                    'name': track['name'],
                    'artist': track['artist'],
                    'image': cover_url or 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=300',
                    'duration': track_info.get('duration', '3:45'),  # Используем правильную длительность
                    'url': track.get('url', '#')
                })
        return tracks
    except Exception as e:
        print(f"Error searching tracks: {e}")
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

@app.route('/api/tracks')
def get_tracks():
    tracks = get_recent_tracks()
    return jsonify(tracks)

@app.route('/api/search')
def search_tracks_route():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    tracks = search_tracks(query)
    return jsonify(tracks)

@app.route('/api/lyrics')
def get_lyrics_route():
    artist = request.args.get('artist', '')
    title = request.args.get('title', '')
    
    if not artist or not title:
        return jsonify({'lyrics': None})
    
    lyrics = get_lyrics(artist, title)
    return jsonify({'lyrics': lyrics})

# Основной маршрут для отдачи HTML - БЕЗ РЕДИРЕКТА
@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'test.html')

# Маршрут для отдачи статических файлов
@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

if __name__ == '__main__':
    app.run(debug=True, port=5500)