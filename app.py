import sys
import io
import os
import threading
from flask import Flask, jsonify, request, render_template, session, redirect, url_for, send_file
from flask_socketio import SocketIO
from config import SECRET_KEY, CORS_ALLOWED_ORIGINS, OUTPUT_DIR
from chrome_driver import get_chrome_driver
from scraper import extract_business_info
from contact_scraper import extract_contact_info
from utils import save_to_csv, save_to_excel

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

app = Flask(__name__)
app.secret_key = SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins=CORS_ALLOWED_ORIGINS)

# 存储提取的商家数据
business_data_store = []

# 全局任务管理器：存储线程和 driver 实例
running_tasks = {}  # 格式: {task_id: {'thread': Thread, 'driver': WebDriver}}

def terminate_all_tasks():
    """终止所有正在运行的任务和 driver 实例"""
    global running_tasks
    for task_id, task_info in list(running_tasks.items()):  # 使用 list 避免运行时修改字典
        thread = task_info['thread']
        driver = task_info['driver']
        try:
            if driver:
                driver.quit()
                print(f"任务 {task_id} 的 Selenium driver 已终止", file=sys.stderr)
            if thread.is_alive():
                # 注意：Python 线程无法强制终止，这里仅记录状态
                print(f"任务 {task_id} 的线程仍在运行，等待其自然结束", file=sys.stderr)
        except Exception as e:
            print(f"终止任务 {task_id} 失败: {e}", file=sys.stderr)
    running_tasks.clear()
    print("所有任务已清理", file=sys.stderr)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == app.config['password']:
            session['logged_in'] = True
            return redirect(url_for('operation'))
        else:
            return render_template('login.html', error="用户名或密码错误")
    return render_template('login.html')

@app.route('/operation')
def operation():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('operation.html')

@app.route('/download/<filename>')
def download_file(filename):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        return "文件不存在", 404
    return send_file(filepath, as_attachment=True, download_name=filename)

@app.route('/start_extraction', methods=['POST'])
def start_extraction():
    if not session.get('logged_in'):
        return jsonify({"status": "error", "message": "请先登录"}), 401

    url = request.form.get('url')
    limit = request.form.get('limit')
    proxy = request.form.get('proxy')

    try:
        limit = int(limit)
        if limit <= 0:
            return jsonify({"status": "error", "message": "limit 必须大于 0"}), 400
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "limit 必须是一个有效的正整数"}), 400

    # 在新任务开始前终止所有现有任务
    terminate_all_tasks()
    socketio.emit('progress_update', {'progress': 0, 'message': '正在清理旧任务...'})

    # 生成唯一的任务 ID（这里简单用时间戳）
    task_id = f"extract_{os.urandom(4).hex()}"

    def background_extraction(search_url, limit, proxy=None, task_id=task_id):
        driver = None
        with app.app_context():
            try:
                driver, proxy_info = get_chrome_driver(proxy)
                running_tasks[task_id] = {'thread': threading.current_thread(), 'driver': driver}
                socketio.emit('progress_update', {'progress': 0, 'message': '正在初始化浏览器...' if not proxy_info else proxy_info})

                extracted_data = []
                for progress, current, business_data, message in extract_business_info(driver, search_url, limit):
                    if business_data:
                        extracted_data.append(business_data)
                    socketio.emit('progress_update', {
                        'progress': progress,
                        'current': current,
                        'business_data': business_data,
                        'message': message
                    })

                if extracted_data:
                    global business_data_store
                    business_data_store = extracted_data
                    csv_filename = save_to_excel(extracted_data)
                    socketio.emit('progress_update', {
                        'progress': 100,
                        'csv_file': csv_filename,
                        'message': '数据提取完成',
                        'data': extracted_data
                    })
                else:
                    socketio.emit('progress_update', {
                        'progress': 100,
                        'message': '未提取到任何数据'
                    })
            except Exception as e:
                print(f"后台任务 {task_id} 发生异常: {e}", file=sys.stderr)
                socketio.emit('progress_update', {
                    'progress': 100,
                    'message': f'后台任务出错: {e}'
                })
            finally:
                if driver:
                    driver.quit()
                if task_id in running_tasks:
                    del running_tasks[task_id]  # 任务完成后移除

    thread = threading.Thread(target=background_extraction, args=(url, limit, proxy, task_id))
    thread.daemon = True
    thread.start()

    return jsonify({"status": "success", "message": "任务已启动，正在提取数据...", "task_id": task_id})

@app.route('/extract_contacts', methods=['POST'])
def extract_contacts():
    if not session.get('logged_in'):
        return jsonify({"status": "error", "message": "请先登录"}), 401

    proxy = request.form.get('proxy')

    def background_contact_extraction(proxy=None):
        driver = None
        with app.app_context():
            try:
                if not business_data_store:
                    socketio.emit('contact_update', {
                        'progress': 100,
                        'message': '没有可用的商家数据，请先执行提取任务'
                    })
                    return

                driver, proxy_info = get_chrome_driver(proxy)
                socketio.emit('contact_update',
                              {'progress': 0, 'message': '正在初始化浏览器...' if not proxy_info else proxy_info})

                for i, name, business_data, message in extract_contact_info(driver, business_data_store):
                    socketio.emit('contact_update', {
                        'progress': int((i + 1) / len(business_data_store) * 100),
                        'name': name,
                        'business_data': business_data,
                        'message': message
                    })

                csv_filename = save_to_excel(business_data_store)
                socketio.emit('contact_update', {
                    'progress': 100,
                    'csv_file': csv_filename,
                    'message': '联系方式提取完成'
                })
            except Exception as e:
                print(f"联系方式提取任务发生异常: {e}", file=sys.stderr)
                socketio.emit('contact_update', {
                    'progress': 100,
                    'message': f'联系方式提取出错: {e}'
                })
            finally:
                if driver:
                    driver.quit()

    thread = threading.Thread(target=background_contact_extraction, args=(proxy,))
    thread.daemon = True
    thread.start()

    return jsonify({"status": "success", "message": "联系方式提取任务已启动..."})

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=80, debug=True)