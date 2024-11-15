import socket
import pyautogui
import threading
import time
import struct
import tkinter as tk
from tkinter import messagebox
import io
from PIL import Image
import os
import sys

class RemoteDesktopServer:
    def __init__(self, root):
        self.root = root
        self.root.title("被控端")

        # 设置目标IP和端口的输入框
        self.target_ip_label = tk.Label(root, text="本机IP地址:")
        self.target_ip_label.grid(row=0, column=0, padx=5, pady=5)
        self.target_ip_entry = tk.Entry(root)
        self.target_ip_entry.grid(row=0, column=1, padx=5, pady=5)
        self.target_ip_entry.insert(0, "0.0.0.0")  # 默认IP地址（监听所有网卡）

        self.port_label = tk.Label(root, text="端口:")
        self.port_label.grid(row=1, column=0, padx=5, pady=5)
        self.port_entry = tk.Entry(root)
        self.port_entry.grid(row=1, column=1, padx=5, pady=5)
        self.port_entry.insert(0, "9999")  # 默认端口

        self.fps_label = tk.Label(root, text="刷新帧率(FPS):")
        self.fps_label.grid(row=2, column=0, padx=5, pady=5)
        self.fps_entry = tk.Entry(root)
        self.fps_entry.grid(row=2, column=1, padx=5, pady=5)
        self.fps_entry.insert(0, "30")  # 默认帧率30

        # 启动和停止按钮
        self.start_button = tk.Button(root, text="启动服务", command=self.start_server)
        self.start_button.grid(row=3, column=0, padx=5, pady=5)

        self.stop_button = tk.Button(root, text="停止服务", command=self.stop_server, state=tk.DISABLED)
        self.stop_button.grid(row=3, column=1, padx=5, pady=5)

        # 隐藏窗口和退出按钮
        self.hide_button = tk.Button(root, text="隐藏窗口", command=self.hide_window)
        self.hide_button.grid(row=4, column=0, padx=5, pady=5)

        self.quit_button = tk.Button(root, text="结束进程", command=self.quit_program)
        self.quit_button.grid(row=4, column=1, padx=5, pady=5)

        # 服务端运行标志
        self.is_running = False

        # 初始化线程和服务器套接字
        self.server_thread = None
        self.server_socket = None

        # 处理窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def start_server(self):
        ip = self.target_ip_entry.get()
        port = int(self.port_entry.get())
        fps = int(self.fps_entry.get())

        if not ip or port <= 0 or fps <= 0:
            messagebox.showerror("无效输入", "请输入有效的 IP、端口和刷新帧率！")
            return

        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        # 启动服务器监听的线程
        self.server_thread = threading.Thread(target=self.run_server, args=(ip, port, fps))
        self.server_thread.start()

    def stop_server(self):
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def run_server(self, ip, port, fps):
        try:
            # 创建Socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_address = (ip, port)
            self.server_socket.bind(socket_address)
            self.server_socket.listen(5)
            print(f"Server listening on {ip}:{port}...")

            while self.is_running:
                # 等待客户端连接
                client_socket, addr = self.server_socket.accept()
                print(f"连接建立自: {addr}")

                # 处理客户端请求
                self.handle_client(client_socket, fps)

            self.server_socket.close()
            print("服务器已停止！")

        except Exception as e:
            # print(f"服务器错误: {e}")
            pass

    def handle_client(self, client_socket, fps):
        try:
            while self.is_running:
                # 获取屏幕截图
                screenshot = pyautogui.screenshot()               

                # 将截图保存为JPEG格式
                with io.BytesIO() as output:
                    screenshot.save(output, format="JPEG")
                    img_data = output.getvalue()

                # 序列化图像数据
                message = struct.pack("Q", len(img_data)) + img_data

                # 发送数据给客户端
                client_socket.sendall(message)

                time.sleep(1 / fps)  # 控制每秒帧数（帧率）

        except Exception as e:
            # print(f"客户端断开连接或发生错误: {e}")
            pass
        finally:
            client_socket.close()

    def on_close(self):
        """Window close handler to stop the server gracefully."""
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
        if self.server_thread:
            self.server_thread.join()  # Ensure the server thread has finished before closing
        self.root.destroy()  # Close the tkinter window

    def hide_window(self):
        """Hide the window (without exiting the program)."""
        self.root.withdraw()

    def quit_program(self):
        """Exit the program completely."""
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
        if self.server_thread:
            self.server_thread.join()
        self.root.quit()  # Terminate the tkinter main loop
        sys.exit(0)  # Exit the program

# 主程序
def main():
    root = tk.Tk()
    server_app = RemoteDesktopServer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
