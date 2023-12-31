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



app_name = "simple_task_manager"

str_code = "utf-8"

permission = 0o764

script_path = os.path.dirname(__file__)
task_folder_path = script_path + "/task"

if 'REQUEST_URI' in os.environ:
    REQUEST_URL = os.environ['REQUEST_URI']
else:
    # IIS用
    REQUEST_URL = os.environ['PATH_INFO']



cgitb.enable(display=1, logdir=None, context=5, format='html')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
form = cgi.FieldStorage()
mode = form.getfirst("mode", '')
q_category = form.getfirst("category", '')

edit_task_id = form.getfirst('edit_task_id', '')
delete_task_id = form.getfirst('delete_task_id', '')

# 更新用
update_task_id = form.getfirst('update_task_id', '')
update_update_datetime = form.getfirst('update_update_datetime', '')
update_state_select = form.getfirst('update_state_select', '')
update_category_input = form.getfirst('update_category_input', '')
update_task_name = form.getfirst('update_task_name', '')
update_content = form.getfirst('update_content', '')

# 作成用
create_task_id = form.getfirst('create_task_id', '')
create_create_datetime = form.getfirst('create_create_datetime', '')
create_update_datetime = form.getfirst('create_update_datetime', '')
create_state_select = form.getfirst('create_state_select', '')
create_category_input = form.getfirst('create_category_input', '')
create_task_name = form.getfirst('create_task_name', '')
create_content = form.getfirst('create_content', '')



# タスク情報の読み込み
def getStatus(url, mode):
    result = {}
    config = configparser.ConfigParser()
    config.read(url + '/config.ini', encoding=str_code)

    result['create_date'] = config['DATA']['CREATE_DATA']
    result['update_date'] = config['DATA']['UPDATE_DATA']

    if config['STATUS']['STATUS'] == 'CONTINUE':
        result['status'] = '継続'
        result['card_color'] = ""
    elif config['STATUS']['STATUS'] == 'COMPLETE':
        result['status'] = '完了'
        result['card_color'] = " text-bg-secondary"
    else:
        result['status'] = '状態不明'

    result['name'] = config['STATUS']['NAME']

    if "CATEGORY" in map(lambda x:x[0].upper(), config.items("STATUS")):
        result['category'] = config['STATUS']['CATEGORY']
    else:
        result['category'] = ""

    f = open(url + '/contents.txt', 'r', encoding=str_code)
    if mode == "index":
        result['content'] = f.read().replace('\n', '<br>')
    elif mode == "edit":
        result['content'] = f.read()

    f.close()

    return result

# カテゴリー一覧を作成
def getCategoryList():
    result = []
    files_file = [f for f in os.listdir(task_folder_path) if os.path.isdir(os.path.join(task_folder_path, f))]
    if len(files_file) > 0:
        for file in files_file:
            config = configparser.ConfigParser()
            config.read(task_folder_path+'/'+file + '/config.ini', encoding=str_code)
            if "CATEGORY" in map(lambda x:x[0].upper(), config.items("STATUS")):
                if config['STATUS']['CATEGORY'] != "":
                    if config['STATUS']['CATEGORY'] not in result:
                        result.append(config['STATUS']['CATEGORY'])
    return result

def header():
    print(f"""
<html lang="ja">
    <head>
        <meta charset="UTF-8">
        <link rel="stylesheet" href="./css/bootstrap.css">
        <script src="./js/bootstrap.bundle.js"></script>
        <title>{app_name}</title>
    </head>
    <body>
""")

def nav():
    categorys = getCategoryList()
    print(f"""
        <nav class="navbar navbar-expand-lg navbar-light bg-light">
            <div class="container-fluid">
                <a class="navbar-brand" href="./index.py">{app_name}</a>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav">
                        <li class="nav-item">
                            <a class="nav-link" href="./index.py?mode=create">新規作成</a>
                        </li>
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">カテゴリー</a>
                            <ul class="dropdown-menu">
""")
    for category in categorys:
        print(f"""
                                <li><a class="dropdown-item" href="./index.py?category={category}">{category}</a></li>
""")
    print("""
                            </ul>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>
""")


def footer():
    print("""
        <script>
            function confirmDelete(link){
                let result = confirm("本当に削除しますか？");
                if(result){
                    window.location.href = link.href;
                }else{
                    return false;
                }
            }
        </script>
    </body>
</html>
""")

if __name__ == '__main__':
    print('Content-type: text/html; charset=UTF-8\r\n')
    # 一覧画面

    if mode == '':
        files_file = [f for f in os.listdir(task_folder_path) if os.path.isdir(os.path.join(task_folder_path, f))]

        content = ""
        categorys = []
        if len(files_file) > 0:
            for file in files_file:
                status = {}
                status = getStatus(task_folder_path+'/'+file+'/', "index")

                temp = ""
                temp = """
        <div class="container">
            <div class="card{card_color}">
                <div class="card-body">
                    <h2 class="card-title">
                        {task_name}
                    </h2>
                    <h5 class="card-subtitle">
                        作成日:{create} 更新日:{update} 状態:{status} カテゴリー:{category}
                    </h5>
                    <div class="card-text border">
                        {content}
                    </div>
                    <a href="./index.py?mode=edit&edit_task_id={file}" class="btn btn-primary">編集</a>
                    <a href="./index.py?mode=delete&delete_task_id={file}" class="btn btn-danger" onclick="return confirmDelete(this);">削除</a>
                </div>
            </div>
        </div>
                """.format(card_color=status['card_color'], file=file, task_name=status['name'], create=datetime.datetime.strptime(status['create_date'], '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d %H:%M:%S'), update=datetime.datetime.strptime(status['update_date'], '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d %H:%M:%S'), content=status['content'], status=status['status'], category=status['category'])

                if q_category == "":
                    content += temp
                else:
                    if q_category == status['category']:
                        content += temp
        else:
            content = """
        <div class="container">
            <div class="card">
                <div class="card-body">
                    <div class="card-text">
                        Task not found
                    </div>
                </div>
            </div>
        </div>
"""
        header()
        nav()
        print(content)
        footer()

# 編集画面 --------------------------------------------------------------------------------------------
    elif mode=="edit":
        status = {}
        status = getStatus(script_path + '/task/'+edit_task_id+'/', "edit")

        status_str = ''
        if status["status"] == '継続':
            status_html = """
<label for="inputState" class="">状態</label>
<select id="inputState" class="" name="update_state_select">
    <option selected value="CONTINUE">継続</option>
    <option value="COMPLETE">完了</option>
</select>
"""
        elif status["status"] == '完了':
            status_html = """
<label for="inputState" class="">状態</label>
<select id="inputState" class="" name="update_state_select">
    <option value="CONTINUE">継続</option>
    <option selected value="COMPLETE">完了</option>
</select>
"""
        else:
            # status_str = '状態不明'
            status_html = """
<label for="inputState" class="">状態</label>
<select id="inputState" class="" name="update_state_select">
    <option selected value="CONTINUE">継続</option>
    <option value="COMPLETE">完了</option>
</select>
"""

        create_html = f"""
作成日 : {datetime.datetime.strptime(status["create_date"], "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")}
"""
        update_html = f"""
<input type="hidden" name="update_update_datetime" value="{datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}">更新時間 : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        category_html = f"""
カテゴリー：<input type="text" name="update_category_input" value="{status["category"]}"/>"""

        header()
        nav()

        print("""
        <div class="container mh-100">
            <form>
                <div class="card h-100">
                    <div class="card-body h-100">
                        <h2 class="card-title" style="height: 5%">
                        {task_name}
                        </h2>
                        <h5 class="card-subtitle" style="height: 5%">
                        {create_html} {update_html} {status_html} {category_html}
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
        </div>
        """.format(edit_task_id=edit_task_id, task_name=status["name"], create_html=create_html, update_html=update_html, status_html=status_html, category_html=category_html, content=status["content"]))

        footer()

# 更新処理 --------------------------------------------------------------------------------------------
    elif mode=="update":
        f = open(script_path + '/task/'+update_task_id+'/contents.txt', 'w', encoding=str_code)
        f.write(str(update_content).replace('\r\n', '\n'))
        f.close()

        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(script_path + '/task/'+update_task_id+'/config.ini', encoding=str_code)
        config['DATA']['UPDATE_DATA'] = update_update_datetime
        config['STATUS']['STATUS'] = update_state_select
        config['STATUS']['CATEGORY'] = update_category_input
        with open(script_path + '/task/'+update_task_id+'/config.ini', mode='w', encoding=str_code) as write_config:
            config.write(write_config)
        url = ("http://" + os.environ['HTTP_HOST'] + REQUEST_URL).split("?")[0]
        print("<meta http-equiv=\"refresh\" content=\"0;URL="+url+"\">")

# 作成画面 --------------------------------------------------------------------------------------------
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
        category_html = f"""
カテゴリー：<input type="text" name="create_category_input" value=""/>"""

        header()
        nav()

        print("""
        <div class="container mh-100">
            <form>
                <div class="card h-100">
                    <div class="card-body h-100">
                        <h2 class="card-title" style="height: 5%">
                            <input type="hidden" name="create_task_id" value="{uuid}" />
                            タスク名<input type="text" name="create_task_name"></input>
                        </h2>
                        <h5 class="card-subtitle" style="height: 5%">
                        {create_html} {update_html} {status_html} {category_html}
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
        </div>
        """.format(uuid=uuid.uuid4(),create_html=create_html, update_html=update_html, status_html=status_html, category_html=category_html))

        footer()
        
# 作成処理 --------------------------------------------------------------------------------------------
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
        config.set("STATUS", 'CATEGORY', create_category_input)

        with open(script_path + '/task/'+create_task_id+'/config.ini', mode='w', encoding=str_code) as write_config:
            config.write(write_config)

        # 権限の変更
        os.chmod(script_path + '/task/'+create_task_id, permission)
        os.chmod(script_path + '/task/'+create_task_id+'/config.ini', permission)
        os.chmod(script_path + '/task/'+create_task_id+'/contents.txt', permission)

        url = ("http://" + os.environ['HTTP_HOST'] + REQUEST_URL).split("?")[0]
        print("<meta http-equiv=\"refresh\" content=\"0;URL="+url+"\">")

# 削除処理 --------------------------------------------------------------------------------------------
    elif mode=="delete":
        shutil.rmtree(script_path + '/task/'+delete_task_id)
        url = ("http://" + os.environ['HTTP_HOST'] + REQUEST_URL).split("?")[0]
        print("<meta http-equiv=\"refresh\" content=\"0;URL="+url+"\">")
