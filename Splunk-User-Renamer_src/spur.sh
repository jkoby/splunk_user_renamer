#!/bin/bash
##############################################################################################################
# Contact: Will Rivendell 
# 	E1: wrivendell@splunk.com
# 	E2: contact@willrivendell.com
##############################################################################################################
### Python3
python3 spur.py \
    -buf './backups/' \
    -csv './csvs/' \
    -csv_h True \
    -csv_old_col 0 \
    -csv_new_col 1 \
    -rsw '=' ' ' '-' ':' '[' \
    -rew '=' ' ' '-' ':' ']' \
    -sph '/opt/splunk/' \
    -ll 3 \
    -fn 'default.meta' 'local.meta' 'authentication.conf' \
    -figl '/system/default/' \
    -figlt False \
    -dm True \
    -tr True

# SEE README FOR ARG DETAILS
# You should always try and use this version as it doesn't need any outside dependencies
# \  = indicates cmd continues on next line in bash
# -buf = --backup_folder | Relative to this script or full path to where backup folders and files will be copied to.
# -csv = --csv_folder | Relative to this script or full path to csv file folder (not the file name itself) to read change map. Assumes column 0 is old names and 1 is new names.
# -csv_h = --csv_header | True or False whether CSV contains header fields or not.
# -csv_old_col = --csv_old_uname_col | Column number in CSV (left to right) old usernames are in. Default is 0 for FIRST column
# -csv_new_col = --csv_new_uname_col | Column number in CSV (left to right) new usernames are in. Default is 1 for SECOND column
# -rsw = --replace_starts_with | List of values the original must have BEFORE the first char to be considered a match for replacement (N/A if match is the start of a string) (this helps avoid replacing substrings inside other strings that match the intended replace) separated by spaces, i.e: '=' ':' "). Don't use if replace all occurences blindly is desired
# -rew = --replace_ends_with | List of values the original must have AFTER the last char to be considered a match for replacement (this helps avoid replacing substrings inside other strings that match the intended replace) separated by spaces, i.e: '=' ':' "). Don't use if replace all occurences blindly is desired
# -up = --uname_prefeix | If CSV is not being used, you may mass rename users to have this prefix. If CSV is specified, this is ignored.
# -us = --uname_suffix | If CSV is not being used, you may mass rename users to have this suffix. If CSV is specified, this is ignored.
# -sph = --splunk_home | Full path to Splunk's install dir.
# -ll = --log_level | 1-3, 1 being less, 3 being most
# -fsl = --file_search_list | List of values the filename must have in order to search in, separated by spaces, i.e: 'server.conf' 'prop' 
# -fslt = --file_search_list_type | True for each item in file_search_list to have to be an exact match, False for contains. If using contains, search in can be lessened to wild cards like 'container' means '*container*'. Do NOT use *, they are implied. 
# -figl = --file_ignore_list | List of values the filename has to ignore AFTER search in list has finished, separated by spaces, i.e: 'server1.conf' 'props_' 
# -figlt = --file_ignore_list_type | True for each item in file_ignore_list to have to be an exact match, False for contains. If using contains, search in can be lessened to wild cards like 'frozenda' means '*frozenda*'. Do NOT use *, they are implied. 
# -fn = --file_names | List of file names to search in, separated by spaces. i.e: 'local.meta' 'test_file.conf'. User directories are handled by default, this is for file contents. 
# -dm = --debug_modules | Will enable deep level debug on all the modules that make up the script. Enable if getting errors, to help dev pinpoint.
# -tr = --test_run | If True, nothing will be modified, only reports what WOULD be modified. Logging is normal.