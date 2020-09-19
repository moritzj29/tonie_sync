**********
Disclaimer
**********

This project is not associated with Boxine, the manufacturer of the Toniebox.
Nor with Spotify.
This is a private proof-of-principle project dor educational purposes. Use at your own risk.
Downloading copyright songs may be illegal in your country. 
You at least need a Spotify Premium account. Please support artists by buying their music.

************
Introduction
************
This project connects ritieks `Spotify-Downloader <https://github.com/ritiek/spotify-downloader>`_
with the `TonieAPI <https://github.com/moritzj29/tonie_api>`_
to provide automatic syncing of spotify playlists to creative tonies.

The easiest way to start is using the Dockerfile to start up a Docker Container.
The sync runs at regular intervals, checking for updates of the spotify playlists.

*******
Example
*******

.. code-block:: python

    import logging
    from TonieAPI.TonieAPI import TonieAPI
    from TonieAPI.TonieSpotifySync import TonieSpotifySync
    from TonieAPI.TonieSpotifySync import PlaylistSync

    # set up detailed logging
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    # create class instance without using a config file
    tss=TonieSpotifySync(
        config_from_file=False,
        username='user@mail.com', password='secret',
        client_id='id', client_secret='secret'
        )

    # manually set up sync job
    tss.sync_jobs=[PlaylistSync(
        tss,'yourplaylistURI',
        tss.tonieAPI.households['yourhouseholdID'].creativetonies['yourtonieID']
        )]

    # run sync job
    tss.run_syncs()


Example `config.json` configuration file. Please update with your credentials.
Attention: Your credentials will be stored in plain text!

To set up the automatic sync, you must specify associations of playlist URIs and tonie IDs.
The household and tonie IDs of your account are written to the logfile upon first start of the docker container.
The playlist URIs can be extracted from the link to the spotify playlist (share playlist).
The last part of the URL is the URI.

.. code-block:: json

    {
        "spotify": {
            "client_id": "id123",
            "client_secret": "secret123"
        },
        "tonies": {
            "username": "test",
            "password": "secret"
        },
        "PlaylistSync": {
            "household1ID": {
                "playlist1URI": "tonie1ID",
                "playlist2URI": "tonie2ID"
            },
            "household2ID": {
                "playlist3URI": "tonie3ID",
                "playlist4URI": "tonie4ID"
            }
        }
    }


*********
Resources
*********
Other projects which are similar or resources helpful for development:

- basically the same in Java, and inspiration for this project `Spotify Toniebox Sync by Maximilan Voß <https://github.com/maximilianvoss/spotify-toniebox-sync>`_
- `Spotify-Downloader by ritiek <https://github.com/ritiek/spotify-downloader>`_