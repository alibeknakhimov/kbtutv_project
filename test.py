import os
import pygame
import numpy as np
from ffpyplayer.player import MediaPlayer

# Инициализация папки с тестовым видеофайлом
VIDEO_FOLDER = "/home/kbtutv1/videos"  # Замените на свой путь
TEST_VIDEO = "ss.mp4"  # Укажите имя видеофайла для теста

def display_video():
    pygame.init()
    screen = pygame.display.set_mode((0, 0))  # Задаем стандартный размер окна
    pygame.display.set_caption("FFpylayer Video Test")

    file_path = os.path.join(VIDEO_FOLDER, TEST_VIDEO)
    if not os.path.exists(file_path):
        print(f"Video file '{file_path}' not found.")
        return

    player = MediaPlayer(file_path, sync=False)  # Создание плеера без синхронизации

    clock = pygame.time.Clock()
    running = True

    while running:
        frame, val = player.get_frame()
        if frame is not None:
            image, pts = frame
            img_array = np.array(image.to_bytearray()[0]).reshape(image.get_size()[::-1] + (3,))
            img_surface = pygame.surfarray.make_surface(img_array.swapaxes(0, 1))

            screen.fill((0, 0, 0))
            screen.blit(img_surface, (0, 0))
            pygame.display.flip()
            clock.tick(30)

        if val == 'eof':
            print("Видео завершилось.")
            running = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

    player.close_player()
    pygame.quit()

if __name__ == "__main__":
    display_video()
