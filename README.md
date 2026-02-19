# 3xp3dition audio

## Dependencies
- freaccmd.exe must be installed and set to path
- all python packages in import statements (obviously)

## Using
- run with --cd argument and it will attempt to find an optical drive and play from it (startup may take a little to rip track #1)
- running with no arguments looks for a hardcoded file path I was using for testing with mp3 files
- track data should display, there is probably an error from MusicBrainz that the query was denied

### author note
As anyone reading this should know, Clair Obscur Expedition 33 is one of the greatest games of all time.  
I recently bought the special edition 8 CD box with the entirety of the 8+ hour soundtrack.  
I refuse to use Windows Media Player, (because I have class) so I created this as a thumbs down to Microsoft.  
It is not the most modular, but should be fairly simple to switch to different media types.  
Currently it rips .wav files off the CD (this does not lower media quality) and then plays temp wav files that are deleted after use, 
because I am not on Linux, I could not get pycdio to work.  
I looked into ASPI/SPTI, and quickly decided I was not going to deal with that assembly-esque code.  
Did not like the jumpscare reminiscent of Computer Architecture and Assembly Course...  
(if any absolute nerds want to implement ASPI/SPTI please feel free to make a pr to which I will promptly respond with 'lgtm')  

### warning to anybody that dares to try my awful code that I designed specifically for my use: there are a lot of dependencies that must be installed and configured perfectly

### Screenshot
<img width="2488" height="1580" alt="image" src="https://github.com/user-attachments/assets/26075138-34e6-4bda-9921-26391bdbdeaf" />
