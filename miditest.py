# =============== Midiuppspelning v1.0 ===============
# Det fungerar nu att stoppa ljudfiler. Har inte testat på mer komplicerade filer. Det som skulle eventuellt krångla är att channel byts. Varje 'sound' identifieras med channel och not
# To Do: 1.Volymmixer
# Mikael vill ha att vid varje åttondel så skrivs tid (från start?) ut. 
# Vet inte  hur man gör funktioner i en class som för debug string.

# ========== Setup ==========
import mido
import pygame
import time 
import threading
import os

pygame.mixer.init()
pygame.mixer.set_num_channels(16)

from mido import MidiFile

global rythmVar

print(f"========== Startat script för spelning av midifiler =========")

# ========== Konvertering ==========
# Konverterar midi nummer till motsvarande notnamn
note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
notes = []
counter = 0
octave = -1

for i in range(0, 128):
    notes.append(f"{note_names[counter]}{octave}") # T.ex 'D4' eller 'F#2'

    counter = counter + 1;

    if counter == 12:
        counter = 0
        octave = octave + 1

# ========== Definera klasser ==========
class debugString: # Skulle användas för felsökning men är nog onödig nu.
    def __init__(self, text):
        self.text = text

    def add(stringAdd):
        #text = f"{text}{stringAdd} || "   
        text = stringAdd

    def print():
        print(string)

class instrument:
    def __init__(self, filePath, fileExtension):
        self.filePath = filePath
        self.fileExtension = fileExtension
        self.isActive = True
        self.isRythm = False

class song:
    def __init__(self, instruments, filePath):
        self.instruments = instruments
        self.filePath = filePath

class messageClass:
    def __init__(self, message, time, instrument, trackNumber, type):
        self.message = message
        self.time = time
        self.instrument = instrument
        self.trackNumber= trackNumber # Denna används inte i v1.0

        # För över data från message till denna modifierade klass för snyggare kod
        self.velocity = 1 # Behövde ha ett godtyckligt värde(?). Ändras sen.
        self.channel = 1
        self.type = type
        self.note = 1

def concatinateTracks(mid): # Sätt ihop alla tracks. Alla messages hamnar på en stor track kallad timeline. Denna sorteras sedan på messages position till tidpunkt noll.
    print(f"\n === Ihopsättning av tracks === ")

    timeline = []
    currentInstrument = 0
    relevantInstruments = []

    for track in mid.tracks:
        trackCounter = 0
        masterTime = 0

        for msg in track: # Hanterar olika meddelandetyper och sparar relevant information i moodifierad meddelandeklass 'msgC'          
            masterTime = masterTime + msg.time

            if msg.type == 'program_change':
                currentInstrument = msg.program 
                relevantInstruments.append(currentInstrument)

            if not msg.type == 'control_change':
                msgC = messageClass(msg, masterTime, currentInstrument, trackCounter, msg.type)
                
                if msg.type == 'note_on':
                    print(msg.channel)

                    msgC.velocity = msg.velocity
                    msgC.channel = msg.channel
                    msgC.note = msg.note
                
                timeline.append(msgC) 

        trackCounter = trackCounter + 1 # Iochmed v1.0 är detta inte nödvändigt men kanske kan komma till använding senare. 

    timeline.sort(key=lambda x: x.time) # Sortera varje objekt 'note' i listan baserat på attributen '.time'
    
    print(f"Instrument på följande program:\n{relevantInstruments}")

    return timeline

# ========== Spela midifil =========
running = True # Blir falsk vid 'ctrl+c'. Går för tillfället inte att pausa musiken.

def playMidiFile(filePath, instruments, notes):

# Setup
    global running # Behövs för att kunna avbryta spelnign med 'ctrl+c'
    currentInstrument = 0 # Kan vara onödig
    rythmVar = 0
    mid = MidiFile(filePath, clip=True)
    activeSounds = {}

# Sätt tempo
    tempo = 500000 # default tempo
    for track in mid.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                tempo = msg.tempo
    seconds_per_tick = tempo / 1_000_000 / mid.ticks_per_beat

# ========== Sätt ihop tracks ==========
    timeline = concatinateTracks(mid)

# ========== Spela filen ==========
    print(f"\n === Spelar midifil === ")

    currentTime = 0
    lastTimestamp = 0
    debug = debugString("")

    for i in timeline:
        
        # Avvakta tills meddelandet ska spelas.
        time.sleep((i.time - lastTimestamp)*seconds_per_tick)
        lastTimestamp = i.time

        if not running: # Avbryter om 'ctrl+c'
            print(f"\n========== Avslutar script =========")    
            break
        
        currentInstrument = i.instrument

        if currentInstrument in instruments:
    
            if instruments[currentInstrument].isActive:
                sound = None 
                soundFilePath = f"{instruments[currentInstrument].filePath}\\{notes[i.note]}.{instruments[currentInstrument].fileExtension}"


                if i.type == 'note_on' and i.velocity > 0:  

                    # ========== Sync Beat ==========
                    if instruments[currentInstrument].isRythm:
                        rythmVar = rythmVar + 1 

                    # print(f"Tid vid åttondel: {int(round(time.time()*1000))}") #Print tid från start eller nåt. Kan inte testa då jag inte kan musescore

                    # ========== Spela ljud =========
                    #soundFilePath = f"{instruments[currentInstrument].filePath}\\{notes[i.note]}.{instruments[currentInstrument].fileExtension}"

                    if os.path.exists(soundFilePath):           

                        soundId = f"{i.channel}_{i.note}"

                        sound = pygame.mixer.Sound(soundFilePath)
                        activeSounds[soundId] = sound  
                        sound.play()

                        print(f"{currentInstrument} spelade {notes[i.note]} på channel {i.channel}")

                    else:
                        print(f"{soundFilePath} saknas")


                elif i.type == 'note_off' or (i.type == 'note_on' and i.velocity == 0): # Bör cehcka om filepath existerar här.
                    
                    soundId = f"{i.channel}_{i.note}"

                    if os.path.exists(soundFilePath):           
                        soundToStop = activeSounds[soundId]
                        
                        if soundToStop is not None:
                            soundToStop.stop()        
                            print(f"Stopped sound on track {i.channel}")    
        else:   
            print(f"Instrument {currentInstrument} saknar tilldelat instrument")

# ========== Skapa instrument ==========
gitarr = instrument(r"C:\Users\Kasper\Programmering\MikaelsFiskespel\instrument\gitarr", "mp3")
bas = instrument(r"C:\Users\Kasper\Programmering\MikaelsFiskespel\instrument\bas", "wav")
trummor = instrument(r"C:\Users\Kasper\Programmering\MikaelsFiskespel\instrument\trummor", "mp3")
rythm = instrument(r"C:\Users\Kasper\Programmering\MikaelsFiskespel\instrument\trummor", "mp3")
rythm.isRythm = True

# Format: 'id : namn'
instruments_1 = {
    24 : gitarr,
}

instruments_2 = {
    26 : gitarr,
    #52 : bas,
    0 : trummor,
    52 : rythm
}

# ========== Skapa sång ==========
song_1 = song(instruments_1, r"C:\Users\Kasper\Programmering\MikaelsFiskespel\midilåtar\fiskespeltest.mid")
song_2 = song(instruments_2, r"C:\Users\Kasper\Programmering\MikaelsFiskespel\midilåtar\test_fleraTracks.mid")


# instrument_1.isActive = False För att inte spela instrumentet
trummor.isActive = True
gitarr.isActive = True

# ========== Threading ==========
# Detta gör att det går att spela ljudfilen samtidigt som annat kan göras. Måste göras då 'sleep' används
thread = threading.Thread(target=playMidiFile, args=(song_2.filePath, song_2.instruments, notes))
thread.start()

try: 
    while thread.is_alive():
        time.sleep(0.1)

except KeyboardInterrupt: # Avbryt programmet genom att klicka 'ctrl+c'
    running = False
    thread.join()