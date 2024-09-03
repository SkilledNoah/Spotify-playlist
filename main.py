"""
---------------------------------------
    * Course: 100 Days of Code - Dra. Angela Yu
    * Author: Noah Louvet
    * Day: 46
    * Subject: Spotify Playlist maker - web scraping - Environment variables - API
---------------------------------------
"""

import pprint
import requests
from bs4 import BeautifulSoup
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import os

CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
USER_ID = os.environ["USER_ID"]
REDIRECT_URI = "http://example.com"

# Get the date from the user
date = input("Which year would you like to travel to? Type the date in this format YYYY-MM-DD:\n")

# Scrape the Billboard Hot 100 chart for the given date
response = requests.get(f"https://www.billboard.com/charts/hot-100/{date}")
song_webpage = response.text

soup = BeautifulSoup(song_webpage, "html.parser")
song_names_spans = soup.select("li ul li h3")

artist_tag = soup.find_all('span', class_='c-label a-no-trucate a-font-primary-s lrv-u-font-size-14@mobile-max u-line-height-normal@mobile-max u-letter-spacing-0021 lrv-u-display-block a-truncate-ellipsis-2line u-max-width-330 u-max-width-230@tablet-only')
artist_1 = soup.find_all('span', class_='c-label a-no-trucate a-font-primary-s lrv-u-font-size-14@mobile-max u-line-height-normal@mobile-max u-letter-spacing-0021 lrv-u-display-block a-truncate-ellipsis-2line u-max-width-330 u-max-width-230@tablet-only u-font-size-20@tablet')

song_names = [song.getText().strip() for song in song_names_spans]
artist_names = [artist.getText().strip() for artist in artist_tag]
first_artist = [artist.getText().strip() for artist in artist_1]
artist_names.insert(0, first_artist[0])
print(artist_names)

artist_song_pairs = [[artist, song] for artist, song in zip(artist_names, song_names)]
print(artist_song_pairs)

# Authenticate with Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET,
                                               redirect_uri=REDIRECT_URI,
                                               scope="playlist-modify-private",
                                               show_dialog=True,
                                               cache_path=".cache",
                                               username=USER_ID))

# # ------------------------- Function to create playlist with retry logic ----------------------


def create_playlist_with_retry(sp, user_id, name, description, max_retries=5):
    for attempt in range(max_retries):
        try:
            playlist = sp.user_playlist_create(user=user_id, name=name, public=False, description=description)
            return playlist
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 502:
                print(f"Attempt {attempt + 1} failed with 502 Bad Gateway.")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print("Max retries reached. Could not create the playlist.")
                    raise
            else:
                raise


playlist_name = f"Top 100 Songs from {date}"
playlist_description = "Top 100 songs from the Billboard Hot 100 chart on your chosen date."

# Create a new playlist with retry logic
playlist = create_playlist_with_retry(sp, USER_ID, playlist_name, playlist_description)
playlist_id = playlist["id"]
user_id = sp.current_user()["id"]

# ----------------------------------------------------------------------------------------------

print(song_names)

all_song_links = []

for i in range(len(artist_song_pairs)):
    result = sp.search(q=f"track:{artist_song_pairs[i][1]} artist:{artist_song_pairs[i][0]}", type='track')
    items = result['tracks']['items']

    track_link = ""
    if items:
        track_link = items[0]['external_urls']['spotify']

    # if not empty
    if track_link:
        all_song_links.append(track_link)

pprint.pprint(all_song_links)
print(len(all_song_links))

sp.playlist_add_items(playlist_id=playlist_id, items=all_song_links)

