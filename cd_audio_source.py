import discid
import musicbrainzngs

musicbrainzngs.set_useragent("CD Audio Source", "1.0", "https://github.com/JacobKirch18/audio-player")

class CDAudioSource:
    def __init__(self):
        self.disc = None
        self.tracks = []
        self.disc_info = None

    def detect_cd(self):
        try:
            self.disc = discid.read()
            print(f"Detected CD: {self.disc}")
            return True
        except discid.DiscError as e:
            print(f"CD detection error: {e}")
            return False

    def get_track_info(self):
        if not self.disc:
            print("No CD detected")
            return []
        try:
            result = musicbrainzngs.get_releases_by_discid(
                self.disc.id,
                includes=['artists', 'recordings']
            )

            if result.get('disc'):
                release = result['disc']['release-list'][0]
                medium = release['medium-list'][0]
                track_list = medium['track-list']

                self.disc_info = {
                    'artist': release['artist-credit-phrase'],
                    'album': release['title'],
                }

                self.tracks = []
                for i, track_data in enumerate(track_list):
                    track = {
                        'number': i + 1,
                        'title': track_data['recording']['title'],
                        'length': self.disc.tracks[i].length,
                        'offset': self.disc.tracks[i].offset
                    }
                    self.tracks.append(track)

                return self.tracks
            
            else:
                print("CD not found in MusicBrainz database")
                return self._get_generic_tracks()
        
        except Exception as e:
            print(f"Error querying MusicBrainz: {e}")
            return self._get_generic_tracks()
    
    def _get_generic_tracks(self):
        self.tracks = []
        for i, track in enumerate(self.disc.tracks):
            self.tracks.append({
                'number': track.number,
                'title': f"Track {track.number}",
                'length': track.length,
                'offset': track.offset
            })
        return self.tracks
    
    def get_disc_info_string(self):
        if self.disc_info:
            return f"{self.disc_info['artist']} - {self.disc_info['album']}"
        else:
            return "Unknown CD"

if __name__ == "__main__":
    cd = CDAudioSource()
    if cd.detect_cd():
        tracks = cd.get_track_info()
        print(f"\n{cd.get_disc_info_string()}\n")
        for track in tracks:
            mins = track['length'] // 60
            secs = track['length'] % 60
            print(f"{track['number']}. {track['title']} ({mins}:{secs:02d})")