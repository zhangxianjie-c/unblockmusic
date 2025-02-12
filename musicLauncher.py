# This is a sample Python script.
import ctypes
import json
import os
import queue
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path

FILE_PATH = "saved_input.txt"  # 存储数据的文件路径


def is_admin():
    """检查当前是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def add_firewall_rule(exe_path):
    """使用 netsh 添加防火墙规则"""
    rule_name = "musicLauncher_AllowSubprocess"
    command = (
        f'netsh advfirewall firewall add rule '
        f'name="{rule_name}" '
        f'dir=in '
        f'action=allow '# 允许通信
        f'program="{exe_path}" '
        f'enable=yes'
        f'profile=any'  # 对所有网络类型生效
    )
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        return False


def get_subprocess_path():
    """智能获取子程序路径"""
    # 开发环境检测
    if getattr(sys, 'frozen', False):
        # 打包后模式
        base_path = Path(sys._MEIPASS)  # PyInstaller临时解压目录
    else:
        # 开发模式
        base_path = Path(__file__).parent  # 脚本所在目录

    # 路径探测优先级
    candidate_paths = [
        base_path / "child/unblockneteasemusic-win-x64.exe",     # 打包后的标准路径
        Path.cwd() / "unblockneteasemusic-win-x64.exe",          # 工作目录
        Path.home() / "AppData/Local/YourApp/unblockneteasemusic-win-x64.exe",  # 用户应用目录
        Path(sys.executable).parent / "unblockneteasemusic-win-x64.exe"  # 主程序所在目录
    ]

    for path in candidate_paths:
        if path.exists():
            return str(path.resolve())

    # 终极验证方案
    try:
        from winreg import OpenKey, QueryValue, HKEY_LOCAL_MACHINE
        with OpenKey(HKEY_LOCAL_MACHINE, r"SOFTWARE\musicLauncher") as key:
            return QueryValue(key, "InstallPath") + "\\unblockneteasemusic-win-x64.exe"
    except:
        raise FileNotFoundError("子程序定位失败，请检查安装完整性")


def load_input():
    """从文件加载上次输入的内容"""
    # if os.path.exists(FILE_PATH):  # 只有在文件存在时才加载
    #     with open(FILE_PATH, "r", encoding="utf-8") as file:
    #         return file.read().strip()
    # return ""  # 如果文件不存在，则返回空字符串
    """从系统目录加载"""
    config_path = Path(os.getenv('LOCALAPPDATA')) / "musicLauncher" / "config.json"
    try:
        with config_path.open() as f:
            return json.load(f).get("last_input", "")
    except (FileNotFoundError, json.JSONDecodeError):
        return ""


def run_external_exe():
    """ 运行打包的 EXE 文件 """
    exe_path = get_subprocess_path()
    if os.path.exists(exe_path):
        return subprocess.Popen(
            exe_path,
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,  # 自动将输出转换为字符串（Python 3.7+）
            encoding="utf-8"
            )



class Application:
    def __init__(self, master=None):
        self.master = master
        # 启动输出轮询
        self.master.after(100, self.check_output_queue)
        # 要读取的程序
        self.process = run_external_exe()
        self.output_queue = queue.Queue()
        self.master.title("网易云启动器")
        self.master.geometry("400x800")
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)
        self.label = tk.Label(self.master, text="网易云音乐路径：")
        self.label.pack(pady=5)

        # 创建输入框
        self.entry = tk.Entry(self.master, width=30)
        self.entry.pack(pady=5)

        # 定义按钮功能
        def get_input():
            self.save_input()
            self.run_music_exe()

        # 创建按钮
        self.button = tk.Button(self.master, text="提交", command=get_input)
        self.button.pack(pady=5)

        self.status_label = tk.Label(self.master, text="", fg="black")
        self.status_label.pack(pady=5)

        # 创建文本显示框
        self.log_label = tk.Text(self.master, wrap=tk.WORD)
        self.log_label.pack(expand=True, fill=tk.BOTH)
        self.log_label.config(state="disabled")

        self.input_text = load_input()
        if self.input_text:
            self.entry.insert(0, self.input_text)
            self.run_music_exe()

        # 启动线程读取输出
        threading.Thread(target=self.read_output, daemon=True).start()

        self.master.mainloop()  # 保持窗口打开

    def save_input(self):
        """将输入框内容保存到文件"""
        # with open(FILE_PATH, "w", encoding="utf-8") as file:
        #     file.write(self.entry.get())
        #     return self.entry.get()
        """存储到系统标准位置"""
        data_dir = Path(os.getenv('LOCALAPPDATA')) / "musicLauncher"
        data_dir.mkdir(exist_ok=True)  # 自动创建目录

        config_path = data_dir / "config.json"
        config = {"last_input": self.entry.get()}
        with config_path.open("w") as f:
            json.dump(config, f)

    def run_music_exe(self):
        try:
            process2 = subprocess.Popen(
                load_input(), creationflags=subprocess.CREATE_NO_WINDOW,)  # 指定编码（根据子进程输出的编码调整）
            if process2.poll() is None:  # poll() 返回 None 说明进程仍在运行
                self.status_label.config(text="✅ 启动成功", fg="green")
            else:
                self.status_label.config(text="❌ 启动失败", fg="red")
        except Exception as e:
            self.status_label.config(text=f"❌ 启动失败: {str(e)}", fg="red")

    def read_output(self):
        """持续读取子进程的输出并更新到文本框"""
        self.append_log("---------------->日志开始")
        while True:
            # 读取一行输出
            line = self.process.stdout.readline()
            if not line and self.process.poll() is not None:
                break  # 进程结束且无剩余输出时退出循环

            # 更新文本框
            if line:
                self.output_queue.put(line)

    def check_output_queue(self):
        """在主线程中处理输出队列"""
        while not self.output_queue.empty():
            line = self.output_queue.get()
            if line is None:  # 结束信号
                self.process_finished()
                continue

            self.append_log(line.rstrip('\n'))

        self.master.after(100, self.check_output_queue)

    def append_log(self, text):
        """安全更新日志显示"""
        self.log_label.config(state="normal")  # 临时启用编辑
        self.log_label.insert(tk.END, text + "\n")
        self.log_label.config(state="disabled")  # 再次禁用
        self.log_label.see(tk.END)  # 自动滚动到底部

    def process_finished(self):
        """进程结束时的处理"""
        return_code = self.process.poll()
        if return_code == 0:
            self.status_label.config(text="进程正常退出", fg="green")
        else:
            self.status_label.config(text=f"进程异常退出 (代码: {return_code})", fg="red")

    def show_error(self, message):
        """显示错误信息"""
        self.log_label.config(state=tk.NORMAL)
        self.log_label.insert(tk.END, f"ERROR: {message}\n", 'error')
        self.log_label.see(tk.END)
        self.log_label.config(state=tk.DISABLED)
        self.status_label.config(text=message, fg="red")

    def terminate_process(self):
        try:
            # Windows: SIGTERM 或 taskkill
            subprocess.run(
                f"taskkill /F /T /PID {self.process.pid}",
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            # os.kill(pid, signal.SIGTERM)
            # subprocess.run(f"taskkill /F /PID {pid}", shell=True)  # 强制终止

        except ProcessLookupError:
            pass  # 进程已退出

    def on_close(self):
        if self.process and self.process.poll() is None:  # 检查进程是否在运行
            self.terminate_process()
        self.master.destroy()  # 关闭GUI


if __name__ == '__main__':
    # if not is_admin():
    #     # 请求UAC提权
    #     ctypes.windll.shell32.ShellExecuteW(
    #         None, "runas", sys.executable, " ".join(sys.argv), None, 1
    #     )
    #     sys.exit()
    # else:
    #     add_firewall_rule(get_subprocess_path())
    root = tk.Tk()
    app = Application(root)


