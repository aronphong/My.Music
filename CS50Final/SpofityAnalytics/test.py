import pprint
import sys

import spotipy
import spotipy.util as util
import simplejson as json
from spotipy.oauth2 import SpotifyClientCredentials


client_credentials_manager = SpotifyClientCredentials(client_id='20580f81b3734588b23c40e35a071d49',
                                                      client_secret='e139583585fe42efa972991cd8ab2287')
                                                      
spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

results = spotify.search(q='Seven Lions', limit=1)
print(results)
# for i, t in enumerate(results['tracks']['items']):
#     print(' ', i, t['name'])

    # """
    #         token = util.prompt_for_user_token('1228163007',scope,client_id='20580f81b3734588b23c40e35a071d49',
    #                                                         client_secret='e139583585fe42efa972991cd8ab2287',
    #                                                         redirect_uri='http://127.0.0.1:5000/callback/')
    #     sp = spotipy.Spotify(auth=token)
    #     sp.trace = False
    #     results = sp.current_user_top_tracks(limit=10)"""