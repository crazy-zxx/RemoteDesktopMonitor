import socket
import cv2
import struct
import numpy as np
import tkinter as tk
from tkinter import messagebox
import threading
import time

class RemoteDesktopClient:
    def __init__(self, root):
        self.root = root
        self.root.title("监控端")

        # 设置目标IP和端口的输入框
        self.target_ip_label = tk.Label(root, text="目标IP地址:")
        self.target_ip_label.grid(row=0, column=0, padx=5, pady=5)
        self.target_ip_entry = tk.Entry(root)
        self.target_ip_entry.grid(row=0, column=1, padx=5, pady=5)
        self.target_ip_entry.insert(0, "10.9.21.2")  # 默认IP地址（被控端的内网IP地址）

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
        self.start_button = tk.Button(root, text="启动服务", command=self.start_monitoring)
        self.start_button.grid(row=3, column=0, padx=5, pady=5)

        self.stop_button = tk.Button(root, text="停止服务", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.grid(row=3, column=1, padx=5, pady=5)

        # 远程控制标志
        self.is_monitoring = False

    def start_monitoring(self):
        ip = self.target_ip_entry.get()
        port = int(self.port_entry.get())
        fps = int(self.fps_entry.get())

        if not ip or port <= 0 or fps <= 0:
            messagebox.showerror("无效输入", "请输入有效的 IP、端口和刷新帧率！")
            return

        self.is_monitoring = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        # 启动接收数据的线程
        self.monitoring_thread = threading.Thread(target=self.receive_screen, args=(ip, port, fps))
        self.monitoring_thread.start()

    def stop_monitoring(self):
        self.is_monitoring = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def receive_screen(self, ip, port, fps):
        try:
            # 创建Socket连接
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((ip, port))

            data = b""
            payload_size = struct.calcsize("Q")

            while self.is_monitoring:
                while len(data) < payload_size:
                    packet = client_socket.recv(4096)  # 根据网络状况调整缓冲区大小
                    if not packet:
                        break
                    data += packet

                if len(data) < payload_size:
                    continue

                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack("Q", packed_msg_size)[0]

                while len(data) < msg_size:
                    data += client_socket.recv(4096)

                frame_data = data[:msg_size]
                data = data[msg_size:]

                # 解码JPEG图像
                frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)

                # 使用OpenCV显示接收到的屏幕
                cv2.imshow("Remote Desktop", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

                time.sleep(1 / fps)  # 控制每秒帧数（帧率）

            client_socket.close()
            cv2.destroyAllWindows()

        except Exception as e:
            messagebox.showerror("Connection Error", f"Error occurred: {str(e)}")
            self.stop_monitoring()

# 主程序
def main():
    root = tk.Tk()
    client_app = RemoteDesktopClient(root)
    root.mainloop()

if __name__ == "__main__":
    main()
