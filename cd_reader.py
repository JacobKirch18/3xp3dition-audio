import discid

try:
    disc = discid.read()
    print(f"CD detected!")
    print(f"Number of tracks: {len(disc.tracks)}")
    print(f"\nTrack list:")

    for track in disc.tracks:
        print(f" Track {track.number}: {track.length} seconds")

except discid.NoDiscError as e:
    print(f"Error reading CD: {e}")
    print("Make sure a CD is in the drive!")