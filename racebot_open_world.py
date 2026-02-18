import pygame
import math
import sys

pygame.init()

# Window
SCREEN_W, SCREEN_H = 960, 540
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Simple Horizon-style Free Drive")

clock = pygame.time.Clock()

# World (big map)
WORLD_W, WORLD_H = 3000, 2000

# Colors
GREEN = (40, 120, 40)
ROAD = (60, 60, 60)
WHITE = (230, 230, 230)
CAR_COLOR = (220, 60, 60)
SKY = (80, 150, 220)
YELLOW = (240, 210, 60)

# Car settings (arcade-ish, but controllable)
class Car:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0
        self.speed = 0
        self.max_speed = 12
        self.accel = 0.4
        self.brake = 0.6
        self.friction = 0.05
        self.turn_speed = 3  # degrees per frame at decent speed
        self.length = 50
        self.width = 26

    def update(self, keys):
        # Throttle / brake
        if keys[pygame.K_UP]:
            self.speed += self.accel
        elif keys[pygame.K_DOWN]:
            self.speed -= self.brake
        else:
            # friction
            if self.speed > 0:
                self.speed -= self.friction
                if self.speed < 0:
                    self.speed = 0
            elif self.speed < 0:
                self.speed += self.friction
                if self.speed > 0:
                    self.speed = 0

        # Clamp speed
        if self.speed > self.max_speed:
            self.speed = self.max_speed
        if self.speed < -self.max_speed * 0.4:
            self.speed = -self.max_speed * 0.4

        # Steering (stronger when moving)
        if abs(self.speed) > 0.2:
            if keys[pygame.K_LEFT]:
                self.angle -= self.turn_speed * (self.speed / self.max_speed)
            if keys[pygame.K_RIGHT]:
                self.angle += self.turn_speed * (self.speed / self.max_speed)

        # Move
        rad = math.radians(self.angle)
        self.x += math.cos(rad) * self.speed
        self.y += math.sin(rad) * self.speed

        # Keep inside world
        self.x = max(0, min(WORLD_W, self.x))
        self.y = max(0, min(WORLD_H, self.y))

    def draw(self, surface, camera_x, camera_y):
        # Draw car as rotated rect
        car_rect = pygame.Rect(0, 0, self.length, self.width)
        car_rect.center = (self.x - camera_x, self.y - camera_y)

        car_surf = pygame.Surface((self.length, self.width), pygame.SRCALPHA)
        pygame.draw.rect(car_surf, CAR_COLOR, (0, 0, self.length, self.width), border_radius=6)
        # roof
        pygame.draw.rect(car_surf, (40, 40, 40),
                         (self.length * 0.25, self.width * 0.15,
                          self.length * 0.5, self.width * 0.7), border_radius=4)
        # windows
        pygame.draw.rect(car_surf, (120, 180, 220),
                         (self.length * 0.3, self.width * 0.2,
                          self.length * 0.4, self.width * 0.6), border_radius=3)

        rotated = pygame.transform.rotate(car_surf, -self.angle)
        rect = rotated.get_rect(center=car_rect.center)
        surface.blit(rotated, rect.topleft)

# Simple “Forza-lite” world: roads + fields
def draw_world(surface, camera_x, camera_y):
    # Sky background
    surface.fill(SKY)

    # Ground
    ground_rect = pygame.Rect(-camera_x, -camera_y, WORLD_W, WORLD_H)
    pygame.draw.rect(surface, GREEN, ground_rect)

    # Main highway (horizontal)
    pygame.draw.rect(surface, ROAD,
                     pygame.Rect(-camera_x, 800 - camera_y, WORLD_W, 120))
    # Vertical road
    pygame.draw.rect(surface, ROAD,
                     pygame.Rect(1400 - camera_x, -camera_y, 120, WORLD_H))

    # A few side roads
    pygame.draw.rect(surface, ROAD,
                     pygame.Rect(400 - camera_x, 300 - camera_y, 900, 80))
    pygame.draw.rect(surface, ROAD,
                     pygame.Rect(1800 - camera_x, 1200 - camera_y, 900, 80))

    # Lane markings (simple dashed lines)
    for x in range(0, WORLD_W, 80):
        pygame.draw.rect(surface, WHITE,
                         pygame.Rect(x - camera_x, 800 + 55 - camera_y, 40, 6))
    for y in range(0, WORLD_H, 80):
        pygame.draw.rect(surface, WHITE,
                         pygame.Rect(1400 + 55 - camera_x, y - camera_y, 6, 40))

    # Some “points of interest” blocks (like buildings)
    for bx, by in [(600, 500), (900, 900), (2000, 600), (2300, 1400)]:
        pygame.draw.rect(surface, (90, 90, 110),
                         pygame.Rect(bx - camera_x, by - camera_y, 160, 120))
        pygame.draw.rect(surface, (130, 130, 160),
                         pygame.Rect(bx + 10 - camera_x, by + 10 - camera_y, 60, 40))

    # Simple sun
    pygame.draw.circle(surface, YELLOW, (80, 80), 40)

# Minimap
def draw_minimap(surface, car):
    map_w, map_h = 220, 150
    margin = 10
    x0 = surface.get_width() - map_w - margin
    y0 = margin

    pygame.draw.rect(surface, (0, 0, 0, 180), (x0, y0, map_w, map_h), border_radius=6)
    mini = pygame.Surface((map_w - 10, map_h - 10), pygame.SRCALPHA)

    # Scale world into minimap
    sx = (map_w - 10) / WORLD_W
    sy = (map_h - 10) / WORLD_H
    s = min(sx, sy)

    # Draw roads (rough)
    pygame.draw.rect(mini, ROAD,
                     pygame.Rect(0, 800 * s, WORLD_W * s, 120 * s))
    pygame.draw.rect(mini, ROAD,
                     pygame.Rect(1400 * s, 0, 120 * s, WORLD_H * s))

    pygame.draw.rect(mini, ROAD,
                     pygame.Rect(400 * s, 300 * s, 900 * s, 80 * s))
    pygame.draw.rect(mini, ROAD,
                     pygame.Rect(1800 * s, 1200 * s, 900 * s, 80 * s))

    # Car dot
    cx = car.x * s
    cy = car.y * s
    pygame.draw.circle(mini, CAR_COLOR, (int(cx), int(cy)), 4)

    surface.blit(mini, (x0 + 5, y0 + 5))

def main():
    car = Car(600, 850)  # start on the main road
    running = True

    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        car.update(keys)

        # Camera follows car
        camera_x = car.x - SCREEN_W / 2
        camera_y = car.y - SCREEN_H / 2

        # Clamp camera to world
        camera_x = max(0, min(WORLD_W - SCREEN_W, camera_x))
        camera_y = max(0, min(WORLD_H - SCREEN_H, camera_y))

        draw_world(screen, camera_x, camera_y)
        car.draw(screen, camera_x, camera_y)
        draw_minimap(screen, car)

        # Simple HUD text
        speed_kmh = int(abs(car.speed) * 10)
        font = pygame.font.SysFont(None, 26)
        txt = font.render(f"Speed: {speed_kmh} km/h", True, (255, 255, 255))
        screen.blit(txt, (10, 10))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
