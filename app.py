import sys
import os
import io
from flask import Flask, jsonify, request, render_template, session, redirect, url_for, send_file
from flask_socketio import SocketIO
import threading
from config import SECRET_KEY, CORS_ALLOWED_ORIGINS, OUTPUT_DIR
from chrome_driver import get_chrome_driver
from scraper import extract_business_info
from utils import save_to_csv

# 设置标准输出和标准错误流的编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 初始化 Flask 应用
app = Flask(__name__)
app.secret_key = SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins=CORS_ALLOWED_ORIGINS)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'password':
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

    def background_extraction(search_url, limit, proxy=None):
        driver = None
        with app.app_context():
            try:
                driver, proxy_info = get_chrome_driver(proxy)
                socketio.emit('progress_update', {'progress': 0, 'message': '正在初始化浏览器...' if not proxy_info else proxy_info})

                # 测试代理是否生效
                try:
                    driver.set_page_load_timeout(30)
                    driver.get("http://httpbin.org/ip")
                    ip_info = driver.page_source
                    print(f"当前 IP 信息: {ip_info}")
                    socketio.emit('progress_update', {'progress': 5, 'message': f'代理测试 IP: {ip_info[:100]}...'})
                except Exception as e:
                    print(f"代理测试失败: {e}", file=sys.stderr)
                    socketio.emit('progress_update', {'progress': 5, 'message': f'代理测试失败: {e}'})
                    return

                # 执行提取任务
                extracted_data = []
                for progress, current, business_data, message in extract_business_info(driver, search_url, limit=limit):
                    if business_data:
                        extracted_data.append(business_data)
                        socketio.emit('progress_update', {
                            'progress': progress,
                            'current': current,
                            'business_data': business_data
                        })
                    elif message:
                        if "失败" in message or "出错" in message:
                            socketio.emit('progress_update', {'progress': progress, 'message': message})
                            return
                        else:
                            socketio.emit('progress_update', {'progress': progress, 'message': message})

                if extracted_data:
                    csv_filename = save_to_csv(extracted_data)
                    socketio.emit('progress_update', {
                        'progress': 100,
                        'csv_file': csv_filename,
                        'message': '提取完成'
                    })
                else:
                    socketio.emit('progress_update', {
                        'progress': 100,
                        'message': '未提取到任何数据'
                    })
            except Exception as e:
                print(f"后台任务发生异常: {e}", file=sys.stderr)
                socketio.emit('progress_update', {
                    'progress': 100,
                    'message': f'后台任务出错: {e}'
                })
            finally:
                if driver:
                    driver.quit()

    thread = threading.Thread(target=background_extraction, args=(url, limit, proxy))
    thread.daemon = True
    thread.start()

    return jsonify({"status": "success", "message": "任务已启动，正在提取数据..."})

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)