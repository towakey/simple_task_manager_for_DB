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
import re



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
q_tag = form.getfirst("tag", '')  # タグによる絞り込み用
sort_by = form.getfirst("sort", 'update_date')  # デフォルトは更新日でソート
sort_order = form.getfirst("order", 'desc')  # デフォルトは降順

edit_task_id = form.getfirst('edit_task_id', '')
delete_task_id = form.getfirst('delete_task_id', '')
view_task_id = form.getfirst('view_task_id', '')  # タスク詳細表示用

# 更新用
update_task_id = form.getfirst('update_task_id', '')
update_update_datetime = form.getfirst('update_update_datetime', '')
update_state_select = form.getfirst('update_state_select', '')
update_category_input = form.getfirst('update_category_input', '')
update_task_name = form.getfirst('update_task_name', '')
update_content = form.getfirst('update_content', '')
update_pinned = form.getfirst('update_pinned', '') == 'on'  # チェックボックスの値を取得
update_tags = form.getfirst('update_tags', '')  # タグ入力用
update_担当者 = form.getfirst('update_担当者', '')
update_大分類 = form.getfirst('update_大分類', '')
update_中分類 = form.getfirst('update_中分類', '')
update_小分類 = form.getfirst('update_小分類', '')

# 作成用
create_task_id = form.getfirst('create_task_id', '')
create_create_datetime = form.getfirst('create_create_datetime', '')
create_update_datetime = form.getfirst('create_update_datetime', '')
create_state_select = form.getfirst('create_state_select', '')
create_category_input = form.getfirst('create_category_input', '')
create_task_name = form.getfirst('create_task_name', '')
create_content = form.getfirst('create_content', '')
create_pinned = form.getfirst('create_pinned', '') == 'on'  # チェックボックスの値を取得
create_tags = form.getfirst('create_tags', '')  # タグ入力用
create_担当者 = form.getfirst('create_担当者', '')
create_大分類 = form.getfirst('create_大分類', '')
create_中分類 = form.getfirst('create_中分類', '')
create_小分類 = form.getfirst('create_小分類', '')



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
        result['card_color'] = " bg-secondary"
    else:
        result['status'] = '状態不明'

    result['name'] = config['STATUS']['NAME']

    # ピン止めの状態を安全に取得
    try:
        result['pinned'] = config['STATUS'].getboolean('PINNED', fallback=False)
    except (configparser.Error, ValueError):
        result['pinned'] = False

    # タグを安全に取得
    try:
        tags_str = config['STATUS'].get('TAGS', fallback='')
        result['tags'] = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
    except (configparser.Error, ValueError):
        result['tags'] = []

    if "CATEGORY" in map(lambda x:x[0].upper(), config.items("STATUS")):
        result['category'] = config['STATUS']['CATEGORY']
    else:
        result['category'] = ""

    if "担当者" in map(lambda x:x[0].upper(), config.items("STATUS")):
        result['担当者'] = config['STATUS']['担当者']
    else:
        result['担当者'] = ""

    if "大分類" in map(lambda x:x[0].upper(), config.items("STATUS")):
        result['大分類'] = config['STATUS']['大分類']
    else:
        result['大分類'] = ""

    if "中分類" in map(lambda x:x[0].upper(), config.items("STATUS")):
        result['中分類'] = config['STATUS']['中分類']
    else:
        result['中分類'] = ""

    if "小分類" in map(lambda x:x[0].upper(), config.items("STATUS")):
        result['小分類'] = config['STATUS']['小分類']
    else:
        result['小分類'] = ""

    f = open(url + '/contents.txt', 'r', encoding=str_code)
    content = f.read()
    f.close()

    if mode == "index":
        # マークダウンリンクをHTMLリンクに変換
        content = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', content)
        result['content'] = content.replace('\n', '<br>')
    elif mode == "edit":
        result['content'] = content
    elif mode == "view":
        result['content'] = content

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
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
        <title>{app_name}</title>
        <style>
            body {{
                padding-top: 70px;
            }}
            .scrollable-dropdown-menu {{
                max-height: 70vh;
                overflow-y: auto;
            }}
        </style>
    </head>
    <body>
""")

def nav():
    categorys = getCategoryList()
    print(f"""
        <nav class="navbar navbar-expand-lg navbar-light bg-light fixed-top">
            <div class="container-fluid">
                <a class="navbar-brand" href="./index.py">{app_name}</a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav">
                        <li class="nav-item">
                            <a class="nav-link" href="./index.py?mode=create">新規作成</a>
                        </li>
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">カテゴリー</a>
                            <ul class="dropdown-menu scrollable-dropdown-menu">
""")
    for category in categorys:
        sort_params = f"&sort={sort_by}&order={sort_order}" if sort_by else ""
        print(f"""
                                <li><a class="dropdown-item" href="./index.py?category={category}{sort_params}">{category}</a></li>
""")
    print("""
                            </ul>
                        </li>
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">ソート</a>
                            <ul class="dropdown-menu scrollable-dropdown-menu">
                                <li><a class="dropdown-item" href="./index.py?sort=name&order=asc">タスク名 (昇順)</a></li>
                                <li><a class="dropdown-item" href="./index.py?sort=name&order=desc">タスク名 (降順)</a></li>
                                <li><hr class="dropdown-divider"></li>
                                <li><a class="dropdown-item" href="./index.py?sort=create_date&order=desc">作成日 (新しい順)</a></li>
                                <li><a class="dropdown-item" href="./index.py?sort=create_date&order=asc">作成日 (古い順)</a></li>
                                <li><hr class="dropdown-divider"></li>
                                <li><a class="dropdown-item" href="./index.py?sort=update_date&order=desc">更新日 (新しい順)</a></li>
                                <li><a class="dropdown-item" href="./index.py?sort=update_date&order=asc">更新日 (古い順)</a></li>
                                <li><hr class="dropdown-divider"></li>
                                <li><a class="dropdown-item" href="./index.py?sort=category&order=asc">カテゴリー (昇順)</a></li>
                                <li><a class="dropdown-item" href="./index.py?sort=category&order=desc">カテゴリー (降順)</a></li>
                                <li><hr class="dropdown-divider"></li>
                                <li><a class="dropdown-item" href="./index.py?sort=status&order=asc">状態 (継続→完了)</a></li>
                                <li><a class="dropdown-item" href="./index.py?sort=status&order=desc">状態 (完了→継続)</a></li>
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

        # タスク情報を取得してリストに格納
        tasks = []
        if len(files_file) > 0:
            for file in files_file:
                status = getStatus(task_folder_path+'/'+file+'/', "index")
                status['id'] = file
                tasks.append(status)

        # ソート処理
        if tasks:
            def get_sort_key(task):
                # 最初にピン止めされたタスクを上に
                pinned_priority = 0 if task['pinned'] else 1
                
                # 二次ソートのキーを取得
                if sort_by == 'name':
                    secondary_key = task['name'].lower()
                elif sort_by in ['create_date', 'update_date']:
                    secondary_key = datetime.datetime.strptime(task[sort_by], '%Y-%m-%dT%H:%M:%S')
                elif sort_by == 'category':
                    secondary_key = task['category'].lower()
                elif sort_by == 'status':
                    secondary_key = task['status']
                
                # 降順の場合は比較を反転
                if sort_order == 'desc' and sort_by in ['create_date', 'update_date']:
                    secondary_key = datetime.datetime.max - secondary_key
                elif sort_order == 'desc':
                    secondary_key = '~' + str(secondary_key)
                
                return (pinned_priority, secondary_key)
            
            # ソート実行
            tasks.sort(key=get_sort_key)

        content = ""
        if len(tasks) > 0:
            for task in tasks:
                if q_category == "" or q_category == task['category']:
                    if q_tag == "" or q_tag in task['tags']:
                        pin_icon_div = '<span class="fs-4">📌</span>' if task.get('pinned', False) else ''
                        temp = """
        <div class="container my-3">
            <div class="card{card_color} shadow-sm">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <div class="d-flex align-items-center">
                            <a href="./index.py?category={category}" class="text-decoration-none me-3">
                                <span class="badge bg-primary px-3 py-2 fs-6">
                                    <i class="bi bi-folder2-open"></i> {category}
                                </span>
                            </a>
                            <h2 class="card-title mb-0">
                                {task_name}
                            </h2>
                        </div>
                        <div>
                            {pin_icon_div}
                        </div>
                    </div>
                    
                    <div class="mt-2">
                        {tag_links}
                    </div>
                    <div class="card-text border p-3 bg-light my-3">
                        {content}
                    </div>
                    <!-- Task metadata with improved styling -->
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <span class="badge bg-info text-dark me-2">
                                <i class="bi bi-person-fill"></i> 担当者: {担当者}
                            </span>
                        </div>
                    </div>
                    
                    <div class="row mb-3">
                        <div class="col-md-12">
                            <small class="text-muted">
                                <i class="bi bi-calendar-check"></i> 更新日: {update} &nbsp;|&nbsp; 
                                <i class="bi bi-calendar-plus"></i> 発生日: {incident}
                            </small>
                        </div>
                    </div>
                    
                    <a href="./index.py?mode=edit&edit_task_id={file}" class="btn btn-primary">
                        <i class="bi bi-pencil"></i> 編集
                    </a>
                    <a href="./index.py?mode=view&view_task_id={file}" class="btn btn-info">
                        <i class="bi bi-eye"></i> 詳細
                    </a>
                    <a href="./index.py?mode=delete&delete_task_id={file}" class="btn btn-danger" onclick="return confirmDelete(this);">
                        <i class="bi bi-trash"></i> 削除
                    </a>
                </div>
            </div>
        </div>
                    """.format(
                        card_color=task['card_color'],
                        file=task['id'],
                        task_name=task['name'],
                        pin_icon_div=pin_icon_div,
                        incident=datetime.datetime.strptime(task.get('発生日', task['create_date']), '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d %H:%M:%S'),
                        update=datetime.datetime.strptime(task['update_date'], '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d %H:%M:%S'),
                        content=task['content'],
                        status=task['status'],
                        category=task['category'],
                        担当者=task.get('担当者', ''),
                        tag_links=' '.join([f'<a href="./index.py?tag={tag}" class="badge bg-secondary text-decoration-none me-1">{tag}</a>' for tag in task['tags']])
                    )
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
"""
        header()
        nav()
        print(content)
        footer()

# 編集画面 --------------------------------------------------------------------------------------------
    elif mode=="edit":
        status = {}
        status = getStatus(script_path + '/task/'+edit_task_id+'/', "edit")

        # ピン止めチェックボックスのHTML
        pinned_checked = 'checked' if status.get('pinned', False) else ''
        pinned_html = f"""
<div class="form-check">
    <input class="form-check-input" type="checkbox" id="pinned" name="update_pinned" {pinned_checked}>
    <label class="form-check-label" for="pinned">ピン止めする</label>
</div>"""

        # タグ入力欄のHTML
        tags_str = ', '.join(status.get('tags', []))
        tags_html = f"""
<div class="form-group mb-3">
    <label for="tags" class="form-label"><i class="bi bi-tags"></i> タグ</label>
    <input type="text" id="tags" name="update_tags" value="{tags_str}" class="form-control" placeholder="カンマ区切りでタグを入力 (例: 重要, 会議, TODO)"/>
    <small class="form-text text-muted">複数のタグをカンマ区切りで入力できます</small>
</div>"""

        # 担当者入力欄のHTML
        担当者_html = f"""
<div class="form-group mb-3">
    <label for="assignee" class="form-label"><i class="bi bi-person"></i> 担当者</label>
    <input type="text" id="assignee" name="update_担当者" value="{status.get('担当者', '')}" class="form-control"/>
</div>"""

        # 大分類、中分類、小分類の入力欄のHTML
        大分類_html = f"""
<div class="form-group mb-3">
    <label for="majorCategory" class="form-label"><i class="bi bi-diagram-3"></i> 大分類</label>
    <input type="text" id="majorCategory" name="update_大分類" value="{status.get('大分類', '')}" class="form-control"/>
</div>"""

        中分類_html = f"""
<div class="form-group mb-3">
    <label for="mediumCategory" class="form-label"><i class="bi bi-diagram-2"></i> 中分類</label>
    <input type="text" id="mediumCategory" name="update_中分類" value="{status.get('中分類', '')}" class="form-control"/>
</div>"""

        小分類_html = f"""
<div class="form-group mb-3">
    <label for="minorCategory" class="form-label"><i class="bi bi-diagram-1"></i> 小分類</label>
    <input type="text" id="minorCategory" name="update_小分類" value="{status.get('小分類', '')}" class="form-control"/>
</div>"""

        create_html = f"""
<div class="form-group mb-2">
    <label class="form-label"><i class="bi bi-calendar-plus"></i> 作成日</label>
    <p class="form-control-plaintext">{datetime.datetime.strptime(status["create_date"], "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")}</p>
</div>
"""
        update_html = f"""
<div class="form-group mb-2">
    <label class="form-label"><i class="bi bi-calendar-check"></i> 更新時間</label>
    <p class="form-control-plaintext">{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    <input type="hidden" name="update_update_datetime" value="{datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}">
</div>
"""
        # 状態選択のHTML修正
        if status["status"] == '継続':
            status_html = """
<div class="form-group mb-3">
    <label for="inputState" class="form-label"><i class="bi bi-list-check"></i> 状態</label>
    <select id="inputState" class="form-select" name="update_state_select">
        <option selected value="CONTINUE">継続</option>
        <option value="COMPLETE">完了</option>
    </select>
</div>
"""
        elif status["status"] == '完了':
            status_html = """
<div class="form-group mb-3">
    <label for="inputState" class="form-label"><i class="bi bi-list-check"></i> 状態</label>
    <select id="inputState" class="form-select" name="update_state_select">
        <option value="CONTINUE">継続</option>
        <option selected value="COMPLETE">完了</option>
    </select>
</div>
"""
        else:
            status_html = """
<div class="form-group mb-3">
    <label for="inputState" class="form-label"><i class="bi bi-list-check"></i> 状態</label>
    <select id="inputState" class="form-select" name="update_state_select">
        <option selected value="CONTINUE">継続</option>
        <option value="COMPLETE">完了</option>
    </select>
</div>
"""

        category_html = f"""
<div class="form-group mb-3">
    <label for="category" class="form-label"><i class="bi bi-folder"></i> カテゴリー</label>
    <input type="text" id="category" name="update_category_input" value="{status["category"]}" class="form-control"/>
</div>"""

        header()
        nav()

        print("""
        <div class="container my-4">
            <div class="row justify-content-center">
                <div class="col-lg-10">
                    <div class="card shadow">
                        <div class="card-header bg-primary text-white">
                            <h3 class="mb-0"><i class="bi bi-pencil-square"></i> タスク編集</h3>
                        </div>
                        <div class="card-body">
                            <form action="{REQUEST_URL}" method="post">
                                <input type="hidden" name="mode" value="update"/>
                                <input type="hidden" name="update_task_id" value="{edit_task_id}" />
                                
                                <div class="form-group mb-3">
                                    <label for="taskName" class="form-label"><i class="bi bi-file-earmark-text"></i> タスク名</label>
                                    <input type="text" id="taskName" name="update_task_name" value="{task_name}" class="form-control form-control-lg" required/>
                                </div>
                                
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        {status_html}
                                    </div>
                                    <div class="col-md-6">
                                        {category_html}
                                    </div>
                                </div>
                                
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        {担当者_html}
                                    </div>
                                    <div class="col-md-6">
                                        {pinned_html}
                                    </div>
                                </div>
                                
                                {tags_html}
                                
                                <div class="row mb-3">
                                    <div class="col-md-4">
                                        {大分類_html}
                                    </div>
                                    <div class="col-md-4">
                                        {中分類_html}
                                    </div>
                                    <div class="col-md-4">
                                        {小分類_html}
                                    </div>
                                </div>
                                
                                <div class="form-group mb-4">
                                    <label for="content" class="form-label"><i class="bi bi-card-text"></i> 内容</label>
                                    <textarea id="content" name="update_content" class="form-control" rows="10">{content}</textarea>
                                    <small class="form-text text-muted">マークダウン記法が使用できます</small>
                                </div>
                                
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        {create_html}
                                    </div>
                                    <div class="col-md-6">
                                        {update_html}
                                    </div>
                                </div>
                                
                                <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                                    <a href="./index.py" class="btn btn-secondary me-md-2">
                                        <i class="bi bi-x-circle"></i> キャンセル
                                    </a>
                                    <button type="submit" class="btn btn-primary">
                                        <i class="bi bi-save"></i> 保存
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """.format(
            edit_task_id=edit_task_id, 
            task_name=status["name"], 
            create_html=create_html, 
            update_html=update_html, 
            status_html=status_html, 
            category_html=category_html, 
            担当者_html=担当者_html, 
            pinned_html=pinned_html, 
            tags_html=tags_html, 
            大分類_html=大分類_html, 
            中分類_html=中分類_html, 
            小分類_html=小分類_html, 
            content=status["content"], 
            REQUEST_URL=REQUEST_URL
        ))
        footer()

# タスク詳細画面 --------------------------------------------------------------------------------------------
    elif mode=="view":
        status = {}
        status = getStatus(script_path + '/task/'+view_task_id+'/', "view")

        # ピン止めアイコン
        pin_icon_div = '<span class="fs-4">📌</span>' if status.get('pinned', False) else ''
        
        # タグリンク
        tag_links = ' '.join([f'<span class="badge bg-secondary me-1">{tag}</span>' for tag in status.get('tags', [])])
        
        # カード色の設定（継続か完了かで背景色を変える）
        card_color = " bg-secondary" if status["status"] == "完了" else ""
        
        header()
        nav()

        print(f"""
        <div class="container my-4">
            <div class="row justify-content-center">
                <div class="col-lg-10">
                    <div class="card{card_color} shadow">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <div class="d-flex align-items-center">
                                    <span class="badge bg-primary px-3 py-2 fs-6 me-3">
                                        <i class="bi bi-folder2-open"></i> {status["category"]}
                                    </span>
                                    <h2 class="card-title mb-0">
                                        {status["name"]}
                                    </h2>
                                </div>
                                <div>
                                    {pin_icon_div}
                                </div>
                            </div>
                            
                            <div class="mt-2">
                                {tag_links}
                            </div>
                            
                            <div class="card-text border p-3 bg-light my-3">
                                {status["content"].replace(chr(10), '<br>')}
                            </div>
                            
                            <!-- Task metadata with improved styling -->
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <span class="badge bg-info text-dark me-2">
                                        <i class="bi bi-person-fill"></i> 担当者: {status.get('担当者', '')}
                                    </span>
                                    <span class="badge bg-secondary me-2">
                                        <i class="bi bi-clock-history"></i> 状態: {status["status"]}
                                    </span>
                                </div>
                            </div>
                            
                            <div class="row mb-3">
                                <div class="col-md-12">
                                    <div class="d-flex flex-wrap">
                                        {status.get('大分類', '') and f'<span class="badge bg-primary me-2"><i class="bi bi-diagram-3"></i> 大分類: {status.get("大分類", "")}</span>' or ''}
                                        {status.get('中分類', '') and f'<span class="badge bg-primary me-2"><i class="bi bi-diagram-2"></i> 中分類: {status.get("中分類", "")}</span>' or ''}
                                        {status.get('小分類', '') and f'<span class="badge bg-primary me-2"><i class="bi bi-diagram-1"></i> 小分類: {status.get("小分類", "")}</span>' or ''}
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row mb-3">
                                <div class="col-md-12">
                                    <small class="text-muted">
                                        <i class="bi bi-calendar-check"></i> 更新日: {datetime.datetime.strptime(status["update_date"], "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")} &nbsp;|&nbsp; 
                                        <i class="bi bi-calendar-plus"></i> 作成日: {datetime.datetime.strptime(status["create_date"], "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")}
                                    </small>
                                </div>
                            </div>
                            
                            <div class="d-flex">
                                <a href="./index.py" class="btn btn-secondary me-2">
                                    <i class="bi bi-arrow-left"></i> 戻る
                                </a>
                                <a href="./index.py?mode=edit&edit_task_id={view_task_id}" class="btn btn-primary">
                                    <i class="bi bi-pencil"></i> 編集
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """)
        footer()

# 更新処理 --------------------------------------------------------------------------------------------
    elif mode=="update":
        f = open(script_path + '/task/'+update_task_id+'/contents.txt', 'w', encoding=str_code)
        f.write(str(update_content).replace('\r\n', '\n'))
        f.close()

        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(script_path + '/task/'+update_task_id+'/config.ini', encoding=str_code)

        # 既存のセクションがない場合は作成
        if not config.has_section('DATA'):
            config.add_section('DATA')
        if not config.has_section('STATUS'):
            config.add_section('STATUS')

        config['DATA']['UPDATE_DATA'] = update_update_datetime
        config['STATUS']['STATUS'] = update_state_select
        config['STATUS']['CATEGORY'] = update_category_input
        config['STATUS']['PINNED'] = str(update_pinned)
        
        # タグを保存（空白を除去してカンマで結合）
        tags = [tag.strip() for tag in update_tags.split(',') if tag.strip()]
        config['STATUS']['TAGS'] = ','.join(tags)

        config['STATUS']['担当者'] = update_担当者
        config['STATUS']['大分類'] = update_大分類
        config['STATUS']['中分類'] = update_中分類
        config['STATUS']['小分類'] = update_小分類

        with open(script_path + '/task/'+update_task_id+'/config.ini', mode='w', encoding=str_code) as write_config:
            config.write(write_config)

        url = ("http://" + os.environ['HTTP_HOST'] + REQUEST_URL).split("?")[0]
        print("<meta http-equiv=\"refresh\" content=\"0;URL="+url+"\">")

# 作成画面 --------------------------------------------------------------------------------------------
    elif mode=="create":
        status_html = """
<div class="form-group mb-3">
    <label for="inputState" class="form-label"><i class="bi bi-list-check"></i> 状態</label>
    <select id="inputState" class="form-select" name="create_state_select">
        <option selected value="CONTINUE">継続</option>
        <option value="COMPLETE">完了</option>
    </select>
</div>
"""
        create_html = f"""
<div class="form-group mb-2">
    <label class="form-label"><i class="bi bi-calendar-plus"></i> 作成時間</label>
    <p class="form-control-plaintext">{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    <input type="hidden" name="create_create_datetime" value="{datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}">
</div>
"""
        update_html = f"""
<div class="form-group mb-2">
    <label class="form-label"><i class="bi bi-calendar-check"></i> 更新時間</label>
    <p class="form-control-plaintext">{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    <input type="hidden" name="create_update_datetime" value="{datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}">
</div>
"""
        category_html = f"""
<div class="form-group mb-3">
    <label for="category" class="form-label"><i class="bi bi-folder"></i> カテゴリー</label>
    <input type="text" id="category" name="create_category_input" value="" class="form-control"/>
</div>"""

        pinned_html = f"""
<div class="form-check">
    <input class="form-check-input" type="checkbox" id="pinned" name="create_pinned">
    <label class="form-check-label" for="pinned">ピン止めする</label>
</div>"""

        tags_html = f"""
<div class="form-group mb-3">
    <label for="tags" class="form-label"><i class="bi bi-tags"></i> タグ</label>
    <input type="text" id="tags" name="create_tags" value="" class="form-control" placeholder="カンマ区切りでタグを入力 (例: 重要, 会議, TODO)"/>
    <small class="form-text text-muted">複数のタグをカンマ区切りで入力できます</small>
</div>"""

        create_担当者_html = f"""
<div class="form-group mb-3">
    <label for="assignee" class="form-label"><i class="bi bi-person"></i> 担当者</label>
    <input type="text" id="assignee" name="create_担当者" value="" class="form-control"/>
</div>"""

        create_大分類_html = f"""
<div class="form-group mb-3">
    <label for="majorCategory" class="form-label"><i class="bi bi-diagram-3"></i> 大分類</label>
    <input type="text" id="majorCategory" name="create_大分類" value="" class="form-control"/>
</div>"""

        create_中分類_html = f"""
<div class="form-group mb-3">
    <label for="mediumCategory" class="form-label"><i class="bi bi-diagram-2"></i> 中分類</label>
    <input type="text" id="mediumCategory" name="create_中分類" value="" class="form-control"/>
</div>"""

        create_小分類_html = f"""
<div class="form-group mb-3">
    <label for="minorCategory" class="form-label"><i class="bi bi-diagram-1"></i> 小分類</label>
    <input type="text" id="minorCategory" name="create_小分類" value="" class="form-control"/>
</div>"""

        header()
        nav()

        print("""
        <div class="container my-4">
            <div class="row justify-content-center">
                <div class="col-lg-10">
                    <div class="card shadow">
                        <div class="card-header bg-success text-white">
                            <h3 class="mb-0"><i class="bi bi-plus-circle"></i> 新規タスク作成</h3>
                        </div>
                        <div class="card-body">
                            <form action="{REQUEST_URL}" method="post">
                                <input type="hidden" name="mode" value="write"/>
                                <input type="hidden" name="create_task_id" value="{uuid}" />
                                
                                <div class="form-group mb-3">
                                    <label for="taskName" class="form-label"><i class="bi bi-file-earmark-text"></i> タスク名</label>
                                    <input type="text" id="taskName" name="create_task_name" class="form-control form-control-lg" required/>
                                </div>
                                
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        {status_html}
                                    </div>
                                    <div class="col-md-6">
                                        {category_html}
                                    </div>
                                </div>
                                
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        {create_担当者_html}
                                    </div>
                                    <div class="col-md-6">
                                        {pinned_html}
                                    </div>
                                </div>
                                
                                {tags_html}
                                
                                <div class="row mb-3">
                                    <div class="col-md-4">
                                        {create_大分類_html}
                                    </div>
                                    <div class="col-md-4">
                                        {create_中分類_html}
                                    </div>
                                    <div class="col-md-4">
                                        {create_小分類_html}
                                    </div>
                                </div>
                                
                                <div class="form-group mb-4">
                                    <label for="content" class="form-label"><i class="bi bi-card-text"></i> 内容</label>
                                    <textarea id="content" name="create_content" class="form-control" rows="10"></textarea>
                                    <small class="form-text text-muted">マークダウン記法が使用できます</small>
                                </div>
                                
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        {create_html}
                                    </div>
                                    <div class="col-md-6">
                                        {update_html}
                                    </div>
                                </div>
                                
                                <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                                    <a href="./index.py" class="btn btn-secondary me-md-2">
                                        <i class="bi bi-x-circle"></i> キャンセル
                                    </a>
                                    <button type="submit" class="btn btn-success">
                                        <i class="bi bi-plus-circle"></i> 作成
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """.format(uuid=uuid.uuid4(), create_html=create_html, update_html=update_html, status_html=status_html, category_html=category_html, create_担当者_html=create_担当者_html, pinned_html=pinned_html, tags_html=tags_html, create_大分類_html=create_大分類_html, create_中分類_html=create_中分類_html, create_小分類_html=create_小分類_html, REQUEST_URL=REQUEST_URL))
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
        config.set("STATUS", 'PINNED', str(create_pinned))  # 新規作成時はピン止めなし
        config.set("STATUS", 'TAGS', create_tags)  # 新規作成時は空のタグで初期化
        config.set("STATUS", '担当者', create_担当者)
        config.set("STATUS", '大分類', create_大分類)
        config.set("STATUS", '中分類', create_中分類)
        config.set("STATUS", '小分類', create_小分類)

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
