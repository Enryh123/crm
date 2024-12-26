import sys
import json
import requests
import pickle
import os
import time
from datetime import datetime
from selenium import webdriver
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                             QVBoxLayout, QListWidget, QTextEdit, QPushButton,
                             QProgressBar, QLabel, QFrame, QDateTimeEdit, QMessageBox, QLineEdit)
from PyQt5.QtCore import Qt, QTimer, QDateTime
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("班级学生信息系统")
        self.setGeometry(100, 100, 1000, 600)

        # 初始化定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.progress_value = 0

        # 初始化cookie字符串
        self.cookie_string = None

        # 存储班级数据的字典
        self.class_data = {}
        # 存储学生数据的字典
        self.student_data = {}
        self.current_student_code = None

        # 初始化session
        self.session = self.initialize_session()

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建主垂直布局
        main_layout = QVBoxLayout(central_widget)

        # 创建上部分的水平布局
        top_layout = QHBoxLayout()

        # ===== 左侧部分 =====
        # 创建左侧容器
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setSpacing(5)  # 设置组件之间的间距

        # 创建搜索区域水平布局
        search_layout = QHBoxLayout()

        # 创建搜索输入框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入班级名称搜索")
        self.search_input.returnPressed.connect(self.on_search_clicked)

        # 创建搜索按钮
        self.search_button = QPushButton("搜索")
        self.search_button.setFixedWidth(60)
        self.search_button.clicked.connect(self.on_search_clicked)

        # 将搜索输入框和按钮添加到搜索布局
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)

        # 创建左侧列表
        self.left_list = QListWidget()
        self.left_list.setMinimumWidth(300)

        # 将搜索布局和列表添加到左侧布局
        left_layout.addLayout(search_layout)  # 添加搜索布局
        left_layout.addWidget(self.left_list)

        # ===== 中间部分 =====
        # 中间列表
        self.middle_list = QListWidget()
        self.middle_list.setMinimumWidth(200)

        # ===== 右侧部分 =====
        # 右侧容器
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # 创建学生信息显示区域
        self.student_info = QTextEdit()
        self.student_info.setMinimumHeight(150)
        self.student_info.setReadOnly(True)

        # 创建第一个分隔线
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.HLine)
        separator1.setFrameShadow(QFrame.Sunken)

        # 创建日期时间选择器区域
        datetime_widget = QWidget()
        datetime_layout = QVBoxLayout(datetime_widget)

        # 创建日期时间标签
        datetime_label = QLabel("选择日期和时间：")
        datetime_label.setStyleSheet("font-weight: bold;")

        # 创建日期时间选择器
        self.datetime_edit = QDateTimeEdit(self)
        self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.datetime_edit.setCalendarPopup(True)

        # 将标签和选择器添加到日期时间布局
        datetime_layout.addWidget(datetime_label)
        datetime_layout.addWidget(self.datetime_edit)

        # 创建第二个分隔线
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)

        # 创建输入框
        self.text_edit = QTextEdit()
        self.text_edit.setMinimumWidth(250)

        # 创建按钮
        self.button = QPushButton("提交")
        self.button.setFixedHeight(30)

        # 将组件添加到右侧布局
        right_layout.addWidget(self.student_info)
        right_layout.addWidget(separator1)
        right_layout.addWidget(datetime_widget)
        right_layout.addWidget(separator2)
        right_layout.addWidget(self.text_edit)
        right_layout.addWidget(self.button)

        # 将左中右部件添加到上部分布局
        top_layout.addWidget(left_container)
        top_layout.addWidget(self.middle_list)
        top_layout.addWidget(right_widget)

        # 创建底部状态区域
        bottom_layout = QHBoxLayout()

        # 创建状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setMinimumWidth(100)

        # 创建进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)

        # 将状态标签和进度条添加到底部布局
        bottom_layout.addWidget(self.status_label)
        bottom_layout.addWidget(self.progress_bar)

        # 将上部分和底部布局添加到主布局
        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)

        # 连接信号
        self.button.clicked.connect(self.on_button_clicked)
        self.left_list.itemClicked.connect(self.on_class_selected)
        self.middle_list.itemClicked.connect(self.on_student_selected)
        self.datetime_edit.dateTimeChanged.connect(self.on_datetime_changed)

        # 加载班级数据
        self.load_class_data()

    def on_search_clicked(self):
        """处理搜索按钮点击事件"""
        search_text = self.search_input.text().strip()
        self.load_class_data(search_text)

    def start_progress(self):
        """开始进度条动画"""
        self.progress_value = 0
        self.progress_bar.setValue(0)
        self.timer.start(30)

    def stop_progress(self):
        """停止进度条动画"""
        self.timer.stop()
        self.progress_bar.setValue(100)
        QTimer.singleShot(500, lambda: self.progress_bar.setValue(0))

    def update_progress(self):
        """更新进度条值"""
        self.progress_value += 5
        if self.progress_value >= 90:
            self.progress_value = 90
        self.progress_bar.setValue(self.progress_value)

    def load_class_data(self):
        self.status_label.setText("正在加载班级列表...")
        self.start_progress()

        url = "https://edu-ems-api.it61.cn/clazz/v1.0/clazz/normal/list"
        payload = json.dumps({
            "centerCode": "1052010303",
            "className": "WHL",
            "pageSize": 10,
            "pageNum": 1
        })
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9',
            'authorization': 'eyJraWQiOiJzaW0wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIxMDAxNDI0OTAsMSIsImF1ZCI6InRjdG1LQ1JNIiwiZXhwIjoxNzM1MTQyNDIxLCJpYXQiOjE3MzUxMjA4MjF9.8-kd44y9bc6i1gfyCqZqC20y2mCd28nsxmU181LLMJw',
            'content-type': 'application/json'
        }

        try:
            response = requests.post(url, headers=headers, data=payload)
            data = response.json()

            if data['code'] == 1000:
                self.left_list.clear()

                for record in data['data']['records']:
                    class_name = record['className']
                    class_code = record['classCode']
                    self.class_data[class_name] = class_code
                    self.left_list.addItem(class_name)

                self.status_label.setText("班级列表加载完成")
            else:
                self.status_label.setText(f"加载失败: {data['msg']}")

        except Exception as e:
            self.status_label.setText(f"错误: {str(e)}")

        finally:
            self.stop_progress()

    def on_class_selected(self, item):
        class_name = item.text()
        class_code = self.class_data.get(class_name)
        if class_code:
            self.load_student_data(class_code)

    def load_student_data(self, class_code):
        self.status_label.setText("正在加载学生列表...")
        self.start_progress()

        url = "https://edu-ems.it61.cn/edu2kcrm/edu/class/details/studentList"
        payload = json.dumps({
            "classCode": class_code,
            "statusList": [],
            "pageSize": 30,
            "pageNum": 1
        })
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9',
            'authorization': 'eyJraWQiOiJzaW0wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIxMDAxNDI0OTAsMSIsImF1ZCI6InRjdG1LQ1JNIiwiZXhwIjoxNzM1MTQyNDIxLCJpYXQiOjE3MzUxMjA4MjF9.8-kd44y9bc6i1gfyCqZqC20y2mCd28nsxmU181LLMJw',
            'content-type': 'application/json',
            'origin': 'https://edu-ems.it61.cn',
            'referer': 'https://edu-ems.it61.cn/',
            'Cookie': 'SESSION=0fa5aad0-73db-432c-8e76-d07a3bebf947; tedu.local.language=zh-CN'
        }

        try:
            response = requests.post(url, headers=headers, data=payload)
            data = response.json()

            if data['code'] == 1000:
                self.middle_list.clear()
                self.student_data.clear()

                for student in data['data']['records']:
                    student_name = student['studentName']
                    self.student_data[student_name] = student
                    self.middle_list.addItem(student_name)

                self.status_label.setText("学生列表加载完成")
            else:
                self.status_label.setText(f"加载失败: {data['msg']}")

        except Exception as e:
            self.status_label.setText(f"错误: {str(e)}")

        finally:
            self.stop_progress()

    # 修改on_student_selected方法
    def on_student_selected(self, item):
        """处理学生选择事件"""
        student_name = item.text()
        student_info = self.student_data.get(student_name)

        if student_info:
            # 获取学生的回访记录
            latest_visit_date = self.load_visit_records(student_info['studentCode'])

            # 格式化学生信息，包含最近回访日期
            info_text = (
                f"学生姓名: {student_info['studentName']}\n"
                f"学生编号: {student_info['studentCode']}\n"
                f"性别: {student_info['studentSex']}\n"
                f"年龄: {student_info['studentAge'] if student_info['studentAge'] else '未知'}\n"
                f"联系电话: {student_info['phoneNumberEncryption']}\n"
                f"城市: {student_info['city']}\n"
                f"所属机构: {student_info['orgCore']}\n"
                f"总课时: {student_info['totalClassHour']}\n"
                f"剩余课时: {student_info['surplusClassHour']}\n"
                f"状态: {student_info['statusString']}\n"
            )

            # 如果有回访记录，添加到信息中
            if latest_visit_date:
                info_text += f"最近回访时间: {latest_visit_date}\n"

            # 更新学生信息显示
            self.student_info.setText(info_text)
            self.student_info.setAlignment(Qt.AlignLeft)
            self.current_student_code = student_info['studentCode']

    def on_datetime_changed(self, qDateTime):
        """处理日期时间改变事件"""
        selected_datetime = qDateTime.toString("yyyy-MM-dd HH:mm:ss")
        print(f"选择的日期时间: {selected_datetime}")

    def on_button_clicked(self):
        """处理提交按钮点击事件"""
        try:
            print(self.current_student_code)
            # 获取当前选中的学生编号
            if not self.current_student_code:
                QMessageBox.warning(self, "提示", "请先选择一个学生")
                return

            # 获取输入框内容
            msg = self.text_edit.toPlainText().strip()
            if not msg:
                QMessageBox.warning(self, "提示", "请输入回访内容")
                return

            # 获取当前选择的日期时间
            visit_date = self.datetime_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss")

            # 计算下一次回访日期（当前日期+14天）
            next_visit = self.datetime_edit.dateTime().addDays(14)
            next_visit_date = next_visit.toString("yyyy-MM-dd")

            # 构建请求数据
            body_data = {
                "studentCode": self.current_student_code,
                "stu": self.current_student_code,
                "visitType": "XYHFLX02",
                "communicationMode": "GTFS003",
                "visitSubject": "XYHFZT002",
                "visitDate": visit_date,
                "nextVisitDate": next_visit_date,
                "evidenceText": "",
                "evidenceUrl": "",
                "evidenceText2": "",
                "evidenceUrl2": "",
                "editorValue": msg,
                "visitRecordValue": msg
            }

            # 将数据转换为 x-www-form-urlencoded 格式
            urlencoded_body = "&".join([f"{key}={requests.utils.quote(str(value))}"
                                        for key, value in body_data.items()])

            # 准备请求
            url = "https://crm.tctm.cn/stuVisit/save"
            headers = {
                'accept': '*/*',
                'accept-language': 'zh-CN,zh;q=0.9',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'cookie': self.cookie_string,
                'origin': 'https://crm.tctm.cn',
                'referer': 'https://crm.tctm.cn/stuVisit/toSavePage',
                'sec-ch-ua-mobile': '?0',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'x-requested-with': 'XMLHttpRequest'
            }

            # 发送请求
            self.status_label.setText("正在提交回访记录...")
            self.start_progress()

            response = requests.post(url, headers=headers, data=urlencoded_body)

            if response.status_code == 200:
                if response.text == "1":  # 成功响应为"1"
                    QMessageBox.information(self, "成功", "回访记录提交成功！")
                    self.text_edit.clear()  # 清空输入框

                    # 重新加载学生的回访记录
                    self.load_visit_records(self.current_student_code)
                else:
                    QMessageBox.warning(self, "失败", "提交失败，请重试")
            else:
                QMessageBox.warning(self, "错误", f"提交请求失败，状态码: {response.status_code}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"发生错误: {str(e)}")

        finally:
            self.stop_progress()
            self.status_label.setText("就绪")

    def get_new_session(self):
        """获取新的session"""
        try:
            # 使用Edge浏览器
            from selenium.webdriver.edge.options import Options

            # 配置Edge选项
            edge_options = Options()
            # edge_options.add_argument('--headless')  # 如果需要无界面模式可以取消注释
            service = Service(EdgeChromiumDriverManager().install())
            driver = webdriver.Edge(service=service, options=edge_options)

            driver.get('https://crm.tctm.cn/login?state=26&sso_ticket=No')

            # 显示提示对话框
            QMessageBox.information(self, "登录提示", "请扫描二维码登录，登录完成后对话框会自动关闭")

            time.sleep(3)
            driver.execute_script("window.scrollBy(1000, 0);")
            time.sleep(15)  # 等待扫码登录

            # 获取所有cookie
            cookies = driver.get_cookies()
            session = requests.Session()

            # 构建完整的cookie字符串
            cookie_pairs = []
            for cookie in cookies:
                session.cookies.set(cookie['name'], cookie['value'])
                cookie_pairs.append(f"{cookie['name']}={cookie['value']}")

            # 保存完整的cookie字符串
            self.cookie_string = "; ".join(cookie_pairs)

            driver.quit()

            # 更新session headers
            session.headers.update({
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'zh-CN,zh;q=0.9',
                'authorization': session.cookies.get('platform.sso.token'),
                'content-type': 'application/json',
                'cookie': self.cookie_string,  # 添加完整的cookie字符串
                'sec-ch-ua-mobile': '?0',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site'
            })

            return session

        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取新session失败: {str(e)}")
            return None

    def save_session(self, session, file_name='session.pkl'):
        """保存session和cookie字符串到本地文件"""
        data = {
            'session': session,
            'cookie_string': self.cookie_string
        }
        with open(file_name, 'wb') as file:
            pickle.dump(data, file)

    def load_session(self, file_name='session.pkl'):
        """从本地文件加载session和cookie字符串"""
        if os.path.exists(file_name):
            with open(file_name, 'rb') as file:
                data = pickle.load(file)
                self.cookie_string = data['cookie_string']
                return data['session']
        return None

    def load_visit_records(self, student_code):
        """加载学生回访记录"""
        url = f"https://crm.tctm.cn/stuVisit/list"
        params = {
            'studentCode': student_code,
            'informationCode': '',
            'sourcePage': ''
        }
        payload = "draw=1&pageSize=12&start=0"
        headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'zh-CN,zh;q=0.9',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'cookie': self.cookie_string,  # 使用保存的cookie字符串
            'origin': 'https://crm.tctm.cn',
            'referer': f'https://crm.tctm.cn/student/toDetail?stuCode={student_code}',
            'sec-ch-ua': '"Not:A-Brand";v="99", "Chromium";v="112"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest'
        }

        try:
            response = self.make_request(url, payload, "POST", params=params,
                                         headers=headers, use_json=False)
            if response:
                data = response.json()
                if data.get('data') and len(data['data']) > 0:
                    # 获取最近的一条回访记录
                    latest_visit = data['data'][0]
                    return latest_visit.get('visitDateStr', '')

        except Exception as e:
            print(f"获取回访记录失败: {str(e)}")

        return None

    def initialize_session(self):
        """初始化session，如果本地没有或已过期则重新获取"""
        session = self.load_session()

        if session is None:
            print("获取新的session")
            session = self.get_new_session()
            if session:
                self.save_session(session)
        else:
            print("使用已保存的session")
            print(f"Cookie string: {self.cookie_string}")

        self.session = session
        return session

    def check_session_valid(self, response):
        """检查session是否有效"""
        if response.status_code != 200:
            return False

        try:
            data = response.json()
            # 根据实际响应结构调整判断条件
            if data.get('code') == 1000 or 'data' in data:
                return True
            return False
        except:
            return False

    def refresh_session_if_needed(self):
        """如果需要则刷新session"""
        self.session = self.get_new_session()
        if self.session:
            self.save_session(self.session)
            return True
        return False

    def make_request(self, url, payload, method="POST", params=None, headers=None, use_json=True):
        """发送请求，支持不同的请求格式"""
        try:
            # 合并headers
            request_headers = self.session.headers.copy()
            if headers:
                request_headers.update(headers)

            # 根据use_json参数决定如何发送数据
            data = json.dumps(payload) if use_json else payload

            if params:
                response = self.session.request(method, url,
                                                params=params,
                                                headers=request_headers,
                                                data=data)
            else:
                response = self.session.request(method, url,
                                                headers=request_headers,
                                                data=data)

            if not self.check_session_valid(response):
                if self.refresh_session_if_needed():
                    # 使用新session重试请求
                    return self.make_request(url, payload, method, params, headers, use_json)
                return None

            return response

        except Exception as e:
            QMessageBox.critical(self, "错误", f"请求失败: {str(e)}")
            return None

    def load_class_data(self, class_name=""):
        """加载班级列表数据"""
        self.status_label.setText("正在加载班级列表...")
        self.start_progress()

        url = "https://edu-ems-api.it61.cn/clazz/v1.0/clazz/normal/list"
        payload = {
            "centerCode": "1052010303",
            "className": class_name,  # 使用搜索输入的班级名称
            "pageSize": 10,
            "pageNum": 1
        }

        try:
            response = self.make_request(url, payload)
            if response:
                data = response.json()

                if data['code'] == 1000:
                    self.left_list.clear()
                    self.class_data.clear()  # 清空之前的数据

                    for record in data['data']['records']:
                        class_name = record['className']
                        class_code = record['classCode']
                        self.class_data[class_name] = class_code
                        self.left_list.addItem(class_name)

                    if self.left_list.count() == 0:
                        self.status_label.setText("未找到匹配的班级")
                    else:
                        self.status_label.setText(f"找到 {self.left_list.count()} 个班级")
                else:
                    self.status_label.setText(f"加载失败: {data['msg']}")

        except Exception as e:
            self.status_label.setText(f"错误: {str(e)}")

        finally:
            self.stop_progress()

    def load_student_data(self, class_code):
        self.status_label.setText("正在加载学生列表...")
        self.start_progress()

        url = "https://edu-ems.it61.cn/edu2kcrm/edu/class/details/studentList"
        payload = {
            "classCode": class_code,
            "statusList": [],
            "pageSize": 30,
            "pageNum": 1
        }

        try:
            response = self.make_request(url, payload)
            if response:
                data = response.json()

                if data['code'] == 1000:
                    self.middle_list.clear()
                    self.student_data.clear()

                    for student in data['data']['records']:
                        student_name = student['studentName']
                        self.student_data[student_name] = student
                        self.middle_list.addItem(student_name)

                    self.status_label.setText("学生列表加载完成")
                else:
                    self.status_label.setText(f"加载失败: {data['msg']}")

        except Exception as e:
            self.status_label.setText(f"错误: {str(e)}")

        finally:
            self.stop_progress()




if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())