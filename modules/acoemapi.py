"""Contains classes and methods that handle communication with the
ACOEM UK API

http://api.airmonitors.net/3.5/documentation/?key=C55638AM

This module contains classes and methods to communicate with the ACOEM
UK API, downloading metadata corresponding to the users account and
then downloads sensor measurements over a specified time period.

    Classes:
        AcoemRequest: Handles requesting information and measurements
        from the ACOEM UK API

"""

__author__ = "Idris Hayward"
__copyright__ = "2021, The University of Surrey & National Physical Laboratory"
__credits__ = ["Idris Hayward"]
__license__ = "GNU General Public License v3.0"
__version__ = "1.0"
__maintainer__ = "Idris Hayward"
__email__ = "j.d.hayward@surrey.ac.uk"
__status__ = "Stable Release"

import requests as req
import datetime as dt


class AcoemRequest:
    """Handles requesting information and measurements
    from the ACOEM UK API

    Attributes:
        auth_token (dict): Contains license and authorisation token for
        ACOEM UK API

        station_meta (dict): Contains metadata for all stations
        associated with user account. Keys correspond to the UUID of a
        sensor

        measurement_data (dict): Contains measurements for all stations
        associated with user account for time period specified. Keys
        correspond to the UUID of a sensor

    Methods:
        dl_station_meta: Download metadata using provided auth info

        dl_station_measurements: Download measurements for a specified
        station over a specified time period

        dl_all_station_measurements: Download measurements for all
        stations over a specified time period

        get_measurement_data: Return measurement data as dict

        get_metadata: Return metadata as dict

        format_as_csv: Parse measurement_data to a csv file, one file
        per sensor per measurement period (TBC)

        format_as_json: Parse measurement_data to more human readable
        json file, measurement_data is formatted to be easily read by
        computers, not humans (TBC)

        clear_measurements: Empty measurement_data
    """

    def __init__(self, auth_token):
        """Initialises class

        Keyword arguments:
            auth_token (dict): Dictionary containing authorisation
            information for ACOEM UK API. Requires three keys:
                - "Token": User token provided by ACOEM UK
                - "License": License key provided by ACOEM UK
                - "API": Link to the API, can be found in
                         documentation
        """
        self.auth_token = auth_token
        self.station_meta = dict()
        self.measurement_data = dict()

    def dl_station_meta(self):
        """Download metadata using provided auth info

        Utilises the ACOEM UK API to check which stations are
        registered to the users account and download metadata for them.
        The metadata is then put in to a dict format that can easily be
        read by the software. The metadata is saved to the station_meta
        attribute.

            Variables:
                meta_req_link (str): Link used to request metadata

                meta_raw (list): Returned metadata from ACOEM UK API,
                formatted as list of dictionaries

                keys_to_remove (list): Keys to be removed from metadata
                file (in this case, location data will be saved as
                separate measurement, not metadata)

                meta_keys (list): List of metadata attributes for
                specified station

                unique_ID (str): UUID of specified station

        """
        # Download metadata from ACOEM UK
        meta_req_link = (
            f'{self.auth_token["API"]}'
            f'{self.auth_token["Token"]}/{self.auth_token["License"]}/stations'
        )
        meta_raw = req.get(meta_req_link).json()

        # Save all data apart from location variables
        keys_to_remove = ["Latitude", "Longitude", "Altitude"]
        for station in meta_raw:
            meta_keys = list(station.keys())
            unique_ID = station["UniqueId"]
            for key in keys_to_remove:
                if key in meta_keys:
                    meta_keys.remove(key)
            self.station_meta[unique_ID] = dict()
            for key in meta_keys:
                self.station_meta[unique_ID][key] = station[key]

    def dl_station_measurements(self, id, day_start, period_length=1):
        """Downloads measurements made by a station over a specified
        period from the ACOEM UK API.

        The function calculates the time period to download data for
        for a specified station, downloads it and then iterates over
        each measurement, formatting each measurement in to a
        separate dict 'container' which has all measurement info.
        Once the container is populated, it is added to a list
        stored in measurement_data[id]. The container contains 4 keys:
            - "time": Time the measurement took place in datetime
                      format
            - "measurement": This will be the name of the measurement
                             if the data is written to InfluxDB,
                             currently hard coded as "ACOEM UK Systems"
            - "fields": All measurements made at "time"
            - "tags": All flags corresponding to measurement, as well
                      as station metadata

            Keyword arguments:
                id (string): UUID for station that data is being
                requested for

                day_start (datetime): Day to start downloading
                measurements from

                period_length (int): Number of days to download data
                for a single period, defaults to 1

            Variables:
                day_end (datetime): day_start + (period_length * 1 day)

                location_keys (list): Keys representing location flags
                in data

                measurement_types (list): The different measurement
                types made by a station that are stored by ACOEM UK API

                data_req_link (str): Link used to request measurements
                for a specific station across a specified time period

                station_measurements (http request): Raw return from
                ACOEM UK API

                data_req_success (bool): True if measurements returned
                successfully, False if connection couldn't be made or
                no data is present for specified station for specified
                time range

                measurement_time (datetime): Datetime format for when
                measurement was made, converted from string format used
                in ACOEM API (%Y-%m-%dT%H:%M:%S%z)

                measurement_container (dict): All data pertaining to
                measurement made at specifific time

                channel (str): Measurements made by different types of
                sensors in a station are split in to channels,
                these contain the four types of measurements seen in
                measurement_types

                flag_string (str): Occasionally multiple flags are
                returned for a measurement, these are reformatted as
                a single string with flags separated by commas

        """
        # Variables for later use
        day_end = day_start + dt.timedelta(days=period_length)
        location_keys = ["Latitude", "Longitude", "Altitude"]
        measurement_types = ["PreScaled", "Scaled", "Slope", "Offset"]

        data_req_link = (
            f'{self.auth_token["API"]}'
            f'{self.auth_token["Token"]}/{self.auth_token["License"]}/'
            f"stationdata/{day_start.isoformat()}/{day_end.isoformat()}/"
            f"{id}"
        )
        station_measurements = req.get(data_req_link)
        data_req_success = (
            station_measurements.status_code == 200
            and station_measurements.content not in b"NO DATA WAS FOUND FOR "
            b"YOUR GIVEN PARAMETERS"
        )

        # Only continue with station if data is returned
        # successfully
        if data_req_success:
            self.measurement_data[id] = list()
            for measurement in station_measurements.json():
                measurement_time = dt.datetime.strptime(
                    measurement["TBTimestamp"], "%Y-%m-%dT%H:%M:%S%z"
                )
                measurement_container = {
                    "time": measurement_time,
                    "measurement": "ACOEM UK Systems",
                    "fields": {},
                    "tags": {},
                }

                # Get location related variables and save
                for key in location_keys:
                    value = measurement[key]
                    if value is not None:
                        measurement_container["fields"][key] = float(value)

                # Get measurements
                for channel in measurement["Channels"]:
                    measurement_available = channel["PreScaled"] is not None
                    # If PreScaled value is None, no successful
                    # measurement recorded
                    if measurement_available:
                        for measurement_type in measurement_types:
                            measurement_container["fields"][
                                f'{channel["SensorName"]} '
                                f"{measurement_type} "
                                f'[{channel["UnitName"]}]'
                            ] = float(channel[measurement_type])

                        # Flags for measurements
                        # If valid flag present, assume others are
                        # redundant
                        if "Valid" in channel["Flags"]:
                            measurement_container["tags"][
                                f"{channel['SensorName']} Flag"
                            ] = "Valid"
                        else:
                            flag_string = channel["Flags"][0]
                            if len(channel["Flags"]) > 1:
                                for flag in channel["Flags"][1:]:
                                    flag_string = f"{flag_string}, {flag}"
                            measurement_container["tags"][
                                f"{channel['SensorName']} Flag"
                            ] = flag_string

                # Add metadata to measurement_container
                for status in list(self.station_meta[id].keys()):
                    measurement_container["tags"][status] = self.station_meta[id][
                        status
                    ]
                if len(list(measurement_container["fields"].keys())) != 0:
                    self.measurement_data[id].append(measurement_container)

    def dl_all_station_measurements(self, day_start, periodLength=1):
        """Downloads measurements made by all stations over a
        specified period from the ACOEM UK API.

        The function calculates the time period to download data for
        for all stations, downloads it and then iterates over
        each measurement, formatting each measurement in to a
        separate dict 'container' which has all measurement info.
        Once the container is populated, it is added to a list
        stored in measurement_data[id]. The container contains 4 keys:
            - "time": Time the measurement took place in datetime
                      format
            - "measurement": This will be the name of the measurement
                             if the data is written to InfluxDB,
                             currently hard coded as "ACOEM UK Systems"
            - "fields": All measurements made at "time"
            - "tags": All flags corresponding to measurement, as well
                      as station metadata

            Keyword arguments:
                day_start (datetime): Day to start downloading
                measurements from

                period_length (int): Number of days to download data
                for a single period, defaults to 1

            Variables:
                day_end (datetime): day_start + (period_length * 1 day)

                location_keys (list): Keys representing location flags
                in data

                measurement_types (list): The different measurement
                types made by a station that are stored by ACOEM UK API

                data_req_link (str): Link used to request measurements
                for a specific station across a specified time period

                station_measurements (http request): Raw return from
                ACOEM UK API

                data_req_success (bool): True if measurements returned
                successfully, False if connection couldn't be made or
                no data is present for specified station for specified
                time range

                measurement_time (datetime): Datetime format for when
                measurement was made, converted from string format used
                in ACOEM API (%Y-%m-%dT%H:%M:%S%z)

                measurement_container (dict): All data pertaining to
                measurement made at specifific time

                channel (str): Measurements made by different types of
                sensors in a station are split in to channels,
                these contain the four types of measurements seen in
                measurement_types

                flag_string (str): Occasionally multiple flags are
                returned for a measurement, these are reformatted as
                a single string with flags separated by commas

        """
        # Variables for later use
        station_IDs = list(self.station_meta.keys())
        day_end = day_start + dt.timedelta(days=1)
        location_keys = ["Latitude", "Longitude", "Altitude"]
        measurement_types = ["PreScaled", "Scaled", "Slope", "Offset"]

        # Loop over every station ID available to user
        for id in station_IDs:
            dataRequestLink = (
                f'{self.auth_token["API"]}'
                f'{self.auth_token["Token"]}/{self.auth_token["License"]}/'
                f"stationdata/{day_start.isoformat()}/{day_end.isoformat()}/"
                f"{id}"
            )
            station_measurements = req.get(dataRequestLink)
            data_req_success = (
                station_measurements.status_code == 200
                and station_measurements.content not in b"NO DATA WAS FOUND FOR "
                b"YOUR GIVEN PARAMETERS"
            )

            # Only continue with station if data is returned
            # successfully
            if data_req_success:
                self.measurement_data[id] = list()
                for measurement in station_measurements.json():
                    measurement_time = dt.datetime.strptime(
                        measurement["TBTimestamp"], "%Y-%m-%dT%H:%M:%S%z"
                    )
                    measurement_container = {
                        "time": measurement_time,
                        "measurement": "ACOEM UK Systems",
                        "fields": {},
                        "tags": {},
                    }

                    # Get location related variables and save
                    for key in location_keys:
                        value = measurement[key]
                        if value is not None:
                            measurement_container["fields"][key] = float(value)

                    # Get measurements
                    for channel in measurement["Channels"]:
                        measurement_available = channel["PreScaled"] is not None
                        # If PreScaled value is None, no successful
                        # measurement recorded
                        if measurement_available:
                            for measurement_type in measurement_types:
                                measurement_container["fields"][
                                    f'{channel["SensorName"]} '
                                    f"{measurement_type} "
                                    f'[{channel["UnitName"]}]'
                                ] = float(channel[measurement_type])

                            # Flags for measurements
                            # If valid flag present, assume others are
                            # redundant
                            if "Valid" in channel["Flags"]:
                                measurement_container["tags"][
                                    f"{channel['SensorName']} Flag"
                                ] = "Valid"
                            else:
                                flag_string = channel["Flags"][0]
                                if len(channel["Flags"]) > 1:
                                    for flag in channel["Flags"][1:]:
                                        flag_string = f"{flag_string}, {flag}"
                                measurement_container["tags"][
                                    f"{channel['SensorName']} Flag"
                                ] = flag_string

                    # Add metadata to measurement_container
                    for status in list(self.station_meta[id].keys()):
                        measurement_container["tags"][status] = self.station_meta[id][
                            status
                        ]
                    if len(list(measurement_container["fields"].keys())) != 0:
                        self.measurement_data[id].append(measurement_container)

    def get_measurement_data(self):
        """Returns measurement data

        This function is safer to use than just calling
        instance.measurement_data in the main function as no accidental
        modification can occur using this method.

            Returns:
                measurement_data class attribute as dict

        """
        return self.measurement_data.copy()

    def get_metadata(self):
        """Returns metadata

        This function is safer to use than just calling
        instance.station_meta in the main function as no accidental
        modification can occur using this method.

            Returns:
                station_meta class attribute as dict

        """
        return self.station_meta.copy()

    def get_key_classifications(self, id):
        """Classified keys as either measurements or tags in a dictionary

        This function classifies the different keys in the measurement container by whether they are a tag or a field. This makes things simpler for saving the measurements as a csv.

        Keyword arguments:
            id (str): The id of the sensor to classify keys for

        Variables:
            keys (dict): Classifcations for returned values as fields or tags

        Returns:
            keys
        """
        keys = {"fields": list(), "tags": list()}
        # Loop over all measurements and add field and tag keys to respective keys categories if not already present
        for measurement in self.measurement_data[id]:
            for field in list(measurement["fields"].keys()):
                if field not in keys["fields"]:
                    keys["fields"].append(field)
            for tag in list(measurement["tags"].keys()):
                if tag not in keys["tags"]:
                    keys["tags"].append(tag)
        return keys

    def format_as_csv(self, id, keys):
        """Formats measurement data as csv file

        Reads through measurements and sorts them into columns for a csv file. Cells are left blank if no value is present.

        Keyword Arguments:
            id (str): The id of the sensor to format measurements for

            keys (dict): Keys returned by ACOEM UK API categorised as either measurements or tags

        Variables:
            variables_measured (dict): The pollutants/system stats measured (e.g CO2) represented by key, with the value being the units

            extra_tags (list): Tags which aren't related to a measurement (e.g position, serial number)

            cav_header (list): Column headers for csv file

            measurement_order (list): The order different measurement types should go in

            csv_raw (str): Raw string format of csv file

            measurements (list): Copy of measurement container list, needs to be reversed to be in chronological order

        Returns:
            csv_raw (str) with all measurements formatted
        """
        variables_measured = dict()
        extra_tags = list()
        csv_header = ["Timestamp"]
        measurement_order = ["PreScaled", "Scaled", "Flag", "Slope", "Offset"]
        csv_raw = ""
        measurements = self.measurement_data[id].copy()
        measurements.reverse()  # This needs to be reversed for timestamp to be in order
        for field in keys["fields"]:
            prescaled_index = field.find("PreScaled")
            if prescaled_index != -1:
                unit_index = field.find("[")
                variables_measured[field[: prescaled_index - 1]] = field[unit_index:]
        for classification in ["fields", "tags"]:
            for tag in keys[classification]:
                if (
                    tag.find("[") == -1 and tag.find("Flag") == -1
                ):  # If [ is present it's a measurement and belongs in variables_measured. We're trying to find everything else. Flag's are also excluded as we look for them later too.
                    extra_tags.append(tag)
        for variable in list(variables_measured.keys()):
            for measurement_type in measurement_order:
                unit = (
                    f" {variables_measured[variable]}"
                    if measurement_type not in ["Flag"]
                    else ""
                )
                csv_header.append(f"{variable} {measurement_type}{unit}")
        for extra_tag in extra_tags:
            csv_header.append(extra_tag)
        csv_raw = f"{csv_header[0]}"
        for column in csv_header[1:]:
            csv_raw = f"{csv_raw}, {column}"
        csv_raw = f"{csv_raw}\n"
        # Start of measurements
        for measurement in measurements:
            csv_raw = f"{csv_raw}{measurement['time'].strftime('%Y-%m-%d %H:%M:%S')}"
            combined_values = {
                **measurement["fields"],
                **measurement["tags"],
            }  # Python 3.5 or later
            measurement_keys = list(combined_values.keys())
            field_keys = list(measurement["fields"].keys())
            for key in csv_header[1:]:
                if key in measurement_keys and key in field_keys:
                    value = combined_values[key]
                elif key in measurement_keys:
                    value = f'"{combined_values[key]}"'
                else:
                    value = ""
                csv_raw = f"{csv_raw}, {value}"
            csv_raw = f"{csv_raw}\n"
        return csv_raw

    def format_as_json(self, id):
        """Formats measurement data as json file

        Reads through measurements and separates them by timestamp in json format

        Keyword Arguments:
            id (str): The id of the sensor to format measurements for

        Variables:
            measurements (list): Copy of measurement container list, needs to be reversed to be in chronological order

            json_measurements (dict): Container for measurements in json format

        Returns:
            json_measurements (dict)
        """
        measurements = self.measurement_data[id].copy()
        measurements.reverse()  # This needs to be reversed for timestamp to be in order
        json_measurements = dict()
        for measurement in measurements:
            container = dict()
            timestamp = measurement["time"].strftime("%Y-%m-%dT%H:%M:%S%z")
            container["Data"] = measurement["fields"]
            container["Status"] = measurement["tags"]
            json_measurements[timestamp] = container
        return json_measurements

    def clear_measurements(self):
        """Clears measurement data

        Empties measurement_data dict, meaning measurements over new
        period can be taken without having to reinitialise class and
        redownload metadata etc

        """
        self.measurement_data = dict()
