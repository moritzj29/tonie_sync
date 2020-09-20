import logging
import os
import json
import threading
from time import sleep
from tonie_api import TonieAPI
from spotdl.command_line.core import Spotdl
from spotdl.helpers import SpotifyHelpers

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class TonieSpotifySync():
    """Sync spotify content to toniecloud.

    :param directory: directory of config file and media storage. 
                      Defaults to current working directory.
    :type dictionary: str, optional
    :param config_from_file: load config from file. Defaults to True.
    :type config_from_file: bool, optional
    :param username: toniecloud username. Defaults to None.
    :type username: str, optional
    :param password: toniecloud password. Defaults to None.
    :type password: str, optional
    :param client_id: Spotify clientID. Defaults to None.
    :type client_id: str, optional
    :param client_secret: Spotify client secret. Defaults to None.
    :type client_secret: str, optional
    """

    def __init__(self, directory=os.getcwd(), config_from_file=True,
                 username=None, password=None,
                 client_id=None, client_secret=None):
        self.directory = directory
        sp_args = {
            # 'output_file': '{track-id}.{output-ext}',
            # is set in SyncClass anyway with path
            'overwrite': 'force'
            }
        if config_from_file:
            if self._load_config():
                # config values overwrite default args
                sp_args = {**sp_args, **self.config['spotify']}
                # check if both keys exist
                if set(['username', 'password']).issubset(
                        set(self.config['tonies'].keys())):
                    tonie_user = self.config['tonies']['username']
                    tonie_password = self.config['tonies']['password']
        # arguments from init call overwrite config if given
        if username is not None:
            tonie_user = username
        if password is not None:
            tonie_password = password
        if client_id is not None:
            sp_args['client_id'] = client_id
        if client_secret is not None:
            sp_args['client_secret'] = client_secret

        self.sp_handler = Spotdl(sp_args)
        self.sp_helpers = SpotifyHelpers()

        self.tonieAPI = TonieAPI(tonie_user, tonie_password)
        self.tonieAPI.update()

        self.sync_jobs = []
        self._sync_running = False
        self._sync_service_running = False

        if config_from_file:
            self.set_syncs()

    def _load_config(self, name='config.json'):
        """Load configuration file from disk. Configuration file
        has to be in JSON format. Entries `spotify` and `tonies`
        are mandatory.

        Example:

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

        :param name: filename of config file, defaults to 'config.json'
        :type name: str, optional
        :return: if config has been set or not
        :rtype: bool
        """
        conf_path = os.path.join(self.directory, name)
        log.info(f'Loading config from {conf_path} ...')
        try:
            self.config = json.load(open(conf_path))
        except FileNotFoundError:
            log.error(f'Config file {conf_path} not found!')
            return False
        if not set(['spotify', 'tonies']).issubset(set(self.config.keys())):
            log.error('Config file does not meet requirements!')
            self.config = None
            return False
        else:
            return True

    def set_syncs(self):
        """Set up sync jobs from configuration.
        """
        if 'PlaylistSync' in self.config.keys():
            # first level: household ID as key
            for hh, jobs in self.config['PlaylistSync'].items():
                # second level: playlist URI as key, tonie ID as value
                for pl, ct in jobs.items():
                    self.sync_jobs.append(PlaylistSync(
                        self, pl,
                        self.tonieAPI.households[hh].creativetonies[ct]
                    ))

    def run_syncs(self):
        """Run all sync jobs.
        """
        self._sync_running = True
        log.info('Started running all sync jobs...')
        for job in self.sync_jobs:
            job.update()
        log.info('Finished running all sync jobs...')
        self._sync_running = False

    def start_sync_service(self, sleeptime=5, background=True):
        """Run sync jobs regularly with a defined break
        time between.

        :param sleeptime: time between sync runs in min, defaults to 5
        :type sleeptime: int, optional
        :param background: run sync in separate thread,
                           defaults to True
        :type background: bool, optional
        """
        # check if service is already running
        if self._sync_service_running:
            log.error('Sync service is already running')
            return
        # set flag that service is running
        self._sync_service_running = True
        log.info(f'Starting sync service with {sleep} minute breaks.')

        # define worker
        def sync_worker(self=self, sleeptime=sleeptime):
            self._sync_continuous = True
            while self._sync_continuous:
                self.run_syncs()
                # check loop condition every 10s
                for _ in range(0, int(sleeptime*60/10)):
                    sleep(10)
                    if not self._sync_continuous:
                        break
        if background:
            self._sync_thread = threading.Thread(target=sync_worker)
            # start service
            self._sync_thread.start()
        else:
            print('Started sync service, interrupt with Ctrl+C.')
            sync_worker()

    def stop_sync_service(self):
        """Stop sync service, if ran in separate thread.
        """
        # set flag to interrupt loop
        self._sync_continuous = False
        # join worker into main thread
        self._sync_thread.join()
        self._sync_service_running = False
        log.info('Sync service has been stopped')


class PlaylistSync():
    """Sync Spotify playlist to creative tonie.

    :param parent: instance of main sync class
    :type parent: class:TonieSpotifySync
    :param playlistURI: URI of the Spotify playlist
    :type playlistURI: str
    :param tonie: Creative Tonie instance
    :type tonie: class:TonieAPI._CreativeTonie
    """

    def __init__(self, parent, playlistURI, tonie):
        self.URI = playlistURI
        self.tonie = tonie
        self.sp_handler = parent.sp_handler
        self.sp_helpers = parent.sp_helpers
        log.info(
            f'Setting up PlaylistSync for playlist {self.URI}'
            f' with creative tonie {self.tonie.id} ({self.tonie.name}).'
        )
        self.directory = os.path.join(parent.directory, self.URI)
        if not os.path.exists(self.directory):
            log.info(f'Directory {self.directory} does not exist,'
                     'creating it.')
            os.mkdir(self.directory)
        self.filelinks_path = os.path.join(self.directory, 'filelinks.json')
        try:
            self.filelinks = json.load(open(self.filelinks_path))
        except FileNotFoundError:
            self.filelinks = {}
            log.info('No filelinks file found, assuming empty tonie.')
        else:
            log.info(f'Loaded {len(self.filelinks)} filelinks from file.')

    def update(self):
        """Update this sync job:

            - update playlist
            - update files to match playlist
            - update Tonie contents
        """
        log.info(f'Started updating sync job'
                 f' playlist {self.URI} to'
                 f' tonie {self.tonie.name} ...')
        # update playlist and write tracks in self.tracks
        self.update_playlist()
        # check if all tracks are downloaded, download new tracks
        self.update_files()
        # upload files to tonie, sort according to playlist
        self.update_tonie()
        log.info(f'Finished updating sync job'
                 f' playlist {self.URI} to'
                 f' tonie {self.tonie.name}.')

    @property
    def tracks(self):
        """Dictionary with metadata information for
        each track in the playlist. Access via track URI.

        :return: metadata of all tracks
        :rtype: dict
        """
        return self._tracks

    @tracks.setter
    def tracks(self, val):
        self._tracks = val

    def update_playlist(self):
        """Read tracks from the Spotify playlist.
        """
        r = self.sp_helpers.fetch_playlist(self.URI)
        self.PLname = r['name']
        # extract URIs
        self.tracks = {
            (track['track']['uri']).split(':')[-1]: track['track']
            for track in r['tracks']['items']
            }
        log.info(f'Fetched playlist {self.PLname} containing '
                 f'{len(self.tracks)} tracks.')
        log.info(f'tracks: {self.tracks.keys()}')

    def update_files(self):
        """Check if files in the job directory match
        the contents of the playlist. Delete or download
        old/new files.
        """
        log.info('Updating files ...')
        (_, _, filenames) = next(os.walk(self.directory))
        filenames = [f for f in filenames if f.endswith('.mp3')]
        newtracks = list(self.tracks.keys())
        for f in filenames:
            name, extension = os.path.splitext(f)
            if f.endswith('.json'):
                continue
            elif name in newtracks:
                # track already downloaded
                newtracks.remove(name)
                # newtracks.remove(name)
            elif name not in newtracks:
                # track downloaded but no longer needed
                log.info(f'Deleting file {name} since no longer in playlist.')
                os.remove(os.path.join(self.directory, name + extension))
        log.info(f'Checked files for {self.PLname}: {len(newtracks)}'
                 ' new tracks to download.')
        for uri in newtracks:
            data = self.tracks[uri]
            self.sp_handler.arguments["output_file"] = os.path.join(
                self.directory, '{track-id}.{output-ext}')
            self.sp_handler.download_track(f'spotify:track:{uri}')
            log.info(f'Downloaded track {data["name"]} ({uri}).')
        log.info('Finished updating files ...')

    def update_tonie(self):
        """Update Tonie contents to match folder content.
        Order tracks according to Spotify playlist.
        Write file with links between Spotify track URI and
        Tonie's track ID to `filelinks.json`.
        """
        log.info('Updating tonie ...')
        # Link URI <-> contentID
        # upload if no ID for URI

        # list of correctly ordered contentids
        tonie_playlist = []
        update_filelinks_file = False

        for uri, data in self.tracks.items():
            path = os.path.join(self.directory, f'{uri}.mp3')
            if (uri not in self.filelinks.keys()) and os.path.exists(path):
                contentid = self.tonie.upload(
                    path,
                    data['name']  # title
                )
                # set link between playlist URI and content ID
                self.filelinks[uri] = contentid
                update_filelinks_file = True
            else:
                # content ID of file is known
                pass
            tonie_playlist.append(self.filelinks[uri])

        # write updated filelinks to file only if there have been changes
        if update_filelinks_file:
            json.dump(self.filelinks, open(self.filelinks_path, 'w'))

        # Sort chapters according to playlist

        # Check of list of contentids match the IDs in tonie cloud
        # if not, sorting would delete entire content on tonie
        contentids = [ch['id'] for ch in self.tonie.chapters]
        if not set(tonie_playlist).issubset(set(contentids)):
            log.warning('Content IDs of tonie cloud and local'
                        ' files do not match!')
            log.warning('Deleting filelinks.json to trigger reupload'
                        ' of content to tonie cloud.')
            os.remove(self.filelinks)
        else:
            # sort chapters according to playlist
            self.tonie.sort_chapters('id', sortlist=tonie_playlist)
