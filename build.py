#!/usr/bin/env python3
import shutil
import zipapp
import os


root_copy =[
    'LICENSE',
    "README.md",
    "req.txt"
]

shutil.rmtree("build",ignore_errors=True)

shutil.copytree('src',"build/temp")

for c in root_copy:
    shutil.copy2(c, 'build/temp')

#remove pycache dirs
[shutil.rmtree(os.path.join(root, '__pycache__')) for root, dirs, files in os.walk('build') if '__pycache__' in dirs]

zipapp.create_archive(
    "build/temp",
    "build/nrc-wrapper.pyz",
    interpreter='/usr/bin/env python3'
)