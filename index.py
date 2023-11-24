# -*- coding: utf-8 -*-

import os
import io
import sys
import datetime
import configparser
import cgi
import cgitb
cgitb.enable(display=1, logdir=None, context=5, format='html')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
form = cgi.FieldStorage()
mode = form.getfirst("mode", '')
task = form.getfirst('task', '')
content = form.getfirst('content', '')
update_datetime = form.getfirst('update_datetime', '')
state_select = form.getfirst('state_select', '')

if __name__ == '__main__':
    print('Content-type: text/html; charset=UTF-8\r\n')
    if mode == '':
        task_folder_path = "./task"

        files_file = [f for f in os.listdir(task_folder_path) if os.path.isdir(os.path.join(task_folder_path, f))]

        print("""
<html lang="ja">
    <head>
        <meta charset="UTF-8">
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
                status = ''
                if config['STATUS']['STATUS'] == 'CONTINUE':
                    status = '継続'
                elif config['STATUS']['STATUS'] == 'COMPLETE':
                    status = '完了'
                else:
                    status = '状態不明'
                content=""
                f = open('./task/'+file+'/contents.txt', 'r', encoding='UTF-8')
                print("""
            <div class="card">
                <div class="card-body">
                    <h2 class="card-title">
                        {file}
                    </h2>
                    <h5 class="card-subtitle">
                        作成日:{create} 更新日:{update} 状態:{status}
                    </h5>
                    <div class="card-text border">
                        {content}
                    </div>
                    <a href="./index.py?mode=edit&task={file}" class="btn btn-primary">編集</a>
                </div>
            </div>
                """.format(file=file,create=datetime.datetime.strptime(config['DATA']['CREATE_DATA'], '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d %H:%M:%S'),update=datetime.datetime.strptime(config['DATA']['UPDATE_DATA'], '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d %H:%M:%S'),content=f.read().replace('\n', '<br>'), status=status))
        else:
            print("task not found")

        print("""
        </div>
    </body>
</html>
        """)
    elif mode=="edit":
        f = open('./task/'+task+'/contents.txt', 'r', encoding='UTF-8')
        content = f.read()
        f.close()
        config = configparser.ConfigParser()
        config.read('./task/'+task+'/config.ini', encoding='cp932')
        create = config['DATA']['CREATE_DATA']
        status = ''
        if config['STATUS']['STATUS'] == 'CONTINUE':
            status = '継続'
            status_html = """
<label for="inputState" class="">状態</label>
<select id="inputState" class="" name="state_select">
    <option selected value="CONTINUE">継続</option>
    <option value="COMPLETE">完了</option>
</select>
"""
        elif config['STATUS']['STATUS'] == 'COMPLETE':
            status = '完了'
            status_html = """
<label for="inputState" class="">状態</label>
<select id="inputState" class="" name="state_select">
    <option value="CONTINUE">継続</option>
    <option selected value="COMPLETE">完了</option>
</select>
"""
        else:
            status = '状態不明'
            status_html = """
<label for="inputState" class="">状態</label>
<select id="inputState" class="" name="state_select">
    <option selected value="CONTINUE">継続</option>
    <option value="COMPLETE">完了</option>
</select>
"""
        
        create_html = f"""
作成日 : {datetime.datetime.strptime(create, "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")}
"""
        update_html = f"""
<input type="hidden" name="update_datetime" value="{datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}">更新時間 : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

        print("""
<html>
    <head>
        <meta charset="UTF-8">
        <link rel="stylesheet" href="./css/bootstrap.css">
        <script src="./js/bootstrap.bundle.js"></script>
    </head>
    <body>
        <div class="container mh-100">
        """)
        print("""
            <form>
            <div class="card h-100">
                <div class="card-body h-100">
                    <h2 class="card-title" style="height: 5%">
                    {task}
                    </h2>
                    <h5 class="card-subtitle" style="height: 5%">
                    {create_html} {update_html} {status_html}
                    </h5>
                    <div class="card-text" style="height: 90%">
                        <div class="input-group" style="height: 90%">
                            <textarea class="form-control h-100" style="" name="content">{content}</textarea>
                        </div>
                        <div class="row align-items-end" style="height: 10%">
                            <div class="col">
                                <div class="d-grid gap-2">
                                    <input type="hidden" name="task" value="{task}" />
                                    <button type="submit" class="btn btn-primary btn-block" name="mode" value="update">編集ボタン</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            </form>
        """.format(task=task, create_html=create_html, update_html=update_html, status_html=status_html, content=content))
        print("""
        </div>
    </body>
</html>
        """)
    elif mode=="update":
        f = open('./task/'+task+'/contents.txt', 'w', encoding='UTF-8')
        f.write(str(content).replace('\r\n', '\n'))
        f.close()

        config = configparser.ConfigParser()
        config.optionxform = str
        config.read('./task/'+task+'/config.ini', encoding='cp932')
        config['DATA']['UPDATE_DATA'] = update_datetime
        config['STATUS']['STATUS'] = state_select
        with open('./task/'+task+'/config.ini', mode='w') as write_config:
            config.write(write_config)

        url = ("http://" + os.environ['HTTP_HOST'] + os.environ['REQUEST_URI']).split("?")[0]
        print("<meta http-equiv=\"refresh\" content=\"0;URL="+url+"\">")
