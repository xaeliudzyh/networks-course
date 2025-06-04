import socket
import threading
import tkinter as tk

SERVER_IP = '127.0.0.1'
SERVER_PORT = 54321

class DrawClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Клиент рисования")
        self.canvas = tk.Canvas(root, bg='white', width=800, height=600)
        self.canvas.pack()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((SERVER_IP, SERVER_PORT))
        self.canvas.bind("<ButtonPress-1>", self.on_down)
        self.canvas.bind("<B1-Motion>", self.on_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_up)
        self.prev = None

    def send_cmd(self, action, x, y):
        msg = f"{action};{x};{y}\n".encode('utf-8')
        try:
            self.sock.sendall(msg)
        except:
            pass

    def on_down(self, event):
        x, y = event.x, event.y
        self.prev = (x, y)
        self.send_cmd('down', x, y)

    def on_move(self, event):
        x, y = event.x, event.y
        x0, y0 = self.prev
        self.canvas.create_line(x0, y0, x, y, fill='blue', width=2)
        self.prev = (x, y)
        self.send_cmd('move', x, y)

    def on_up(self, event):
        x, y = event.x, event.y
        self.send_cmd('up', x, y)
        self.prev = None

if __name__ == "__main__":
    root = tk.Tk()
    app = DrawClient(root)
    root.mainloop()