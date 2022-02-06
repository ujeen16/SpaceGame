import pygame
import os
import random
pygame.font.init()
pygame.mixer.init()


WIDTH, HEIGHT = 750, 750
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders")

WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

RED_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_red_small.png"))
GREEN_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_green_small.png"))
BLUE_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_blue_small.png"))

BOSS_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_boss.png"))

# Player ship
YELLOW_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_yellow.png"))
LASER_SOUND = pygame.mixer.Sound(os.path.join("assets", "SpaceLaserShot.mp3"))

# Lasers
RED_lASER = pygame.image.load(os.path.join("assets", "pixel_laser_red.png"))
GREEN_lASER = pygame.image.load(os.path.join("assets", "pixel_laser_green.png"))
BLUE_lASER = pygame.image.load(os.path.join("assets", "pixel_laser_blue.png"))

BOSS_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_beam_boss.png"))
BOSS_BOMB = pygame.image.load(os.path.join("assets", "pixel_bomb.png"))
BOSS_ICE_BLAST = pygame.image.load(os.path.join("assets", "pixel_ice_laser.png"))
BOSS_MUSIC = pygame.mixer.Sound(os.path.join("assets", "Orbital Colossus.mp3"))

YELLOW_lASER = pygame.image.load(os.path.join("assets", "pixel_laser_yellow.png"))

# Background
BG = pygame.transform.scale(pygame.image.load(os.path.join("assets", "background-black.png")), (WIDTH, HEIGHT))

# rather than working with a hit box we work with masks which represent the pixels of the ship and laser
# we use the offset as a parameter ie the distance from the top left corner of each
# when no collision is dettected we will return None if collision then return (x,y)


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
        return not(self.y <= height and self.y >= 0)

    def collision(self, obj):
        return collide(self, obj)


class Ship:
    def __init__(self, x, y, health=100, firerate=60):
        self.x = x
        self.y = y
        self.health = health
        self.ship_img = None
        self.laser_img = None
        self.laser_sound = None
        self.firerate = firerate  # speed of lasers shooting
        self.lasers = []
        self.cool_down_counter = 0

    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))
        # rectangular shape para1: where is it para2: color para3: (start_loc_x, start_loc_y, x_size, y_size)
        # para4: if value then rectangle has width specified. if no val. then filled in rectangle
        # pygame.draw.rect(window, RED, (self.x, self.y, 50, 50))
        for laser in self.lasers:
            laser.draw(window)

    def move_lasers(self, vel, obj):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(obj):
                obj.health -= 10
                self.lasers.remove(laser)

    def cooldown(self):
        if self.cool_down_counter >= self.firerate:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()


class Player(Ship):
    def __init__(self, x, y, health=100, firerate=45, currency=0, upgrade_counter=[1, 1, 1]):
        super().__init__(x, y, health, firerate)
        self.ship_img = YELLOW_SPACE_SHIP
        self.currency = currency
        self.upgrade_counter = upgrade_counter
        self.laser_img = YELLOW_lASER
        self.laser_sound = LASER_SOUND
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health

    def move_lasers(self, vel, objs, b_objs):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                for obj in objs:
                    if laser.collision(obj):
                        if laser.collision(obj):
                            self.currency += 1

                        # these three lines are for health regen upgrade
                        if self.upgrade_counter[2] > 1:
                            for i in range(self.upgrade_counter[2] - 1):
                                self.health_regen()
                        if laser.collision(obj):
                            objs.remove(obj)
                        # if remove this then laser remains until HEIGHT limitation not on distruction?
                        if laser in self.lasers:
                            self.lasers.remove(laser)
                if b_objs:
                    if laser.collision(b_objs[0]):
                        if self.upgrade_counter[2] > 1:
                            for i in range(self.upgrade_counter[2] - 1):
                                self.health_regen()
                        if laser.collision(b_objs[0]):
                            # need to remove health here
                            if (b_objs[0].hit(b_objs)) == 0:
                                b_objs.remove(b_objs[0])
                                BOSS_MUSIC.stop()
                        if laser in self.lasers:
                            self.lasers.remove(laser)

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1
            self.laser_sound.play()

    def end_round_currency(self):
        self.currency += 6

    def draw(self, window):
        super().draw(window)
        self.healthbar(window)

    def health_regen_endround(self):
        max_heal = .2 * self.max_health
        if self.max_health-self.health < max_heal:
            self.health = self.max_health
        else:
            self.health += max_heal

    def health_regen(self):
        if self.health == 99:
            self.health += 1
        elif self.health == 98:
            self.health += 2
        elif self.health == 97:
            self.health += 3
        elif self.health <= 96:
            self.health += 4

    # basic idea: 2 different bars overlap each other one colored green and the other red
    # green will be over the red and move left based on the percent of health remaining in opposition to max health
    # the bar is placed slightly over a player ship img and stretches the full length of that img
    def healthbar(self, window):
        pygame.draw.rect(window, RED, (self.x, self.y + self.ship_img.get_height() + 10,
                                       self.ship_img.get_width(), 10))
        pygame.draw.rect(window, GREEN, (self.x, self.y + self.ship_img.get_height() + 10,
                                         self.ship_img.get_width() * (self.health/self.max_health), 10))

    def upgrade_firerate(self):
        cost = 10 * self.upgrade_counter[0]
        if self.currency > cost:
            self.currency -= cost
            if cost > 30:
                self.firerate -= 3
            else:
                self.firerate -= 5
            self.upgrade_counter[0] += .5

    def upgrade_maxhealth(self):
        cost = 10 * self.upgrade_counter[1]
        if self.currency > cost:
            self.currency -= cost
            self.health += 100
            self.max_health = self.health
            self.upgrade_counter[1] += .5

    def upgrade_lifesteal(self):
        cost = 10 * self.upgrade_counter[2]
        if self.currency > cost:
            self.currency -= cost
            self.upgrade_counter[2] += 1


class Enemy(Ship):
    COLOR_MAP = {
        "red": (RED_SPACE_SHIP, RED_lASER),
        "green": (GREEN_SPACE_SHIP, GREEN_lASER),
        "blue": (BLUE_SPACE_SHIP, BLUE_lASER)
    }

    def __init__(self, x, y, color, health=100, firerate=45):
        super().__init__(x, y, health, firerate)
        self.ship_img, self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.color = color

    # blue ships move faster
    def move(self, vel):
        if self.color == "blue":
            self.y += vel
        self.y += vel

    # red ship does double damage
    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x-20, self.y, self.laser_img)
            self.lasers.append(laser)
            if self.color == "red":
                laser_2x_dmg = Laser(self.x-20, self.y, self.laser_img)
                self.lasers.append(laser_2x_dmg)

            self.cool_down_counter = 1


class Boss(Ship):
    def __init__(self, x, y, health=1000, firerate=60):
        super().__init__(x, y, health, firerate)
        self.ship_img, self.laser_img = BOSS_SHIP, BOSS_LASER
        self.boss_ice_laser_img = BOSS_ICE_BLAST
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health
        self.right = True
        self.cool_down_counter_ice = 0
        self.cool_down_counter_bomb = 0

    # boss comes down the screen and stops moving right and left
    def move(self, vel):
        if self.y < 100:
            self.y += vel
        if self.x > 15 and self.right:
            self.x -= vel
            if self.x < 25:
                self.right = False
        else:
            self.x += vel
            if self.x > 530:
                self.right = True

    def cooldown_ice(self):
        if self.cool_down_counter_ice >= self.firerate:
            self.cool_down_counter_ice = 0
        elif self.cool_down_counter_ice > 0:
            self.cool_down_counter_ice += 1

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x+40, self.y, self.laser_img)
            self.lasers.append(laser)
            laserr = Laser(self.x-40, self.y, self.laser_img)
            self.lasers.append(laserr)
            laserrr = Laser(self.x+120, self.y, self.laser_img)
            self.lasers.append(laserrr)
            self.cool_down_counter = 1

    def ice_shot(self):
        if self.cool_down_counter_ice == 0:
            ice_laser = Laser(self.x+5, self.y + 30, self.boss_ice_laser_img)
            self.lasers.append(ice_laser)
            ice_laserr = Laser(self.x+220, self.y + 30, self.boss_ice_laser_img)
            self.lasers.append(ice_laserr)
            self.cool_down_counter_ice += 1

    def move_lasers(self, vel, obj):
        self.cooldown()
        self.cooldown_ice()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(obj):
                obj.health -= 10
                self.lasers.remove(laser)

    def hit(self, b_objs):
        self.health -= 10
        return self.health

    def draw(self, window):
        super().draw(window)
        self.healthbar(window)

    def healthbar(self, window):
        pygame.draw.rect(window, RED, (self.x, self.y - 20,
                                       self.ship_img.get_width(), 10))
        pygame.draw.rect(window, GREEN, (self.x, self.y - 20,
                                         self.ship_img.get_width() * (self.health/self.max_health), 10))


def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) is not None


def render_multi_line(text, x, y, fsize, font, color):
    lines = text.splitlines()
    for i, l in enumerate(lines):
        WIN.blit(font.render(l, True, color), (x, y + fsize*i))


def main():
    run = True
    FPS = 60
    level = 0
    lives = 5
    main_font = pygame.font.SysFont("comicsans", 45)
    lost_font = pygame.font.SysFont("comicsans", 60)

    enemies = []
    bosses = []
    wave_length = 4
    enemy_vel = 1

    player_vel = 5
    laser_vel = 5

    player = Player(300, 630)

    clock = pygame.time.Clock()

    lost = False
    won = False
    lost_count = 0
    won_count = 0

    def redraw_window():
        # coordinate grid starts in top left so...draw BackGround starting in top right corner
        WIN.blit(BG, (0, 0))
        # draw text
        lives_label = main_font.render(f"Lives: {lives}", True, WHITE)
        level_label = main_font.render(f"Level: {level}", True, WHITE)
        currency_label = main_font.render(f"Currency: {player.currency}", True, WHITE)

        # we want ten so that words are not right on the very edge of screen
        # we write these labels and use the get width to save enough space on right side for
        # the level label to write plus the ten space so not right on edge again
        WIN.blit(lives_label, (10, 10))
        WIN.blit(level_label, (WIDTH - level_label.get_width() - 10, 10))
        WIN.blit(currency_label, (lives_label.get_width() + 90, 10))
        for boss in bosses:
            boss.draw(WIN)
        for enemy in enemies:
            enemy.draw(WIN)

        player.draw(WIN)

        if lost:
            lost_label = lost_font.render("You Lost!!", True, WHITE)
            # use getters/2 to account for the size of the label words to perfectly center
            WIN.blit(lost_label, (WIDTH/2 - lost_label.get_width()/2, HEIGHT/2 - lost_label.get_height()/2))

        if won:
            won_label = lost_font.render("YOU WON!!!!", True, WHITE)
            WIN.blit(won_label, (WIDTH/2 - won_label.get_width()/2, HEIGHT/2 - won_label.get_height()/2))

        pygame.display.update()

    while run:
        if level == 11:
            won = True
        clock.tick(FPS)
        redraw_window()

        # Once a condition to lost is met increase set lost to True triggering next if
        if lives <= 0 or player.health <= 0:
            lost = True
            lost_count += 1
        # Once lost, display the message for duration of lost_count. lost count is increased by 1 every FPS
        # bc of this FPS * the number of secs we want the message to remain on screen before closing on later condition

        if lost:
            if lost_count > FPS * 3:
                run = False
            else:
                continue

        if won:
            if won_count > FPS * 3:
                run = False
            else:
                continue

        # when finishing a wave do this, this is why wave technically starts at 0
        if len(enemies) == 0:
            level += 1
            wave_length += 5
            player.health_regen_endround()
            if level != 0:
                player.end_round_currency()
            if level == 10:
                boss = Boss(200, -350)
                bosses.append(boss)
                BOSS_MUSIC.play()


            waveOne = ["green"]
            waveTwo = ["green", "green", "green", "red"]
            waveThree = ["green", "green", "red"]
            waveFour = ["green", "green", "red"]
            waveFive = ["green", "green", "green", "green", "red", "red", "blue"]
            waveSix = ["red"]
            waveSeven = ["green", "green", "green", "red", "blue", "blue"]
            waveEight = ["blue"]
            waveNine = ["green", "red", "blue"]
            waveTen = ["green", "red", "red", "red", "blue"]
            waves = [waveOne, waveTwo, waveThree, waveFour, waveFive, waveSix, waveSeven, waveEight, waveNine, waveTen, waveTen]

            for i in range(wave_length):
                # enemy takes an x and a y value and picks a value in acceptable x coordinates
                # y will be above the map with different values so ships come down at different times
                # could change the y value of 1500 to adjust based on wave divided by a number for higher num of enemies
                # random picks a random collored ship...currently collor makes no difference

                enemy = Enemy(random.randrange(50, WIDTH-100), random.randrange(-1500, -100),
                              random.choice(waves[level-1]))
                # green enemys have no buff therefore they will be the more common enemy
                enemies.append(enemy)
        # if call an event to end the game then quit the window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # rather than run=False bc that would cause x to lead to the menu option to play again
                quit()

        # this allows player to press multiple keys and have them register
        # logic is included which keeps the ship in the bounds of the map using and statement
        # 9 is adjustment used because the ship has some extra blank space on top left and right but not bottom
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] and player.x - player_vel + 9 > 0:  # left
            player.x -= player_vel
        if keys[pygame.K_d] and player.x + player_vel + player.get_width() - 9 < WIDTH:  # right
            player.x += player_vel
        if keys[pygame.K_w] and player.y - player_vel + 9 > 0:  # up
            player.y -= player_vel
        if keys[pygame.K_s] and player.y + player_vel + player.get_height() + 15 < HEIGHT:  # down
            player.y += player_vel
        if keys[pygame.K_SPACE]:
            player.shoot()

        if keys[pygame.K_1]:
            player.upgrade_firerate()
        if keys[pygame.K_2]:
            player.upgrade_maxhealth()
        if keys[pygame.K_3]:
            player.upgrade_lifesteal()

        for boss in bosses[:]:
            boss.move(enemy_vel)
            boss.move_lasers(laser_vel, player)
            if random.randrange(0, 2*FPS) == 1:
                boss.shoot()
            if random.randrange(0, 2*FPS) == 1:
                boss.ice_shot()
            # dont run into the boss
            if collide(boss, player):
                player.health -= 1000
                bosses.remove(boss)

        for enemy in enemies[:]:
            enemy.move(enemy_vel)
            enemy.move_lasers(laser_vel, player)

            # 50% chance that every second an enemy will shoot
            if random.randrange(0, 2*FPS) == 1:
                enemy.shoot()

            # these handle the situation when an enemy comes in contact with player or hits the bottom of screen
            # elif is used because both cant happen together
            if collide(enemy, player):
                player.health -= 10
                enemies.remove(enemy)
            elif enemy.y + enemy.get_height() > HEIGHT:
                lives -= 1
                enemies.remove(enemy)

        player.move_lasers(-laser_vel, enemies, bosses)


def main_menu():
    title_font = pygame.font.SysFont("comicsans", 55)
    info_font = pygame.font.SysFont("comicsans", 18)
    run = True
    while run:
        WIN.blit(BG, (0, 0))
        title_label = title_font.render("Press the mouse to begin...", True, WHITE)
        game_info_text = "GAME INFO\n" \
            "lives will reduce by 1 when enemies reach the bottom of the screen\n" \
            "total health is 100, total lives are 5\n" \
            "health decreases by 10 when hit by a laser or hitting ship\n" \
            "careful the red ships do double dmg and blue ships move double speed\n" \
            "move with: wasd and shoot with spacebar\n" \
            "hold spacebar for max firerate may lose accuracy\n" \
            "currecy is gained when defeating an enemy or ending a level\n" \
            "upgrades will be needed to survive\n" \
            "press 1 or 3 for upgrades\n" \
            "cost is not displayed and is part of the game/strategy\n" \
            "1: is firerate cost is 10 and increases 5 each upgrade\n" \
            "2: is a 100 health boost to players maximum health\n" \
            "3: is lifesteal cost is 10 and increases 10 each upgrade\n" \
            "level ten is the final round before winning the game\n" \
            "beware of a new enemy at level ten"
        render_multi_line(game_info_text, 30, 30, 30, info_font, WHITE)
        WIN.blit(title_label, (WIDTH/2 - title_label.get_width()/2, 500))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                main()

    pygame.quit()


main_menu()
