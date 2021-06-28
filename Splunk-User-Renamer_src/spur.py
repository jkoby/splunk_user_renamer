#!/usr/bin/env python3
##############################################################################################################
# Contact: Will Rivendell 
# 	E1: wrivendell@splunk.com
# 	E2: contact@willrivendell.com
##############################################################################################################

### Imports ###########################################
import datetime, time, threading, sys, os, pandas

from lib import wr_arguments as arguments
from lib import wr_logging as log
from lib import wr_common as wrc

# Clear Function First
def clearConsole():
	if 'win' in sys.platform:
		os.system('cls')
	else:
		os.system('clear')

###########################################
# Globals
########################################### 
# log files
clearConsole()
main_log = 'spur'
log_file = log.LogFile(main_log, remove_old_logs=True, log_level=arguments.args.log_level, log_retention_days=10, debug=arguments.args.debug_modules)

# start easy timer for the overall operation - in standalone
spur_op_timer = wrc.timer('spur_timer', 600)
threading.Thread(target=spur_op_timer.start, name='spur_op_timer', args=(), daemon=False).start()

# normalize things
splunk_home = wrc.normalizePathOS(arguments.args.splunk_home)
splunk_user_folders = wrc.normalizePathOS(splunk_home + 'etc/users/')
if arguments.args.csv_folder:
	csv_path = wrc.normalizePathOS(arguments.args.csv_folder)
else:
	csv_path = ''

## master list of files and folders to be searched and modified
master_file_list = arguments.args.file_names #  file names specified by user used to get full paths
## full paths to the file names found
master_file_path_list = [] # main - used later
search_in = splunk_home,
for fn in master_file_list:
	found = wrc.findFileByName(fn, search_in, arguments.args.file_search_list, 
											arguments.args.file_search_list_type, 
											arguments.args.file_ignore_list, 
											arguments.args.file_ignore_list_type)
	if found[0]:
		for i in found[1]: # if full paths found add to master list
			master_file_path_list.append(i)

user_folders_list = os.listdir(splunk_user_folders) # main - used later
user_rename_dict = {} # main - used later
user_folder_failed_renames = []

# Print Console Info
print("\n")
print("- SPUR(" + str(sys._getframe().f_lineno) +"): --- Splunk User Renamer: Starting ---- \n")
print("- SPUR(" + str(sys._getframe().f_lineno) +"): --- Splunk User Renamer: Timer Started ---- \n")
print("- SPUR(" + str(sys._getframe().f_lineno) +"): Main Log Created at: ./logs/" + (main_log) + " -")
log_file.writeLinesToFile(["SPUR(" + str(sys._getframe().f_lineno) +"): --- Splunk User Renamer: Starting ----"])
print("\n")
if arguments.args.test_run:
	print("- SPUR(" + str(sys._getframe().f_lineno) +"): ########################################### -")
	print("- SPUR(" + str(sys._getframe().f_lineno) +"): TEST RUN - No actual changes will be made!! -")
	print("- SPUR(" + str(sys._getframe().f_lineno) +"): ########################################### -")
	log_file.writeLinesToFile(["SPUR(" + str(sys._getframe().f_lineno) +"): TEST RUN - No actual changes will be made."])

########################################### ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# Globals
###########################################

###########################################
# Runtime >>>
###########################################
# process csv or rename params
if not csv_path:
	prefix_or_suffix_specified = False
	uname_prefix = ''
	uname_suffix = ''
	if arguments.args.uname_prefix:
		uname_prefix = str(arguments.args.uname_prefix)
		prefix_or_suffix_specified = True
	if arguments.args.uname_suffix:
		uname_suffix = str(arguments.args.uname_suffix)
		prefix_or_suffix_specified = True
	if not prefix_or_suffix_specified:
		print("- SPUR(" + str(sys._getframe().f_lineno) +"): No CSV specified and no prefix or suffix specified, therefore nothing to do. Exiting. -")
		log_file.writeLinesToFile(["SPUR(" + str(sys._getframe().f_lineno) +"): No CSV specified and no prefix or suffix specified, therefore nothing to do. Exiting."])
		spur_op_timer.stop()
		sys.exit()
	else:
		print("- SPUR(" + str(sys._getframe().f_lineno) +"): No CSV specified, creating rename dict from prefix and suffix. -")
		log_file.writeLinesToFile(["SPUR(" + str(sys._getframe().f_lineno) +"): No CSV specified, creating rename dict from prefix and suffix."])
		user_rename_dict[uname_prefix]=uname_suffix
		for uname in user_folders_list:
			user_rename_dict[str(uname)]=uname_prefix + str(uname) + uname_suffix
else:
	print("- SPUR(" + str(sys._getframe().f_lineno) +"): CSV Specified, attempting to read. -")
	log_file.writeLinesToFile(["SPUR(" + str(sys._getframe().f_lineno) +"): CSV Specified, attempting to read."])
	try:
		df = pandas.read_csv(csv_path, header=None, engine='python')
		if arguments.args.csv_header:
			df = df.iloc[1:]
		df = df.iloc[:, arguments.args.csv_old_uname_col:arguments.args.csv_new_uname_col]
		user_rename_dict = df.set_index(0)[1].to_dict()
	except Exception as ex:
		print("- WRC(" + str(sys._getframe().f_lineno) + "): CSV Could not be read. Exiting. -")
		print(ex)
		log_file.writeLinesToFile(["(" + str(sys._getframe().f_lineno) + "): CSV Could not be read. Exiting."] )
		log_file.writeLinesToFile(["(" + str(sys._getframe().f_lineno) + "): " + str(ex)] )
		spur_op_timer.stop()
		sys.exit()

# startup checks
if not master_file_path_list:
	print("- SPUR(" + str(sys._getframe().f_lineno) +"): No file names found to search in for users. Exiting. -")
	log_file.writeLinesToFile(["SPUR(" + str(sys._getframe().f_lineno) +"): No file names found to search in for users. Exiting."])
	spur_op_timer.stop()
	sys.exit()

if not splunk_user_folders:
	print("- SPUR(" + str(sys._getframe().f_lineno) +"): No user folders found to rename. Exiting. -")
	log_file.writeLinesToFile(["SPUR(" + str(sys._getframe().f_lineno) +"): No user folders found to rename. Exiting."])
	spur_op_timer.stop()
	sys.exit()

# start renaming user folders
for u in user_folders_list:
	for k, v in user_rename_dict:
		if str(u) == str(k):
			if wrc.renameFolder(splunk_user_folders + str(k), splunk_user_folders + str(v), create_backup=True, backup_to=arguments.args.backup_folder, test_run=arguments.args.test_run):
				print("- SPUR(" + str(sys._getframe().f_lineno) +"): Original: " + splunk_user_folders + str(k))
				print("- SPUR(" + str(sys._getframe().f_lineno) +"): Renamed To: " + splunk_user_folders + str(v))
				log_file.writeLinesToFile(["SPUR(" + str(sys._getframe().f_lineno) +"): Original: " + splunk_user_folders + str(k)])
				log_file.writeLinesToFile(["SPUR(" + str(sys._getframe().f_lineno) +"): Renamed To: " + splunk_user_folders + str(v)])
			else:
				user_folder_failed_renames.append(splunk_user_folders + str(k))
print("- SPUR(" + str(sys._getframe().f_lineno) +"): Rename complete, successfuls will have a backup at: " + arguments.args.backup_folder + " -\n")
log_file.writeLinesToFile(["SPUR(" + str(sys._getframe().f_lineno) +"): Rename complete, successfuls will have a backup at: " + arguments.args.backup_folder])
print("- SPUR(" + str(sys._getframe().f_lineno) +"): The following user folders failed to backup: -" )
for i in user_folder_failed_renames:
	print("- SPUR(" + str(sys._getframe().f_lineno) +"):	" + i + " -" )
	log_file.writeLinesToFile(["SPUR(" + str(sys._getframe().f_lineno) +"):		" + i])

# start replacing usernames in files
# pre-flight reporting
print("- SPUR(" + str(sys._getframe().f_lineno) +"): The following files are being searched in for user renames. -")
log_file.writeLinesToFile(["SPUR(" + str(sys._getframe().f_lineno) +"): The following files are being searched in for user renames."])
for f in master_file_path_list:
	print("- SPUR(" + str(sys._getframe().f_lineno) +"):	- " + f + "-")
	log_file.writeLinesToFile(["SPUR(" + str(sys._getframe().f_lineno) +"): 	- " + f])
	wrc.replaceTextInFile(f, user_rename_dict, create_backup=True, backup_to=arguments.args.backup_folder, test_run=arguments.args.test_run, verbose_prints=True)
print("- SPUR(" + str(sys._getframe().f_lineno) +"): All specified file modifications complete, successfuls will have a backup at: " + arguments.args.backup_folder + " -")
print("- SPUR(" + str(sys._getframe().f_lineno) +"): Check 'wrc' log for details. -\n")
log_file.writeLinesToFile(["SPUR(" + str(sys._getframe().f_lineno) +"): All specified file modifications complete, successfuls will have a backup at: " + arguments.args.backup_folder])
log_file.writeLinesToFile(["SPUR(" + str(sys._getframe().f_lineno) +"): Check 'wrc' log for details."])


spur_op_timer.stop()
sys.exit()