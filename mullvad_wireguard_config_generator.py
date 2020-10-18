# -*- coding: utf-8 -*-
"""
Usage: python3 mullvad_config_generator.py

Fetches all Wireguard servers from Mullvad's public API
Generates a wireguard .conf file for each Wireguard server
that Mullvad has available.

Config files are saved to /MullvadConfigs

This script is useful because you may set your own DNS
server, and I think it's faster and more convenient to
run this script to get the latest servers (and delete old
/retired ones). I also think the naming convention is better
for the config files are better
"""

import pathlib
import requests
import os

MULLVAD_SERVER_LIST_ENDPOINT = "https://api.mullvad.net/www/relays/all/"
ADDRESS = "10.0.0.1/32,fc00:bbbb:bbbb:bbbb::5:5/128"
PRIVATE_KEY = "IDfT7VrnvBWxX+XOk8DO0mo6VT2D3IJDsgAmMuCOGWs="
DNS = "1.1.1.1"
FILE_ILLEGAL_CHARS = r"/?:\<>*|#, "

CONFIG_DIRECTORY = f"{pathlib.Path().absolute()}\MullvadConfigs"

def sanitise_string(text): #removes all characters that are illegal in windows filenames
	return text.translate({ord(c): None for c in FILE_ILLEGAL_CHARS})

def remove_all_files_in_directory(directory): #removes all FILES in a given directory
	for root, dirs, files in os.walk(directory):
		for file in files:
			os.remove(os.path.join(root, file))

def save_config_to_file(jsondata): #given a server json, make a config file from it
	servername = jsondata.get('hostname').replace("-wireguard", "")
	#city_code = jsondata.get('city_code')
	city_code = jsondata.get('city_name')
	provider = jsondata.get('provider')

	filename = f"{servername}-{city_code}-{provider}.conf"
	filename = sanitise_string(filename)
	configstring = generate_wireguard_config(jsondata)

	with open(f"{CONFIG_DIRECTORY}\{filename}", "w", encoding="utf-8") as outfile:
		outfile.write(f"{configstring}")

def generate_wireguard_config(jsondata): #generates a wireguard config string, given a server json
	configstring = "[Interface]\n"
	configstring += f"PrivateKey = {PRIVATE_KEY}\n"
	configstring += f"Address = {ADDRESS}\n"
	configstring += f"DNS = {DNS}\n\n"
	configstring += "[Peer]\n"
	configstring += f"PublicKey = {jsondata['pubkey']}\n"
	configstring += "AllowedIPs = 0.0.0.0/0,::0/0\n"
	configstring += f"Endpoint = {jsondata['ipv4_addr_in']}:51820\n"

	return configstring

if __name__ == "__main__":
	pathlib.Path(f"{CONFIG_DIRECTORY}").mkdir(parents=True, exist_ok=True)
	remove_all_files_in_directory(CONFIG_DIRECTORY) #remove all old config files

	server_data_request = requests.get(MULLVAD_SERVER_LIST_ENDPOINT, timeout=(11,30))
	server_data_request.raise_for_status()

	server_data = server_data_request.json()

	for item in server_data:
		server_type = item.get("type")

		if server_type == "wireguard":
			#print(item)
			save_config_to_file(item)

	print(f"Saved {len(server_data)} config files to {CONFIG_DIRECTORY}")
