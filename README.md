# Music Transfer Scripts

Transfer your music between different streaming platforms with these Python scripts.

## 🎵 Deezer → Spotify

### Prerequisites
- Python 3.7+
- Deezer account with public favorites/playlists
- Spotify account with Developer app

### Installation
```bash
pip install deezer-python spotipy
```

### Spotify API Setup
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Note down `Client ID` and `Client Secret`
4. Add `http://127.0.0.1:8000/callback` as Redirect URI

### Find Deezer User ID
1. Go to your Deezer profile
2. Copy the numbers from the URL (e.g., `deezer.com/profile/123456789`)

### Usage

#### Transfer All Deezer Favorites
```bash
python all_deezer_music_2_spotify.py
```
- Enter your Spotify credentials and Deezer User ID in the script
- Supports checkpoints for interruption recovery
- Automatic rate limiting handling

#### Transfer Single Deezer Playlist
```bash
python single_deezer_playlist_2_spotify.py
```
- Enter your Spotify credentials in the script
- Find playlist ID in Deezer URL (e.g., `deezer.com/playlist/1234567890`)
- Update the playlist ID in the script

## 🎵 Spotify → YouTube Music

### Prerequisites
- Python 3.7+
- Spotify account with Developer app
- YouTube Music account

### Installation
```bash
pip install spotipy ytmusicapi
```

### YouTube Music Authentication Setup
1. Follow the instructions on [ytmusicapi Documentation](https://ytmusicapi.readthedocs.io/en/stable/setup/browser.html)
2. Fill your Request Header into the example file headers_auth.json

### YouTube Music Authentication Setup (Alternative)
1. Delete the example file headers_auth.json
2. Install the browser extension [ytmusicapi Cookie Helper](https://github.com/sigma67/ytmusicapi#authentication)
3. Run:
   ```bash
   ytmusicapi browser
   ```
4. Follow the instructions to create `headers_auth.json`
   
### Spotify API Setup
Use the same credentials as for Deezer→Spotify (see above)

### Usage
```bash
python spotify_2_ytmusic.py
```
- Enter your Spotify credentials in the script
- Ensure `headers_auth.json` is in the same directory
- Enter your Spotify username when prompted
- It may redirect you to an empty website --> Copy the URL and paste it into the terminal if asked
- Transfers all your Spotify playlists

## ⚠️ Important Notes

- **Rate Limits**: Scripts implement automatic delays
- **Duplicates**: Already existing songs are automatically skipped
- **Missing Songs**: Will be displayed in the console
- **Credentials**: Never upload your real API keys to public repositories

## 🔧 Troubleshooting

### Spotify Authentication Fails
- Check Client ID, Client Secret, and Redirect URI
- Ensure Redirect URI matches exactly

### YouTube Music Authentication Fails
- Delete `headers_auth.json` and recreate it
- Make sure you're logged into YouTube Music

### Deezer Favorites Not Found
- Check your User ID
- Ensure your favorites are set to public

## 📝 License

MIT License - Use these scripts freely for personal purposes.
