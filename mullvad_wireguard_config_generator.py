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
import sys
import pprint

MULLVAD_SERVER_LIST_ENDPOINT = "https://api.mullvad.net/www/relays/all/"
ADDRESS = "10.555.555.555/32,fc00:bbbb:bbbb:bb01::5:511e/128"
PRIVATE_KEY = "PUT YOUR PRIVATE KEY HERE"
DNS = "1.1.1.1"
FILE_ILLEGAL_CHARS = r"/?:\<>*|#, "
CONFIG_DIRECTORY = f"{pathlib.Path().absolute()}\MullvadConfigs"

# A filter that returns unique providers for each city
# gives the server with the highest number
# Returns a list of servers
def filter_newest_unique_provider(server_data):
	server_with_numbers = []
	filtered_servers = {}

	#There *has* to be a better way to do this
	for server in server_data:
		country_code = server.get("country_code")
		city_server_number = server.get("hostname").replace("-wireguard", "").replace(country_code, "")
		server["city_server_number"] = city_server_number
		server_with_numbers.append(server)

	for server in server_with_numbers:
		server_num = 0
		server_city_name = server["city_name"]
		server_provider = server["provider"]
		server_string = f"{server_city_name}-{server_provider}"
		if server_string in filtered_servers:
			server_num = int(filtered_servers[server_string]["city_server_number"])
		
		if int(server["city_server_number"]) > server_num:
			filtered_servers[server_string] = server
	
	return list(filtered_servers.values())

# removes all characters that are illegal in windows filenames
def sanitise_string(text): 
	return text.translate({ord(c): None for c in FILE_ILLEGAL_CHARS})

# removes all FILES in a given directory
def remove_all_files_in_directory(directory): 
	for root, dirs, files in os.walk(directory):
		for file in files:
			os.remove(os.path.join(root, file))

# given a server json, make a config file from it
def save_config_to_file(jsondata): 
	servername = jsondata.get('hostname').replace("-wireguard", "")
	#city_code = jsondata.get('city_code')
	city_code = jsondata.get('city_name')
	provider = jsondata.get('provider')

	filename = f"{servername}-{city_code}-{provider}.conf"
	filename = sanitise_string(filename)
	configstring = generate_wireguard_config(jsondata)

	with open(f"{CONFIG_DIRECTORY}\{filename}", "w", encoding="utf-8") as outfile:
		outfile.write(f"{configstring}")

# generates a wireguard config string, given a server json
def generate_wireguard_config(jsondata): 
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
	# remove all old config files
	remove_all_files_in_directory(CONFIG_DIRECTORY) 

	server_data_request = requests.get(MULLVAD_SERVER_LIST_ENDPOINT, timeout=(11,30))
	server_data_request.raise_for_status()

	server_data = server_data_request.json()

	wireguard_servers = [server for server in server_data if server.get("type") == "wireguard"]
	
	# Filter out to unique providers/city only
	#filtered_servers = filter_newest_unique_provider(wireguard_servers)
	filtered_servers = wireguard_servers

	#print(wireguard_servers)
	for server_item in filtered_servers:
		save_config_to_file(server_item)

	print(f"Saved {len(filtered_servers)} config files to {CONFIG_DIRECTORY}")
