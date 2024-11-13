import socket
import subprocess
import os
import glob
import psutil

def kill_existing_process(port):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for conn in proc.connections(kind='inet'):
                if conn.laddr.port == port:
                    proc.kill()
                    print(f"Процесс с PID {proc.pid} на порту {port} завершен.")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

def get_save_path(file_name):
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
    video_extensions = {".mp4", ".avi", ".mov", ".mkv", ".flv"}

    _, ext = os.path.splitext(file_name)
    ext = ext.lower()

    if ext in image_extensions:
        save_dir = "/home/kbtutv7/images"
        mode = "image"
    elif ext in video_extensions:
        save_dir = "/home/kbtutv7/videos"
        mode = "video"
    else:
        save_dir = "/home/kbtutv7/other"
        mode = None

    os.makedirs(save_dir, exist_ok=True)
    return os.path.join(save_dir, file_name), mode

def send_curl_request(mode, file_path):
    url = f"http://localhost:5000/set_mode?mode={mode}&filename={file_path}"
    subprocess.run(["/usr/bin/curl", url], capture_output=True, text=True)
    print(f"Отправлен запрос: {url}")

def delete_old_files(directory, current_file):
    files = glob.glob(f"{directory}/*")
    files.sort(key=os.path.getmtime)

    for file in files:
        if file != current_file and not file.endswith("default.jpg"):
            os.remove(file)
            print(f"Удален файл: {file}")

def receive_file(port=5001):
    kill_existing_process(port)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("", port))
        s.listen(1)
        print("Ожидание подключения...")

        while True:
            try:
                conn, addr = s.accept()
                with conn:
                    print("Подключен к:", addr)

                    file_info = conn.recv(1024).decode()
                    file_name, file_size = file_info.split(",")
                    file_size = int(file_size)
                    conn.sendall(b"INFO RECEIVED")

                    save_path, mode = get_save_path(file_name)
                    bytes_received = 0

                    with open(save_path, "wb") as f:
                        while bytes_received < file_size:
                            try:
                                chunk = conn.recv(1024)
                                if not chunk:
                                    break
                                f.write(chunk)
                                bytes_received += len(chunk)
                            except ConnectionResetError:
                                print("Ошибка: соединение прервано клиентом.")
                                break

                    if bytes_received == file_size:
                        print(f"Файл успешно сохранен: {save_path}")
                        if mode:
                            send_curl_request(mode, save_path)
                        delete_old_files(os.path.dirname(save_path), save_path)
                    else:
                        print("Ошибка: файл получен не полностью.")

                    print("Ожидание следующего файла...\n")

            except Exception as e:
                print(f"Произошла ошибка: {e}")
                continue

receive_file()