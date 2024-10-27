import sys
print("Current Python:", sys.executable)
print("System PATH:", sys.path)

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
    # Определяем папку для сохранения в зависимости от типа файла
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
    video_extensions = {".mp4", ".avi", ".mov", ".mkv", ".flv"}

    _, ext = os.path.splitext(file_name)
    ext = ext.lower()

    if ext in image_extensions:
        save_dir = "/home/kbtutv1/images"
        mode = "image"
    elif ext in video_extensions:
        save_dir = "/home/kbtutv1/videos"
        mode = "video"
    else:
        save_dir = "/home/kbtutv1/other"
        mode = None  # Для файлов другого типа запрос не отправляется

    # Создаем директорию, если она не существует
    os.makedirs(save_dir, exist_ok=True)
    return os.path.join(save_dir, file_name), mode

def send_curl_request(mode, file_path):
    # Формируем и отправляем curl запрос
    url = f"http://localhost:5000/set_mode?mode={mode}&filename={file_path}"
    subprocess.run(["/usr/bin/curl", url], capture_output=True, text=True)
    print(f"Отправлен запрос: {url}")


def delete_old_files(directory, current_file):
    # Получаем список всех файлов в папке
    files = glob.glob(f"{directory}/*")
    files.sort(key=os.path.getmtime)  # Сортируем по времени изменения

    # Удаляем все файлы, кроме текущего
    for file in files:
        if file != current_file and not file.endswith("default.jpg"):
            os.remove(file)
            print(f"Удален файл: {file}")

def receive_file(port=5001):
    # Завершаем любой существующий процесс на этом порту
    kill_existing_process(port)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Повторное использование адреса
        s.bind(("", port))
        s.listen(1)
        print("Ожидание подключения...")

        while True:
            conn, addr = s.accept()
            with conn:
                print("Подключен к:", addr)

                # Получаем имя файла и размер
                file_info = conn.recv(1024).decode()
                file_name, file_size = file_info.split(",")
                file_size = int(file_size)
                conn.sendall(b"INFO RECEIVED")  # Подтверждение

                # Определяем путь для сохранения файла и его mode
                save_path, mode = get_save_path(file_name)

                # Принимаем и записываем файл по частям
                with open(save_path, "wb") as f:
                    bytes_received = 0
                    while bytes_received < file_size:
                        chunk = conn.recv(1024)
                        if not chunk:
                            break
                        f.write(chunk)
                        bytes_received += len(chunk)
                        print(f"Получено {bytes_received}/{file_size} байт")

                if bytes_received == file_size:
                    print(f"Файл успешно сохранен: {save_path}")
                    
                    # Отправляем curl запрос в зависимости от типа файла
                    if mode:
                        send_curl_request(mode, save_path)

                    # Удаляем предыдущие файлы в папке
                    delete_old_files(os.path.dirname(save_path), save_path)
                else:
                    print("Ошибка: файл получен не полностью.")

                print("Ожидание следующего файла...\n")

# Пример использования:
receive_file()
