import random

import pygame

pygame.init()

W, H = 1920, 1080
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption('Звездное противостояние')

background = pygame.transform.scale(pygame.image.load('images/background.png'), (W, H))

background_sound = pygame.mixer.Sound('sounds/background_sound.mp3')
fire_sound = pygame.mixer.Sound('sounds/fire_sound.mp3')
hit_sound = pygame.mixer.Sound('sounds/hit_sound.mp3')

background_sound.set_volume(0.07)
fire_sound.set_volume(0.07)
hit_sound.set_volume(0.1)

red_ship = pygame.image.load('images/pixel_ship_red_small.png')
green_ship = pygame.image.load('images/pixel_ship_green_small.png')
blue_ship = pygame.image.load('images/pixel_ship_blue_small.png')
player_ship = pygame.image.load('images/pixel_ship_yellow.png')

red_laser = pygame.image.load('images/pixel_laser_red.png')
green_laser = pygame.image.load('images/pixel_laser_green.png')
blue_laser = pygame.image.load('images/pixel_laser_blue.png')
player_laser = pygame.image.load('images/pixel_laser_yellow.png')


class Laser:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def move(self, vel):
        self.y += vel

    def off_screen(self, height):
        return not (height >= self.y >= 0)

    def collision(self, obj):
        return collide(self, obj)


class Ship:
    COOLDOWN = 30

    def __init__(self, x, y, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.ship_img = None
        self.laser_img = None
        self.lasers = []
        self.cool_down_counter = 0

    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

    def move_lasers(self, vel, obj):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(H):
                self.lasers.remove(laser)
            elif laser.collision(obj):
                obj.health -= 10
                self.lasers.remove(laser)

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1
            fire_sound.play()

    def cooldown(self):
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()


class Player(Ship):
    def __init__(self, x, y, health=100):
        super().__init__(x, y, health)
        self.ship_img = player_ship
        self.laser_img = player_laser
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health

    def move_lasers(self, vel, objs):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(H):
                self.lasers.remove(laser)
            else:
                for obj in objs:
                    if laser.collision(obj):
                        objs.remove(obj)
                        hit_sound.play()
                        if laser in self.lasers:
                            self.lasers.remove(laser)

    def draw(self, window):
        super().draw(window)
        self.healthbar(window)

    def healthbar(self, window):
        pygame.draw.rect(window, (0, 255, 0), (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width(), 10))
        pygame.draw.rect(window, (255, 0, 0), (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width() * (1 - (self.health / self.max_health)), 10))


class Enemy(Ship):
    COLOR_MAP = {
        'blue': (blue_ship, blue_laser),
        'green': (green_ship, green_laser),
        'red': (red_ship, red_laser)
    }

    def __init__(self, x, y, color, health=100):
        super().__init__(x, y, health)
        self.ship_img, self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)

    def move(self, vel):
        self.y += vel

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x - 20, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1


def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) is not None


def main():
    running = True
    level = 0
    lives = 5
    main_font = pygame.font.SysFont('impact', 50)
    lost_font = pygame.font.SysFont('impact', 60)

    enemies = []
    wave_length = 5
    enemy_vel = 2

    player_vel = 10
    laser_vel = 8

    player = Player(890, H - 300)

    clock = pygame.time.Clock()

    lost = False
    lost_count = 0

    def redraw_window():
        screen.blit(background, (0, 0))

        lives_label = main_font.render(f"Жизни: {lives}", 1, (255, 255, 255))
        level_label = main_font.render(f"Уровень: {level}", 1, (255, 255, 255))

        screen.blit(lives_label, (10, 10))
        screen.blit(level_label, (W - level_label.get_width() - 10, 10))

        for enemy in enemies:
            enemy.draw(screen)

        player.draw(screen)

        if lost:
            lost_label = lost_font.render('Ты проиграл(', 1, (255, 255, 255))
            screen.blit(lost_label, (W / 2 - lost_label.get_width() / 2, 350))

        pygame.display.update()

    while running:
        clock.tick(60)
        redraw_window()

        if lives <= 0 or player.health <= 0:
            lost = True
            lost_count += 1

        if lost:
            if lost_count > 180:
                running = False

        if len(enemies) == 0:
            level += 1
            wave_length += 5

            for i in range(wave_length):
                enemy = Enemy(random.randrange(50, W - 100), random.randrange(-1200, -100), random.choice(['red', 'green', 'blue']))
                enemies.append(enemy)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] and player.x + player_vel > 0:
            player.x -= player_vel
        if keys[pygame.K_d] and player.x + player_vel + player.get_width() < W:
            player.x += player_vel
        if keys[pygame.K_w] and player.y - player_vel > 0:
            player.y -= player_vel
        if keys[pygame.K_s] and player.y + player_vel + player.get_height() + 15 < H:
            player.y += player_vel
        if keys[pygame.K_SPACE]:
            player.shoot()

        for enemy in enemies[:]:
            enemy.move(enemy_vel)
            enemy.move_lasers(laser_vel, player)

            if random.randrange(120) == 1:
                enemy.shoot()

            if collide(enemy, player):
                player.health -= 10
                enemies.remove(enemy)
            elif enemy.y + enemy.get_height() > H:
                lives -= 1
                enemies.remove(enemy)

        player.move_lasers(-laser_vel, enemies)


def main_menu():
    title_font = pygame.font.SysFont('impact', 90)

    running = True
    while running:
        screen.blit(background, (0, 0))
        title_label = title_font.render('Нажми на мышку, чтобы начать', 1, (255, 255, 255))
        screen.blit(title_label, (W / 2 - title_label.get_width() / 2, 450))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                main()

    pygame.quit()


background_sound.play(-1)
main_menu()
