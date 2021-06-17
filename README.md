<h1 align="center">
ACOEM UK API InfluxDB Export Tool
</h1>

---

Unofficial Python3 script that utilises the [ACOEM UK API](http://api.airmonitors.net/3.5/documentation/?key=C55638AM) to download user's equipment measurements
Measurements can then be exported to an InfluxDB 2.0 database

<p align="center">
  <a href="#key-features">Key Features</a> •
  <a href="#requirements">Requirements</a> •
  <a href="#operational-procedure">Operational Procedure</a> •
  <a href="#api">API</a> •
  <a href="#license">License</a>
</p>

---

## Key Features

- Determines all systems registered to user's ACOEM UK account
- Downloads data across selected date range (split in to 24 hour periods to avoid taxing the ACOEM servers) and saves it as a JSON file to specified path
- Measurements then exported to InfluxDB 2.0 database
- Measurements can also be saved as csv and/or json

---

## Requirements

- This program requires an **authorisation token** and **license** provided by ACOEM UK, this software does not come with one included
- This program was developed with **Python 3.8.5** for an **Ubuntu 20.04 LTS** machine
  - Earlier versions of Python 3, different versions of Ubuntu and other Linux distributions may work but are untested
- **python3-pip** and **python3-venv** are required for creating the virtual environment for the program to run with

---

## Operational Procedure

```
# Clone this repository
$ git clone https://github.com/CaderIdris/ACOEM-API-InfluxDB-Export.git

# Go in to repository
$ cd ACOEM-API-InfluxDB-Export

# Setup the virtual environment
$ ./venv_setup.sh

# Configure settings.json with file path and InfluxDB configuration

# Add auth token data to auth.json

# Run software
$ ./run.sh

# Input date range to download data
    Start Date: (YYYY-MM-DD)
    End Date:   (YYYY-MM-DD)
```

---

## API

TBA

---

## License

GNU General Public License v3
