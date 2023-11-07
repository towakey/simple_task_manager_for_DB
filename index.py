# -*- coding: utf-8 -*-

import os

task_folder_path = "./task"

files_file = [f for f in os.listdir(task_folder_path) if os.path.isfile(os.path.join(task_folder_path, f))]

print("Content-Type: text/html\n")
print("""
<html>
    <head>
    </head>
    <body>
""")

if len(files_file) > 0:
    print("""
<ul>
    """)
    for file in files_file:
        print("<li>"+file+"</li>")
    print("""
</ul>
    """)
else:
    print("task not found")

print("""
    </body>
</html>
""")