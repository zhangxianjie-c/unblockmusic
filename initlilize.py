# This is a sample Python script.
import os
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import subprocess
import sys
import time
import win32gui
import win32con
import tkinter as tk

programs = [
        # r"D:\Application\CloudMusic\cloudmusic.exe",
        # r"D:\Application\Clash for Windows\Clash for Windows.exe",
        # r"D:\WeChat\WeChat.exe",
        # r"D:\unblockneteasemusic-win-x64.exe",
]
processes = []

FILE_PATH = "saved_input.txt"  # 存储数据的文件路径


def save_input():
    """将输入框内容保存到文件"""
    with open(FILE_PATH, "w", encoding="utf-8") as file:
        file.write(entry.get())


def load_input():
    """从文件加载上次输入的内容"""
    if os.path.exists(FILE_PATH):  # 只有在文件存在时才加载
        with open(FILE_PATH, "r", encoding="utf-8") as file:
            return file.read().strip()
    return ""  # 如果文件不存在，则返回空字符串


def get_exe_path():
    """ 获取 some_program.exe 的路径，适配 PyInstaller 的打包方式 """
    if getattr(sys, 'frozen', False):
        # 运行时（已打包成 EXE），程序在 _MEIPASS 临时目录下
        base_path = sys._MEIPASS
    else:
        # 运行时（未打包，直接运行 Python 脚本）
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, "unblockneteasemusic-win-x64.exe")


def run_external_exe():
    """ 运行打包的 EXE 文件 """
    exe_path = get_exe_path()
    if os.path.exists(exe_path):
        subprocess.Popen(exe_path, creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        print(f"错误: {exe_path} 未找到！")


if __name__ == '__main__':
    # 使用 subprocess 启动多个程序
    for program in programs:
        process = subprocess.Popen(program ,creationflags=subprocess.CREATE_NO_WINDOW)  # 启动每个程序
        processes.append(process)  # 将进程对象添加到列表中

    run_external_exe()

    root = tk.Tk()
    root.title("网易云启动器")
    root.geometry("600x200")

    label = tk.Label(root, text="所有程序已启动，关闭此窗口以退出")
    label.pack(pady=20)

    # 创建输入框
    entry = tk.Entry(root, width=30)
    entry.pack(pady=5)

    entry.insert(0, load_input())

    # 定义按钮功能
    def get_input():
        user_input = entry.get()  # 获取输入框内容
        save_input()
        print("用户输入:", user_input)


    # 创建按钮
    button = tk.Button(root, text="提交", command=get_input)
    button.pack(pady=5)

    root.mainloop()  # 保持窗口打开


    # 等待所有程序完成（可选）
    for process in processes:
        process.wait()  # 等待该进程结束

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
