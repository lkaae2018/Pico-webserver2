# Forsøg at importere 'usocket' (bruges i MicroPython). Fallback til 'socket' hvis det fejler.
try:
  import usocket as socket
except:
  import socket

from machine import Pin         # Importer Pin-klassen til at styre GPIO
import time
import network                  # Importer WiFi-netværksmodulet
import gc                       # Importer garbage collector
gc.collect()                    # Ryd op i hukommelsen

max_wait = 10  # maks ventetid i sekunder
wait_time = 0


# Indtast dine egne WiFi-oplysninger her
ssid = 'Miranet'
password = '3fg847kaae'

# Opret et WLAN-objekt i station mode (klient-tilstand)
station = network.WLAN(network.STA_IF)

station.active(True)            # Aktivér WiFi-adapteren
station.connect(ssid, password) # Forbind til WiFi-netværket

# Vent indtil forbindelsen er oprettet
while not station.isconnected() and wait_time < max_wait:
    print("Venter på WiFi-forbindelse...")
    time.sleep(1)
    wait_time += 1

if station.isconnected():
    print("WiFi-forbindelse oprettet")
    print(station.ifconfig())
else:
    print("Kunne ikke oprette forbindelse til WiFi efter", max_wait, "sekunder")

# Når WiFi er forbundet, vis forbindelsesoplysninger
print('Connection successful')
print(station.ifconfig())

# Definer LED-pin (GPIO25 på Raspberry Pi Pico = "LED")
led = Pin('LED', Pin.OUT)
led_state = "OFF"  # Start-tilstand for LED

# Funktion der genererer HTML-siden som svar til browseren
def web_page():
    html = """<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- Link til FontAwesome-ikoner (til visuel LED) -->
    <link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.7.2/css/all.css"
     integrity="sha384-fnmOCqbTlWIlj8LyTjo7mOUStjsKC4pOpQbqyi7RrhN7udi9RwhKkMHpvLbHG9Sr" crossorigin="anonymous">
    <style>
        html {
            font-family: Arial;
            display: inline-block;
            margin: 0px auto;
            text-align: center;
        }
        .button {
            background-color: #ce1b0e; /* Rød baggrund for LED ON */
            border: none;
            color: white;
            padding: 16px 40px;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
        }
        .button1 {
            background-color: #000000; /* Sort baggrund for LED OFF */
        }
    </style>
</head>

<body>
    <h2>Raspberry Pi Pico Web Server</h2>
    <p>LED state: <strong>""" + led_state + """</strong></p> <!-- Viser LED-status -->
    <p>
        <i class="fas fa-lightbulb fa-3x" style="color:#c81919;"></i> <!-- Tændt pære-ikon -->
        <a href="led_on"><button class="button">LED ON</button></a> <!-- LED ON-knap -->
    </p>
    <p>
        <i class="far fa-lightbulb fa-3x" style="color:#000000;"></i> <!-- Slukket pære-ikon -->
        <a href="led_off"><button class="button button1">LED OFF</button></a> <!-- LED OFF-knap -->
    </p>
</body>
</html>"""
    return html  # Returnér HTML-strengen

# Opret og konfigurer socket-server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))    # Lyt på alle netværksinterfaces på port 80 (standard HTTP-port)
s.listen(5)         # Maks. 5 ventende forbindelser

# Uendelig løkke til at håndtere HTTP-forespørgsler
while True:
    try:
        conn, addr = s.accept()               # Acceptér indkommende forbindelse
        conn.settimeout(3.0)                  # Timeout for modtagelse
        print('Received HTTP GET connection request from %s' % str(addr))
        request = conn.recv(1024)             # Læs HTTP-request
        conn.settimeout(None)                 # Fjern timeout
        request = str(request)                # Konverter bytes til streng
        print('GET Request Content = %s' % request)

        # Check om der er trykket på LED ON- eller OFF-link
        led_on = request.find('/led_on')
        led_off = request.find('/led_off')

        if led_on == 6:  # URL "/led_on" fundet
            print('LED ON -> GPIO25')
            led_state = "ON"
            led.on()     # Tænd LED

        if led_off == 6:  # URL "/led_off" fundet
            print('LED OFF -> GPIO25')
            led_state = "OFF"
            led.off()     # Sluk LED

        # Send HTML-svar til klient
        response = web_page()
        conn.send('HTTP/1.1 200 OK\n')           # HTTP-statuskode
        conn.send('Content-Type: text/html\n')   # Indholdstype
        conn.send('Connection: close\n\n')       # Luk forbindelsen efter svar
        conn.sendall(response)                   # Send hele HTML-siden
        conn.close()                             # Luk forbindelsen
    except OSError as e:
        conn.close()     # Luk forbindelse ved fejl
        print('Connection closed')
