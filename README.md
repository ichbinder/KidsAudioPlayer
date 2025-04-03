# Kids MP3 Player with RFID Functionality

A kid-friendly MP3 player with RFID functionality, specifically designed for Raspberry Pi. This application allows children to control music playback by simply placing and removing RFID cards, without needing to interact with a touchscreen or keyboard.

![Kids MP3 Player Screenshot](generated-icon.png)

## Features

- **RFID Control**: Music automatically plays when an RFID card is placed on the reader and stops when removed
- **Kid-friendly Interface**: Large controls and a colorful, intuitive layout
- **Flexible Music Management**: Easily add MP3 files to the `mp3s` folder
- **RFID Tag Management**: Link RFID cards to specific songs through a simple admin interface
- **Dark Mode**: Toggleable light and dark color schemes
- **Sleep Timer**: Set a timer to automatically stop music after a specified time
- **Album Cover Support**: Displays matching image files as album covers
- **Colorful Volume Control**: Child-friendly volume slider with vibrant colors

## Hardware Requirements

- Raspberry Pi (tested on Raspberry Pi A+ with 512MB RAM)
- RC522 RFID reader
- MIFARE Classic 1K RFID cards/tags
- Speakers or headphones
- Power supply for the Raspberry Pi
- Recommended: Pibow Frame for Raspberry Pi Touch Display 2 for an integrated case solution

## Software Requirements

- Python 3.8+ (due to Flask 2.3+ requirements)
- Flask 2.3.3+
- Flask-SQLAlchemy 3.1.1+
- SQLAlchemy 2.0.23+
- MFRC522 Python library 0.0.7+
- RPi.GPIO 0.7.1+ 
- gunicorn 23.0.0+
- psycopg2-binary 2.9.9+ (optional, for PostgreSQL support)

## Installation

1. Clone the repository:
   ```
   git clone git@github.com:ichbinder/KidsAudioPlayer.git
   cd KidsAudioPlayer
   ```

2. Set up a virtual environment (recommended for Raspberry Pi OS):
   ```
   # First ensure you have python3-venv installed
   sudo apt install python3-full python3-venv
   
   # Create virtual environment
   python3 -m venv venv
   
   # Activate the virtual environment
   source venv/bin/activate
   ```

3. Install dependencies (within the virtual environment):
   ```
   pip install flask flask-sqlalchemy sqlalchemy gunicorn mfrc522 rpi-gpio psycopg2-binary
   ```
   
   Alternatively, you can create a requirements.txt file with the following content and then run `pip install -r requirements.txt`:
   ```
   flask>=2.3.3
   flask-sqlalchemy>=3.1.1
   sqlalchemy>=2.0.23
   gunicorn>=23.0.0
   mfrc522>=0.0.7
   rpi-gpio>=0.7.1
   psycopg2-binary>=2.9.9
   ```
   
   **Note:** If you get an "externally-managed-environment" error, this is due to PEP 668 protections in newer Debian/Raspberry Pi OS. You must use a virtual environment as shown above.

4. Initialize the database:
   ```
   # The database is automatically created when the application is started for the first time
   ```

5. Connect the RFID reader:
   - Connect the RC522 RFID reader to the Raspberry Pi GPIO pins according to the following pinout:
     - SDA → Pin 24
     - SCK → Pin 23
     - MOSI → Pin 19
     - MISO → Pin 21
     - GND → GND
     - RST → Pin 22
     - 3.3V → 3.3V

6. Add MP3 files:
   - Place your MP3 files in the `mp3s` folder
   - For album covers, place image files with the same name as the MP3 in the same folder (supported formats: .jpg, .jpeg, .png, .gif, .bmp, .webp)

## Starting the Application

If you're using a virtual environment, make sure it's activated:
```
source venv/bin/activate
```

Then start the application:
```
python main.py
```

For production deployment, you can use gunicorn:
```
gunicorn --bind 0.0.0.0:5000 main:app
```

The application is then accessible via a web browser at `http://[raspberry-pi-ip]:5000`.

## Configuring RFID Tags

1. Navigate to the RFID management page via the gear button in the top right corner of the main page
2. Click on "Scan RFID Tag" and hold an RFID card to the reader
3. Enter a user-friendly name for the card (optional)
4. Select a song from the dropdown list
5. Click "Register"

## Project Structure

```
KidsAudioPlayer/
├── app.py                 # Flask app configuration
├── main.py                # Main entry point
├── db.py                  # Database initialization
├── models.py              # Database models
├── controllers/
│   └── rfid_controller.py # RFID tag management logic
├── routes/
│   ├── api_routes.py      # API endpoints
│   └── rfid_routes.py     # RFID management routes
├── static/
│   ├── css/               # Stylesheets
│   ├── js/                # JavaScript files
│   └── svg/               # SVG icons
├── templates/
│   ├── index.html         # Main player interface
│   └── rfid_management.html # RFID management page
├── utils/
│   ├── file_handler.py    # File management functions
│   ├── rfid_handler.py    # RFID hardware interface
│   └── rfid_player.py     # RFID player integration
└── mp3s/                  # Music files
```

## How It Works

1. The RFID handler continuously monitors the RC522 RFID reader
2. When a card is detected, the associated tag ID is read
3. The RFID controller searches for the tag ID in the database
4. If an entry is found, the linked song is played
5. When the card is removed, playback stops

The Pibow Frame for Raspberry Pi Touch Display 2 provides an elegant housing solution, making the whole setup more durable and child-friendly, with easy access to the touch screen interface.

In simulation mode (when no RFID reader is connected), a virtual RFID tag with ID "12345678" is simulated.

## Troubleshooting

### RFID Reader Not Detected
- Check the wiring of the RC522 reader
- Make sure SPI is enabled on your Raspberry Pi:
  ```
  sudo raspi-config
  ```
  Go to "Interface Options" > "SPI" > "Yes"

### No Music Playing
- Check if MP3 files are present in the `mp3s` folder
- Check the audio output settings of your Raspberry Pi
- Make sure the RFID tag is correctly registered

### Admin Interface Shows No Songs
- Restart the application to update the database
- Check if the MP3 files are correctly placed in the `mp3s` folder

## Customization

### Adding New Music
Simply place MP3 files in the `mp3s` folder. The application detects them automatically.

### Changing the Design
The CSS styles are located in `static/css/styles.css`. Change colors, sizes, and layouts as needed.

### Customizing RFID Simulation
In development mode or when no RFID reader is connected, a virtual RFID tag is simulated. Modify the simulation logic in `utils/rfid_handler.py`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- RFID library: [mfrc522](https://github.com/pimylifeup/MFRC522-python)
- SVG icons: [Feather Icons](https://feathericons.com/)
- Demo MP3s: [Pixabay](https://pixabay.com/music/)
- Pibow Frame for Raspberry Pi Touch Display 2: [Pimoroni](https://shop.pimoroni.com/)