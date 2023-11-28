# -*- coding: utf-8 -*-

import os
import io
import sys
import datetime
import configparser
import cgi
import cgitb
import uuid
import shutil

cgitb.enable(display=1, logdir=None, context=5, format='html')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
form = cgi.FieldStorage()
mode = form.getfirst("mode", '')

edit_task_id = form.getfirst('edit_task_id', '')
delete_task_id = form.getfirst('delete_task_id', '')

update_task_id = form.getfirst('update_task_id', '')
update_update_datetime = form.getfirst('update_update_datetime', '')
update_state_select = form.getfirst('update_state_select', '')
update_task_name = form.getfirst('update_task_name', '')
update_content = form.getfirst('update_content', '')

create_task_id = form.getfirst('create_task_id', '')
create_create_datetime = form.getfirst('create_create_datetime', '')
create_update_datetime = form.getfirst('create_update_datetime', '')
create_state_select = form.getfirst('create_state_select', '')
create_task_name = form.getfirst('create_task_name', '')
create_content = form.getfirst('create_content', '')

str_code = "utf-8"

script_path = os.path.dirname(__file__)

if __name__ == '__main__':
    print('Content-type: text/html; charset=UTF-8\r\n')
    if mode == '':
        task_folder_path = script_path + "/task"

        files_file = [f for f in os.listdir(task_folder_path) if os.path.isdir(os.path.join(task_folder_path, f))]

        print("""
<html lang="ja">
    <head>
        <meta charset="UTF-8">
        <link rel="stylesheet" href="./css/bootstrap.css">
        <script src="./js/bootstrap.bundle.js"></script>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-light bg-light">
            <div class="container-fluid">
                <a class="navbar-brand" href="./index.py">simple_task_manager</a>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav">
                        <li class="nav-item">
                            <a class="nav-link" href="./index.py?mode=create">新規作成</a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>
        <div class="container">
""")

        if len(files_file) > 0:
            for file in files_file:
                config = configparser.ConfigParser()
                config.read(script_path + '/task/'+file+'/config.ini', encoding=str_code)
                status = ''
                if config['STATUS']['STATUS'] == 'CONTINUE':
                    status = '継続'
                elif config['STATUS']['STATUS'] == 'COMPLETE':
                    status = '完了'
                else:
                    status = '状態不明'

                task_name = config['STATUS']['NAME']

                content=""
                f = open(script_path + '/task/'+file+'/contents.txt', 'r', encoding=str_code)
                print("""
            <div class="card">
                <div class="card-body">
                    <h2 class="card-title">
                        {task_name}
                    </h2>
                    <h5 class="card-subtitle">
                        作成日:{create} 更新日:{update} 状態:{status}
                    </h5>
                    <div class="card-text border">
                        {content}
                    </div>
                    <a href="./index.py?mode=edit&edit_task_id={file}" class="btn btn-primary">編集</a>
                    <a href="./index.py?mode=delete&delete_task_id={file}" class="btn btn-danger">削除</a>
                </div>
            </div>
                """.format(file=file,task_name=task_name,create=datetime.datetime.strptime(config['DATA']['CREATE_DATA'], '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d %H:%M:%S'),update=datetime.datetime.strptime(config['DATA']['UPDATE_DATA'], '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d %H:%M:%S'),content=f.read().replace('\n', '<br>'), status=status))
        else:
            print("task not found")

        print("""
        </div>
    </body>
</html>
        """)
    elif mode=="edit":
        f = open(script_path + '/task/'+edit_task_id+'/contents.txt', 'r', encoding=str_code)
        content = f.read()
        f.close()
        config = configparser.ConfigParser()
        config.read(script_path + '/task/'+edit_task_id+'/config.ini', encoding=str_code)
        create = config['DATA']['CREATE_DATA']
        task_name = config['STATUS']['NAME']
        status = ''
        if config['STATUS']['STATUS'] == 'CONTINUE':
            status = '継続'
            status_html = """
<label for="inputState" class="">状態</label>
<select id="inputState" class="" name="update_state_select">
    <option selected value="CONTINUE">継続</option>
    <option value="COMPLETE">完了</option>
</select>
"""
        elif config['STATUS']['STATUS'] == 'COMPLETE':
            status = '完了'
            status_html = """
<label for="inputState" class="">状態</label>
<select id="inputState" class="" name="update_state_select">
    <option value="CONTINUE">継続</option>
    <option selected value="COMPLETE">完了</option>
</select>
"""
        else:
            status = '状態不明'
            status_html = """
<label for="inputState" class="">状態</label>
<select id="inputState" class="" name="update_state_select">
    <option selected value="CONTINUE">継続</option>
    <option value="COMPLETE">完了</option>
</select>
"""
        
        create_html = f"""
作成日 : {datetime.datetime.strptime(create, "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")}
"""
        update_html = f"""
<input type="hidden" name="update_update_datetime" value="{datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}">更新時間 : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

        print("""
<html>
    <head>
        <meta charset="UTF-8">
        <link rel="stylesheet" href="./css/bootstrap.css">
        <script src="./js/bootstrap.bundle.js"></script>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-light bg-light">
            <div class="container-fluid">
                <a class="navbar-brand" href="./index.py">simple_task_manager</a>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav">
                        <li class="nav-item">
                            <a class="nav-link" href="./index.py?mode=create">新規作成</a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>
        <div class="container mh-100">
            <form>
                <div class="card h-100">
                    <div class="card-body h-100">
                        <h2 class="card-title" style="height: 5%">
                        {task_name}
                        </h2>
                        <h5 class="card-subtitle" style="height: 5%">
                        {create_html} {update_html} {status_html}
                        </h5>
                        <div class="card-text" style="height: 90%">
                            <div class="input-group" style="height: 90%">
                                <textarea class="form-control h-100" style="" name="update_content">{content}</textarea>
                            </div>
                            <div class="row align-items-end" style="height: 10%">
                                <div class="col">
                                    <div class="d-grid gap-2">
                                        <input type="hidden" name="update_task_id" value="{edit_task_id}" />
                                        <button type="submit" class="btn btn-primary btn-block" name="mode" value="update">編集ボタン</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </form>
        """.format(edit_task_id=edit_task_id, task_name=task_name, create_html=create_html, update_html=update_html, status_html=status_html, content=content))
        print("""
        </div>
    </body>
</html>
        """)
    elif mode=="update":
        f = open(script_path + '/task/'+update_task_id+'/contents.txt', 'w', encoding=str_code)
        f.write(str(update_content).replace('\r\n', '\n'))
        f.close()

        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(script_path + '/task/'+update_task_id+'/config.ini', encoding=str_code)
        config['DATA']['UPDATE_DATA'] = update_update_datetime
        config['STATUS']['STATUS'] = update_state_select
        with open(script_path + '/task/'+update_task_id+'/config.ini', mode='w', encoding=str_code) as write_config:
            config.write(write_config)

        url = ("http://" + os.environ['HTTP_HOST'] + os.environ['REQUEST_URI']).split("?")[0]
        print("<meta http-equiv=\"refresh\" content=\"0;URL="+url+"\">")

    elif mode=="create":
        status_html = """
<label for="inputState" class="">状態</label>
<select id="inputState" class="" name="create_state_select">
    <option selected value="CONTINUE">継続</option>
    <option value="COMPLETE">完了</option>
</select>
"""
        create_html = f"""
<input type="hidden" name="create_create_datetime" value="{datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}">作成時間 : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        update_html = f"""
<input type="hidden" name="create_update_datetime" value="{datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}">更新時間 : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        print("""
<html>
    <head>
        <meta charset="UTF-8">
        <link rel="stylesheet" href="./css/bootstrap.css">
        <script src="./js/bootstrap.bundle.js"></script>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-light bg-light">
            <div class="container-fluid">
                <a class="navbar-brand" href="./index.py">simple_task_manager</a>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav">
                        <li class="nav-item">
                            <a class="nav-link" href="./index.py?mode=create">新規作成</a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>
        <div class="container mh-100">
        """)
        print("""
            <form>
            <div class="card h-100">
                <div class="card-body h-100">
                    <h2 class="card-title" style="height: 5%">
                        <input type="hidden" name="create_task_id" value="{uuid}" />
                        タスク名<input type="text" name="create_task_name"></input>
                    </h2>
                    <h5 class="card-subtitle" style="height: 5%">
                    {create_html} {update_html} {status_html}
                    </h5>
                    <div class="card-text" style="height: 90%">
                        <div class="input-group" style="height: 90%">
                            <textarea class="form-control h-100" style="" name="create_content"></textarea>
                        </div>
                        <div class="row align-items-end" style="height: 10%">
                            <div class="col">
                                <div class="d-grid gap-2">
                                    <button type="submit" class="btn btn-primary btn-block" name="mode" value="write">作成ボタン</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            </form>
        """.format(uuid=uuid.uuid4(),create_html=create_html, update_html=update_html, status_html=status_html))
        print("""
        </div>
    </body>
</html>
        """)
    elif mode=="write":
        os.mkdir(script_path + '/task/'+create_task_id)
        f = open(script_path + '/task/'+create_task_id+'/contents.txt', 'w', encoding=str_code)
        f.write(str(create_content).replace('\r\n', '\n'))
        f.close()

        config = configparser.ConfigParser()
        config.optionxform = str
        config.add_section("DATA")
        config.set("DATA", 'CREATE_DATA', create_create_datetime)
        config.set("DATA", 'UPDATE_DATA', create_create_datetime)
        config.add_section("STATUS")
        config.set("STATUS", 'NAME', create_task_name)
        config.set("STATUS", 'STATUS', create_state_select)

        with open(script_path + '/task/'+create_task_id+'/config.ini', mode='w', encoding=str_code) as write_config:
            config.write(write_config)

        url = ("http://" + os.environ['HTTP_HOST'] + os.environ['REQUEST_URI']).split("?")[0]
        print("<meta http-equiv=\"refresh\" content=\"0;URL="+url+"\">")

    elif mode=="delete":
        shutil.rmtree(script_path + '/task/'+delete_task_id)
        url = ("http://" + os.environ['HTTP_HOST'] + os.environ['REQUEST_URI']).split("?")[0]
        print("<meta http-equiv=\"refresh\" content=\"0;URL="+url+"\">")
