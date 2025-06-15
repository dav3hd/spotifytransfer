import deezer
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Initialize Deezer API client
deezer_client = deezer.Client()

# Initialize Spotify API client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="xxxx",
    client_secret="xxxx",
    redirect_uri="http://127.0.0.1:8000/callback",
    scope="playlist-modify-private playlist-modify-public"
))

def transfer_playlist(deezer_playlist_id):
    # Get Deezer playlist
    deezer_playlist = deezer_client.get_playlist(deezer_playlist_id)
    
    # Create a new Spotify playlist
    spotify_playlist = sp.user_playlist_create(
        sp.me()['id'],
        deezer_playlist.title,
        public=False,
        description=f"Transferred from Deezer: {deezer_playlist.description}"
    )
    
    # Transfer songs
    spotify_track_ids = []
    for track in deezer_playlist.tracks:
        # Search for the song on Spotify
        results = sp.search(q=f"track:{track.title} artist:{track.artist.name}", type="track", limit=1)
        if results['tracks']['items']:
            spotify_track_ids.append(results['tracks']['items'][0]['id'])
    
    # Add songs to the Spotify playlist
    chunk_size = 100
    for i in range(0, len(spotify_track_ids), chunk_size):
        chunk = spotify_track_ids[i:i + chunk_size]
        sp.playlist_add_items(spotify_playlist['id'], chunk)
        print(f"Added chunk {i//chunk_size + 1} ({len(chunk)} songs)")
    
    print(f"Playlist '{deezer_playlist.title}' successfully transferred!")

# Example call
transfer_playlist('xxxx')
