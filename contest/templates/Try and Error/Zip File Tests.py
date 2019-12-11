import os
import zipfile
import subprocess

path = '/home/bruno/dev/pandora_V2/contest/templates/Try and Error/Files/dasdsas.zip'

dir_path = os.path.dirname(path)
dir_path_parts = dir_path.split('/')
immediate_before_dir = dir_path_parts[len(dir_path_parts) - 1]

print("\nFile path: " + path)

with zipfile.ZipFile(path, 'r') as ZIP:
    ZIP.extractall(dir_path)
    # ZIP.extractall(immediate_before_dir)
    # ZIP.extractall('tmp_ins')
file = open("/home/bruno/dev/pandora_V2/contest/templates/Try and Error/Files/dasdsas.zip", 'r')

# def check_output(command, cwd):
#     print('cwd = ' + cwd)
#     process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
#                                universal_newlines=True, cwd=cwd)
#     output = process.communicate()
#     retcode = process.poll()
#     print(output)
#     print(retcode)
#     return output, retcode
#
#
# def handle_zip_file(attempt, f, contest):
#     src_path = os.path.abspath(path)
#     src_base = os.path.basename(src_path)
#     submission_dir = os.path.dirname(src_path)
#
#     my_cmd = 'unzip ' + src_path
#     print('extraction: ' + my_cmd)
#     output, ret = check_output(my_cmd, submission_dir)
#
#     return