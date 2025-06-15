import deezer
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import pickle
import time

# File path for checkpoint file
CHECKPOINT_FILE = "deezer_transfer_checkpoint.pkl"

# Initialize Spotify API client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="xxxx",
    client_secret="xxxx",
    redirect_uri="http://127.0.0.1:8000/callback",
    scope="playlist-modify-private playlist-modify-public"
))

def save_checkpoint(playlist_id, processed_tracks, spotify_track_ids):
    """Saves the current progress to the checkpoint file."""
    checkpoint = {
        'playlist_id': playlist_id,
        'processed_tracks': processed_tracks,
        'spotify_track_ids': spotify_track_ids
    }
    with open(CHECKPOINT_FILE, 'wb') as f:
        pickle.dump(checkpoint, f)
    print(f"Checkpoint saved. {len(processed_tracks)} tracks processed so far.")

def load_checkpoint():
    """Loads progress from the checkpoint file."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'rb') as f:
            checkpoint = pickle.load(f)
        print(f"Checkpoint loaded: {len(checkpoint['processed_tracks'])} tracks already processed.")
        return checkpoint
    return None

def transfer_favorite_songs():
    try:
        # Check if a checkpoint exists
        checkpoint = load_checkpoint()
        playlist_id = None
        processed_tracks = set()  # Tracks already processed (set of Deezer track IDs)
        spotify_track_ids = []    # Spotify track IDs found so far
        
        if checkpoint:
            playlist_id = checkpoint['playlist_id']
            processed_tracks = checkpoint['processed_tracks']
            spotify_track_ids = checkpoint['spotify_track_ids']
            
            print(f"Resuming transfer: {len(processed_tracks)} tracks processed, {len(spotify_track_ids)} Spotify tracks found.")
        
        # Initialize Deezer client
        deezer_client = deezer.Client()
        
        # Fetch Deezer favorite songs directly with the User ID
        user_id = "xxxx"  # Enter your numeric Deezer ID here
        print(f"Connecting to Deezer account ID: {user_id}")
        user = deezer_client.get_user(user_id)
        print(f"Connected to Deezer account: {user.name}")
        
        # Fetch favorite songs
        print("Loading favorite songs from Deezer...")
        deezer_favorites = user.get_tracks()
        
        if not deezer_favorites:
            print("No favorite songs found in your Deezer account!")
            return
        
        # Create playlist if it doesn't exist yet
        if not playlist_id:
            spotify_playlist = sp.user_playlist_create(
                sp.me()['id'],
                "My Deezer Favorites",
                public=False,
                description="Favorite songs transferred from Deezer"
            )
            playlist_id = spotify_playlist['id']
            print(f"Created new Spotify playlist: {playlist_id}")
        else:
            print(f"Using existing playlist: {playlist_id}")
                  
        # Transfer songs
        total_tracks = len(deezer_favorites)
        to_process = [track for track in deezer_favorites if track.id not in processed_tracks]
        
        print(f"Transferring {len(to_process)} of {total_tracks} new favorite songs from Deezer to Spotify...")

        # A conservative limit for Spotify's rate limiting
        MAX_REQUESTS_PER_MINUTE = 80
        request_count = 0
        minute_start = time.time()
        
        for i, track in enumerate(to_process):
            request_count += 1
            
            # Rate Limiting: Pause if too many requests in a short time
            if request_count >= MAX_REQUESTS_PER_MINUTE:
                elapsed = time.time() - minute_start
                if elapsed < 60:
                    sleep_time = 60 - elapsed + 5  # 5 seconds extra buffer
                    print(f"Rate limit reached, pausing for {sleep_time:.1f} seconds...")
                    time.sleep(sleep_time)
                minute_start = time.time()
                request_count = 0
            
            # Show progress
            if (i + 1) % 10 == 0 or i == 0 or i == len(to_process) - 1:
                print(f"Processing track {i+1}/{len(to_process)}: {track.title} by {track.artist.name}")
            
            # Search for the song on Spotify
            try:
                query = f"track:{track.title} artist:{track.artist.name}"
                results = sp.search(q=query, type="track", limit=1)
                
                if results['tracks']['items']:
                    spotify_track_ids.append(results['tracks']['items'][0]['id'])
                else:
                    # Try a less specific search
                    alternative_query = f"{track.title} {track.artist.name}"
                    alt_results = sp.search(q=alternative_query, type="track", limit=1)
                    
                    if alt_results['tracks']['items']:
                        spotify_track_ids.append(alt_results['tracks']['items'][0]['id'])
                        print(f"✓ Found alternative for: {track.title} - {track.artist.name}")
                    else:
                        print(f"✗ Could not find '{track.title}' by {track.artist.name} on Spotify.")
                
                # Mark track as processed
                processed_tracks.add(track.id)
                
                # Save checkpoint periodically (every 20 songs)
                if (i + 1) % 20 == 0:
                    save_checkpoint(playlist_id, processed_tracks, spotify_track_ids)
                    
            except Exception as e:
                print(f"Error searching for '{track.title}': {e}")
                # Save checkpoint before stopping
                save_checkpoint(playlist_id, processed_tracks, spotify_track_ids)
                print("Progress saved. You can run the script again later to continue.")
                # Short pause before next attempt
                time.sleep(5)
        
        # Add all newly found tracks to the playlist
        if spotify_track_ids:
            # Add songs in chunks due to Spotify's limit
            chunk_size = 100
            
            # Get tracks already in the Spotify playlist
            existing_tracks = set()
            results = sp.playlist_items(playlist_id, fields='items.track.id')
            for item in results['items']:
                if item['track']:
                    existing_tracks.add(item['track']['id'])
            
            # Only add tracks that are not already in the playlist
            new_tracks = [track_id for track_id in spotify_track_ids if track_id not in existing_tracks]
            
            if new_tracks:
                print(f"Adding {len(new_tracks)} new songs to the playlist...")
                
                for i in range(0, len(new_tracks), chunk_size):
                    chunk = new_tracks[i:i + chunk_size]
                    sp.playlist_add_items(playlist_id, chunk)
                    print(f"Added chunk {i//chunk_size + 1} ({len(chunk)} songs)")
            else:
                print("All found songs are already in the playlist.")
        
        # Result summary
        print(f"\nTransfer complete!")
        print(f"Total processed: {len(processed_tracks)} of {total_tracks} favorite songs.")
        print(f"Found on Spotify: {len(spotify_track_ids)} songs.")
        print(f"Playlist URL: https://open.spotify.com/playlist/{playlist_id}")
        
        # Delete checkpoint file on successful completion
        if len(processed_tracks) == total_tracks:
            if os.path.exists(CHECKPOINT_FILE):
                os.remove(CHECKPOINT_FILE)
                print("Checkpoint file deleted as the transfer is fully complete.")
        
    except deezer.exceptions.DeezerErrorResponse as e:
        print(f"Deezer API Error: {e}")
        if "OAuthException" in str(e):
            print("Authentication error. Ensure your Deezer user ID is correct and your favorites are public.")
    except spotipy.exceptions.SpotifyException as e:
        print(f"Spotify API Error: {e}")
        # Save checkpoint
        if 'processed_tracks' in locals() and 'spotify_track_ids' in locals() and 'playlist_id' in locals():
            save_checkpoint(playlist_id, processed_tracks, spotify_track_ids)
            print("Progress saved. You can run the script again later.")
    except Exception as e:
        print(f"An error occurred: {e}")
        # Save checkpoint if possible
        if 'processed_tracks' in locals() and 'spotify_track_ids' in locals() and 'playlist_id' in locals():
            save_checkpoint(playlist_id, processed_tracks, spotify_track_ids)
            print("Progress saved. You can run the script again later.")

# Call the function
if __name__ == "__main__":
    transfer_favorite_songs()
