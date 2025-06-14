import spotipy
from spotipy.oauth2 import SpotifyOAuth
from ytmusicapi import YTMusic
import os

# --- Configuration ---
# Enter your Spotify credentials here
SPOTIPY_CLIENT_ID = 'xyz'
SPOTIPY_CLIENT_SECRET = 'xyz'
SPOTIPY_REDIRECT_URI = 'https://127.0.0.1' # Must be the same as in your Spotify API settings!

# Ensure 'headers_auth.json' is in the same directory
YT_AUTH_FILE = 'headers_auth.json'

# --- Spotify Authentication ---
def get_spotify_playlists(username):
    try:
        scope = 'playlist-read-private'
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=SPOTIPY_CLIENT_ID,
            client_secret=SPOTIPY_CLIENT_SECRET,
            redirect_uri=SPOTIPY_REDIRECT_URI,
            scope=scope,
            username=username))
        
        results = sp.current_user_playlists()
        return results['items']
    except Exception as e:
        print(f"Error during Spotify authentication or fetching playlists: {e}")
        return None

# --- Get All Spotify Playlist Tracks ---
def get_playlist_tracks(playlist_id):
    try:
        scope = 'playlist-read-private'
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=SPOTIPY_CLIENT_ID,
            client_secret=SPOTIPY_CLIENT_SECRET,
            redirect_uri=SPOTIPY_REDIRECT_URI,
            scope=scope))
            
        results = sp.playlist_tracks(playlist_id)
        tracks = []
        
        while results:
            for item in results['items']:
                track = item['track']
                if track:
                    artist_name = track['artists'][0]['name'] if track['artists'] else 'Unknown Artist'
                    track_name = track['name']
                    tracks.append(f"{artist_name} - {track_name}")
            
            if results['next']:
                results = sp.next(results)
            else:
                results = None

        return tracks
        
    except Exception as e:
        print(f"Error fetching playlist tracks: {e}")
        return []

# --- YouTube Music Functions ---

def get_or_create_yt_playlist(ytmusic, title, description):
    """Checks for an existing playlist by title, otherwise creates a new one."""
    playlists = ytmusic.get_library_playlists(limit=500) # Increase limit if you have more playlists
    for playlist in playlists:
        if playlist['title'] == title:
            print(f"Found existing YouTube Music playlist '{title}'.")
            return playlist['playlistId']
            
    print(f"No existing playlist found. Creating new YouTube Music playlist '{title}'.")
    return ytmusic.create_playlist(title, description)


# --- Main Script ---
if __name__ == '__main__':
    if not os.path.exists(YT_AUTH_FILE):
        print(f"Error: Authentication file '{YT_AUTH_FILE}' not found.")
        print("Please follow the ytmusicapi setup guide to create it.")
    else:
        spotify_username = input("Enter your Spotify username: ")
        
        spotify_playlists = get_spotify_playlists(spotify_username)
        
        if spotify_playlists:
            print(f"\nFound {len(spotify_playlists)} Spotify playlists.")
            
            ytmusic = YTMusic(YT_AUTH_FILE)
            
            for i, sp_playlist in enumerate(spotify_playlists):
                sp_playlist_name = sp_playlist['name']
                print(f"\n--- Processing playlist {i+1}/{len(spotify_playlists)}: {sp_playlist_name} ---")
                
                # Step 1: Get or create YT playlist
                yt_playlist_id = get_or_create_yt_playlist(ytmusic, sp_playlist_name, sp_playlist.get('description', ''))
                
                if not yt_playlist_id:
                    print(f"Could not create or find YouTube Music playlist for '{sp_playlist_name}'. Skipping.")
                    continue

                # Step 2: Get existing tracks from the YT playlist
                try:
                    yt_playlist_details = ytmusic.get_playlist(yt_playlist_id, limit=None) # limit=None gets all tracks
                    # Store existing video IDs in a set for fast lookup
                    existing_yt_video_ids = {track['videoId'] for track in yt_playlist_details.get('tracks', []) if track.get('videoId')}
                    print(f"{len(existing_yt_video_ids)} songs already exist in the YouTube playlist.")
                except Exception as e:
                    print(f"Could not retrieve YouTube playlist details: {e}. Skipping add.")
                    continue
                    
                # Step 3: Get all tracks from the Spotify playlist
                spotify_tracks = get_playlist_tracks(sp_playlist['id'])
                print(f"Fetched {len(spotify_tracks)} songs from Spotify.")
                
                # Step 4: Find new tracks to add
                tracks_to_add = []
                for j, track_query in enumerate(spotify_tracks):
                    try:
                        search_results = ytmusic.search(track_query, filter="songs", limit=1)
                        if search_results:
                            video_id = search_results[0]['videoId']
                            # Check if the song already exists in the YT playlist
                            if video_id not in existing_yt_video_ids:
                                tracks_to_add.append(video_id)
                                # Add new videoId to the set to prevent duplicates in this run
                                existing_yt_video_ids.add(video_id)
                        else:
                            print(f"  -> Could not find '{track_query}' on YouTube Music.")
                    except Exception as e:
                        print(f"Error searching for '{track_query}': {e}")
                
                # Step 5: Add all new songs in a single, efficient request
                if tracks_to_add:
                    print(f"\nAdding {len(tracks_to_add)} new song(s) to playlist '{sp_playlist_name}'...")
                    try:
                        ytmusic.add_playlist_items(yt_playlist_id, tracks_to_add)
                        print("Successfully added!")
                    except Exception as e:
                        print(f"Error adding the collected songs: {e}")
                else:
                    print("\nAll songs are already up to date. Nothing to do.")

            print("\nTransfer complete! 🎉")
