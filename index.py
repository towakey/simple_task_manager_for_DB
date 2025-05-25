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
import csv
import json
import db

app_name = "simple_task_manager_for_DB"

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
q_groupCategory = form.getfirst("groupCategory", '')  # グループによる絞り込み用
q_daiCategory = form.getfirst("daiCategory", '')  # 大分類による絞り込み用
q_chuCategory = form.getfirst("chuCategory", '')  # 中分類による絞り込み用
q_shoCategory = form.getfirst("shoCategory", '')  # 小分類による絞り込み用
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
update_groupCategory = form.getfirst('update_groupCategory', '')
update_大分類 = form.getfirst('update_大分類', '')
update_中分類 = form.getfirst('update_中分類', '')
update_小分類 = form.getfirst('update_小分類', '')
update_regular = form.getfirst('update_regular', 'off') == 'on'  # スイッチの値を取得 (on/off)

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
create_groupCategory = form.getfirst('create_groupCategory', '')
create_大分類 = form.getfirst('create_大分類', '')
create_中分類 = form.getfirst('create_中分類', '')
create_小分類 = form.getfirst('create_小分類', '')
create_regular = form.getfirst('create_regular', 'off') == 'on'  # スイッチの値を取得 (on/off)

# 既存ヘルパを置き換え -------------------------------------------------------------
def _row_to_detail(row):
    """db.fetch_* で取得した行(dict)を既存UIが期待するキーへ変換"""
    detail = row.copy()
    # ステータスを日本語表記へ変換し card_color を追加
    if row.get("status") == "COMPLETE":
        detail["status"] = "完了"
        detail["card_color"] = " bg-secondary"
    else:
        detail["status"] = "継続"
        detail["card_color"] = ""
    # bool pinned 既に bool
    # group_category → groupCategory
    if "group_category" in detail:
        detail["groupCategory"] = detail.pop("group_category")
    return detail

# タスク情報の読み込み
def getStatus(task_id, mode):
    result = {}
    row = db.fetch_one(task_id)
    if row:
        result = _row_to_detail(row)
    else:
        result['name'] = ""
        result['create_date'] = ""
        result['update_date'] = ""
        result['complete_date'] = ""
        result['status'] = ""
        result['card_color'] = ""
        result['pinned'] = False
        result['content'] = ""
        result['category'] = ""
        result['tags'] = []
        result['groupCategory'] = ""
        result['担当者'] = ""
        result['大分類'] = ""
        result['中分類'] = ""
        result['小分類'] = ""
        result['regular'] = ""
    if mode == "index":
        # マークダウンリンクをHTMLリンクに変換し、改行を<br>タグに変換
        content = result['content']
        content = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', content)
        result['content'] = content.replace('\n', '<br>')
    return result

# カテゴリー一覧を作成
def getCategoryList():
    cats = set()
    for row in db.fetch_all():
        cat = row.get("category", "")
        if cat:
            cats.add(cat)
    return list(cats)

# 分類データの読み込み
def getClassifications():
    classifications = []
    classifications_file = script_path + "/classification.csv"
    if os.path.exists(classifications_file):
        with open(classifications_file, 'r', encoding=str_code) as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                if len(row) >= 4:
                    classifications.append({
                        'group': row[0],
                        'dai': row[1],
                        'chu': row[2],
                        'sho': row[3]
                    })
    return classifications

# 分類一覧からユニークなグループのリストを取得
def getGroupCategories(classifications):
    result = []
    for item in classifications:
        if item['group'] not in result:
            result.append(item['group'])
    return result

# 分類一覧からユニークな大分類のリストを取得
def getDaiCategories(classifications, group_category=None):
    result = []
    for item in classifications:
        if (group_category is None or item['group'] == group_category) and item['dai'] not in result:
            result.append(item['dai'])
    return result

# 特定のグループと大分類に属する中分類のリストを取得
def getChuCategories(classifications, dai_category, group_category=None):
    result = []
    for item in classifications:
        if (group_category is None or item['group'] == group_category) and item['dai'] == dai_category and item['chu'] not in result:
            result.append(item['chu'])
    return result

# 特定のグループ、大分類、中分類に属する小分類のリストを取得
def getShoCategories(classifications, dai_category, chu_category, group_category=None):
    result = []
    for item in classifications:
        if (group_category is None or item['group'] == group_category) and item['dai'] == dai_category and item['chu'] == chu_category and item['sho'] not in result:
            result.append(item['sho'])
    return result

def header():
    print(f"""
<html lang="ja">
    <head>
        <meta charset="UTF-8">
        <link rel="stylesheet" href="./css/bootstrap.css">
        <link rel="stylesheet" href="./css/custom.css">
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
            .sidebar {{
                min-height: calc(100vh - 70px);
                background-color: #f8f9fa;
                padding: 15px;
            }}
            .sidebar .nav-link {{
                padding: 0.5rem 0;
                color: #333;
            }}
            .sidebar .nav-link:hover {{
                color: #0d6efd;
            }}
            .sidebar .nav-link.active {{
                color: #0d6efd;
                font-weight: bold;
            }}
            .sidebar .nav-item {{
                padding-left: 10px;
            }}
            .chu-category, .sho-category {{
                display: none;
            }}
            .show {{
                display: block;
            }}
        </style>
""")
    # JavaScriptコードを別途出力
    print("""
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                // グループをクリックしたときのイベント
                document.querySelectorAll('.group-category').forEach(function(item) {
                    item.addEventListener('click', function(e) {
                        const groupCat = this.getAttribute('data-group');
                        
                        // すべての大分類を非表示
                        document.querySelectorAll('.dai-category').forEach(function(dai) {
                            dai.style.display = 'none';
                        });
                        
                        // 選択されたグループに属する大分類のみ表示
                        document.querySelectorAll(`.dai-category[data-group="${{groupCat}}"]`).forEach(function(dai) {
                            dai.style.display = 'block';
                        });
                        
                        // 中分類と小分類を非表示
                        document.querySelectorAll('.chu-category, .sho-category').forEach(function(item) {
                            item.style.display = 'none';
                        });
                    });
                });
                
                // 大分類をクリックしたときのイベント
                document.querySelectorAll('.dai-category a').forEach(function(item) {
                    item.addEventListener('click', function(e) {
                        const daiCat = this.parentElement.getAttribute('data-dai');
                        const groupCat = this.parentElement.getAttribute('data-group');
                        
                        // すべての中分類を非表示
                        document.querySelectorAll('.chu-category').forEach(function(chu) {
                            chu.style.display = 'none';
                        });
                        
                        // 選択されたグループと大分類に属する中分類のみ表示
                        document.querySelectorAll(`.chu-category[data-group="${{groupCat}}"][data-dai="${{daiCat}}"]`).forEach(function(chu) {
                            chu.style.display = 'block';
                        });
                        
                        // すべての小分類を非表示
                        document.querySelectorAll('.sho-category').forEach(function(sho) {
                            sho.style.display = 'none';
                        });
                    });
                });
                
                // 中分類をクリックしたときのイベント
                document.querySelectorAll('.chu-category a').forEach(function(item) {
                    item.addEventListener('click', function(e) {
                        const daiCat = this.parentElement.getAttribute('data-dai');
                        const chuCat = this.parentElement.getAttribute('data-chu');
                        const groupCat = this.parentElement.getAttribute('data-group');
                        
                        // すべての小分類を非表示
                        document.querySelectorAll('.sho-category').forEach(function(sho) {
                            sho.style.display = 'none';
                        });
                        
                        // 選択されたグループ、大分類と中分類に属する小分類のみ表示
                        document.querySelectorAll(`.sho-category[data-group="${{groupCat}}"][data-dai="${{daiCat}}"][data-chu="${{chuCat}}"]`).forEach(function(sho) {
                            sho.style.display = 'block';
                        });
                    });
                });
            });
        </script>
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

# --- Legacy task folder import ------------------------------------------------

def import_legacy_tasks():
    """Scan ./task directory and import entries that do not yet exist in DB."""
    imported = 0
    skipped = 0
    if not os.path.isdir(task_folder_path):
        return (0,0)
    for task_id in os.listdir(task_folder_path):
        dir_path = os.path.join(task_folder_path, task_id)
        if not os.path.isdir(dir_path):
            continue
        # skip if already exists
        if db.fetch_one(task_id):
            skipped += 1
            continue
        cfg_path = os.path.join(dir_path, 'config.ini')
        content_path = os.path.join(dir_path, 'contents.txt')
        if not os.path.isfile(cfg_path):
            skipped += 1
            continue
        config = configparser.ConfigParser()
        config.read(cfg_path, encoding=str_code)
        try:
            data_sec = config['DATA']
            stat_sec = config['STATUS']
        except KeyError:
            skipped += 1
            continue
        task_dict = {
            "id": task_id,
            "name": stat_sec.get('NAME', ''),
            "status": stat_sec.get('STATUS', 'CONTINUE'),
            "create_date": data_sec.get('CREATE_DATA', ''),
            "update_date": data_sec.get('UPDATE_DATA', ''),
            "complete_date": data_sec.get('COMPLETE_DATE', None),
            "pinned": stat_sec.getboolean('PINNED', fallback=False),
            "category": stat_sec.get('CATEGORY', ''),
            "group_category": stat_sec.get('GROUPCATEGORY', ''),
            "担当者": stat_sec.get('担当者', ''),
            "大分類": stat_sec.get('大分類', ''),
            "中分類": stat_sec.get('中分類', ''),
            "小分類": stat_sec.get('小分類', ''),
            "regular": stat_sec.get('REGULAR', 'Regular'),
            "tags": [t.strip() for t in stat_sec.get('TAGS', '').split(',') if t.strip()],
            "content": open(content_path, 'r', encoding=str_code).read() if os.path.isfile(content_path) else '',
        }
        db.insert(task_dict)
        imported += 1
    return (imported, skipped)

# テンプレート読み込み関数
def load_templates():
    try:
        with open('templates.json', 'r', encoding='utf-8') as f:
            templates = json.load(f)
        return templates
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []

TEMPLATE_MODAL_HTML_SCRIPT = r"""
<div class="modal fade" id="templateModal" tabindex="-1" aria-labelledby="templateModalLabel" aria-hidden="true">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="templateModalLabel">テンプレートを選択</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <div class="modal-body">
        <div class="mb-3">
          <label for="templateSelect" class="form-label">テンプレート名</label>
          <select id="templateSelect" class="form-select">
            <option value="">選択してください</option>
          </select>
        </div>
        <div class="mb-3">
          <label for="templateContents" class="form-label">テンプレート内容</label>
          <textarea id="templateContents" class="form-control" rows="5" readonly></textarea>
        </div>
        <div id="templateInputsContainer"></div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">閉じる</button>
        <button type="button" class="btn btn-primary" id="applyTemplateButton">入力</button>
      </div>
    </div>
  </div>
</div>
<script>
  let currentTargetTextareaId = '';
  let allTemplates = [];
  document.addEventListener('DOMContentLoaded', function() {
    const templateModal = new bootstrap.Modal(document.getElementById('templateModal'));
    const templateSelect = document.getElementById('templateSelect');
    const templateContents = document.getElementById('templateContents');
    const templateInputsContainer = document.getElementById('templateInputsContainer');
    const applyTemplateButton = document.getElementById('applyTemplateButton');
    document.querySelectorAll('.open-template-modal-button').forEach(function(button) {
      button.addEventListener('click', function() {
        currentTargetTextareaId = this.dataset.targetTextarea;
        loadTemplatesToModal();
        templateModal.show();
      });
    });
    function loadTemplatesToModal() {
      templateSelect.innerHTML = '<option value="">選択してください</option>';
      allTemplates.forEach(function(template, index) {
        const option = document.createElement('option');
        option.value = index;
        option.textContent = template.name;
        templateSelect.appendChild(option);
      });
    }
    templateSelect.addEventListener('change', function() {
      const selectedIndex = this.value;
      templateInputsContainer.innerHTML = '';
      if (selectedIndex === "") {
        templateContents.value = '';
        return;
      }
      const selectedTemplate = allTemplates[selectedIndex];
      templateContents.value = selectedTemplate.contents;
      if (selectedTemplate.input_contents) {
        selectedTemplate.input_contents.forEach(function(inputItem) {
          const formGroup = document.createElement('div');
          formGroup.classList.add('mb-3');
          const label = document.createElement('label');
          label.classList.add('form-label');
          label.textContent = inputItem.input_name;
          formGroup.appendChild(label);
          if (inputItem.type === 'textarea') {
            const textarea = document.createElement('textarea');
            textarea.classList.add('form-control');
            textarea.dataset.inputName = inputItem.input_name;
            formGroup.appendChild(textarea);
          } else if (inputItem.type === 'select' && inputItem.options) {
            const select = document.createElement('select');
            select.classList.add('form-select');
            select.dataset.inputName = inputItem.input_name;
            inputItem.options.forEach(function(opt) {
              const optionElement = document.createElement('option');
              optionElement.value = opt;
              optionElement.textContent = opt;
              select.appendChild(optionElement);
            });
            formGroup.appendChild(select);
          } else {
            const input = document.createElement('input');
            input.type = inputItem.type || 'text';
            input.classList.add('form-control');
            input.dataset.inputName = inputItem.input_name;
            formGroup.appendChild(input);
          }
          templateInputsContainer.appendChild(formGroup);
        });
      }
    });
    applyTemplateButton.addEventListener('click', function() {
      const targetTextarea = document.getElementById(currentTargetTextareaId);
      if (!targetTextarea) return;
      let combinedContent = templateContents.value;
      const inputs = templateInputsContainer.querySelectorAll('[data-input-name]');
      inputs.forEach(function(input) {
        combinedContent += "\n" + input.dataset.inputName + ": " + input.value;
      });
      targetTextarea.value += "\n" + combinedContent;
      templateModal.hide();
    });
  });
  function setTemplatesData(templates) {
    allTemplates = templates;
  }
</script>
"""

if __name__ == '__main__':
    print('Content-type: text/html; charset=UTF-8\r\n')
    # 一覧画面
    if mode == '':
        header()
        nav()

        # 分類データを取得
        classifications = getClassifications()
        group_categories = getGroupCategories(classifications)
        
        # サイドバー付きのレイアウト開始
        print("""
        <div class="container-fluid">
            <div class="row">
                <!-- サイドバー部分 -->
                <div class="col-md-3 col-lg-2 sidebar">
                    <h5 class="mb-3">分類から探す</h5>
                    <div class="nav flex-column">
        """)
        
        # グループを表示
        for group in group_categories:
            active_class = "active" if group == q_groupCategory else ""
            print(f"""
                        <a href="./index.py?groupCategory={group}" class="nav-link group-category {active_class}" data-group="{group}">
                            <i class="bi bi-folder"></i> {group}
                        </a>
            """)
            
            # このグループに属する大分類を取得
            dai_categories_in_group = getDaiCategories(classifications, group)
            for dai in dai_categories_in_group:
                display_style = "block" if group == q_groupCategory else "none"
                active_class = "active" if dai == q_daiCategory and group == q_groupCategory else ""
                print(f"""
                        <div class="nav-item dai-category" data-group="{group}" data-dai="{dai}" style="display: {display_style};">
                            <a href="./index.py?groupCategory={group}&daiCategory={dai}" class="nav-link {active_class}">
                                <i class="bi bi-diagram-3"></i> {dai}
                            </a>
                        </div>
                """)
                
                # このグループと大分類に属する中分類を取得
                chu_categories = getChuCategories(classifications, dai, group)
                for chu in chu_categories:
                    display_style = "block" if group == q_groupCategory and dai == q_daiCategory else "none"
                    active_class = "active" if chu == q_chuCategory and dai == q_daiCategory and group == q_groupCategory else ""
                    print(f"""
                            <div class="nav-item chu-category" data-group="{group}" data-dai="{dai}" data-chu="{chu}" style="display: {display_style};">
                                <a href="./index.py?groupCategory={group}&daiCategory={dai}&chuCategory={chu}" class="nav-link {active_class}">
                                    <i class="bi bi-diagram-2"></i> {chu}
                                </a>
                            </div>
                    """)
                    
                    # このグループ、大分類、中分類に属する小分類を取得
                    sho_categories = getShoCategories(classifications, dai, chu, group)
                    for sho in sho_categories:
                        display_style = "block" if group == q_groupCategory and dai == q_daiCategory and chu == q_chuCategory else "none"
                        active_class = "active" if sho == q_shoCategory and chu == q_chuCategory and dai == q_daiCategory and group == q_groupCategory else ""
                        print(f"""
                                <div class="nav-item sho-category" data-group="{group}" data-dai="{dai}" data-chu="{chu}" data-sho="{sho}" style="display: {display_style};">
                                    <a href="./index.py?groupCategory={group}&daiCategory={dai}&chuCategory={chu}&shoCategory={sho}" class="nav-link {active_class}">
                                        <i class="bi bi-diagram-1"></i> {sho}
                                    </a>
                                </div>
                        """)
        
        print("""
                    </div>
                </div>
                
                <!-- メインコンテンツ部分 -->
                <div class="col-md-9 col-lg-10">
        """)
        
        # DB から全タスクを取得
        tasks = []
        for row in db.fetch_all():
            tasks.append({"id": row["id"], "detail": _row_to_detail(row)})

        # ソート用の関数
        def get_sort_key(task):
            # 最初にピン止めされたタスクを上に
            pinned_priority = 0 if task['detail']['pinned'] else 1
            
            # 二次ソートのキーを取得
            if sort_by == 'name':
                secondary_key = task['detail']['name'].lower()
            elif sort_by in ['create_date', 'update_date']:
                secondary_key = datetime.datetime.strptime(task['detail'][sort_by], '%Y-%m-%dT%H:%M:%S')
            elif sort_by == 'category':
                secondary_key = task['detail']['category'].lower()
            elif sort_by == 'status':
                secondary_key = task['detail']['status']
            
            # 降順の場合は比較を反転
            if sort_order == 'desc' and sort_by in ['create_date', 'update_date']:
                secondary_key = datetime.datetime.max - secondary_key
            elif sort_order == 'desc':
                secondary_key = '~' + str(secondary_key)
            
            return (pinned_priority, secondary_key)
        
        # ソート実行
        tasks.sort(key=get_sort_key)

        # カテゴリフィルタリング
        if q_category != "":
            filtered_tasks = []
            for task in tasks:
                if 'category' in task['detail'] and task['detail']['category'] == q_category:
                    filtered_tasks.append(task)
            tasks = filtered_tasks
        
        # タグフィルタリング
        if q_tag != "":
            filtered_tasks = []
            for task in tasks:
                if 'tags' in task['detail'] and q_tag in task['detail']['tags']:
                    filtered_tasks.append(task)
            tasks = filtered_tasks
            
        # グループによるフィルタリング
        if q_groupCategory != "":
            filtered_tasks = []
            for task in tasks:
                if 'groupCategory' in task['detail'] and task['detail']['groupCategory'] == q_groupCategory:
                    filtered_tasks.append(task)
            tasks = filtered_tasks
            
        # 大分類によるフィルタリング
        if q_daiCategory != "":
            filtered_tasks = []
            for task in tasks:
                if '大分類' in task['detail'] and task['detail']['大分類'] == q_daiCategory:
                    filtered_tasks.append(task)
            tasks = filtered_tasks
            
        # 中分類によるフィルタリング
        if q_chuCategory != "":
            filtered_tasks = []
            for task in tasks:
                if '中分類' in task['detail'] and task['detail']['中分類'] == q_chuCategory:
                    filtered_tasks.append(task)
            tasks = filtered_tasks
            
        # 小分類によるフィルタリング
        if q_shoCategory != "":
            filtered_tasks = []
            for task in tasks:
                if '小分類' in task['detail'] and task['detail']['小分類'] == q_shoCategory:
                    filtered_tasks.append(task)
            tasks = filtered_tasks

        # ピン止めされたタスクを先頭に表示
        pinned_tasks = []
        unpinned_tasks = []
        
        for task in tasks:
            if task['detail']['pinned']:
                pinned_tasks.append(task)
            else:
                unpinned_tasks.append(task)
                
        tasks = pinned_tasks + unpinned_tasks

        content = ""
        if len(tasks) > 0:
            for task in tasks:
                if q_category == "" or q_category == task['detail']['category']:
                    if q_tag == "" or q_tag in task['detail']['tags']:
                        pin_icon_div = '<span class="fs-4">📌</span>' if task['detail']['pinned'] else ''
                        regular_badge = '<span class="badge bg-info me-1">Regular</span>' if task['detail'].get('regular', 'Regular') == 'Regular' else '<span class="badge bg-warning me-1">Irregular</span>'
                        border_class = " border-info" if task['detail'].get('regular', 'Regular') == 'Regular' else " border-danger"
                        bg_class = "" if task['detail']['status'] == "完了" else (" bg-regular-task" if task['detail'].get('regular', 'Regular') == 'Regular' else " bg-irregular-task")

                        temp = """
        <div class="container my-3">
            <div class="card{card_color}{border_class}{bg_class} shadow-sm">
                <div class="card-body">
                    <h5 class="card-title mb-3 fw-bold">
                        <a href="./index.py?category={category}" class="text-decoration-none me-3">
                            <span class="badge bg-primary">{category}</span>
                        </a>

                        <a href="./index.py?mode=view&view_task_id={file}" class="text-decoration-none text-dark">
                            {task_name}
                        </a>
                    </h5>
                    
                    <div class="d-flex justify-content-between align-items-center mb-2">
<!--                        <div class="d-flex align-items-center">
                            {regular_badge}
                        </div>-->
                        <div>
                            {pin_icon_div}
                        </div>
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
                                <i class="bi bi-calendar-plus"></i> 作成日: {incident} &nbsp;|&nbsp; 
                                <i class="bi bi-calendar2-check"></i> 完了日: {complete}
                            </small>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        {tag_links}
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
                        card_color=task['detail']['card_color'],
                        file=task['id'],
                        task_name=task['detail']['name'],
                        pin_icon_div=pin_icon_div,
                        incident=datetime.datetime.strptime(task['detail'].get('発生日', task['detail']['create_date']), '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S'),
                        update=datetime.datetime.strptime(task['detail']['update_date'], '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S'),
                        complete=(datetime.datetime.strptime(task['detail']['complete_date'], '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S') if task['detail'].get('complete_date') else ''),
                        content=task['detail']['content'].replace('\n', '<br>'),
                        status=task['detail']['status'],
                        category=task['detail']['category'],
                        担当者=task['detail'].get('担当者', ''),
                        tag_links=' '.join([f'<a href="./index.py?tag={tag}" class="badge bg-secondary text-decoration-none me-1">{tag}</a>' for tag in task['detail']['tags']]),
                        regular_badge=regular_badge,
                        border_class=border_class,
                        bg_class=bg_class
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
        print(content)
        
        # サイドバー付きのレイアウト終了
        print("""
                </div>
            </div>
        </div>
        """)
        
        print(TEMPLATE_MODAL_HTML_SCRIPT) # 先に関数定義を含むスクリプトを出力
        templates_json_data = json.dumps(load_templates())
        print(f"<script>setTemplatesData({templates_json_data});</script>")
        footer()

# 編集画面 --------------------------------------------------------------------------------------------
    elif mode=="edit":
        # 編集対象のタスク情報を取得
        target_task_detail = getStatus(edit_task_id, "detail")
        
        # プルダウンのオプションを作成
        classifications = getClassifications()
        group_categories = getGroupCategories(classifications)
        
        # 選択されたグループに基づく大分類を取得
        selected_group = target_task_detail.get("groupCategory", "")
        
        group_options = ""
        for group in group_categories:
            selected = " selected" if group == selected_group else ""
            group_options += f'<option value="{group}"{selected}>{group}</option>'
        
        # 大分類のオプションを作成
        selected_dai = target_task_detail.get("大分類", "")
        dai_options = ""
        for dai in getDaiCategories(classifications, selected_group):
            selected = " selected" if dai == selected_dai else ""
            dai_options += f'<option value="{dai}"{selected}>{dai}</option>'
        
        # 中分類のオプションを作成
        selected_chu = target_task_detail.get("中分類", "")
        chu_options = ""
        chuCategories = getChuCategories(classifications, selected_dai, selected_group)
        for chu in chuCategories:
            selected = " selected" if chu == selected_chu else ""
            chu_options += f'<option value="{chu}"{selected}>{chu}</option>'
        
        # 小分類のオプションを作成
        selected_sho = target_task_detail.get("小分類", "")
        sho_options = ""
        shoCategories = getShoCategories(classifications, selected_dai, selected_chu, selected_group)
        for sho in shoCategories:
            selected = " selected" if sho == selected_sho else ""
            sho_options += f'<option value="{sho}"{selected}>{sho}</option>'

        # ピン止めチェックボックスのHTML
        pinned_checked = 'checked' if target_task_detail.get('pinned', False) else ''
        pinned_html = f"""
<div class="form-check">
    <input class="form-check-input" type="checkbox" id="pinned" name="update_pinned" {pinned_checked}>
    <label class="form-check-label" for="pinned">ピン止めする</label>
</div>"""

        # 辞書型で渡された場合はタグ名のみを抽出
        def extract_tag_names(tags):
            if isinstance(tags, list):
                names = []
                for tag in tags:
                    if isinstance(tag, dict) and 'name' in tag:
                        names.append(tag['name'])
                    else:
                        names.append(str(tag))
                return ','.join(names)
            elif isinstance(tags, dict) and 'name' in tags:
                return tags['name']
            return str(tags) if tags else ''

        # タグ入力欄のHTML
        tags_value = extract_tag_names(target_task_detail.get('tags', ''))
        tags_html = f"""
<div class="form-group mb-3">
    <label for="tags" class="form-label"><i class="bi bi-tags"></i> タグ（カンマ区切り）</label>
    <input type="text" id="tags" name="update_tags" value="{tags_value}" class="form-control" placeholder="例：重要, フォローアップ, 会議"/>
</div>"""

        # 担当者入力欄のHTML
        担当者_html = f"""
<div class="form-group mb-3">
    <label for="assignee" class="form-label"><i class="bi bi-person"></i> 担当者</label>
    <input type="text" id="assignee" name="update_担当者" value="{target_task_detail.get('担当者', '')}" class="form-control"/>
</div>"""

        # グループ入力欄のHTML - ドロップダウンメニューに変更
        current_group = target_task_detail.get('groupCategory', '')
        if not current_group:
            create_group_html = f"""
<div class="form-group mb-3">
    <label for="group" class="form-label"><i class="bi bi-people"></i> グループ</label>
    <select id="group" name="update_groupCategory" class="form-select" onchange="updateDaiCategories()">
        <option value="">選択してください</option>
        {group_options}
    </select>
</div>"""
        else:
            create_group_html = f'''<input type="hidden" name="update_groupCategory" value="{current_group}">'''

        # 大分類入力欄のHTML - ドロップダウンメニューに変更
        current_dai = target_task_detail.get('大分類', '')
        if not current_dai:
            create_大分類_html = f"""
<div class="form-group mb-3">
    <label for="majorCategory" class="form-label"><i class="bi bi-diagram-3"></i> 大分類</label>
    <select id="majorCategory" name="update_大分類" class="form-select" onchange="updateChuCategories()">
        <option value="">選択してください</option>
        {dai_options}
    </select>
</div>"""
        else:
            create_大分類_html = f'''<input type="hidden" name="update_大分類" value="{current_dai}">'''

        # 中分類入力欄のHTML - ドロップダウンメニューに変更
        current_chu = target_task_detail.get('中分類', '')
        if not current_chu:
            create_中分類_html = f"""
<div class="form-group mb-3">
    <label for="mediumCategory" class="form-label"><i class="bi bi-diagram-2"></i> 中分類</label>
    <select id="mediumCategory" name="update_中分類" class="form-select" onchange="updateShoCategories()">
        <option value="">選択してください</option>
        {chu_options}
    </select>
</div>"""
        else:
            create_中分類_html = f'''<input type="hidden" name="update_中分類" value="{current_chu}">'''

        # 小分類入力欄のHTML - ドロップダウンメニューに変更
        current_sho = target_task_detail.get('小分類', '')
        if not current_sho:
            create_小分類_html = f"""
<div class="form-group mb-3">
    <label for="smallCategory" class="form-label"><i class="bi bi-diagram-1"></i> 小分類</label>
    <select id="smallCategory" name="update_小分類" class="form-select">
        <option value="">選択してください</option>
        {sho_options}
    </select>
</div>"""
        else:
            create_小分類_html = f'''<input type="hidden" name="update_小分類" value="{current_sho}">'''

        # Regular/Irregular スイッチのHTML
        is_regular = target_task_detail.get('regular', 'Regular') == 'Regular'
        regular_checked = "checked" if is_regular else ""
        regular_html = f"""
<div class="form-check form-switch mb-3">
  <input class="form-check-input" type="checkbox" role="switch" id="update_regular" name="update_regular" {regular_checked}>
  <label class="form-check-label" for="update_regular">定型タスク (Regular)</label>
</div>
"""

        create_html = f"""
<div class="form-group mb-2">
    <label class="form-label"><i class="bi bi-calendar-plus"></i> 作成時間</label>
    <p class="form-control-plaintext">{target_task_detail['create_date']}</p>
</div>
"""
        update_html = f"""
<div class="form-group mb-2">
    <label class="form-label"><i class="bi bi-calendar-check"></i> 更新時間</label>
    <p class="form-control-plaintext">{datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}</p>
    <input type="hidden" name="update_update_datetime" value="{datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}">
</div>
"""
        # ステータス選択のHTML修正
        status_selected_continue = ""
        status_selected_complete = ""
        if target_task_detail['status'] == "完了":
            status_selected_complete = "selected"
        else:
            status_selected_continue = "selected"
            
        status_html = f"""
<div class="form-group mb-3">
    <label for="state" class="form-label"><i class="bi bi-flag"></i> ステータス</label>
    <select id="state" name="update_state_select" class="form-select">
        <option value="CONTINUE" {status_selected_continue}>継続</option>
        <option value="COMPLETE" {status_selected_complete}>完了</option>
    </select>
</div>"""

        category_html = f"""
<div class="form-group mb-3">
    <label for="category" class="form-label"><i class="bi bi-folder"></i> カテゴリー</label>
    <input type="text" id="category" name="update_category_input" value="{target_task_detail['category']}" class="form-control"/>
</div>"""

        # JavaScriptのための変数準備
        create_regular_js = f"""
<script>
// 分類データ
const classifications = {json.dumps(classifications)};

// グループが変更されたときに大分類を更新
function updateDaiCategories() {{
    const groupSelect = document.getElementById('group');
    const daiSelect = document.getElementById('majorCategory');
    
    if (!groupSelect || (groupSelect.tagName !== 'SELECT') || !daiSelect || (daiSelect.tagName !== 'SELECT')) {{
        updateChuCategories();
        return;
    }}

    const selectedGroup = groupSelect.value;
    daiSelect.innerHTML = '<option value="">選択してください</option>';
    
    const uniqueDai = new Set();
    if (classifications && Array.isArray(classifications)) {{
        classifications.forEach(item => {{
            if (selectedGroup === '' || item.group === selectedGroup) {{
                if (item.dai) uniqueDai.add(item.dai);
            }}
        }});
    }}
    
    Array.from(uniqueDai).sort().forEach(dai => {{
        const option = document.createElement('option');
        option.value = dai;
        option.textContent = dai;
        daiSelect.appendChild(option);
    }});
    updateChuCategories();
}}

// 大分類が変更されたときに中分類を更新
function updateChuCategories() {{
    const groupSelect = document.getElementById('group');
    const daiSelect = document.getElementById('majorCategory');
    const chuSelect = document.getElementById('mediumCategory');

    if (!daiSelect || (daiSelect.tagName !== 'SELECT' && daiSelect.value === '') || !chuSelect || (chuSelect.tagName !== 'SELECT')) {{
         updateShoCategories();
        return;
    }}
    
    const selectedGroup = groupSelect && groupSelect.tagName === 'SELECT' ? groupSelect.value : (document.getElementsByName('update_groupCategory')[0] ? document.getElementsByName('update_groupCategory')[0].value : '');
    const selectedDai = daiSelect.tagName === 'SELECT' ? daiSelect.value : (document.getElementsByName('update_大分類')[0] ? document.getElementsByName('update_大分類')[0].value : '');

    chuSelect.innerHTML = '<option value="">選択してください</option>';
    
    const uniqueChu = new Set();
    if (classifications && Array.isArray(classifications)) {{
        classifications.forEach(item => {{
            if ((selectedGroup === '' || item.group === selectedGroup) && 
                (selectedDai === '' || item.dai === selectedDai)) {{
                if (item.chu) uniqueChu.add(item.chu);
            }}
        }});
    }}
    
    Array.from(uniqueChu).sort().forEach(chu => {{
        const option = document.createElement('option');
        option.value = chu;
        option.textContent = chu;
        chuSelect.appendChild(option);
    }});
    updateShoCategories();
}}

// 中分類が変更されたときに小分類を更新
function updateShoCategories() {{
    const groupSelect = document.getElementById('group');
    const daiSelect = document.getElementById('majorCategory');
    const chuSelect = document.getElementById('mediumCategory');
    const shoSelect = document.getElementById('smallCategory');

    if (!chuSelect || (chuSelect.tagName !== 'SELECT' && chuSelect.value === '') || !shoSelect || (shoSelect.tagName !== 'SELECT')) {{
        return;
    }}

    const selectedGroup = groupSelect && groupSelect.tagName === 'SELECT' ? groupSelect.value : (document.getElementsByName('update_groupCategory')[0] ? document.getElementsByName('update_groupCategory')[0].value : '');
    const selectedDai = daiSelect && daiSelect.tagName === 'SELECT' ? daiSelect.value : (document.getElementsByName('update_大分類')[0] ? document.getElementsByName('update_大分類')[0].value : '');
    const selectedChu = chuSelect.tagName === 'SELECT' ? chuSelect.value : (document.getElementsByName('update_中分類')[0] ? document.getElementsByName('update_中分類')[0].value : '');
    
    shoSelect.innerHTML = '<option value="">選択してください</option>';
    
    const uniqueSho = new Set();
    if (classifications && Array.isArray(classifications)) {{
        classifications.forEach(item => {{
            if ((selectedGroup === '' || item.group === selectedGroup) && 
                (selectedDai === '' || item.dai === selectedDai) && 
                (selectedChu === '' || item.chu === selectedChu)) {{
                if (item.sho) uniqueSho.add(item.sho);
            }}
        }});
    }}
    
    Array.from(uniqueSho).sort().forEach(sho => {{
        const option = document.createElement('option');
        option.value = sho;
        option.textContent = sho;
        shoSelect.appendChild(option);
    }});
}}

document.addEventListener('DOMContentLoaded', function() {{
    if (document.getElementById('group') && document.getElementById('group').tagName === 'SELECT') {{
        if (document.getElementById('group').value) {{
            updateDaiCategories();
        }}
    }} else if (document.getElementById('majorCategory') && document.getElementById('majorCategory').tagName === 'SELECT') {{
         if (document.getElementById('majorCategory').value) {{
            updateChuCategories();
        }}
    }} else if (document.getElementById('mediumCategory') && document.getElementById('mediumCategory').tagName === 'SELECT') {{
         if (document.getElementById('mediumCategory').value) {{
            updateShoCategories();
        }}
    }}

    const regularSwitch = document.getElementById('update_regular');
    if (regularSwitch) {{
        const cardElement = regularSwitch.closest('.card'); 
        
        function applyStyling() {{
            if (cardElement) {{
                if (regularSwitch.checked) {{
                    cardElement.classList.remove('bg-irregular-task');
                    cardElement.classList.add('bg-regular-task');
                }} else {{
                    cardElement.classList.remove('bg-regular-task');
                    cardElement.classList.add('bg-irregular-task');
                }}
            }}
        }}
        
        applyStyling();
        regularSwitch.addEventListener('change', applyStyling);
    }}
}});
</script>
"""

        header()
        nav()

        # 背景色クラス
        edit_bg_class = "bg-regular-task" if target_task_detail.get('regular', 'Regular') == 'Regular' else "bg-irregular-task"

        print("""
        <div class="container my-4">
            <div class="row justify-content-center">
                <div class="col-lg-10">
                    <form action="{REQUEST_URL}" method="post">
                        <div class="card shadow">
                            <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                                <h3 class="mb-0"><i class="bi bi-pencil-square"></i> タスク編集</h3>
                                {regular_html}
                            </div>
                            <div class="card-body">
                                <input type="hidden" name="mode" value="update"/>
                                <input type="hidden" name="update_task_id" value="{edit_task_id}" />
                                
                                <div class="form-group mb-3">
                                    <label for="taskName" class="form-label"><i class="bi bi-file-earmark-text"></i> タスク名</label>
                                    <input type="text" id="taskName" name="update_task_name" value="{task_name}" class="form-control form-control-lg" required/>
                                </div>

                                <div class="form-group mb-4">
                                    <label for="content" class="form-label"><i class="bi bi-card-text"></i> 内容</label>
                                    <button type="button" class="btn btn-sm btn-outline-secondary ms-2 open-template-modal-button" data-target-textarea="content"><i class="bi bi-file-earmark-plus"></i> テンプレートを開く</button>
                                    <textarea id="content" name="update_content" class="form-control" rows="10">{content}</textarea>
                                    <small class="form-text text-muted">マークダウン記法が使用できます</small>
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
                                </div>
                                
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        {pinned_html}
                                    </div>
                                </div>
                                
                                {tags_html}

                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        {create_group_html}
                                    </div>
                                </div>

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
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        
        {create_regular_js}
        
        """.format(
            edit_task_id=edit_task_id, 
            task_name=target_task_detail["name"], 
            create_html=create_html, 
            update_html=update_html, 
            status_html=status_html, 
            category_html=category_html, 
            create_group_html=create_group_html, 
            担当者_html=担当者_html, 
            pinned_html=pinned_html, 
            tags_html=tags_html, 
            create_大分類_html=create_大分類_html, 
            create_中分類_html=create_中分類_html, 
            create_小分類_html=create_小分類_html, 
            regular_html=regular_html, 
            content=target_task_detail['content'], 
            create_regular_js=create_regular_js,
            REQUEST_URL=REQUEST_URL,
            edit_bg_class=edit_bg_class
        ))
        
        print(TEMPLATE_MODAL_HTML_SCRIPT) # 先に関数定義を含むスクリプトを出力
        templates_json_data = json.dumps(load_templates())
        print(f"<script>setTemplatesData({templates_json_data});</script>")
        footer()

# タスク詳細画面 --------------------------------------------------------------------------------------------
    elif mode=="view":
        status = {}
        status = getStatus(view_task_id, "view")

        # ピン止めアイコン
        pin_icon_div = '<span class="fs-4">📌</span>' if status.get('pinned', False) else ''
        
        # タグリンク
        tag_links = ' '.join([f'<span class="badge bg-secondary me-1">{tag}</span>' for tag in status.get('tags', [])])
        
        # カード色の設定（継続か完了かで背景色を変える）
        card_color = " bg-secondary" if status["status"] == "完了" else ""
        
        # Regular/Irregular バッジ
        regular_badge = '<span class="badge bg-info me-1">Regular</span>' if status.get('regular', 'Regular') == 'Regular' else '<span class="badge bg-warning me-1">Irregular</span>'

        header()
        nav()

        # 背景色クラス
        view_bg_class = "bg-regular-task" if status.get('regular', 'Regular') == 'Regular' else "bg-irregular-task"

        print(f"""
        <div class="container my-4">
            <div class="row justify-content-center">
                <div class="col-lg-10">
                    <div class="card{card_color} {view_bg_class} shadow">
                        <div class="card-body">
                            <h5 class="card-title mb-3 fw-bold">
                                <a href="./index.py?category={status["category"]}" class="text-decoration-none me-3">
                                    <span class="badge bg-primary">{status["category"]}</span>
                                </a>
                                <a href="./index.py?mode=view&view_task_id={view_task_id}" class="text-decoration-none text-dark">
                                    {status["name"]}
                                </a>
                            </h5>
                            
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <div class="d-flex align-items-center">
                                    <!--{regular_badge}-->
                                </div>
                                <div>
                                    {pin_icon_div}
                                </div>
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
                                    <small class="text-muted">
                                        <i class="bi bi-calendar-check"></i> 更新日: {datetime.datetime.strptime(status["update_date"], "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%dT%H:%M:%S")} &nbsp;|&nbsp; 
                                        <i class="bi bi-calendar-plus"></i> 作成日: {datetime.datetime.strptime(status["create_date"], "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%dT%H:%M:%S")} &nbsp;|&nbsp; 
                                        <i class="bi bi-calendar2-check"></i> 完了日: {datetime.datetime.strptime(status.get("complete_date",""), "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%dT%H:%M:%S") if status.get("complete_date") else ""}
                                    </small>
                                </div>
                            </div>

                            <div class="mb-3">
                                {tag_links}
                            </div>

                            <div class="row mb-3">
                                <div class="col-md-12">
                                    <div class="d-flex flex-wrap">
                                        {status.get('groupCategory', '') and f'<span class="badge bg-primary me-2"><i class="bi bi-people"></i> グループ: {status.get("groupCategory", "")}</span>' or ''}
                                        {status.get('大分類', '') and f'<span class="badge bg-primary me-2"><i class="bi bi-diagram-3"></i> 大分類: {status.get("大分類", "")}</span>' or ''}
                                        {status.get('中分類', '') and f'<span class="badge bg-primary me-2"><i class="bi bi-diagram-2"></i> 中分類: {status.get("中分類", "")}</span>' or ''}
                                        {status.get('小分類', '') and f'<span class="badge bg-primary me-2"><i class="bi bi-diagram-1"></i> 小分類: {status.get("小分類", "")}</span>' or ''}
                                    </div>
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
        
        """.format(
            view_task_id=view_task_id, 
            task_name=status["name"], 
            pin_icon_div=pin_icon_div, 
            tag_links=tag_links, 
            card_color=card_color, 
            regular_badge=regular_badge, 
            view_bg_class=view_bg_class
        ))
        
        print(TEMPLATE_MODAL_HTML_SCRIPT) # 先に関数定義を含むスクリプトを出力
        templates_json_data = json.dumps(load_templates())
        print(f"<script>setTemplatesData({templates_json_data});</script>")
        footer()

# 更新処理 --------------------------------------------------------------------------------------------
    elif mode=="update":
        # 更新内容を整形
        updates = {
            "name": update_task_name,
            "status": update_state_select,
            "update_date": update_update_datetime or datetime.datetime.utcnow().isoformat(timespec="seconds"),
            "pinned": update_pinned,
            "category": update_category_input,
            "group_category": update_groupCategory,
            "担当者": update_担当者,
            "大分類": update_大分類,
            "中分類": update_中分類,
            "小分類": update_小分類,
            "regular": "Regular" if update_regular else "Irregular",
            "content": update_content.replace('\r\n', '\n').replace('\r', '\n'),
            "tags": [t.strip() for t in update_tags.split(',') if t.strip()],
        }

        # 完了ステータスの場合は complete_date を付与
        if update_state_select == "COMPLETE" and update_update_datetime:
            updates["complete_date"] = update_update_datetime
        elif update_state_select == "CONTINUE":
            updates["complete_date"] = None

        try:
            db.update(update_task_id, updates)
        except Exception:
            import traceback, html
            header()
            print("<pre>")
            print(html.escape(traceback.format_exc()))
            print("</pre>")
            footer()
            sys.exit(0)

        url = ("http://" + os.environ['HTTP_HOST'] + REQUEST_URL).split("?")[0]
        print(f"<meta http-equiv=\"refresh\" content=\"0;URL={url}\" />")

# 作成画面 --------------------------------------------------------------------------------------------
    elif mode=="create":
        classifications = getClassifications()
        tasks = []
        files = os.listdir(task_folder_path)
        
        # ここでドロップダウンオプションを生成
        group_categories = getGroupCategories(classifications)
        group_options = ""
        for group in group_categories:
            group_options += f'<option value="{group}">{group}</option>'
            
        dai_options = ""
        dai_categories = getDaiCategories(classifications)
        for dai in dai_categories:
            dai_options += f'<option value="{dai}">{dai}</option>'
            
        chu_options = ""
        chu_categories = getChuCategories(classifications, "")
        for chu in chu_categories:
            chu_options += f'<option value="{chu}">{chu}</option>'
            
        sho_options = ""
        sho_categories = getShoCategories(classifications, "", "")
        for sho in sho_categories:
            sho_options += f'<option value="{sho}">{sho}</option>'
        
        uuid = str(uuid.uuid4())
        create_create_datetime = str(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
        create_update_datetime = create_create_datetime
        create_html = ""
        # ステータス選択のドロップダウン
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
    <p class="form-control-plaintext">{create_create_datetime}</p>
    <input type="hidden" name="create_create_datetime" value="{create_create_datetime}" />
</div>
"""
        update_html = f"""
<div class="form-group mb-2">
    <label class="form-label"><i class="bi bi-calendar-check"></i> 更新時間</label>
    <p class="form-control-plaintext">{create_update_datetime}</p>
    <input type="hidden" name="create_update_datetime" value="{create_update_datetime}" />
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
    <label for="tags" class="form-label"><i class="bi bi-tags"></i> タグ（カンマ区切り）</label>
    <input type="text" id="tags" name="create_tags" value="" class="form-control" placeholder="例：重要, フォローアップ, 会議"/>
</div>"""

        create_担当者_html = f"""
<div class="form-group mb-3">
    <label for="assignee" class="form-label"><i class="bi bi-person"></i> 担当者</label>
    <input type="text" id="assignee" name="create_担当者" value="" class="form-control"/>
</div>"""

        create_group_html = f"""
<div class="form-group mb-3">
    <label for="group" class="form-label"><i class="bi bi-people"></i> グループ</label>
    <select id="group" name="create_groupCategory" class="form-select" onchange="updateDaiCategories()">
        <option value="">選択してください</option>
        {group_options}
    </select>
</div>"""

        create_大分類_html = f"""
<div class="form-group mb-3">
    <label for="majorCategory" class="form-label"><i class="bi bi-diagram-3"></i> 大分類</label>
    <select id="majorCategory" name="create_大分類" class="form-select" onchange="updateChuCategories()">
        <option value="">選択してください</option>
        {dai_options}
    </select>
</div>"""

        create_中分類_html = f"""
<div class="form-group mb-3">
    <label for="mediumCategory" class="form-label"><i class="bi bi-diagram-2"></i> 中分類</label>
    <select id="mediumCategory" name="create_中分類" class="form-select" onchange="updateShoCategories()">
        <option value="">選択してください</option>
        {chu_options}
    </select>
</div>"""

        create_小分類_html = f"""
<div class="form-group mb-3">
    <label for="smallCategory" class="form-label"><i class="bi bi-diagram-1"></i> 小分類</label>
    <select id="smallCategory" name="create_小分類" class="form-select">
        <option value="">選択してください</option>
        {sho_options}
    </select>
</div>"""

        # Regular/Irregular スイッチのHTML
        regular_html = """
<div class="form-check form-switch mb-3">
  <input class="form-check-input" type="checkbox" role="switch" id="create_regular" name="create_regular" checked>
  <label class="form-check-label" for="create_regular">定型タスク (Regular)</label>
</div>
"""

        # 背景色クラス（デフォルトは定型）
        create_bg_class = "bg-regular-task"

        # JavaScriptのための変数準備
        create_regular_js = """
<script>
// 分類データ
const classifications = """ + str(classifications).replace("'", '"') + """;

// グループが変更されたときに大分類を更新
function updateDaiCategories() {
    const groupSelect = document.getElementById('group');
    const daiSelect = document.getElementById('majorCategory');
    const selectedGroup = groupSelect.value;
    
    // 大分類のオプションをクリア
    daiSelect.innerHTML = '<option value="">選択してください</option>';
    
    // 選択されたグループに基づいて大分類を更新
    const uniqueDai = new Set();
    classifications.forEach(item => {
        if (selectedGroup === '' || item.group === selectedGroup) {
            uniqueDai.add(item.dai);
        }
    });
    
    // 大分類のオプションを追加
    Array.from(uniqueDai).forEach(dai => {
        const option = document.createElement('option');
        option.value = dai;
        option.textContent = dai;
        daiSelect.appendChild(option);
    });
    updateChuCategories();
}

// 大分類が変更されたときに中分類を更新
function updateChuCategories() {
    const groupSelect = document.getElementById('group');
    const daiSelect = document.getElementById('majorCategory');
    const chuSelect = document.getElementById('mediumCategory');
    const selectedGroup = groupSelect.value;
    const selectedDai = daiSelect.value;
    
    // 中分類のオプションをクリア
    chuSelect.innerHTML = '<option value="">選択してください</option>';
    
    // 選択されたグループと大分類に基づいて中分類を更新
    const uniqueChu = new Set();
    classifications.forEach(item => {
        if ((selectedGroup === '' || item.group === selectedGroup) && 
            (selectedDai === '' || item.dai === selectedDai)) {
            uniqueChu.add(item.chu);
        }
    });
    
    // 中分類のオプションを追加
    Array.from(uniqueChu).forEach(chu => {
        const option = document.createElement('option');
        option.value = chu;
        option.textContent = chu;
        chuSelect.appendChild(option);
    });
    updateShoCategories();
}

// 中分類が変更されたときに小分類を更新
function updateShoCategories() {
    const groupSelect = document.getElementById('group');
    const daiSelect = document.getElementById('majorCategory');
    const chuSelect = document.getElementById('mediumCategory');
    const shoSelect = document.getElementById('smallCategory');
    const selectedGroup = groupSelect.value;
    const selectedDai = daiSelect.value;
    const selectedChu = chuSelect.value;
    
    // 小分類のオプションをクリア
    shoSelect.innerHTML = '<option value="">選択してください</option>';
    
    // 選択されたグループ、大分類、中分類に基づいて小分類を更新
    const uniqueSho = new Set();
    classifications.forEach(item => {
        if ((selectedGroup === '' || item.group === selectedGroup) && 
            (selectedDai === '' || item.dai === selectedDai) && 
            (selectedChu === '' || item.chu === selectedChu)) {
            uniqueSho.add(item.sho);
        }
    });
    
    // 小分類のオプションを追加
    Array.from(uniqueSho).forEach(sho => {
        const option = document.createElement('option');
        option.value = sho;
        option.textContent = sho;
        shoSelect.appendChild(option);
    });
}

// 編集モードでの値の設定
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('group') && document.getElementById('group').tagName === 'SELECT') {{
        if (document.getElementById('group').value) {{
            updateDaiCategories();
        }}
    }} else if (document.getElementById('majorCategory') && document.getElementById('majorCategory').tagName === 'SELECT') {{
         if (document.getElementById('majorCategory').value) {{
            updateChuCategories();
        }}
    }} else if (document.getElementById('mediumCategory') && document.getElementById('mediumCategory').tagName === 'SELECT') {{
         if (document.getElementById('mediumCategory').value) {{
            updateShoCategories();
        }}
    }}

    const regularSwitch = document.getElementById('create_regular');
    if (!regularSwitch) return;
    const cardElement = regularSwitch.closest('.card'); 
    
    // 初期状態の設定（デフォルトはchecked=trueなのでborder-info）
    cardElement.classList.add('border-info');
    
    // スイッチの変更を監視
    regularSwitch.addEventListener('change', function() {
        if (this.checked) {
            cardElement.classList.remove('border-danger');
            cardElement.classList.add('border-info');
        } else {
            cardElement.classList.remove('border-info');
            cardElement.classList.add('border-danger');
        }
    });
});

// Regular/Irregularスイッチの背景色変更
document.addEventListener('DOMContentLoaded', function() {
    const regularSwitch = document.getElementById('create_regular');
    if (!regularSwitch) return;
    const cardElement = regularSwitch.closest('.card'); 
    
    // 初期状態の設定（デフォルトはchecked=trueなのでbg-regular-task）
    cardElement.classList.add('bg-regular-task');
    
    // スイッチの変更を監視
    regularSwitch.addEventListener('change', function() {
        if (this.checked) {
            cardElement.classList.add('bg-regular-task');
            cardElement.classList.remove('bg-irregular-task');
        } else {
            cardElement.classList.remove('bg-regular-task');
            cardElement.classList.add('bg-irregular-task');
        }
    });
});
</script>
"""

        header()
        nav()

        print("""
        <div class="container my-4">
            <div class="row justify-content-center">
                <div class="col-lg-10">
                    <form action="{REQUEST_URL}" method="post">
                        <div class="card shadow">
                            <div class="card-header bg-success text-white d-flex justify-content-between align-items-center">
                                <h3 class="mb-0"><i class="bi bi-plus-circle"></i> 新規タスク作成</h3>
                                {regular_html}
                            </div>
                            <div class="card-body">
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
                                        {create_group_html}
                                    </div>
                                    <div class="col-md-6">
                                        {create_担当者_html}
                                    </div>
                                </div>
                                
                                <div class="row mb-3">
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
                                    <label for="content_create" class="form-label"><i class="bi bi-card-text"></i> 内容</label>
                                    <button type="button" class="btn btn-sm btn-outline-secondary ms-2 open-template-modal-button" data-target-textarea="content_create"><i class="bi bi-file-earmark-plus"></i> テンプレートを開く</button>
                                    <textarea id="content_create" name="create_content" class="form-control" rows="10"></textarea>
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
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        
        {create_regular_js}
        
        """.format(uuid=uuid, create_html=create_html, update_html=update_html, status_html=status_html, category_html=category_html, create_group_html=create_group_html, create_担当者_html=create_担当者_html, pinned_html=pinned_html, tags_html=tags_html, create_大分類_html=create_大分類_html, create_中分類_html=create_中分類_html, create_小分類_html=create_小分類_html, regular_html=regular_html, create_regular_js=create_regular_js, REQUEST_URL=REQUEST_URL, create_bg_class=create_bg_class))
        
        print(TEMPLATE_MODAL_HTML_SCRIPT) # 先に関数定義を含むスクリプトを出力
        templates_json_data = json.dumps(load_templates())
        print(f"<script>setTemplatesData({templates_json_data});</script>")
        footer()
        
# 作成処理 --------------------------------------------------------------------------------------------
    elif mode=="write":
        # タスク辞書を構築してデータベースへ登録
        task_dict = {
            "id": create_task_id or str(uuid.uuid4()),
            "name": create_task_name,
            "status": create_state_select or "CONTINUE",
            "create_date": create_create_datetime or datetime.datetime.utcnow().isoformat(timespec="seconds"),
            "update_date": create_update_datetime or datetime.datetime.utcnow().isoformat(timespec="seconds"),
            "complete_date": (create_create_datetime if create_state_select == "COMPLETE" else None),
            "pinned": create_pinned,
            "category": create_category_input,
            "group_category": create_groupCategory,
            "担当者": create_担当者,
            "大分類": create_大分類,
            "中分類": create_中分類,
            "小分類": create_小分類,
            "regular": "Regular" if create_regular else "Irregular",
            "content": create_content.replace('\r\n', '\n').replace('\r', '\n'),
            # タグはカンマ区切り文字列→リストへ変換し、空要素除外
            "tags": [t.strip() for t in create_tags.split(',') if t.strip()],
        }

        # データベースへ挿入
        try:
            db.insert(task_dict)
        except Exception as e:
            # DB エラー時は簡易的にスタックトレースをブラウザへ表示してデバッグしやすくする
            import traceback, html
            header()
            print("<pre>")
            print(html.escape(traceback.format_exc()))
            print("</pre>")
            footer()
            sys.exit(0)

        # 登録後にリダイレクト
        url = ("http://" + os.environ['HTTP_HOST'] + REQUEST_URL).split("?")[0]
        print(f"<meta http-equiv=\"refresh\" content=\"0;URL={url}\" />")
        
# 削除処理 --------------------------------------------------------------------------------------------
    elif mode=="delete":
        try:
            db.delete(delete_task_id)
        except Exception:
            import traceback, html
            header()
            print("<pre>")
            print(html.escape(traceback.format_exc()))
            print("</pre>")
            footer()
            sys.exit(0)
        url = ("http://" + os.environ['HTTP_HOST'] + REQUEST_URL).split("?")[0]
        print(f"<meta http-equiv=\"refresh\" content=\"0;URL={url}\" />")

# Legacy task folder import
    elif mode=="import":
        imported, skipped = import_legacy_tasks()
        header()
        nav()
        print(f"<div class='container my-5'><div class='alert alert-success'>Legacy tasks imported: {imported} (skipped {skipped})</div></div>")

        print(TEMPLATE_MODAL_HTML_SCRIPT) # 先に関数定義を含むスクリプトを出力
        templates_json_data = json.dumps(load_templates())
        print(f"<script>setTemplatesData({templates_json_data});</script>")
        footer()
