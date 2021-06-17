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
  <a href="#settings">Settings</a> •
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

## Settings

### config.json

|Key|Type|Description|Options|
|---|---|---|---|
|*File Path*|`str`|Path to save files to, do not include /|Any valid path|
|*File Format*|`str`|Format that local backups should take|"csv","json","both"|
|*Write to Influx*|`bool`|Export data to InfluxDB?|true/false|
|*Debug Stats*|`bool`|Print debug stats?|true/false|
|*Influx Bucket*|`str`|Bucket to export data to|Any valid bucket, can be blank if *Write to Influx* is false|
|*Influx IP*|`str`|IP address of InfluxDB 2.x database|IP of database, localhost if hosted on same machine, can be blank if *Write to Influx* is false|
|*Influx Port*|`str`|Port of InfluxDB 2.x database|Port of database (usually 8086), can be blank if *Write to Influx* is false|
|*Influx Token*|`str`|Auth token for InfluxDB 2.x database|Auth token provided by your admin, can be blank if *Write to Influx* is false|
|*Influx Organisation*|`str`|Organisation your token is associated with|Organisation associated with auth token, can be blank if *Write to Influx* is false|

### auth.json

|Key|Type|Description|Options|
|---|---|---|---|
|*Token*|`str`|Auth token provided by ACOEM UK|Any valid auth token|
|*License*|`str`|License KEY provided by ACOEM UK|Any vald license key|
|*API*|`str`|URL for API requests||

---

## API

### [main.py](./main.py)
The main script for running the program, utilises modules found in [modules](./modules/) using config specified in [Settings](./Settings)

#### Command line arguments:

| Argument | Type | Usage | Required? | Default |
|---|---|---|---|---|
|-s / --start-date|`str`|Date to begin data download (YYYY-MM-DD)|Y|None|
|-e / --end-date|`str`|Date to end data download (YYYY-MM-DD)|Y|None|
|-c / --config|`str`|Alternate path to config file, use `/` in place of `\`|N|Settings/config.json|
|-a / --auth|`str`|Alternate path to auth file, use `/` in place of `\`|N|Settings/auth.json|


#### Functions

##### parse_date_string

Parses input string from and returns `datetime` object. The string can have the following formats (see strftime.org for more info):
|Simplified|strftime|
|---|---|
|YYYY-MM-DD|%Y-%m-%d|
|YYYY/MM/DD|%Y/%m/%d|
|YYYY\MM\DD|%Y\%m\%d|
|YYYY.MM.DD|%Y.%m.%d|

###### Keyword Arguments

| Argument | Type | Usage | Required? | Default |
|---|---|---|---|---|
|*date_string*|`str`|The string to be parsed in to a `datetime` object|Y|None|

###### Returns

`datetime` object parsed from *date_string*

###### Raises

|Error Type|Cause|
|---|---|
|`ValueError`|*date_string* does not match any of the valid formats|

##### fancy_print

Makes a nicer output to the console

###### Keyword Arguments

| Argument | Type | Usage | Required? | Default |
|---|---|---|---|---|
|*str_to_print*|`str`|String that gets printed to console|Y|None|
|*length*|`int`|Character length of output|N|70|
|*form*|`str`|Output type (listed below)|N|NORM|
|*char*|`str`|Character used as border, should only be 1 character|N|\U0001F533 (White box emoji)|
|*end*|`str`|Appended to end of string, generally should be `\n` unless output is to be overwritten, then use `\r`|N|\r|
|*flush*|`bool`|Flush the output stream?|N|False|

**Valid options for _form_**
| Option | Description |
|---|---|
|TITLE|Centres the string, one char at start and end|
|NORM|Left aligned string, one char at start and end|
|LINE|Prints line of *char* of specified *length*|

##### get_json

Open json file and return as dict

###### Keyword Arguments

| Argument | Type | Usage | Required? | Default |
|---|---|---|---|---|
|*path_to_json*|`str`|The path to the json file, can be relative e.g Settings/config.json|Y|None|

###### Returns

`dict` containing contents of json file

###### Raises

|Error Type|Cause|
|---|---|
|`FileNotFoundError`|File is not present|
|`ValueError`|Formatting error in json file, such as ' used instead of " or comma after last item|

##### save_to_file

Saves string to text file, format specified in filename

###### Keyword Arguments

| Argument | Type | Usage | Required? | Default |
|---|---|---|---|---|
|*write_data*|`str`|Text to be written to file|Y|None|
|*path_to_file|`str`|Path to save file to, can be relative to working directory, do not add / to end|Y|None|
|*filename*|`str`|Name of file, including filetype e.g data.csv|Y|None|


### [acoemapi.py](./modules/acoemapi.py)

Contains all classes and functions pertaining to communication with ACOEM UK API

#### Classes

##### AcoemRequest
Handles requesting metadata and measurements from ACOEM UK API

###### Keyword Arguments

| Argument | Type | Usage | Required? | Default |
|---|---|---|---|---|
|*auth_token*|`dict`|Contains auth info for ACOEM UK API|Y|None|


###### Attributes

| Attribute | Type | Description |
|---|---|---|
|*auth_token*|`dict`|Contains license and auth token for ACOEM UK API|
|*station_meta*|`dict`|Contains metadata for all stations that user has access to, keys correspond to sensor UUID|
|*measurement_data*|`dict`|Contains measurements for all stations, keys correspond to sensor UUID|

###### Methods

**dl_station_metadata**

Downlaods metadata for stations associated with user from ACOEM UK API

- Keyword Arguments
None

**dl_station_measurements**

Downloads measurements for stations associated with user from ACOEM UK API for specified date range

- Keyword arguments

| Argument | Type | Usage | Required? | Default |
|---|---|---|---|---|
|*id*|`str`|UUID for station|Y|None|
|*day_start*|`datetime`|Day to begin downloading measurements from|Y|None|
|*period_length*|`int`|Number of days to download measurements for|N|1|

**dl_all_station_measurements**

Needs refactoring to use dl_station_measurements, recommended not to use this for now

**get_measurement_data**

Returns copy of measurement_data

- Keyword Arguments

None

- Returns

Copy of measurement_data instance (`dict`)

**get_metadata**

Returns copt of metadata

- Keyword Arguments

None

- Returns

Copy of metadata instance (`dict`)

**get_key_classifications**

Classifies whether keys are a measurement or a field, useful for formatting csv file

- Keyword Arguments

| Argument | Type | Usage | Required? | Default |
|---|---|---|---|---|
|*id*|`str`|UUID of sensor|Y|None|

- Returns

`dict` splitting measurements and metadata in to "fields" and "tags"

**format_as_csv**

Formats measurement data as csv file

- Keyword Arguments

| Argument | Type | Usage | Required? | Default |
|---|---|---|---|---|
|*id*|`str`|UUID of sensor|Y|None|
|*keys*|`dict`|Output of **get_key_classification**, splits keys in to "fields" and "tags"|

- Returns

String format representing csv file

**format_as_json**

Formats measurement data as json file

- Keyword Arguments

| Argument | Type | Usage | Required? | Default |
|---|---|---|---|---|
|*id*|`str`|UUID of sensor|Y|None|

**clear_measurements**

Clears measurement_data

- Keyword Arguments
None

- Returns
None

### [influxwrite.py](./modules/influxwrite.py)

Contains functions and classes pertaining to writing data to InfluxDB 2.x database

#### Classes

##### InfluxWriter

Handles connection and export to InfluxDB 2.x database

###### Keyword Arguments

| Argument | Type | Usage | Required? | Default |
|---|---|---|---|---|
|*influx_config*|`dict`|Contains all info relevant to connecting to InfluxDB database|

###### Attributes

| Attribute | Type | Description |
|---|---|---|
|*config*|`dict`|Config info for InfluxDB 2.x database|
|*client*|`InfluxDBClient`|Client object for InfluxDB 2.x database|
|*write_client*|`InfluxDBClient.write_api`|Write client object for InfluxDB 2.x database|

###### Methods

**write_container_list

Writes list of measurement containers to InfluxDB 2.x database, synchronous write used as asynchronous write caused memory issues on a 16 GB machine.

- Keyword Arguments

| Argument | Type | Usage | Required? | Default |
|---|---|---|---|---|
|*list_of_containers*|`list`|Exports list of data containers to InfluxDB 2.x database|

Containers must have the following keys:
|Key|Description|
|---|---|
|*time*|Measurement time in datetime format|
|*measurement*|Name of measurement in the bucket|
|*fields*|Measurements made at *time*|
|*tags*|Metadata for measurements made at *time*|

- Returns
None

### [timetools.py](./modules/timetools.py)

Temporary class used for time based calculations, will be replaced eventually

#### Classes

##### TimeCalculator

Used for time based calculations

###### Keyword arguments

| Argument | Type | Usage | Required? | Default |
|---|---|---|---|---|
|*date_start*|`datetime`|Start date|Y|None|
|*date_end*|`datetime`|End date|Y|None|

###### Attributes

| Attribute | Type | Description |
|---|---|---|
|*start*|`datetime`|Start date|
|*end*|`datetime`|End date|

###### Methods

**day_difference**

Calculates days between *start* and *end*

- Keyword Arguments
None

- Returns
`int` Representing number of days between *start* and *end*

---

## License

GNU General Public License v3
