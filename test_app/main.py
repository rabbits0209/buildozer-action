import requests
import json
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.text import LabelBase  # 用来设置字体
import threading
import time

API_URL = "https://kimi.moonshot.cn/api/chat"
API_HEADERS = {
    "Authorization": "Bearer eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ1c2VyLWNlbnRlciIsImV4cCI6MTc0NTEzMTY5NSwiaWF0IjoxNzM3MzU1Njk1LCJqdGkiOiJjdTZ2M2J0M3Y4OWpxczFoNGNhMCIsInR5cCI6ImFjY2VzcyIsImFwcF9pZCI6ImtpbWkiLCJzdWIiOiJjdTZ2M2JsM3Y4OWpxczFoNDg0MCIsInNwYWNlX2lkIjoiY3U2dXZkbDN2ODlqcXMxZjk0Y2ciLCJhYnN0cmFjdF91c2VyX2lkIjoiY3U2dXZkbDN2ODlqcXMxZjk0YzAiLCJzc2lkIjoiMTczMTEyODI4MTM5MTU3NTEyMCIsImRldmljZV9pZCI6Ijc0NjE4ODI4NDY0MTI1NzQyMDkifQ.XhAQLZSp8YAbh77zYwVQwVnXKlxAyiJON9qECU2LMjhSoV2MjvpXtaYOkrBdbDn0E73jfzJ8HTbDWYu5eq4nJQ"
}

chat_id = None  # 用于存储会话ID

# 添加中文字体路径
LabelBase.register(name="SimHei", fn_regular="SimHei.ttf")  # 请确保字体文件在同级目录下，或者指定路径

def create_chat():
    """第一次请求，创建会话并获取 chat_id"""
    global chat_id
    first_request_payload = {
        "name": "rebot",
        "born_from": "chat",
        "kimiplus_id": "kimi",
        "is_example": False,
        "source": "web",
        "tags": []
    }

    response = requests.post(API_URL, headers=API_HEADERS, json=first_request_payload)

    if response.status_code == 200:
        try:
            response_data = response.json()
            chat_id = response_data.get("id")
            if not chat_id:
                raise ValueError("无法获取会话ID")
            print("会话已创建，Chat ID: ", chat_id)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"创建会话失败: {e}")
    else:
        print(f"创建会话失败，状态码: {response.status_code}")

def send_message_to_bot(user_message):
    """发送消息到机器人并获取回复"""
    if not chat_id:
        print("错误: 会话未创建，请先创建会话")
        return "会话创建失败"

    second_request_payload = {
        "kimiplus_id": "kimi",
        "extend": {"sidebar": True},
        "use_research": False,
        "use_search": True,
        "messages": [{"role": "user", "content": user_message}],
        "segment_id": None,
        "refs": [],
        "history": [],
        "scene_labels": []
    }

    second_request_url = f"{API_URL}/{chat_id}/completion/stream"
    assistant_message = ""
    try:
        second_response = requests.post(second_request_url, headers=API_HEADERS, json=second_request_payload, stream=True)

        if second_response.status_code == 200:
            for line in second_response.iter_lines():
                if line:
                    line_text = line.decode("utf-8").strip()
                    if line_text.startswith("data:"):
                        line_text = line_text[5:].strip()
                        if line_text:
                            data = json.loads(line_text)
                            event_type = data.get("event")
                            if event_type == "cmpl":
                                assistant_message += data.get("text", "")
                            elif event_type == "all_done":
                                return assistant_message
        else:
            print(f"请求失败，状态码: {second_response.status_code}")
            return "请求失败，状态码: {}".format(second_response.status_code)
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return "请求失败: {}".format(e)

class ChatApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical')

        # Chat output label with text wrapping enabled
        self.chat_output = Label(
            size_hint_y=0.8, 
            text="欢迎来到聊天机器人！", 
            font_name="SimHei", 
            halign='left', 
            valign='top', 
            text_size=(400, None)  # 控制文本宽度自动换行
        )
        self.layout.add_widget(self.chat_output)

        # User input field
        self.user_input = TextInput(size_hint_y=0.1, multiline=False, font_name="SimHei")
        self.layout.add_widget(self.user_input)

        # Send button
        self.send_button = Button(text="发送", size_hint_y=0.1, font_name="SimHei")
        self.send_button.bind(on_press=self.on_send)
        self.layout.add_widget(self.send_button)

        # 创建会话
        if not chat_id:
            create_chat()

        return self.layout

    def on_send(self, instance):
        user_message = self.user_input.text
        if user_message:
            # 创建线程以免阻塞主线程
            threading.Thread(target=self.handle_message, args=(user_message,)).start()

            # 清空输入框
            self.user_input.text = ""

    def handle_message(self, user_message):
        # 显示用户消息
        self.chat_output.text += f"\n你: {user_message}"

        # 获取机器人回复并更新UI
        response = send_message_to_bot(user_message)
        self.chat_output.text += f"\n机器人: {response}"

if __name__ == "__main__":
    ChatApp().run()
