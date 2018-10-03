# coding=utf-8
# Freies Radio Goeppingen e.V. Title-Updater
# Alexander Kurz 03.11.2015
# Version 0.4
#
# Dieses Script holt die jeweils aktuellen Now-Playing-Informationen
# aus der entsprechenden Quelle, abhängig vom derzeit sendenden Studio,
# und stellt diese Infos in einem Textfile für den RDS-Coder bereit.
# Desweiteren Sendet es die aktuellen Titelinfos auch an die fips-Webstreams. (derzeit noch nicht)

# ---
# 06.01.2015 - Anpassungen URLs für Webupdate
# 09.06.2017 - Ausgabe Log auch in Konsole.
# 21.08.2017 - 0.1 Sekunden Sleep in Main-Loop eingefügt
# 21.08.2017 - Schreiben von onair-studio.txt und now-onair.txt bei IO-Error abgefangen.
# 21.08.2017 - Filtern von Umlauten und ß funktioniert jetzt.
# 19.12.2017 - IO-Exception block verlässt nun die funktion mit return.
# 15.09.2018 - Sleep im  Main-Loop auf 1 Sekunde erhoeht
# ---

import pifacedigitalio as io # import io libraries
import time # import time libraries (for sleep e.g.)
import urllib #import libs for http-requests
io.init() # initialize piface-board

path_zara = "/mnt/rds/source-current/CurrentSong.txt"
path_studio1 = "/mnt/rds/source-current/Studio1-current.txt"
path_studio2 = "/mnt/rds/source-current/Studio2-current.txt"
path_mobfw = "/mnt/rds/source-current/StudioMOBFW-current.txt"
path_geis = "/mnt/rds/source-current/StudioGEIS-current.txt"
nowplaying = "/mnt/rds/now-onair.txt"
onairsource = "/mnt/rds/onair-studio.txt"
logfile = "/mnt/rds/logfile.txt"


def check_input(): # check-function for reading input-ports
    if io.digital_read(0) == 1:
        return 'Havarie'
    elif io.digital_read(1) == 1:
        return 'Studio 1'
    elif io.digital_read(2) == 1:
        return 'Studio 2'
    elif io.digital_read(3) == 1:
        return 'Studio Geislingen'
    elif io.digital_read(4) == 1:
        return 'Studio Mobil/FW'
    elif io.digital_read(5) == 1:
        return 'Loop / Zara'
    else:
        return 'Keine Rueckmeldung von der Kreuzschiene'

    
def write_source_onair(): # write actual on air source to file
    file = open(onairsource, "r+") #opening file
    source = file.read() #read file content
    if source == check_input(): # compare if filecontet is already the actual state. if yes, close the file
        file.close()
    else:
        file.truncate(0) # Empty file before writing new info
        file.seek(0,0) # Set position in file on very first position
        try:
             file.write(check_input()) # write actual state to file (call check_input-function)
        except IOError:
             write_logfile ("FEHLER: ", "Kann OnAir-Source nicht schreiben!")
        file.close() # close file
        write_logfile ("QUELLE: ", check_input())

def write_logfile (prefix, info):
    print (time.strftime("%d.%m.%Y | %H:%M:%S") + " | " + prefix + info) #output to console
    file = open(logfile, "a")
    file.write(time.strftime("%d.%m.%Y | %H:%M:%S") + " | " + prefix + info)
    #file.write("\r\n")
    file.close()

def replace_umlaute(input):
    input = input.replace("ä","ae") #convert German "Umlaute" into something ASCII can do
    input = input.replace("ü","ue")
    input = input.replace("ö","oe")
    input = input.replace("Ä","AE")
    input = input.replace("Ü","UE")
    input = input.replace("Ö","OE")
    input = input.replace("ß","ss")
    return input
    
def update_web(input):
    # replace spaces in input with URL-Like "%20"
    input = input.replace (" ", "%20")
    urlbase_mp3 = "streamlink-1"
    urlbase_mp3_2="streamlink-2"
    urlbase_aac = "streamlink-3"
    #build URL to send (combining input with base URL) for both mp3- an the aac-Stream
    urlsend_mp3 = urlbase_mp3 + input + " | radiofips"
    urlsend_mp3_2 = urlbase_mp3_2 + input + " | radiofips"
    urlsend_aac = urlbase_aac + input + " | radiofips"
    # print urlsend_mp3 # just to test, what's going on ;)
    # send combined URL to Streaming-Server
    try: # try-except-block to suppress errors from "urlopen" (shoutcastserver does not answer -> error)
        urllib.urlopen(urlsend_mp3) # send url
        urllib.urlopen(urlsend_mp3_2)
        urllib.urlopen(urlsend_aac)
        write_logfile("WEB-Update: ", input)
    except:
       print "blubb" # except does not work without code ;-)

def update_rds(): 
    if io.digital_read(0) == 1:
        filedest = open(nowplaying, "r+")
        if filedest.read() == "FIPS ;-)":
            filedest.close()
        else:
            filedest.truncate(0)
            filedest.seek(0,0)
            filedest.write("FIPS ;-)")
            write_logfile("TITEL: ", "Notprogramm")
            filedest.close()
    if io.digital_read(1) == 1: # Studio 1 check
        filesrc = open(path_studio1, "r") # open Source and Dest Files
        filedest = open(nowplaying, "r+")
        if filesrc.read() == filedest.read(): # if source didn't change, don't write dest-file
            filesrc.close()
            filedest.close()
        else: # if source changed...
            filedest.truncate(0) # Empty file before writing new info
            filedest.seek(0,0) # Set position in file on very first position
            filesrc.seek(0,0) # Set position in sourcefile on very first position
            try: # Catch IOError when file can't be written
                filedest.write(replace_umlaute(filesrc.read())) # write filecontent from source to dest
            except IOError:
                write_logfile ("FEHLER: ", "Kann now-onair.txt nicht schreiben!") # Catch IO-Error, write log
                return #exit funktion
            filesrc.seek(0,0) # Set position in sourcefile on very first position
            write_logfile("TITEL: ", filesrc.read())
            filesrc.close()
            filedest.close()
    elif io.digital_read(2) == 1: # Studio 2 check
        filesrc = open(path_studio2, "r")
        filedest = open(nowplaying, "r+")
        if filesrc.read() == filedest.read():
            filesrc.close()
            filedest.close()
        else:
            filedest.truncate(0)
            filedest.seek(0,0)
            filesrc.seek(0,0)
            try:
                filedest.write(replace_umlaute(filesrc.read()))
            except IOError:
                write_logfile ("FEHLER: ", "Kann now-onair.txt nicht schreiben!")
                return
            filesrc.seek(0,0)
            write_logfile("TITEL: ", filesrc.read())
            filesrc.close()
            filedest.close()
    elif io.digital_read(3) == 1: # Studio Geislingen check
        filesrc = open(path_geis, "r")
        filedest = open(nowplaying, "r+")
        if filesrc.read() == filedest.read():
            filesrc.close()
            filedest.close()
        else:
            filedest.truncate(0)
            filedest.seek(0,0)
            filesrc.seek(0,0)
            try:
                filedest.write(replace_umlaute(filesrc.read()))
            except IOError:
                write_logfile ("FEHLER: ", "Kann now-onair.txt nicht schreiben!")
                return
            filesrc.seek(0,0)
            write_logfile("TITEL: ", filesrc.read())
            filesrc.close()
            filedest.close()
    elif io.digital_read(4) == 1: # Studio Mobil / FW check
        filesrc = open(path_mobfw, "r")
        filedest = open(nowplaying, "r+")
        if filesrc.read() == filedest.read():
            filesrc.close()
            filedest.close()
        else:
            filedest.truncate(0)
            filedest.seek(0,0)
            filesrc.seek(0,0)
            try:
                filedest.write(replace_umlaute(filesrc.read()))
            except IOError:
                write_logfile ("FEHLER: ", "Kann now-onair.txt nicht schreiben!")
                return
            filesrc.seek(0,0)
            write_logfile("TITEL: ", filesrc.read())
            filesrc.close()
            filedest.close()
    elif io.digital_read(5) == 1: # Zara / Loop check
        filesrc = open(path_zara, "r")
        try:
            filedest = open(nowplaying, "r+")
        except IOError:
            write_logfile ("FEHLER: ", "Kann now-onair.txt nicht öffnen!")
            return
        if filesrc.read() == filedest.read():
            filesrc.close()
            filedest.close()
        else:
            filedest.truncate(0)
            filedest.seek(0,0)
            filesrc.seek(0,0)
            try:
                filedest.write(replace_umlaute(filesrc.read()))
            except IOError:
                write_logfile ("FEHLER: ", "Kann now-onair.txt nicht schreiben!")
                return
            filesrc.seek(0,0)
            write_logfile("TITEL: ", filesrc.read())
            filesrc.close()
            filedest.close()
    else:
        filedest = open(nowplaying, "r+")
        filedest.truncate(0)
        filedest.seek(0,0)
        try:
            filedest.write("Irgendwas stimmt hier garnicht...")
        except IOError:
            write_logfile ("FEHLER: ", "Kann now-onair.txt nicht schreiben!")
            return
        write_logfile("ERROR: ", "PiFace-Quelle unbekannt!")
        filedest.close()


while True: # main program-loop
    
    write_source_onair()
    update_rds()
    time.sleep (1)
    
    if io.digital_read(7) == 1: # exit condition
        io.deinit() # deinitialize piface-board
        break # exit program
