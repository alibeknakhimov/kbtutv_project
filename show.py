import os
import pygame
from PIL import Image
from ffpyplayer.player import MediaPlayer
from flask import Flask, request
import threading
import numpy as np

# Создание сервера Flask
app = Flask(__name__)
current_mode = "image"  # Начальный режим
current_file = "/home/kbtutv1/images/default.jpg"  # Текущее имя файла
interrupt_flag = False  # Флаг для прерывания текущего режима

# Папки для изображений и видео
IMAGE_FOLDER = "images"
VIDEO_FOLDER = "videos"

# Обработка запроса для смены режима и файла
@app.route('/set_mode', methods=['GET'])
def set_mode():
    global current_mode, current_file, interrupt_flag
    mode = request.args.get('mode')
    filename = request.args.get('filename')
    
    # Проверяем наличие режима и имени файла
    if mode in ["image", "video"] and filename:
        current_mode = mode
        current_file = filename
        interrupt_flag = True  # Устанавливаем флаг прерывания
        return f"Mode set to {mode} with file {filename}", 200
    return "Invalid mode or filename missing", 400

# Функция для запуска Flask в отдельном потоке
def run_server():
    app.run(port=5000)

# Function to display an image without flickering
def display_image(screen, file_name):
    global interrupt_flag
    file_path = os.path.join(IMAGE_FOLDER, file_name)  # Путь к изображению

    # Проверка существования файла
    if not os.path.exists(file_path):
        print(f"Image file '{file_path}' not found.")
        return

    # Load the image once
    image = Image.open(file_path)
    image = image.convert('RGB')
    image_data = image.tobytes()
    pygame_image = pygame.image.fromstring(image_data, image.size, 'RGB')

    running = True
    while running:
        # Check interruption before updating display
        if check_interrupted() == "video" or interrupt_flag:
            interrupt_flag = False  # Сбрасываем флаг после прерывания
            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Display the image only once and keep it on the screen
        screen.blit(pygame_image, (0, 0))
        pygame.display.flip()  # Use flip instead of update for stable screen rendering

        # Small delay to reduce CPU usage
        pygame.time.delay(100)  # Adjust the delay as needed

# Function to display video using ffpyplayer in its original resolution without scaling or positioning adjustments
def display_video(screen, file_name):
    global interrupt_flag
    file_path = os.path.join(VIDEO_FOLDER, file_name)  # Путь к видео

    # Проверка существования файла
    if not os.path.exists(file_path):
        print(f"Video file '{file_path}' not found.")
        return

    pygame.display.set_caption("Video Player")
    player = MediaPlayer(file_path, sync=False)  # Disable synchronization to avoid skipping frames

    clock = pygame.time.Clock()
    running = True

    while running:
        # Check for interruption on each frame to allow instant switching
        if check_interrupted() == "image" or interrupt_flag:
            player.close_player()
            interrupt_flag = False  # Сбрасываем флаг после прерывания
            break

        frame, val = player.get_frame()
        if frame is not None:
            image, pts = frame
            img_array = np.array(image.to_bytearray()[0]).reshape(image.get_size()[::-1] + (3,))
            img_surface = pygame.surfarray.make_surface(img_array.swapaxes(0, 1))

            # Display the video at its original resolution in the top-left corner
            screen.fill((0, 0, 0))  # Clear the screen with black before blitting
            screen.blit(img_surface, (0, 0))  # Draw the video without any positioning adjustments
            pygame.display.flip()  # Use flip for stable screen rendering

            clock.tick(30)  # Set the FPS to 30

        # Stop playback when video ends
        if val == 'eof':
            running = False  # Stop playback after video ends

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                player.close_player()
                running = False

# Function to check if an interruption is needed based on mode
def check_interrupted():
    global current_mode
    return current_mode

# Main loop of the program
def main_loop():
    pygame.init()
    screen_info = pygame.display.Info()
    screen = pygame.display.set_mode((screen_info.current_w, screen_info.current_h), pygame.FULLSCREEN)
    while True:
        mode = check_interrupted()
        screen.fill((0, 0, 0))  # Clear the screen
        pygame.display.update()

        if mode == "image":
            display_image(screen, current_file)
        elif mode == "video":
            display_video(screen, current_file)

if __name__ == "__main__":
    # Запуск сервера Flask в отдельном потоке
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    main_loop()
