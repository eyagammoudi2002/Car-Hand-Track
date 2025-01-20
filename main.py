import cv2
import mediapipe as mp
import pygame
import sys
import random

# راه‌اندازی MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_draw = mp.solutions.drawing_utils

# تنظیمات Pygame
pygame.init()
WIDTH, HEIGHT = 800, 600
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hand-Controlled Car Game")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# بارگذاری تصاویر
try:
    car_image_path = 'car.png'
    road_image_path = 'road.png'
    obstacle_car_images_paths = ['obstacle_car1.png', 'obstacle_car2.png', 'obstacle_car3.png']

    car_image = pygame.image.load(car_image_path)
    road_image = pygame.image.load(road_image_path)
    obstacle_car_images = [pygame.image.load(img_path) for img_path in obstacle_car_images_paths]
    
    desired_car_width, desired_car_height = 50, 80
    
    car_image = pygame.transform.scale(car_image, (desired_car_width, desired_car_height))
    road_image = pygame.transform.scale(road_image, (WIDTH, HEIGHT))
    obstacle_car_images = [pygame.transform.scale(img, (desired_car_width, desired_car_height)) for img in obstacle_car_images]
    
except Exception as e:
    print("خطا در بارگذاری تصاویر:", e)
    sys.exit()

CAR_WIDTH, CAR_HEIGHT = car_image.get_size()
car_x = WIDTH // 2 - CAR_WIDTH // 2
car_y = HEIGHT - CAR_HEIGHT - 20

road_left_border = 304
road_right_border = 440

scroll_y = 0
distance = 0
font = pygame.font.SysFont("comicsans", 30)

clock = pygame.time.Clock()

# تنظیمات برای ماشین های موانع
NUM_OBSTACLE_CARS = 3
class ObstacleCar:
    def __init__(self, x, y, speed, image):
        self.x = x
        self.y = y
        self.speed = speed
        self.image = image

obstacle_cars = []

def spawn_obstacle_cars(num_cars):
    for _ in range(num_cars):
        x_position = random.randint(road_left_border, road_right_border - CAR_WIDTH)
        y_position = random.randint(-1000, 0)
        speed = random.randint(1, 3)
        image = random.choice(obstacle_car_images)
        obstacle_car = ObstacleCar(x_position, y_position, speed, image)
        obstacle_cars.append(obstacle_car)

spawn_obstacle_cars(NUM_OBSTACLE_CARS)

def calculate_speed(hand_y, min_speed=2, max_speed=100, sensitivity=1.5):
    adjusted_y = 1 - hand_y
    speed = min_speed + adjusted_y ** sensitivity * (max_speed - min_speed)
    return int(speed)

def draw_window(car_x, car_y, scroll_y, distance, current_speed, lives):
    win.fill(WHITE)
    win.blit(road_image, (0, scroll_y))
    win.blit(road_image, (0, scroll_y - HEIGHT))
    win.blit(car_image, (car_x, car_y))
    
    for obstacle_car in obstacle_cars:
        win.blit(obstacle_car.image, (obstacle_car.x, obstacle_car.y))
    
    distance_text = font.render(f"Distance: {distance} km", True, BLACK)
    win.blit(distance_text, (WIDTH - distance_text.get_width() - 10, 10))

    speed_text = font.render(f"Speed: {current_speed} km/h", True, BLACK)
    win.blit(speed_text, (10, 10))
    
    lives_text = font.render(f"Lives: {lives}", True, BLACK)
    win.blit(lives_text, (10, 40))

    pygame.display.update()

def is_fist_closed(hand_landmarks):
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    
    thumb_index_distance = abs(thumb_tip.x - index_tip.x) + abs(thumb_tip.y - index_tip.y)
    index_middle_distance = abs(index_tip.x - middle_tip.x) + abs(index_tip.y - middle_tip.y)
    
    return thumb_index_distance < 0.05 and index_middle_distance < 0.05

def update_obstacles(current_speed):
    for obs in obstacle_cars:
        obs.y += obs.speed + current_speed // 10 
        if obs.y > HEIGHT:
            obs.y = random.randint(-500, -100)
            obs.x = random.randint(road_left_border, road_right_border - CAR_WIDTH)

def check_and_handle_collisions(car_x, car_y):
    global lives
    car_rect = pygame.Rect(car_x, car_y, CAR_WIDTH, CAR_HEIGHT)
    
    for obs in obstacle_cars:
        obstacle_rect = pygame.Rect(obs.x, obs.y, CAR_WIDTH, CAR_HEIGHT)
        
        if car_rect.colliderect(obstacle_rect):
            obs.y = random.randint(-500, -100)
            obs.x = random.randint(road_left_border, road_right_border - CAR_WIDTH)
            lives -= 1
            print(f"Lives left: {lives}")
            
            if lives <= 0:
                print("Game Over!")
                return False
    return True

cap = cv2.VideoCapture(0)

lives = 6  # تعریف تعداد جان‌ها

try:
    running = True
    current_speed = 0
    while running:
        ret, frame = cap.read()
        if not ret:
            print("خطا در دریافت فریم دوربین")
            break

        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                if is_fist_closed(hand_landmarks):
                    current_speed = 0
                else:
                    finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                    current_speed = calculate_speed(finger_tip.y)
                    new_car_x = WIDTH - int(finger_tip.x * WIDTH) - CAR_WIDTH // 2

                    if new_car_x < road_left_border:
                        new_car_x = road_left_border
                    elif new_car_x > road_right_border:
                        new_car_x = road_right_border

                    car_x = new_car_x

        scroll_y += current_speed
        if scroll_y >= HEIGHT:
            scroll_y = 0

        distance += current_speed / 100
        distance = round(distance, 1)

        cv2.imshow("Hand Tracking", frame)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        update_obstacles(current_speed)  
        
        if not check_and_handle_collisions(car_x, car_y):
            break

        draw_window(car_x, car_y, scroll_y, distance, current_speed, lives)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        clock.tick(60)

finally:
    cap.release()
    cv2.destroyAllWindows()
    pygame.quit()
    sys.exit()
