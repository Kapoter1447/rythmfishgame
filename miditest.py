# ========== Setup ==========
import mido
import pygame
import time 
import threading
import os

pygame.mixer.init()
pygame.mixer.set_num_channels(16)

from mido import MidiFile

# ========== Konvertering ==========
# Konverterar midi nummer till motsvarande notnamn
note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
notes = []
counter = 0
octave = -1

for i in range(0, 128):
    notes.append(f"{note_names[counter]}{octave}")

    counter = counter + 1;

    if counter == 12:
        counter = 0
        octave = octave + 1

# ========== Definera klasser ==========
class instrument:
    def __init__(self, idNr, filePath, fileExtension):
        self.filePath = filePath
        self.idNr = idNr
        self.fileExtension = fileExtension
        self.isActive = True

class song:
    def __init__(self, instruments, filePath):
        self.instruments = instruments
        self.filePath = filePath

running = True

def playMidiFile(filePath, instruments, notes):

# Setup
    global running # Behövs för att kunna avbryta spelnign med 'ctrl+c'

    mid = MidiFile(filePath, clip=True) 
    currentInstrument = 0 # Skapar current instrument med godtycklig siffra. 

    activeSounds = []

# Sätt tempo
    tempo = 500000 # default tempo
    for track in mid.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                tempo = msg.tempo
    seconds_per_tick = tempo / 1_000_000 / mid.ticks_per_beat

# Sätt ihop alla tracks. Alla messeges hamnar på en stor track kallad timeline. Denna sorteras sedan på messages position till noll.
    timeline = []

    class messageClass:
        def __init__(self, message, time, instrument):
            self.message = message
            self.time = time
            self.instrument = instrument

    for track in mid.tracks:

        masterTime = 0

        for msg in track:
            masterTime = masterTime + msg.time

            if msg.type == 'program_change':
                currentInstrument = msg.program                

            if not msg.type == 'control_change':
                msgC = messageClass(msg, masterTime, currentInstrument)            
                timeline.append(msgC) 

    timeline.sort(key=lambda x: x.time) # Sortera varje objekt 'note' i listan baserat på attributen '.time'

# Spela filen

    currentTime = 0
    lastTimestamp = 0

    for i in timeline:

        msg = i.message

        time.sleep((i.time - lastTimestamp)*seconds_per_tick)
        lastTimestamp = i.time

        if not running:
            break
        
        currentInstrument = i.instrument

        if currentInstrument in instruments and instruments[currentInstrument].isActive:

            sound = None 

            if msg.type == 'note_on' and msg.velocity > 0:  

                soundFilePath = f"{instruments[currentInstrument].filePath}\\{notes[msg.note]}.{instruments[currentInstrument].fileExtension}"


                if os.path.exists(soundFilePath):

                    sound = pygame.mixer.Sound(soundFilePath)
                    activeSounds.append(sound)
                    sound.play()
                    print(sound)
                    print(f"{currentInstrument} spelade {notes[msg.note]}")

                else:

                    print(f"{soundFilePath} saknas")

            if msg.type == 'note_on' :   
                print(f"Note on with vel {msg.velocity}")
                if msg.velocity == 0:
                    print("Vel 0") 

            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                if sound is not None:
                    sound.stop()        
                    print("Sound stopped")    


# ========== Skapa instrument ==========
gitarr = instrument(24, r"C:\Users\Kasper\Programmering\MikaelsFiskespel\instrument\gitarr", "mp3")
bas = instrument(34, r"C:\Users\Kasper\Programmering\MikaelsFiskespel\instrument\bas", "wav")
trummor = instrument(0, r"C:\Users\Kasper\Programmering\MikaelsFiskespel\instrument\trummor", "mp3")

instruments = {
    gitarr.idNr : gitarr,
    bas.idNr : bas,
    trummor.idNr : trummor,
}

# ========== Skapa sång ==========
#song_1 = song(instruments, r"C:\Users\Kasper\Programmering\MikaelsFiskespel\Namnlös1.mid") # Gittar är 26
song_1 = song(instruments, r"C:\Users\Kasper\Programmering\MikaelsFiskespel\fiskespeltest.mid")


# instrument_1.isActive = False För att inte spela instrumentet
trummor.isActive = True
gitarr.isActive = True

# ========== Threading ==========
# Detta gör att det går att spela ljudfilen samtidigt som annat kan göras. Måste göras då 'sleep' används
thread = threading.Thread(target=playMidiFile, args=(song_1.filePath, song_1.instruments, notes))
thread.start()

try: 
    while thread.is_alive():
        time.sleep(0.1)

except KeyboardInterrupt: # Avbryt programmet genom att klicka 'ctrl+c'
    running = False
    thread.join()