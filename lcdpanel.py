#!/usr/bin/python

# Pin Layout
#
# Data lines D1 through D4 are only used in 8-bit Mode
#  ___________________________________________
# | LCD Pin | RPi Pin | GPIO    | Description |
# |-------------------------------------------|
# |    1    |   12    |   18    | Data (D8)   |
# |    2    |   16    |   23    | Data (D7)   |
# |    3    |   18    |   24    | Data (D6)   |
# |    4    |   22    |   25    | Data (D5)   |
# |    5    |    x    |    x    | Data (D4)   |
# |    6    |    x    |    x    | Data (D3)   |
# |    7    |    x    |    x    | Data (D2)   |
# |    8    |    x    |    x    | Data (D1)   |
# |    9    |   24    |    8    | Pin_e       |
# |   10    |   30    |    x    | Ground      |
# |   11    |   26    |    7    | Pin_rs      |
# |   12    |  1/20   |    x    | Contrast    |
# |   13    |    2    |    x    | 5v          |
# |   14    |   14    |    x    | Ground      |
# |   15    |    6    |    x    | Ground      |
# |   16    |    4    |    x    | 5v          |
#  -------------------------------------------
#
__author__ = "Justin Verel"
__copyright__ = "marverinc"
__version__ = "0.1"
__date__ = "27-02-2018"
__maintainer__ = "Justin Verel"
__email__ = "justin@marverinc.nl"
__status__ = "Development"

"""Python imports"""
from time import sleep, strftime
from datetime import datetime
import socket
import subprocess
import atexit

"""PIP imports"""
from mpd import MPDClient, ConnectionError
import netifaces as ni
import unidecode

"""Raspberry Pi imports"""
from RPLCD import CharLCD
from RPi import GPIO

"""Global Variables"""
lcd = CharLCD(
        cols=16,
        rows=2,
        pin_rs=26,
        pin_e=24,
        pins_data=[
            22,
            18,
            16,
            12
        ],
        numbering_mode=GPIO.BOARD
)

"""Setup socket for incomming connection"""
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('0.0.0.0', 9988))
s.setblocking(0)
s.listen(1)

"""Global declarations"""
status = 'main'
mpd = 'inactive'
mpdstatus = ''

def write_to_lcd(lcd, framebuffer, num_cols):
    """Write the framebuffer out to the specified LCD"""
    lcd.home()
    for row in framebuffer:
        lcd.write_string(row.ljust(num_cols)[:num_cols])
        lcd.write_string('\r\n')

def loop_string(string, lcd, framebuffer, row, num_cols, delay=0.3):
    """Create looping text on row"""
    padding = ' ' * 2
    string = padding + string + padding
    for i in range(len(string) - num_cols +1):
        framebuffer[row] = string[i:i+num_cols]
        write_to_lcd(lcd, framebuffer, num_cols)
        sleep(delay)

def getIPAddress():
    ni.ifaddresses('eth0')
    ip = ni.ifaddresses('eth0')[ni.AF_INET][0]['addr']
    return ip

def getTemp():
    """Get Temperature""" 
    cpu = subprocess.Popen("cat /sys/class/thermal/thermal_zone0/temp", shell=True, stdout=subprocess.PIPE).stdout.read()
    cpu = float(cpu) / 1000
    cpu = round(cpu, 1)
    gpu = subprocess.Popen("vcgencmd measure_temp", shell=True, stdout=subprocess.PIPE).stdout.read()
    gpu = gpu.replace("temp=", "")
    output = "C: " + str(cpu) + " G: " + gpu
    return output

def main():
    global status
    global mpd
    global mpdstatus

    while True:
        print(mpd)
        if mpd is 'inactive':
            mpdclient = MPDClient()
            try:
                mpdclient.connect('localhost', 6600)
                mpd = 'active'
            except (ConnectionError, socket.error) as error:
                pass
        
        if status is 'main':
            x = 0
            y = 0
            while status is 'main':
                try:
                    mpdstatus = mpdclient.status()['state']
                except (ConnectionError, socket.error) as error:
                    pass

                if mpdstatus == "play":
                    status = 'mpd'
                
                if x is 1:
                    y = 0
                    while y is not 5:
                        lcd.clear()
                        lcd.write_string(datetime.now().strftime('%b %d  %H:%M:%S'))
                        lcd.cursor_pos = (1, 0)
                        lcd.write_string('' + getIPAddress())
                        y = y + 1
                        sleep(1)
                    x = 0
                else:
                    y = 0
                    while y is not 5:
                        lcd.clear()
                        lcd.write_string(datetime.now().strftime('%b %d  %H:%M:%S'))
                        lcd.cursor_pos = (1, 0)
                        lcd.write_string(str(getTemp()))
                        y = y + 1
                        sleep(1)
                    x = 1
        elif status is 'connection':
            lcd.clear()
            lcd.write_string("connection made")
        elif status is 'mpd':
            lcd.clear()
            try:
                mpdstatus = mpdclient.status()['state']
            except (ConnectionError, socket.error) as error:
                pass
            while mpdstatus == 'play':
                curSongInfo = mpdclient.currentsong()

                framebuffer = [
                        'MPD Playing:',
                        '',
                ]

                artist = curSongInfo['artist']
                title = curSongInfo['title']
    
                curSongString =  artist + ' - ' + title
                curSongString = unicode(curSongString, "utf-8")
                curSongString = unidecode.unidecode(curSongString)

                loop_string(curSongString, lcd, framebuffer, 1, 16)
            
            status = 'main'
    
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        lcd.clear()
        GPIO.cleanup()

atexit.register(lcd.clear())
atexit.register(GPIO.cleanup())
