""" Downloads data from ACOEM UK API, then optionally saves it in
csv/json format and/or writes it to an InfluxDB 2.0 database

This program communicates with the ACOEM UK API using an authorisation
token not provided with this software. It must be provided by ACOEM UK.
The software then determines the stations linked to the user's account,
downloads measurements made by each station for the stated time range
(iterating daily so as to not overwhelm the ACOEM UK server) and format
them as a csv file and/or a json file, both of which can be read by
InfluxDB v2.0. If the user requests it, the file can be saved locally
and can also be written to an InfluxDB v2.0 bucket.

    Command Line Arguments:
        -s/--start-date (str): Date to start downloading data from

        -e/--end-date (str): Date to terminate data download,
            program will not download data from this day

        -c/--config (str) [OPTIONAL]: Alternate path to config file

        -a/--auth (str) [OPTIONAL]: Alternate path to auth file

    Parameters:

"""

__author__ = "Idris Hayward"
__copyright__ = "2021, The University of Surrey & National Physical Laboratory"
__credits__ = ["Idris Hayward"]
__license__ = "GNU General Public License v3.0"
__version__ = "1.0"
__maintainer__ = "Idris Hayward"
__email__ = "j.d.hayward@surrey.ac.uk"
__status__ = "Stable Release"

import argparse
import json
import sys
import datetime as dt
import os

from modules.acoemapi import AcoemRequest
from modules.influxwrite import InfluxWriter
from modules.timetools import TimeCalculator


def parse_date_string(dateString):
    """Parses input strings in to date objects

    Keyword arguments:
        date_string (str): String to be parsed in to date object

    Variables:
        parsable_formats (list): List of formats recognised by
        the program. If none are suitable, the program informs
        the user of suitable formats that can be used instead

    Returns:
        Datetime object equivalent of input

    Raises:
        ValueError if input isn't in a suitable format

    """
    parsableFormats = ["%Y-%m-%d", "%Y/%m/%d", "%Y\\%m\\%d", "%Y.%m.%d"]
    for fmt in parsableFormats:
        try:
            return dt.datetime.strptime(dateString, fmt)
        except ValueError:
            pass
    raise ValueError(
        f'"{dateString}" is not in the correct format. Please'
        f" use one of the following:\n{parsableFormats}"
    )


def fancy_print(
    str_to_print,
    length=70,
    form="NORM",
    char="\U0001F533",
    end="\n",
    flush=False,
):
    """Makes strings output to the console look nicer

    This function is used to make the console output of python
    scripts look nicer. This function is used in a range of
    modules to save time in formatting console output.

        Keyword arguments:
            str_to_print (str): The string to be formatted and printed

            length (int): Total length of formatted string

            form (str): String indicating how 'str_to_print' will be
            formatted. The options are:
                'TITLE': Centers 'str_to_print' and puts one char at
                         each end
                'NORM': Left justifies 'str_to_print' and puts one char
                        at each end (Norm doesn't have to be specified,
                        any option not listed here has the same result)
                'LINE': Prints a line of 'char's 'length' long

            char (str): The character to print.

        Variables:
            length_slope (float): Slope used to adjust length of line.
            Used if an emoji is used for 'char' as they take up twice
            as much space. If one is detected, the length is adjusted.

            length_offset (int): Offset used to adjust length of line.
            Used if an emoji is used for 'char' as they take up twice
            as much space. If one is detected, the length is adjusted.

        Returns:
            Nothing, prints a 'form' formatted 'str_to_print' of
            length 'length'
    """
    length_adjust = 1
    length_offset = 0
    if len(char) > 1:
        char = char[0]
    if len(char.encode("utf-8")) > 1:
        length_adjust = 0.5
        length_offset = 1
    if form == "TITLE":
        print(
            f"{char} {str_to_print.center(length - 4, ' ')} {char}",
            end=end,
            flush=flush,
        )
    elif form == "LINE":
        print(
            char * int(((length) * length_adjust) + length_offset),
            end=end,
            flush=flush,
        )
    else:
        print(
            f"{char} {str_to_print.ljust(length - 4, ' ')} {char}",
            end=end,
            flush=flush,
        )


def get_json(path_to_json):
    """Finds json file and returns it as dict

    Creates blank file with required keys at path if json file is not
    present

        Keyword Arguments:
            path_to_json (str): Path to the json file, including
            filename and .json extension

        Returns:
            Dict representing contents of json file

        Raises:
            FileNotFoundError if file is not present, blank file created

            ValueError if file can not be parsed
    """

    try:
        with open(path_to_json, "r") as jsonFile:
            try:
                return json.load(jsonFile)
            except json.decoder.JSONDecodeError:
                raise ValueError(
                    f"{path_to_json} is not in the proper"
                    f"format. If you're having issues, consider"
                    f"using the template from the Github repo or "
                    f" use the format seen in README.md"
                )
    except FileNotFoundError:
        raise FileNotFoundError(
            f"{path_to_json} could not be found, use the "
            f"template from the Github repo or use the "
            f"format seen in README.md"
        )


def save_to_file(write_data, path_to_file, filename):
    """Saves data to file in specified path

    This format agnostic function saves a string of data to a specified file.
    File format and path to file are determined by keyword arguments,
    this just writes data (preferrably string format)

    Keyword Arguments:
        write_data (str): Data to be written to file, preferably in string
        format

        path_to_file (str): The path that the file will be created in,
        if it's not present it will be created

        filename (str): Name of file to write data to, please include file
        format e.g "filename.csv"

    """
    while not os.path.isdir(path_to_file):
        os.makedirs(path_to_file, exist_ok=True)
    with open(f"{path_to_file}/{filename}", "w") as newfile:
        newfile.write(write_data)


if __name__ == "__main__":
    # Parse incoming arguments
    arg_parser = argparse.ArgumentParser(
        description="Downloads data from "
        "ACOEM UK API, then optionally saves it in csv/json format "
        "and/or writes it to an InfluxDB 2.0 database. The following "
        "formats can be used for date strings: [YYYY-MM-DD, YYYY/MM/DD, "
        "YYYY\\MM\\DD, YYYY.MM.DD]"
    )
    arg_parser.add_argument(
        "-s",
        "--start-date",
        type=str,
        help="Date to start download from",
        default="N/A",
    )
    arg_parser.add_argument(
        "-e",
        "--end-date",
        type=str,
        help="Date to end download at, this date is not included in download",
        default="N/A",
    )
    arg_parser.add_argument(
        "-c",
        "--config",
        type=str,
        help="Alternate location for config json file (Defaults to "
        "./Settings/config.json)",
        default="Settings/config.json",
    )
    arg_parser.add_argument(
        "-a",
        "--auth",
        type=str,
        help="Alternate location for auth token json file (Defaults to "
        "./Settings/auth.json)",
        default="Settings/auth.json",
    )
    args = vars(arg_parser.parse_args())
    start_date_string = args["start_date"]
    end_date_string = args["end_date"]
    auth_path = args["auth"]
    config_path = args["config"]

    fancy_print("", form="LINE")
    fancy_print("ACOEM UK API Unofficial Download Tool", form="TITLE")
    fancy_print(f"Author:  {__author__}")
    fancy_print(f"Contact: {__email__}")
    fancy_print(f"Version: {__version__}")
    fancy_print(f"Status:  {__status__}")
    fancy_print(f"License: {__license__}")
    fancy_print("", form="LINE")

    # Raise error if either date is not provided and parse dates
    if "N/A" in [start_date_string, end_date_string]:
        raise ValueError(
            "One or more required dates not provided, "
            "please provide start (-s) and end (-e) date as arguments"
        )
    start_date = parse_date_string(start_date_string)
    end_date = parse_date_string(end_date_string)
    fancy_print(
        f'Downloading data from {start_date.strftime("%Y-%m-%d")} '
        f'until {end_date.strftime("%Y-%m-%d")}'
    )
    time_config = TimeCalculator(start_date, end_date)
    number_of_days = time_config.day_difference()
    fancy_print(f"- {number_of_days} days worth of data will be downloaded")
    # Get config and auth data
    config_settings = get_json(config_path)
    fancy_print(f"Imported settings from {config_path}")
    auth_token = get_json(auth_path)
    fancy_print(f"Imported authorisation token from {auth_path}")
    fancy_print("", form="LINE")

    # Debug stats
    if config_settings["Debug Stats"]:
        fancy_print(f"DEBUG STATS", form="TITLE")
        fancy_print(f"")
        fancy_print(f"config.json", form="TITLE")
        for key, item in config_settings.items():
            if len(str(item)) > 45:
                item = f"{item[:45]}..."
            fancy_print(f"{key}: {item}")
        fancy_print(f"")
        fancy_print(f"auth.json", form="TITLE")
        for key, item in auth_token.items():
            if len(str(item)) > 45:
                item = f"{item[:45]}..."
            fancy_print(f"{key}: {item}")
        fancy_print("", form="LINE")

    # Communicate with ACOEM UK API
    acoem_API = AcoemRequest(auth_token)
    fancy_print("Downloading station metadata")
    acoem_API.dl_station_meta()
    available_stations = list(acoem_API.get_metadata().keys())
    fancy_print(f"- {len(available_stations)} stations registered to account")
    fancy_print("", form="LINE")
    # Loop over days
    for day in range(number_of_days):
        day_start = start_date + dt.timedelta(days=day)
        # Download measurements
        fancy_print(
            f"Downloading measurements for "
            f'{day_start.strftime("%Y-%m-%d")} [Day {day+1} of '
            f"{number_of_days}]"
        )
        for index, station in enumerate(available_stations):
            fancy_print(
                f"- Downloading measurements for {station} "
                f"({index+1} of {len(available_stations)})",
                end="\r",
                flush=True,
            )
            acoem_API.dl_station_measurements(station, day_start)
        stations_with_data = list(acoem_API.get_measurement_data().keys())
        fancy_print(
            f"- {len(stations_with_data)} stations returned valid "
            f"measurements"
        )
        # Save local files
        if config_settings["File Format"] in ["csv", "json", "both"]:
            fancy_print("Saving local files")
        if config_settings["File Format"] in ["csv", "both"]:
            fancy_print(f"Saving files as csv")
            for index, station in enumerate(stations_with_data):
                fancy_print(
                    f"- Station {index + 1} of {len(stations_with_data)}"
                    f" [{station}]",
                    end="\r",
                    flush=True,
                )
                tags = acoem_API.get_key_classifications(station)
                raw_csv = acoem_API.format_as_csv(station, tags)
                csv_path = f"{config_settings['File Path']}/csv/{station}"
                csv_name = f"{day_start.strftime('%Y-%m-%d')}.csv"
                save_to_file(raw_csv, csv_path, csv_name)
            fancy_print(
                f"- Local data saved as csv for {len(stations_with_data)} "
                f"stations"
            )
        if config_settings["File Format"] in ["json", "both"]:
            fancy_print("Saving files as json")
            for index, station in enumerate(stations_with_data):
                fancy_print(
                    f"- Station {index + 1} of {len(stations_with_data)}" 
                    f" [{station}]",
                    end="\r",
                    flush=True,
                )
                raw_json = acoem_API.format_as_json(station)
                json_string = json.dumps(raw_json, sort_keys=True, indent=4)
                json_path = f"{config_settings['File Path']}/json/{station}"
                json_name = f"{day_start.strftime('%Y-%m-%d')}.json"
                save_to_file(json_string, json_path, json_name)
            fancy_print(
                f"- Local data saved as json for {len(stations_with_data)}" 
                f" stations"
            )
        # Upload to Influx database
        if config_settings["Write to Influx"]:
            fancy_print("Connecting to InfluxDB database")
            station_measurements = acoem_API.get_measurement_data()
            influx_writer = InfluxWriter(config_settings)
            fancy_print("- Connection established")
            fancy_print("Uploading measurements")
            for index, station in enumerate(stations_with_data):
                fancy_print(
                    f"- Station {index + 1} of {len(stations_with_data)}" 
                    f" [{station}]",
                    end="\r",
                    flush=True,
                )
                influx_writer.write_container_list(
                    station_measurements[station]
                )
            fancy_print("- Measurements successfully uploaded")
        # Delete measurements before loop begins anew
        acoem_API.clear_measurements()
        fancy_print("", form="LINE")

