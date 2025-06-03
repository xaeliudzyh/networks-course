#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import threading
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

BUFFER_SIZE = 1024


class FTPClientSocket:

    def __init__(self, host: str, port: int, user: str, passwd: str):
        self.server = (host, port)
        self.user = user
        self.passwd = passwd
        self.ctrl_sock: socket.socket | None = None

    def connect(self) -> str:
        self.ctrl_sock = socket.create_connection(self.server)
        banner = self._recv_ctrl()
        self._send_cmd(f"USER {self.user}")
        self._send_cmd(f"PASS {self.passwd}")
        self._send_cmd("TYPE I")
        return banner

    def _recv_ctrl(self) -> str:
        data = b""
        assert self.ctrl_sock is not None
        while True:
            part = self.ctrl_sock.recv(BUFFER_SIZE)
            data += part
            if len(part) < BUFFER_SIZE:
                break
        return data.decode(errors="ignore")

    def _send_cmd(self, cmd: str) -> str:
        assert self.ctrl_sock is not None
        self.ctrl_sock.sendall((cmd + "\r\n").encode())
        return self._recv_ctrl()

    def _enter_pasv(self) -> tuple[str, int]:
        resp = self._send_cmd("PASV")
        start = resp.find("(") + 1
        end = resp.find(")")
        parts = resp[start:end].split(",")
        nums = list(map(int, parts))
        host_data = ".".join(map(str, nums[:4]))
        port_data = nums[4] * 256 + nums[5]
        return host_data, port_data

    @staticmethod
    def _recv_data(dsock: socket.socket) -> bytes:
        data = b""
        while True:
            chunk = dsock.recv(BUFFER_SIZE)
            if not chunk:
                break
            data += chunk
        return data

    def list_files(self) -> list[str]:
        host_data, port_data = self._enter_pasv()
        with socket.create_connection((host_data, port_data)) as data_sock:
            _ = self._send_cmd("LIST")
            raw = self._recv_data(data_sock)
        _ = self._recv_ctrl()
        lines = raw.decode(errors="ignore").splitlines()
        return lines

    def download(self, remote_filename: str) -> bytes | None:
        host_data, port_data = self._enter_pasv()
        with socket.create_connection((host_data, port_data)) as data_sock:
            resp = self._send_cmd(f"RETR {remote_filename}")
            if not resp.startswith("150"):
                self._recv_ctrl()
                return None
            content = self._recv_data(data_sock)
        # Ждём финальный 226
        _ = self._recv_ctrl()
        return content

    def upload(self, filename: str, data_bytes: bytes) -> bool:
        host_data, port_data = self._enter_pasv()
        with socket.create_connection((host_data, port_data)) as data_sock:
            resp = self._send_cmd(f"STOR {filename}")
            if not resp.startswith("150"):
                self._recv_ctrl()
                return False
            data_sock.sendall(data_bytes)
        # Ждём финальный 226
        final = self._recv_ctrl()
        return final.startswith("226")

    def delete(self, filename: str) -> bool:
        resp = self._send_cmd(f"DELE {filename}")
        return resp.startswith("250")

    def quit(self) -> None:
        if self.ctrl_sock:
            try:
                self._send_cmd("QUIT")
            except Exception:
                pass
            self.ctrl_sock.close()
            self.ctrl_sock = None


class FTPClientGUI(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Ftp Client")
        self.resizable(False, False)

        self.var_user = tk.StringVar(value="")            # логин
        self.var_hostport = tk.StringVar(value="127.0.0.1:21")  # host:port
        self.var_pass = tk.StringVar(value="")            # пароль
        self.var_filename = tk.StringVar(value="")        # поле для имени файла

        self.ftp: FTPClientSocket | None = None

        self._build_widgets()

    def _build_widgets(self):
        pad = {"padx": 5, "pady": 5}

        ttk.Label(self, text="User:").grid(row=0, column=0, sticky="w", **pad)
        entry_user = ttk.Entry(self, textvariable=self.var_user, width=20)
        entry_user.grid(row=0, column=1, sticky="w", **pad)

        ttk.Label(self, text="Server (host:port):").grid(row=0, column=2, sticky="w", **pad)
        entry_host = ttk.Entry(self, textvariable=self.var_hostport, width=20)
        entry_host.grid(row=0, column=3, sticky="w", **pad)

        ttk.Label(self, text="Password:").grid(row=1, column=0, sticky="w", **pad)
        entry_pass = ttk.Entry(self, textvariable=self.var_pass, width=20, show="*")
        entry_pass.grid(row=1, column=1, sticky="w", **pad)

        self.btn_connect = ttk.Button(self, text="Connect", command=self.on_connect, width=15)
        self.btn_connect.grid(row=1, column=3, sticky="e", **pad)

        self.listbox = tk.Listbox(self, height=15, width=50)
        self.listbox.grid(row=2, column=0, columnspan=4, **pad, sticky="nsew")
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.listbox.yview)
        scrollbar.grid(row=2, column=4, sticky="ns", **pad)
        self.listbox.configure(yscrollcommand=scrollbar.set)

        ttk.Entry(self, textvariable=self.var_filename, width=30).grid(row=3, column=0, columnspan=3, sticky="w", **pad)

        btn_create = ttk.Button(self, text="Create", command=self.on_create, width=12)
        btn_create.grid(row=4, column=0, sticky="w", **pad)

        btn_retrieve = ttk.Button(self, text="Retrieve", command=self.on_retrieve, width=12)
        btn_retrieve.grid(row=4, column=1, sticky="w", **pad)

        btn_update = ttk.Button(self, text="Update", command=self.on_update, width=12)
        btn_update.grid(row=4, column=2, sticky="w", **pad)

        btn_delete = ttk.Button(self, text="Delete", command=self.on_delete, width=12)
        btn_delete.grid(row=4, column=3, sticky="w", **pad)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_connect(self):
        user = self.var_user.get().strip()
        passwd = self.var_pass.get().strip()
        hp = self.var_hostport.get().strip()

        if not user or ":" not in hp:
            messagebox.showwarning("Warning", "Введите User и корректный Server:port")
            return

        host, sep, port_str = hp.partition(":")
        try:
            port = int(port_str)
        except ValueError:
            messagebox.showwarning("Warning", "Port должен быть числом")
            return

        self.btn_connect.config(state="disabled", text="Connecting...")
        def do_connect():
            try:
                client = FTPClientSocket(host, port, user, passwd)
                banner = client.connect()
                self.ftp = client
                # После успешного логина – заполняем listbox
                self._fill_listbox()
                messagebox.showinfo("Success", f"Connected:\n{banner.strip()}")
                self.btn_connect.config(text="Connected")
            except Exception as e:
                messagebox.showerror("Error", f"Не удалось подключиться:\n{e}")
                self.btn_connect.config(state="normal", text="Connect")
                self.ftp = None

        threading.Thread(target=do_connect, daemon=True).start()

    def _fill_listbox(self):
        if not self.ftp:
            return
        try:
            items = self.ftp.list_files()
            self.listbox.delete(0, tk.END)
            for line in items:
                self.listbox.insert(tk.END, line)
        except Exception as e:
            messagebox.showerror("Error", f"Ошибка при LIST:\n{e}")

    def on_create(self):
        if self.ftp is None:
            messagebox.showwarning("Warning", "Сначала подключитесь")
            return
        filename = self.var_filename.get().strip()
        if not filename:
            messagebox.showwarning("Warning", "Введите имя файла в поле Filename")
            return

        self._open_editor(filename, initial_text="", is_update=False)

    def on_retrieve(self):
        if self.ftp is None:
            messagebox.showwarning("Warning", "Сначала подключитесь")
            return

        sel = self.listbox.curselection()
        if sel:
            line = self.listbox.get(sel[0])
            remote_name = line.split()[-1]
        else:
            remote_name = self.var_filename.get().strip()

        if not remote_name:
            messagebox.showwarning("Warning", "Выберите файл в списке или введите его имя")
            return

        def do_retrieve():
            data = self.ftp.download(remote_name)
            if data is None:
                messagebox.showerror("Error", f"Файл '{remote_name}' не найден на сервере.")
                return
            text = data.decode(errors="ignore")
            # Показываем содержимое в отдельном окне
            self._show_text_window(remote_name, text)

        threading.Thread(target=do_retrieve, daemon=True).start()

    def on_update(self):
        if self.ftp is None:
            messagebox.showwarning("Warning", "Сначала подключитесь")
            return

        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Warning", "Сначала выберите файл в списке")
            return
        line = self.listbox.get(sel[0])
        filename = line.split()[-1]

        def do_download_for_update():
            data = self.ftp.download(filename)
            if data is None:
                messagebox.showerror("Error", f"Не удалось скачать '{filename}'.")
                return
            text = data.decode(errors="ignore")
            self._open_editor(filename, initial_text=text, is_update=True)

        threading.Thread(target=do_download_for_update, daemon=True).start()

    def on_delete(self):
        if self.ftp is None:
            messagebox.showwarning("Warning", "Сначала подключитесь")
            return

        sel = self.listbox.curselection()
        if sel:
            line = self.listbox.get(sel[0])
            filename = line.split()[-1]
        else:
            filename = self.var_filename.get().strip()

        if not filename:
            messagebox.showwarning("Warning", "Выберите файл в списке или введите его имя")
            return

        if not messagebox.askyesno("Confirm", f"Удалить '{filename}'?"):
            return

        def do_delete():
            ok = self.ftp.delete(filename)
            if ok:
                messagebox.showinfo("Success", f"'{filename}' удалён.")
                self._fill_listbox()
            else:
                messagebox.showerror("Error", f"Не удалось удалить '{filename}'.")

        threading.Thread(target=do_delete, daemon=True).start()

    def _open_editor(self, filename: str, initial_text: str, is_update: bool):
        editor = tk.Toplevel(self)
        editor.title(("Update: " if is_update else "Create: ") + filename)
        editor.geometry("600x400")

        txt = tk.Text(editor, wrap="none")
        txt.insert("1.0", initial_text)
        txt.pack(expand=True, fill="both", padx=5, pady=5)

        def on_save():
            content = txt.get("1.0", "end-1c").encode()
            def do_upload():
                ok = self.ftp.upload(filename, content)
                if ok:
                    messagebox.showinfo("Success", f"'{filename}' успешно сохранён на сервере.")
                    editor.destroy()
                    self._fill_listbox()
                else:
                    messagebox.showerror("Error", f"Не удалось сохранить '{filename}' на сервере.")
            threading.Thread(target=do_upload, daemon=True).start()

        btn_save = ttk.Button(editor, text="Save", command=on_save)
        btn_save.pack(pady=5)

    def _show_text_window(self, title: str, text: str):
        win = tk.Toplevel(self)
        win.title("Retrieve: " + title)
        win.geometry("600x400")
        txt = tk.Text(win, wrap="none")
        txt.insert("1.0", text)
        txt.pack(expand=True, fill="both", padx=5, pady=5)

    def on_close(self):
        if self.ftp:
            try:
                self.ftp.quit()
            except Exception:
                pass
        self.destroy()


if __name__ == "__main__":
    app = FTPClientGUI()
    app.mainloop()
