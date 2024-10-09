from machine import UART, Pin, SPI
import time, utime
import st7789
import vga1_8x8 as f
import vga1_16x16 as f2

u = UART(0, 115200)
s = SPI(1, baudrate=40000000, sck=Pin(10), mosi=Pin(11))
t = st7789.ST7789(s, 135, 240, reset=Pin(12, Pin.OUT), cs=Pin(9, Pin.OUT), dc=Pin(8, Pin.OUT), backlight=Pin(13, Pin.OUT), rotation=1)
l = []

reset_button = Pin(15, Pin.IN, Pin.PULL_UP)


def read_led_status():
    u.write('AT+GPIO?\r\n')
    time.sleep(0.1)
    if u.any():
        response = u.read()
        response = ''.join([chr(c) if 32 <= c < 127 else '?' for c in response])
        print(response)
        return response
    return None


def init_disp():
    t.init()
    t.fill(0)


def send(cmd, ack, tout=10000):
    u.write(cmd + '\r\n')
    t_start = utime.ticks_ms()
    while (utime.ticks_ms() - t_start) < tout:
        if u.any():
            resp = u.read().decode()
            l.append(resp)
            print(resp)
            if ack in resp:
                return True
    return False


def show_msg(text, x, y, color=st7789.WHITE, font=f):
    t.text(font, text, x, y, color)


def wifi_sni():
    init_disp()
    show_msg("Sniff en cours...", 5, 10, st7789.YELLOW)
    while True:

        if send("AT+CWLAP", "OK", 20000):
            for response in l:
                lignes = response.split('+CWLAP:')
            a = ""
            a = lignes
            e = 0
            i = 1
            init_disp()
            for response in a:
                a_gros = response.strip()
                Debut_nom_wifi = a_gros.find('"') + 1
                Fin_nom_wifi = a_gros.find('"', Debut_nom_wifi)
                nom_wifi = a_gros[Debut_nom_wifi:Fin_nom_wifi]

                try:
                    debut_dBm = a_gros.find(',', Fin_nom_wifi) + 1
                    fin_dBm = a_gros.find(',', debut_dBm)
                    dbm_wifi = a_gros[debut_dBm:fin_dBm]
                except:
                    print("Pas de dBm pour: ", nom_wifi)

                try:
                    debut_address_mac = a_gros.find('"', Fin_nom_wifi + 1) + 1
                    fin_address_mac = a_gros.find('"', debut_address_mac)
                    mac_wifi = a_gros[debut_address_mac:fin_address_mac]
                except:
                    print("Pas de mac pour: ", nom_wifi)

                try:
                    fin_address_mac = a_gros.find('"', debut_address_mac)
                    debut_channel = a_gros.find(',', fin_address_mac) + 1
                    fin_channel = a_gros.find(',', debut_channel)
                    canal_wifi = a_gros[debut_channel:fin_channel]
                except:
                    print("Pas de canal pour: ", nom_wifi)

                try:
                    debut_security = a_gros.rfind(',') - 1
                    fin_security = a_gros.rfind(',')
                    security_type = a_gros[debut_security:fin_security].strip()

                    if security_type == "0":
                        try:
                            dbm_value = int(dbm_wifi.strip())
                            if dbm_value <= -60:
                                show_msg(f"[ ]{nom_wifi}|CH:{canal_wifi}|{dbm_wifi}dBm", 4, 9 * i, st7789.RED)
                            elif -60 < dbm_value <= -45:
                                show_msg(f"[ ]{nom_wifi}|CH:{canal_wifi}|{dbm_wifi}dBm", 4, 9 * i, st7789.YELLOW)
                            elif dbm_value > -45:
                                show_msg(f"[ ]{nom_wifi}|CH:{canal_wifi}|{dbm_wifi}dBm", 4, 9 * i, st7789.GREEN)
                        except ValueError:
                            print("Erreur de conversion dBm")
                    else:
                        try:
                            dbm_value = int(dbm_wifi.strip())
                            if dbm_value <= -60:
                                show_msg(f"[X]{nom_wifi}|CH:{canal_wifi}|{dbm_wifi}dBm", 4, 9 * i, st7789.RED)
                            elif -60 < dbm_value <= -45:
                                show_msg(f"[X]{nom_wifi}|CH:{canal_wifi}|{dbm_wifi}dBm", 4, 9 * i, st7789.YELLOW)
                            elif dbm_value > -45:
                                show_msg(f"[X]{nom_wifi}|CH:{canal_wifi}|{dbm_wifi}dBm", 4, 9 * i, st7789.GREEN)
                        except ValueError:
                            print("Erreur de conversion dBm")
                except Exception as ex:
                    print(f"Erreur: {ex}")
                e += 1
                i += 1

        else:
            print("Pas de Réseaux trouvé.")

        time.sleep(3)


def menu():
    init_disp()
    show_msg("/\\_/\\", 77, 5, st7789.BLUE, f2)
    show_msg("( o.o )", 62, 25, st7789.BLUE, f2)
    show_msg(" > ^ <", 62, 45, st7789.BLUE, f2)
    show_msg("READY", 5, 5, st7789.GREEN, f)
    show_msg("""-------------""", 65, 70, st7789.BLUE, f)
    show_msg("""|Outils WiFi|""", 65, 78, st7789.BLUE, f)
    show_msg("""-------------""", 65, 88, st7789.BLUE, f)
    show_msg("Press Reset -> Sniffer WiFi", 5, 120, st7789.BLUE, f)

    print(""" 
    ═══════════════════════════════
            🛠  Outils WiFi                    
    ═══════════════════════════════
     Press Reset -> Sniffer WiFi
    """)
    while True:
        response = read_led_status()
        if response:
            # Vérifie si un message d'erreur apparaît dans la réponse
            if "ERROR" in response:
                print("")
                # Ne fait rien si une erreur est détectée
            else:
                # Vérifie si la LED est éteinte
                if "GPIO2=0" in response:
                    print("LED éteinte (bouton reset non appuyé)")
                    wifi_sni()  # Lance le programme de sniffer WiFi
                    break  # Sort de la boucle principale
                else:
                    print("LED allumée")
                    wifi_sni()
                    break
        time.sleep(0.5)

if __name__ == '__main__':
    menu()