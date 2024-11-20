import os
import pygame
from PIL import Image, ImageDraw
from ffpyplayer.player import MediaPlayer
from flask import Flask, request
import threading
import numpy as np

# Создание сервера Flask
app = Flask(__name__)
current_mode = "image"  # Начальный режим
current_file = "/home/kbtutv2/images/default.jpg"  # Текущее имя файла
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
    file_path = os.path.join(IMAGE_FOLDER, file_name)

    if not os.path.exists(file_path):
        print(f"Image file '{file_path}' not found.")
        return

    # Load the image
    image = Image.open(file_path).convert('RGB')
    image_width, image_height = image.size

    # Get left and right colors
    left_color = image.crop((0, 0, 10, image.height)).resize((1, 1)).getpixel((0, 0))
    right_color = image.crop((image.width - 10, 0, image.width, image.height)).resize((1, 1)).getpixel((0, 0))

    # Create gradient background
    screen_width, screen_height = screen.get_size()
    gradient_surface = pygame.Surface((screen_width, screen_height))

    for x in range(screen_width):
        factor = x / screen_width
        color = (
            int(left_color[0] * (1 - factor) + right_color[0] * factor),
            int(left_color[1] * (1 - factor) + right_color[1] * factor),
            int(left_color[2] * (1 - factor) + right_color[2] * factor)
        )
        pygame.draw.line(gradient_surface, color, (x, 0), (x, screen_height))

    # Scale and center the image
    scale_factor = min(screen_width / image_width, screen_height / image_height)
    new_width = int(image_width * scale_factor)
    new_height = int(image_height * scale_factor)
    pygame_image = pygame.image.fromstring(image.tobytes(), image.size, 'RGB')
    pygame_image = pygame.transform.scale(pygame_image, (new_width, new_height))
    x_offset = (screen_width - new_width) // 2
    y_offset = (screen_height - new_height) // 2

    running = True
    while running:
        if check_interrupted() == "video" or interrupt_flag:
            interrupt_flag = False
            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Draw the gradient background
        screen.blit(gradient_surface, (0, 0))

        # Draw the centered original image
        screen.blit(pygame_image, (x_offset, y_offset))
        pygame.display.flip()

        pygame.time.delay(100)
def display_video(screen, file_name):
    global interrupt_flag
    file_path = os.path.join(VIDEO_FOLDER, file_name)

    if not os.path.exists(file_path):
        print(f"Video file '{file_path}' not found.")
        return

    pygame.display.set_caption("Video Player")
    player = MediaPlayer(file_path, sync=False)

    clock = pygame.time.Clock()
    screen_size = screen.get_size()
    running = True

    while running:
        if check_interrupted() == "image" or interrupt_flag:
            player.close_player()
            interrupt_flag = False
            break

        frame, val = player.get_frame()
        if frame is not None:
            image, pts = frame
            img_array = np.array(image.to_bytearray()[0]).reshape(image.get_size()[::-1] + (3,))

            # Resize video frame to fit screen
            img_surface = pygame.surfarray.make_surface(img_array.swapaxes(0, 1))
            img_surface = pygame.transform.scale(img_surface, screen_size)

            screen.fill((0, 0, 0))
            screen.blit(img_surface, (0, 0))
            pygame.display.flip()

        if val == 'eof':
            running = False

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
    pygame.mouse.set_visible(False)
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
