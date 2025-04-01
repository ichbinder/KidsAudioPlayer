# Kids MP3 Player mit RFID-Funktionalität

Ein kinderfreundlicher MP3-Player mit RFID-Funktionalität, speziell entwickelt für den Raspberry Pi. Diese Anwendung ermöglicht es Kindern, Musik durch einfaches Auflegen und Entfernen von RFID-Karten zu steuern, ohne mit einem Touchscreen oder einer Tastatur interagieren zu müssen.

![Kids MP3 Player Screenshot](generated-icon.png)

## Funktionen

- **RFID-Steuerung**: Musik wird automatisch abgespielt, wenn eine RFID-Karte auf den Leser gelegt wird, und stoppt, wenn die Karte entfernt wird
- **Kinderfreundliche Benutzeroberfläche**: Große Steuerelemente und ein farbenfroher, intuitiver Aufbau
- **Flexibles Musikmanagement**: Füge MP3-Dateien einfach zum `mp3s`-Ordner hinzu
- **RFID-Tag-Verwaltung**: Verknüpfe RFID-Karten mit bestimmten Songs über eine einfache Admin-Oberfläche
- **Dunkelmodus**: Umschaltbare helle und dunkle Farbschemata
- **Schlaftimer**: Stell einen Timer ein, um die Musik nach einer bestimmten Zeit automatisch zu stoppen
- **Albumcover-Unterstützung**: Zeigt passende Bilddateien als Albumcover an

## Hardware-Anforderungen

- Raspberry Pi (getestet auf Raspberry Pi A+ mit 512MB RAM)
- RC522 RFID-Lesegerät
- MIFARE Classic 1K RFID-Karten/Tags
- Lautsprecher oder Kopfhörer
- Stromversorgung für den Raspberry Pi

## Software-Anforderungen

- Python 3.6+
- Flask 2.3.3
- Flask-SQLAlchemy 3.1.1
- SQLAlchemy 2.0.23
- MFRC522 Python-Bibliothek 0.0.7
- RPi.GPIO 0.7.1 
- gunicorn 23.0.0
- email-validator 2.1.0
- psycopg2-binary 2.9.9 (für PostgreSQL-Unterstützung)

## Installation

1. Repository klonen:
   ```
   git clone https://github.com/yourusername/kids-rfid-music-player.git
   cd kids-rfid-music-player
   ```

2. Abhängigkeiten installieren:
   ```
   pip install -r requirements.txt
   ```

3. Datenbank initialisieren:
   ```
   # Die Datenbank wird automatisch erstellt, wenn die Anwendung zum ersten Mal gestartet wird
   ```

4. RFID-Reader anschließen:
   - Verbinde den RC522 RFID-Reader mit den GPIO-Pins des Raspberry Pi gemäß folgendem Schema:
     - SDA → Pin 24
     - SCK → Pin 23
     - MOSI → Pin 19
     - MISO → Pin 21
     - GND → GND
     - RST → Pin 22
     - 3.3V → 3.3V

5. MP3-Dateien hinzufügen:
   - Lege deine MP3-Dateien im Ordner `mp3s` ab
   - Für Albumcover lege Bilddateien mit demselben Namen wie die MP3 im gleichen Ordner ab (unterstützt werden .jpg, .jpeg, .png, .gif, .bmp, .webp)

## Starten der Anwendung

```
python main.py
```

Die Anwendung ist dann über einen Webbrowser unter `http://[raspberry-pi-ip]:5000` erreichbar.

## RFID-Tags konfigurieren

1. Navigiere zur RFID-Verwaltungsseite über den Zahnrad-Button in der rechten oberen Ecke der Hauptseite
2. Klicke auf "RFID-Tag scannen" und halte eine RFID-Karte an den Leser
3. Gib einen benutzerfreundlichen Namen für die Karte ein (optional)
4. Wähle einen Song aus der Dropdown-Liste aus
5. Klicke auf "Registrieren"

## Projektstruktur

```
kids-rfid-music-player/
├── app.py                 # Flask App-Konfiguration
├── main.py                # Haupteinstiegspunkt
├── db.py                  # Datenbankinitialisierung
├── models.py              # Datenbankmodelle
├── controllers/
│   └── rfid_controller.py # RFID-Tag-Verwaltungslogik
├── routes/
│   ├── api_routes.py      # API-Endpunkte
│   └── rfid_routes.py     # RFID-Verwaltungsrouten
├── static/
│   ├── css/               # Stylesheets
│   ├── js/                # JavaScript-Dateien
│   └── svg/               # SVG-Icons
├── templates/
│   ├── index.html         # Hauptspieler-Oberfläche
│   └── rfid_management.html # RFID-Verwaltungsseite
├── utils/
│   ├── file_handler.py    # Dateiverwaltungsfunktionen
│   ├── rfid_handler.py    # RFID-Hardware-Schnittstelle
│   └── rfid_player.py     # RFID-Player-Integration
└── mp3s/                  # Musikdateien
```

## Wie es funktioniert

1. Der RFID-Handler überwacht kontinuierlich den RC522 RFID-Reader
2. Wenn eine Karte erkannt wird, wird die zugehörige Tag-ID gelesen
3. Der RFID-Controller sucht in der Datenbank nach der Tag-ID
4. Wenn ein Eintrag gefunden wird, wird der verknüpfte Song abgespielt
5. Wenn die Karte entfernt wird, wird die Wiedergabe gestoppt

Im Simulationsmodus (wenn kein RFID-Reader angeschlossen ist) wird ein virtueller RFID-Tag mit der ID "12345678" simuliert.

## Problembehebung

### RFID-Reader wird nicht erkannt
- Überprüfe die Verkabelung des RC522-Readers
- Stelle sicher, dass SPI auf deinem Raspberry Pi aktiviert ist:
  ```
  sudo raspi-config
  ```
  Gehe zu "Interface Options" > "SPI" > "Yes"

### Keine Musik wird abgespielt
- Überprüfe, ob MP3-Dateien im Ordner `mp3s` vorhanden sind
- Überprüfe die Audioausgabeeinstellungen deines Raspberry Pi
- Stelle sicher, dass der RFID-Tag korrekt registriert wurde

### Admin-Oberfläche zeigt keine Songs
- Starte die Anwendung neu, um die Datenbank zu aktualisieren
- Überprüfe, ob die MP3-Dateien korrekt im `mp3s`-Ordner platziert sind

## Anpassung

### Hinzufügen neuer Musik
Lege einfach MP3-Dateien im Ordner `mp3s` ab. Die Anwendung erkennt diese automatisch.

### Ändern des Designs
Die CSS-Stile befinden sich in `static/css/styles.css`. Ändere Farben, Größen und Layouts nach Bedarf.

### Anpassen der RFID-Simulation
Im Entwicklungsmodus oder wenn kein RFID-Reader angeschlossen ist, wird ein virtueller RFID-Tag simuliert. Ändere die Simulationslogik in `utils/rfid_handler.py`.

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz - siehe die [LICENSE](LICENSE) Datei für Details.

## Danksagungen

- RFID-Bibliothek: [mfrc522](https://github.com/pimylifeup/MFRC522-python)
- SVG-Icons: [Feather Icons](https://feathericons.com/)
- Demo-MP3s: [Pixabay](https://pixabay.com/music/)