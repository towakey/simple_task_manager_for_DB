#!C:\Users\kyosg\AppData\Local\Programs\Python\Python38\python.exe
# -*- coding: utf-8 -*-

import os
import configparser

if __name__ == '__main__':
    task_folder_path = "./task"

    files_file = [f for f in os.listdir(task_folder_path) if os.path.isdir(os.path.join(task_folder_path, f))]

    print("Content-Type: text/html\n")
    print("""
<html>
    <head>
        <link rel="stylesheet" href="./css/bootstrap.css">
        <script src="./js/bootstrap.bundle.js"></script>
    </head>
    <body>
        <div class="container">
    """)

    if len(files_file) > 0:
        for file in files_file:
            config = configparser.ConfigParser()
            config.read('./task/'+file+'/config.ini')
            content=""
            f = open('./task/'+file+'/contents.txt', 'r', encoding='UTF-8')
            print("""
            <div class="card">
                <div class="card-body">
                    <h2 class="card-title">
                        {file}
                    </h2>
                    <h5 class="card-subtitle">
                        作成日:{create} 更新日:{update}
                    </h5>
                    <div class="card-text">
                        {content}
                    </div>
                </div>
            </div>
            """.format(file=file,create=config['DATA']['CREATE_DATA'],update=config['DATA']['UPDATE_DATA'],content=f.read()))
    else:
        print("task not found")

    print("""
        </div>
    </body>
</html>
    """)