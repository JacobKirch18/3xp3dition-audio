#!/usr/bin/env python3

import discid
import musicbrainzngs
import sys
import subprocess
import tempfile
import os
import struct
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

musicbrainzngs.set_useragent("CD Audio Source", "1.0", "https://github.com/JacobKirch18/3xp3dition-audio")

class CDAudioSource:
    def __init__(self):
        self.disc = None
        self.tracks = []
        self.disc_info = None
        self.temp_dir = tempfile.gettempdir()
        self.ripped_files = []
        self.current_process = None

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
            time.sleep(1)
            result = musicbrainzngs.get_releases_by_discid(
                self.disc.id,
                includes=['artists', 'recordings']
            )

            if result.get('disc'):
                release = result['disc']['release-list'][0]

                disc_info = result['disc']
                medium_index = 0

                if 'offset-list'in disc_info:
                    for i, medium in enumerate(release['medium-list']):
                        if 'disc-list' in medium:
                            for disc in medium['disc-list']:
                                if disc['id'] == self.disc.id:
                                    medium_index = i
                                    break

                if medium_index < len(release['medium-list']):
                    medium = release['medium-list'][medium_index]
                else:
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
                        'length': self.disc.tracks[i].length // 75,
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
                'length': track.length // 75,
                'offset': track.offset
            })
        return self.tracks
    
    def get_disc_info_string(self):
        if self.disc_info:
            return f"{self.disc_info['artist']} - {self.disc_info['album']}"
        else:
            return "Unknown CD"    

    def _find_cd_drive(self):
        import string
        from ctypes import windll
        
        bitmask = windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drive = f"{letter}"
                if windll.kernel32.GetDriveTypeW(f"{drive}:\\") == 5:
                    return letter
            bitmask >>= 1
        return None

    def rip_track_to_wav(self, track_number):
        if not self.tracks:
            print("No tracks loaded")
            return None
        
        output_path = os.path.join(self.temp_dir, f"track_{track_number:02d}.wav")

        if os.path.exists(output_path):
            print(f"Track {track_number} already ripped")
            if output_path not in self.ripped_files:
                self.ripped_files.append(output_path)
            return output_path
        
        if output_path not in self.ripped_files:
            self.ripped_files.append(output_path)

        try:
            cd_drive = self._find_cd_drive()
            if not cd_drive:
                print("Could not find CD drive")
                return None
            
            print(f"Ripping track {track_number}...")
            
            cmd = [
                "freaccmd.exe",
                f"--encoder=sndfile-wave",
                f"--drive={cd_drive}:",
                f"--track={track_number}",
                "-o", output_path
            ]
            
            self.current_process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                stdout, stderr = self.current_process.communicate(timeout=120)
                self.current_process = None
            except subprocess.TimeoutExpired:
                print(f"Ripping track {track_number} timed out.", flush=True)
                if self.current_process:
                    self.current_process.kill()
                    self.current_process = None
                return 
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"Successfully ripped track {track_number}")
                return output_path
            else:
                print(f"Rip failed.")
                return None
                
        except subprocess.TimeoutExpired:
            print(f"Ripping track {track_number} timed out.")
            return None
        
        except FileNotFoundError:
            print("freaccmd.exe not found. Make sure it's in your PATH or project folder.")
            return None

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        return None

    def stop_current_rip(self):
        if self.current_process:
            print("Killing active rip process...", flush=True)
            try:
                self.current_process.kill()
                self.current_process.wait(timeout=2)
            except Exception as e:
                print(f"Error killing process: {e}", flush=True)
            finally:
                self.current_process = None

    def cleanup_temp_files(self):
        print(f"Starting cleanup of {len(self.ripped_files)} files...")
        
        deleted_count = 0
        failed_count = 0
        
        for file_path in self.ripped_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
                    deleted_count += 1
                else:
                    print(f"File not found: {file_path}")
            except PermissionError as e:
                print(f"Permission denied (file may be in use): {file_path}")
                failed_count += 1
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")
                failed_count += 1
        
        print(f"Cleanup complete: {deleted_count} deleted, {failed_count} failed")
        self.ripped_files.clear()

if __name__ == "__main__":
    cd = CDAudioSource()
    if cd.detect_cd():
        tracks = cd.get_track_info()

        wav_path = cd.rip_track_to_wav(1)
        print(f"wav file: {wav_path}")

        # print(f"\n{cd.get_disc_info_string()}\n")
        # for track in tracks:
        #     mins = track['length'] // 60
        #     secs = track['length'] % 60
        #     print(f"{track['number']}. {track['title']} ({mins}:{secs:02d})")