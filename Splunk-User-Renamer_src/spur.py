#!/usr/bin/env python3
##############################################################################################################
# Contact: Will Rivendell 
# 	E1: wrivendell@splunk.com
# 	E2: contact@willrivendell.com
##############################################################################################################

### Imports ###########################################
import threading, sys, os, re, pandas

from lib import wr_arguments as arguments
from lib import wr_logging as log
from lib import wr_common as wrc

###########################################
# Globals
########################################### 
# log files
wrc.clearConsole()
main_log = 'spur'
log_file = log.LogFile(main_log, remove_old_logs=True, log_level=arguments.args.log_level, log_retention_days=10, debug=arguments.args.debug_modules)

# start easy timer for the overall operation
spur_op_timer = wrc.timer('spur_timer', 600)
threading.Thread(target=spur_op_timer.start, name='spur_op_timer', args=(), daemon=False).start()

# normalize things
splunk_home = wrc.normalizePathOS(arguments.args.splunk_home)
splunk_user_folders_path = wrc.normalizePathOS(splunk_home + 'etc/users/')
if arguments.args.csv_folder:
	csv_path = wrc.normalizePathOS(arguments.args.csv_folder)
else:
	csv_path = ''

## master list of files and folders to be searched and modified
master_file_list = arguments.args.file_names #  file names to look in for username matches to replace. Specified by user in args-> used to get full file paths
## full paths to the file names found
master_file_path_list = [] # main - used later
search_in = splunk_home, # trailing comma is to make this a single item tuple as the function requires
for fn in master_file_list:
	found = wrc.findFileByName(fn, search_in, arguments.args.file_search_list, 
											arguments.args.file_search_list_type, 
											arguments.args.file_ignore_list, 
											arguments.args.file_ignore_list_type)
	if found[0]:
		for i in found[1]: # if full paths found add to master list
			master_file_path_list.append(i)

user_folders_list = os.listdir(splunk_user_folders_path) # main - used later
user_rename_dict = {} # main - used later
user_folder_failed_renames = []
email_regex = '^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]{2,}$' # used to check if usernames in csv match usernames in splunk when one may be email address and one may not be

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
# Globals - END
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
		print("- SPUR(" + str(sys._getframe().f_lineno) +"): No CSV folder specified and no prefix or suffix specified, therefore nothing to do. Exiting. -")
		log_file.writeLinesToFile(["SPUR(" + str(sys._getframe().f_lineno) +"): No CSV folder specified and no prefix or suffix specified, therefore nothing to do. Exiting."])
		spur_op_timer.stop()
		sys.exit()
	else:
		print("- SPUR(" + str(sys._getframe().f_lineno) +"): No CSV specified, creating rename dict from prefix and suffix. -")
		log_file.writeLinesToFile(["SPUR(" + str(sys._getframe().f_lineno) +"): No CSV specified, creating rename dict from prefix and suffix."])
		for uname in user_folders_list:
			user_rename_dict[str(uname)]=uname_prefix + str(uname) + uname_suffix
else:
	print("- SPUR(" + str(sys._getframe().f_lineno) +"): CSV Folder Specified, attempting to read. -")
	log_file.writeLinesToFile(["SPUR(" + str(sys._getframe().f_lineno) +"): CSV Folder Specified, attempting to read."])
	try:
		csv_folder_filenames = os.listdir(csv_path) # main - used later
		if not csv_folder_filenames:
			raise
		csv_df_list = []
		for csv in csv_folder_filenames:
			df = pandas.read_csv(csv_path + csv, header=None, engine='python')
			if arguments.args.csv_header:
				df = df.iloc[1:] # remove the header
			df = df.iloc[:, arguments.args.csv_old_uname_col:arguments.args.csv_new_uname_col] # we only want the two columns we care about (old and new unames)
			csv_df_list.append(df)
		df_full = pandas.concat(df_full, axis=0, ignore_index=True)
		user_rename_dict = df_full.set_index(0)[1].to_dict()
	except Exception as ex:
		print("- WRC(" + str(sys._getframe().f_lineno) + "): CSV Could not be read or processed. Exiting. -")
		print(ex)
		log_file.writeLinesToFile(["(" + str(sys._getframe().f_lineno) + "): CSV Could not be read or processed. Exiting."] )
		log_file.writeLinesToFile(["(" + str(sys._getframe().f_lineno) + "): " + str(ex)] )
		spur_op_timer.stop()
		sys.exit()

### startup checks
if not master_file_path_list:
	print("- SPUR(" + str(sys._getframe().f_lineno) +"): No file names found to search in for users. Exiting. -")
	log_file.writeLinesToFile(["SPUR(" + str(sys._getframe().f_lineno) +"): No file names found to search in for users. Exiting."])
	spur_op_timer.stop()
	sys.exit()

if not user_folders_list:
	print("- SPUR(" + str(sys._getframe().f_lineno) +"): No user folders found to rename. Exiting. -")
	log_file.writeLinesToFile(["SPUR(" + str(sys._getframe().f_lineno) +"): No user folders found to rename. Exiting."])
	spur_op_timer.stop()
	sys.exit()

# do a quick check to make sure the user didnt provide emaill addresses instead of usernames when users aren't email addresses or vice versa
for u in user_folders_list:
	orig_u_email_format = False
	if(re.search(email_regex, str(u))):
		orig_u_email_format = True
	for k, v in user_rename_dict:
		if not str(u) == str(k): # if uname doesnt match new uname
			if orig_u_email_format: # but original was an email address
				if not re.search(email_regex, str(k)): # provided original was not an email address
					new_k = k + '@' + u.split('@')[1] # add the email domain from the found splunk user to the provided original username and see if it matches now
				if str(u) == str(k): # if they match now, add the modified uname to the list instead
					print("- SPUR(" + str(sys._getframe().f_lineno) +"): Original: " + str(u) + " but non-email username: " + str(k) + " specified for replacement. Using email version.")
					log_file.writeLinesToFile(["SPUR(" + str(sys._getframe().f_lineno) +"): Original: " + str(u) + " but non-email username: " + str(k) + " specified for replacement. Using email version."])
					user_rename_dict[new_k] = user_rename_dict.pop(k)
			else:
				if re.search(email_regex, str(k)): # if splunk user doesnt have email address, strip it from the provided original which does and see if matches now
					new_k = k.split('@')[0]
				if str(u) == str(k): # if they match now, add the modified uname to the list instead
					print("- SPUR(" + str(sys._getframe().f_lineno) +"): Original: " + str(u) + " but email username: " + str(k) + " specified for replacement. Using non-email version.")
					log_file.writeLinesToFile(["SPUR(" + str(sys._getframe().f_lineno) +"): Original: " + str(u) + " but email username: " + str(k) + " specified for replacement. Using non-email version."])
					user_rename_dict[new_k] = user_rename_dict.pop(k)

# start renaming user folders
for u in user_folders_list:
	for k, v in user_rename_dict:
		if str(u) == str(k):
			if wrc.renameFolder(splunk_user_folders_path + str(k), splunk_user_folders_path + str(v), create_backup=True, backup_to=arguments.args.backup_folder, test_run=arguments.args.test_run):
				print("- SPUR(" + str(sys._getframe().f_lineno) +"): Original: " + splunk_user_folders_path + str(k))
				print("- SPUR(" + str(sys._getframe().f_lineno) +"): Renamed To: " + splunk_user_folders_path + str(v))
				log_file.writeLinesToFile(["SPUR(" + str(sys._getframe().f_lineno) +"): Original: " + splunk_user_folders_path + str(k)])
				log_file.writeLinesToFile(["SPUR(" + str(sys._getframe().f_lineno) +"): Renamed To: " + splunk_user_folders_path + str(v)])
			else:
				user_folder_failed_renames.append(splunk_user_folders_path + str(k))
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