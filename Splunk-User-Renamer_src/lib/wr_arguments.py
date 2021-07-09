#!/usr/bin/env python3
##############################################################################################################
# Contact: Will Rivendell 
# 	E1: wrivendell@splunk.com
# 	E2: contact@willrivendell.com
##############################################################################################################

### Imports
import argparse

### CLASSES ###########################################

class LoadFromFile (argparse.Action):
	#Class for Loading Arguments in a file if wanted
	def __call__ (self, parser, namespace, values, option_string = None):
		with values as f:
			parser.parse_args(f.read().split(), namespace)

### FUNCTIONS ###########################################

def str2bool(string: str) -> bool:
	#Define common 'string values' for bool args to accept 'Yes' as well as 'True'
	if isinstance(string, bool):
		return(string)
	if string.lower() in ('yes', 'true', 't', 'y', '1'):
		return(True)
	elif string.lower() in ('no', 'false', 'f', 'n', '0'):
		return(False)
	else:
		raise argparse.ArgumentTypeError('Boolean value expected. True / False.')

def checkPositive(value: str) -> int:
	ivalue = int(value)
	if ivalue < 0:
		raise argparse.ArgumentTypeError('%s is an invalid (below 0) int value' % value)
	return ivalue

def Arguments():
	# Arguments the app will accept
	global parser
	parser = argparse.ArgumentParser()
	parser.add_argument("--file", type=open, action=LoadFromFile)
	parser.add_argument("-buf", "--backup_folder", nargs="?", default="./backup/", required=False, help="Relative to this script or full path to where backup folders and files will be copied to.")
	parser.add_argument("-csv", "--csv_folder", nargs="?", default="", required=False, help="Relative to this script or full path to csv file folder (not the file name itself) to read change map. Assumes column 0 is old names and 1 is new names.")
	parser.add_argument("-csv_h", "--csv_header", nargs="?", const=True, default="None", required=False, help="True or False whether CSV contains header fields or not.")
	parser.add_argument("-csv_old_col", "--csv_old_uname_col", type=checkPositive, nargs="?", default=0, required=False, help="Column number in CSV (left to right) old usernames are in. Default is 0 for FIRST column")
	parser.add_argument("-csv_new_col", "--csv_new_uname_col", type=checkPositive, nargs="?", default=1, required=False, help="Column number in CSV (left to right) new usernames are in. Default is 1 for SECOND column")
	parser.add_argument("-rsw", "--replace_starts_with", nargs="*", default=[], required=False, help="List of values the the original must have BEFORE the first char to be considered a match for replacement (N/A if match is the start of a string) (this helps avoid replacing substrings inside other strings that match the intended repalce) separated by spaces, i.e: '=' ':' ")
	parser.add_argument("-rew", "--replace_ends_with", nargs="*", default=[], required=False, help="List of values the the original must have AFTER the last char to be considered a match for replacement (this helps avoid replacing substrings inside other strings that match the intended repalce) separated by spaces, i.e: '=' ':' ")
	parser.add_argument("-up", "--uname_prefeix", nargs="?", default="", required=False, help="If CSV is not being used, you may mass rename users to have this prefix. If CSV is specified, this is ignored.")
	parser.add_argument("-us", "--uname_suffix", nargs="?", default="", required=False, help="If CSV is not being used, you may mass rename users to have this suffix. If CSV is specified, this is ignored.")
	parser.add_argument("-sph", "--splunk_home", nargs="?", default="/opt/splunk/", required=False, help="Full path to Splunk's install dir.")
	parser.add_argument("-ll", "--log_level", type=checkPositive, nargs="?", default=1, required=False, help="1-3, 1 being less, 3 being most")
	parser.add_argument("-fsl", "--file_search_list", nargs="*", default=[], required=False, help="List of values the filename must have in order to search in, separated by spaces, i.e: 'server.conf' 'prop' ")
	parser.add_argument("-fslt", "--file_search_list_type", type=str2bool, nargs="?", const=True, default=False, required=False, help="True for each item in file_search_list to have to be an exact match, False for contains. If using contains, search in can be lessened to wild cards like 'container' means '*container*'. Do NOT use *, they are implied. ")
	parser.add_argument("-figl", "--file_ignore_list", nargs="*", default=[], required=False, help="List of values the filename has to ignore AFTER search in list has finished, separated by spaces, i.e: 'server1.conf' 'props_' ")
	parser.add_argument("-figlt", "--file_ignore_list_type", type=str2bool, nargs="?", const=True, default=False, required=False, help="True for each item in file_ignore_list to have to be an exact match, False for contains. If using contains, search in can be lessened to wild cards like 'frozenda' means '*frozenda*'. Do NOT use *, they are implied. ")
	parser.add_argument("-fn", "--file_names", nargs="*", default=['local.meta'], required=False, help="List of file names to search in, separated by spaces. i.e: 'local.meta' 'authentication.conf'. User directories are handled by default, this is for file contents. ")
	parser.add_argument("-dm", "--debug_modules", type=str2bool, nargs="?", const=True, default=False, required=False, help="Will enable deep level debug on all the modules that make up the script. Enable if getting errors, to help dev pinpoint.")
	parser.add_argument("-tr", "--test_run", type=str2bool, nargs="?", const=True, default=False, required=False, help="If True, nothing will be modified, only reports what WOULD be modified. Logging is normal.")

############## RUNTIME
Arguments()
args = parser.parse_args()

# Dependency arg checks
if args.csv_folder:
	if args.csv_header == 'None':
		raise argparse.ArgumentTypeError('CSV Specified therefore -csv_h / --csv_header needs be specified as well, True or False.')
	else:
		args.csv_header = str2bool(args.csv_header)