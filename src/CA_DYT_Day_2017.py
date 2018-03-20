#Snippet1######################
# Benoetigte Module Importieren
###############################
import machine, neopixel, time, network, onewire, ds18x20, sys, umqtt
from umqtt.robust import MQTTClient

#Snippet2#############
# Globale Definitionen
######################
# ab hier anpassen bis ....
ARBEITSPLATZ=""
WLAN_ESSID = ""
WLAN_PASSWORD = ""
MQTT_URL = ""
MQTT_USERNAME = ""
MQTT_KEY = ""
MQTT_PORT = 1883
# ... bis hier!

PIXEL_PIN = machine.Pin(2, machine.Pin.OUT)
PIXEL_COUNT = 24
PIXEL_BRIGHTNESS = 40
DS1820_PIN = 5
MQTT_CLIENT = "Platz"+ARBEITSPLATZ
RUN = True


#Snippet3#####################################
# NeoPixel Objekt erstellen und initialisieren
##############################################
np = neopixel.NeoPixel(PIXEL_PIN, PIXEL_COUNT)
np.fill((0,0,0))
np.write()

#Snippet4##################################################
# Zur Startindikation, alle LEDs einmal auf- und abblenden
##########################################################
for i in range (PIXEL_BRIGHTNESS):
    np.fill((i,i,i))
    np.write()
for i in range (PIXEL_BRIGHTNESS):
    np.fill((PIXEL_BRIGHTNESS-i-1,PIXEL_BRIGHTNESS-i-1,PIXEL_BRIGHTNESS-i-1))
    np.write()

#Snippet5###########
# Mit WLAN verbinden
####################
sta_if = network.WLAN(network.STA_IF)
retries = 0
if not sta_if.isconnected():
    sta_if.active(True)
    sta_if.connect(WLAN_ESSID, WLAN_PASSWORD)
    while not sta_if.isconnected():
        time.sleep_ms(500)
        retries = retries + 1
        print('.', end=' ')
        if retries == 20:
            # wenn keine WLAN Verbindung, rot blinken und Exit hier
            for i in range (0,6):
                np.fill((PIXEL_BRIGHTNESS,0,0))
                np.write()
                time.sleep_ms(100)
                np.fill((0,0,0,0))
                np.write()
                time.sleep_ms(100)
            sys.exit()
print('Network connected:', sta_if.ifconfig())
for i in range (0,3):
    np.fill((0,PIXEL_BRIGHTNESS,0))
    np.write()
    time.sleep_ms(100)
    np.fill((0,0,0))
    np.write()
    time.sleep_ms(100)
                
#Snippet6###############
# Temperatursensor Setup
########################
dat = machine.Pin(DS1820_PIN)
ds = ds18x20.DS18X20(onewire.OneWire(dat))
roms = ds.scan()
print('found devices:', roms)

#Snippet7##############################################################
# Diese 'CallBack' Funktion wird aufgerufen, wenn eine "MQTT Nachricht"
# über die LED Farbe vorhanden ist und setzt den Farbwert entsprechend.
#######################################################################
def sub_cb(topic, msg):
    global led_colour, RUN

    if "farbe" in topic:
        led_colour = ((int(msg[1:3],16), int(msg[3:5],16), int(msg[5:],16)))
    elif "stop" in topic:
        RUN = False
    elif "rainbow" in topic:
        print('rainbow')
        rainbowCycle()


#Snippet8###########
# MQTT konfigurieren
####################
# MQTT client Objekt kreieren
c = MQTTClient(MQTT_CLIENT, MQTT_URL, MQTT_PORT, MQTT_USERNAME, MQTT_KEY)
# MQTT Callback definieren
c.set_callback(sub_cb)
# Zum MQTT Server verbinden
cstatus = c.connect()
# Topics abonnieren
c.subscribe(ARBEITSPLATZ+"/farbe")
c.subscribe(ARBEITSPLATZ+"/stop")
c.subscribe(ARBEITSPLATZ+"/rainbow")

##########################################
# NeoPixel Rainbow Animation from Adafruit
##########################################
def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)

def rainbowCycle(wait_ms=2, iterations=1):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for j in range(256*iterations):
        for i in range(PIXEL_COUNT):
            tcolour = wheel((int(i * 256 / PIXEL_COUNT) + j) & 255)
            np[i] = (tcolour)
            # strip.setPixelColor(i, wheel((int(i * 256 / strip.numPixels()) + j) & 255))
        np.write()
        time.sleep(wait_ms/1000.0)


# Initiale LED Farbe setzen
led_colour=((PIXEL_BRIGHTNESS,0,0))

#Snippet9################################################################
# Hauptprogramm
#########################################################################
j = 1
while RUN:
    # 24 Mal (ein Umlauf)
    for i in range (0,PIXEL_COUNT):
        # Erst alle LEDs aus, dann die 'Nächste' mit der entsprechenden
        # Farbe befüllen und schreiben
        np.fill((0,0,0))
        np[i] = (led_colour)
        np.write()
        # Bei der vorletzten LED lassen wir die Temperatur 'vorbereiten'
        if i == 23:
            # Konvertiere die Temperatur!
            ds.convert_temp()
        else:
            # ansonsten warte 50 Milisekunden, wegen der Animation
            time.sleep_ms(20)
        # hier schauen wir nach, ob es eine neue LED Farbe für uns gibt
        c.check_msg()
    # für alle Temperatursensoren, sende Daten zum MQTT Broker
    print("Count:", j, end = ' ')
    j = j + 1
    for rom in roms:
        TEMP = str(ds.read_temp(rom))
        print("Temperature: ", TEMP, "°C ")
        c.publish(ARBEITSPLATZ+"/temperatur", TEMP)


#Snippet10####
# Programmende
##############
c.disconnect()
print("Disconnected!")
sys.exit()

###################################
# END                             #
###################################
