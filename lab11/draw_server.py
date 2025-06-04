import socket
import threading
import tkinter as tk

HOST = '0.0.0.0'
PORT = 54321

class DrawServer:
    def __init__(self, root):
        self.root = root
        self.root.title("Сервер рисования")
        self.canvas = tk.Canvas(root, bg='white', width=800, height=600)
        self.canvas.pack()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((HOST, PORT))
        self.sock.listen(1)
        threading.Thread(target=self.accept_loop, daemon=True).start()

    def accept_loop(self):
        conn, addr = self.sock.accept()
        print(f"Клиент {addr} подключился")
        buf = ""
        while True:
            try:
                data = conn.recv(1024).decode('utf-8')
                if not data:
                    break
                buf += data
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    self.handle_command(line)
            except:
                break
        conn.close()
        print("Клиент отключился")

    def handle_command(self, cmd: str):
        parts = cmd.split(';')
        if len(parts) != 3:
            return
        action, xs, ys = parts
        x, y = float(xs), float(ys)
        if action == 'down':
            self.last = (x, y)
        elif action == 'move':
            x0, y0 = self.last
            self.canvas.create_line(x0, y0, x, y, fill='black', width=2)
            self.last = (x, y)
        elif action == 'up':
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = DrawServer(root)
    root.mainloop()