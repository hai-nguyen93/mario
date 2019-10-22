import pygame
from pygame.sprite import Sprite
from pygame.locals import *
from timer import Timer
from bullet import Bullet
from pygame.sprite import Group
from sound_clip import SoundClip


def tint(image, tint_color):
    image = image.copy()
    image.fill((0, 0, 0, 255), None, BLEND_RGB_MULT)
    image.fill(tint_color[0:3] + (0,), None, BLEND_RGBA_ADD)
    return image


class Player(Sprite):
    def __init__(self, screen, settings, stats, stage_manager, camera, hud):
        super().__init__()
        self.screen = screen
        self.screen_rect = screen.get_rect()
        self.settings = settings
        self.stats = stats
        self.sm = stage_manager
        self.camera = camera
        self.hud = hud
        self.bullets = Group()
        self.idle_image = pygame.image.load('images/player/idle.bmp')
        self.big_idle_image = pygame.image.load('images/player/big_idle.bmp')
        self.big_crouch_image = pygame.image.load('images/player/big_crouch.bmp')
        self.rect = self.idle_image.get_rect()
        self.rect.x, self.rect.y = 17, 0
        self.y = float(self.rect.y)
        self.x = float(self.rect.x)

        # movement variables
        self.vel = pygame.Vector2()
        self.vel.x, self.vel.y = 0, 0
        self.gravity = 0.3
        self.max_gravity = 8
        self.max_water_gravity = 4.5
        self.speed = 4
        self.jump_power = 8
        self.swim_power = 4.5
        self.is_grounded = False
        self.is_sliding = False
        self.is_crouching = False
        self.is_firing = False

        # player's states variables
        self.level = 1  # 1 = small, 2 = big, 3 = fire
        self.stage_clear = False
        self.dead = False
        self.invincible = False
        self.invin_time = 10000
        self.invin_start_time = 0
        self.invulnerable = False
        self.invuln_time = 1500
        self.invuln_start_time = 0

        # animations
        self.facing_right = True
        self.die_anim = Timer([pygame.image.load('images/player/die.bmp')])
        # small
        self.walk_anim = Timer([pygame.image.load('images/player/walk1.bmp'),
                                pygame.image.load('images/player/walk2.bmp'),
                                pygame.image.load('images/player/walk3.bmp')])
        self.idle_anim = Timer([self.idle_image])
        self.jump_anim = Timer([pygame.image.load('images/player/jump.bmp')])
        self.slide_anim = Timer([pygame.image.load('images/player/slide.bmp')])
        self.swim_anim = Timer([pygame.image.load('images/player/swim1.bmp'),
                                pygame.image.load('images/player/swim2.bmp'),
                                pygame.image.load('images/player/swim3.bmp'),
                                pygame.image.load('images/player/swim4.bmp')])
        # big
        self.big_idle_anim = Timer([self.big_idle_image])
        self.big_walk_anim = Timer([pygame.image.load('images/player/big_walk1.bmp'),
                                    pygame.image.load('images/player/big_walk2.bmp'),
                                    pygame.image.load('images/player/big_walk3.bmp')])
        self.big_jump_anim = Timer([pygame.image.load('images/player/big_jump.bmp')])
        self.big_slide_anim = Timer([pygame.image.load('images/player/big_slide.bmp')])
        self.big_crouch_anim = Timer([self.big_crouch_image])
        self.big_swim_anim = Timer([pygame.image.load('images/player/big_swim1.bmp'),
                                    pygame.image.load('images/player/big_swim2.bmp'),
                                    pygame.image.load('images/player/big_swim3.bmp'),
                                    pygame.image.load('images/player/big_swim4.bmp'),
                                    pygame.image.load('images/player/big_swim5.bmp'),
                                    pygame.image.load('images/player/big_swim6.bmp')])
        # fire
        self.fire_idle_anim = Timer([pygame.image.load('images/player/fire_idle.bmp')])
        self.fire_walk_anim = Timer([pygame.image.load('images/player/fire_walk1.bmp'),
                                    pygame.image.load('images/player/fire_walk2.bmp'),
                                    pygame.image.load('images/player/fire_walk3.bmp')])
        self.fire_jump_anim = Timer([pygame.image.load('images/player/fire_jump.bmp')])
        self.fire_slide_anim = Timer([pygame.image.load('images/player/fire_slide.bmp')])
        self.fire_crouch_anim = Timer([pygame.image.load('images/player/fire_crouch.bmp')])
        self.fire_throw_anim = Timer([pygame.image.load('images/player/fire_throw.bmp')],
                                     wait=150, step=0, looponce=True)
        self.fire_swim_anim = Timer([pygame.image.load('images/player/fire_swim1.bmp'),
                                     pygame.image.load('images/player/fire_swim2.bmp'),
                                     pygame.image.load('images/player/fire_swim3.bmp'),
                                     pygame.image.load('images/player/fire_swim4.bmp'),
                                     pygame.image.load('images/player/fire_swim5.bmp'),
                                     pygame.image.load('images/player/fire_swim6.bmp')])
        self.current_anim = self.idle_anim

        # sounds
        self.jump_sound = pygame.mixer.Sound('audio/jump.wav')
        self.big_jump_sound = pygame.mixer.Sound('audio/big_jump.wav')
        self.live_up_sound = pygame.mixer.Sound('audio/1-up.wav')
        self.die_sound = SoundClip('audio/die.wav')
        self.stage_clear_sound = SoundClip('audio/stage_clear.wav')
        self.stomp_sound = pygame.mixer.Sound('audio/stomp.wav')
        self.level_up_sound = pygame.mixer.Sound('audio/powerup.wav')
        self.fire_sound = pygame.mixer.Sound('audio/fire.wav')
        self.break_brick_sound = pygame.mixer.Sound('audio/breakbrick.wav')
        self.gameover_sound = pygame.mixer.Sound('audio/gameover.wav')
        self.invincible_sound = pygame.mixer.Sound('audio/invincibility.ogg')

    def update(self, platforms, enemies):
        # check stage clear:
        if self.stage_clear:
            if self.stage_clear_sound.is_finished():
                self.stats.current_stage += 1
                self.sm.load_stage(self.stats.current_stage, self.hud)
                self.reset()
            else:
                self.vel.x = self.vel.y = 0
                return

        # check falling off:
        if self.rect.y + self.camera.rect.y > self.screen_rect.height:
            if not self.dead:
                self.die()
            else:
                if self.die_sound.is_finished():
                    self.respawn()

        # check invincible timer
        if self.invincible:
            if pygame.time.get_ticks() - self.invin_start_time > self.invin_time:
                self.invincible_sound.stop()
                self.sm.bgm.play(-1)
                self.invincible = False

        # check invulnerable timer
        if self.invulnerable:
            if pygame.time.get_ticks() - self.invuln_start_time > self.invuln_time:
                self.invulnerable = False

        # check collision
        self.is_grounded = False
        if not self.dead:
            sprites_hit = pygame.sprite.spritecollide(self, platforms, False)
            if sprites_hit:
                for s in sprites_hit:
                    if s.tag == 'item':
                        if self.level < 2:
                            self.level_up(2)
                        s.kill()
                    if s.tag == 'flower':
                        if self.level < 3:
                            self.level_up(3)
                        s.kill()
                    if s.tag == 'star':
                        if not self.invincible:
                            self.sm.bgm.stop()
                            self.invincible_sound.play(-1)
                        self.invincible = True
                        self.invin_start_time = pygame.time.get_ticks()
                        s.kill()
                    if s.tag == 'brick':
                        self.collide_brick(s)
                    if s.tag == 'win':
                        pygame.mixer.stop()
                        self.stage_clear_sound.play()
                        self.stage_clear = True
                        score = int(abs(s.rect.bottom - self.rect.bottom) * 10 +
                                    ((self.sm.time_limit - self.sm.time_elapsed)//1000) * 10)
                        self.stats.score += score
                        self.hud.prep_score()
            # check collision with enemies
            enemies_hit = pygame.sprite.spritecollide(self, enemies, False)
            if enemies_hit:
                for e in enemies_hit:
                    self.collide_enemy(e)

        self.move()
        self.y += self.vel.y
        if self.camera.out_of_camera(self):
            self.x = -self.camera.rect.x
            self.vel.x = 0
        else:
            self.x += self.vel.x
        self.rect.y = int(self.y)
        self.rect.x = int(self.x)

        # update bullets
        for b in self.bullets:
            b.update(self, platforms, enemies)

    def move(self):
        # key inputs
        key_pressed = pygame.key.get_pressed()
        left = key_pressed[K_a] or key_pressed[K_LEFT]
        right = key_pressed[K_d] or key_pressed[K_RIGHT]
        crouch = key_pressed[K_s] or key_pressed[K_DOWN]

        # gravity
        if not self.is_grounded:
            self.vel.y += self.gravity
            if self.stats.current_stage == 2:
                if self.vel.y >= self.max_water_gravity:
                    self.vel.y = self.max_water_gravity
            else:
                if self.vel.y >= self.max_gravity:
                    self.vel.y = self.max_gravity
        else:
            self.vel.y = 0

        if not self.dead:
            # crouch
            if self.level > 1:
                if self.is_grounded:
                    self.is_crouching = crouch
                else:
                    self.is_crouching = crouch and self.is_crouching

                if self.is_crouching:
                    self.change_rect(self.big_crouch_image.get_rect())
                else:
                    self.change_rect(self.big_idle_image.get_rect())
            # move
            if not self.is_crouching:
                if left:  # move left
                    if self.vel.x > 0:
                        self.is_sliding = True
                    else:
                        self.is_sliding = False

                    if self.facing_right:
                        self.facing_right = not self.facing_right
                    if not self.camera.out_of_camera(self):
                        self.vel.x -= 0.1
                        if self.vel.x <= -self.speed:
                            self.vel.x = -self.speed
                    else:
                        self.vel.x = 0
                if right:  # move right
                    if self.vel.x < 0:
                        self.is_sliding = True
                    else:
                        self.is_sliding = False

                    if not self.facing_right:
                        self.facing_right = not self.facing_right
                    self.vel.x += 0.1
                    if self.vel.x >= self.speed:
                        self.vel.x = self.speed
            if not (left or right) or self.is_crouching:
                self.is_sliding = False
                if self.vel.x > 0:
                    self.vel.x -= 0.1
                    if self.vel.x <= 0:
                        self.vel.x = 0
                elif self.vel.x < 0:
                    self.vel.x += 0.1
                    if self.vel.x >= 0:
                        self.vel.x = 0

    def update_animation(self):
        if self.dead:
            self.current_anim = self.die_anim
            return

        if self.is_firing:
            if self.current_anim.finished:
                self.is_firing = False
            else:
                return

        if self.is_crouching:  # crouch
            if self.level == 2:
                self.current_anim = self.big_crouch_anim
            elif self.level == 3:
                self.current_anim = self.fire_crouch_anim
        else:
            if self.vel.y != 0:  # jump/fall animation
                if self.level == 1:
                    if self.stats.current_stage == 2:
                        self.current_anim = self.swim_anim
                    else:
                        self.current_anim = self.jump_anim
                elif self.level == 2:
                    if self.stats.current_stage == 2:
                        self.current_anim = self.big_swim_anim
                    else:
                        self.current_anim = self.big_jump_anim
                else:
                    if self.stats.current_stage == 2:
                        self.current_anim = self.fire_swim_anim
                    else:
                        self.current_anim = self.fire_jump_anim
            else:
                if self.is_sliding:  # slide animation
                    if self.level == 1:
                        self.current_anim = self.slide_anim
                    elif self.level == 2:
                        self.current_anim = self.big_slide_anim
                    else:
                        self.current_anim = self.fire_slide_anim
                else:
                    if self.vel.x != 0:  # walk animation
                        if self.level == 1:
                            self.current_anim = self.walk_anim
                        elif self.level == 2:
                            self.current_anim = self.big_walk_anim
                        else:
                            self.current_anim = self.fire_walk_anim
                    if self.vel.x == 0:  # idle animation
                        if self.level == 1:
                            self.current_anim = self.idle_anim
                        elif self.level == 2:
                            self.current_anim = self.big_idle_anim
                        else:
                            self.current_anim = self.fire_idle_anim

    def level_up(self, new_level):
        self.level = new_level
        self.level_up_sound.play()
        if self.level == 2:
            self.change_rect(self.big_idle_image.get_rect())
        if self.level >= 3:
            self.change_rect(self.big_idle_image.get_rect())

    def change_rect(self, new_rect):
        bot = self.rect.bottom
        self.rect = new_rect
        self.rect.x = int(self.x)
        self.rect.bottom = bot
        self.y = float(self.rect.y)

    def get_hit(self):
        if not self.invulnerable:
            if self.level > 1:
                self.level = 1
                self.change_rect(self.idle_image.get_rect())
                self.invulnerable = True
                self.invuln_start_time = pygame.time.get_ticks()
            else:
                self.die()

    def die(self):
        pygame.mixer.stop()
        self.die_sound.play()
        self.dead = True
        self.invulnerable = False
        self.bullets.empty()
        self.vel.x = 0
        self.vel.y = -12
        self.is_grounded = False
        self.y += self.vel.y
        self.rect.y = int(self.y)

    def fire(self):
        if self.level == 3:
            if len(self.bullets) < self.settings.bullet_limit:
                self.fire_sound.play()
                if self.facing_right:
                    d = 1
                    x = self.rect.right
                else:
                    d = -1
                    x = self.rect.left
                y = self.rect.centery
                self.bullets.add(Bullet(screen=self.screen, direction=d, x=x, y=y))
                if not self.is_crouching:
                    self.is_firing = True
                    self.fire_throw_anim.reset()
                    self.current_anim = self.fire_throw_anim

    def jump(self):
        if self.stage_clear:
            return

        jump_power = self.jump_power
        if self.stats.current_stage == 2:  # swim stage
            jump_power = self.swim_power
        else:
            self.jump_sound.play()
        self.vel.y = -jump_power
        self.y += self.vel.y
        self.rect.y = int(self.y)

    def reset(self):
        self.dead = self.is_grounded = self.invulnerable = self.invincible = self.stage_clear = False
        self.camera.reset()
        self.rect.x = 17
        self.rect.y = 0
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)
        self.vel.x = self.vel.y = 0

    def respawn(self):
        if self.stats.lives_left > 0:
            self.stats.lives_left -= 1
            self.level = 1
            self.change_rect(self.idle_image.get_rect())
            self.hud.prep_lives()
            self.reset()
            self.sm.reset(self.hud)
        else:
            self.stats.current_stage = -1
            self.gameover_sound.play()

    def collide_brick(self, brick):
        c = self.rect.clip(brick.rect)  # collision rect
        if c.width >= c.height:
            if self.vel.y >= 0 and self.rect.top < brick.rect.top:
                self.rect.bottom = brick.rect.top + 1
                self.y = float(self.rect.y)
                self.is_grounded = True
                self.vel.y = 0
            if self.vel.y < 0:
                self.rect.top = brick.rect.bottom
                self.y = float(self.rect.y)
                self.vel.y = 0
                if brick.tag == 'brick' and self.level > 1:
                    brick.kill()
                    self.break_brick_sound.play()
        if c.width < c.height:
            if self.rect.right > brick.rect.left > self.rect.left:
                self.vel.x = -1
                self.rect.right = brick.rect.left
                self.x = float(self.rect.x)
            elif self.rect.left < brick.rect.right < self.rect.right:
                self.vel.x = 1
                self.rect.left = brick.rect.right
                self.x = float(self.rect.x)

    def collide_enemy(self, enemy):
        if self.invincible:
            self.stats.score += enemy.point
            self.hud.prep_score()
            enemy.die()
            return

        c = self.rect.clip(enemy.rect)  # collision rect
        if c.width > c.height and self.vel.y > 0:
            self.stomp_sound.play()
            self.stats.score += enemy.point
            self.hud.prep_score()
            self.vel.y = -6
            self.y += self.vel.y
            self.rect.y = int(self.y)
            enemy.die()
            return

        self.get_hit()

    def draw1(self):  # draw with camera
        self.update_animation()

        # draw bullets
        for b in self.bullets:
            b.draw(self.camera)

        # draw player
        if self.facing_right:
            image = self.current_anim.imagerect()
        else:
            image = pygame.transform.flip(self.current_anim.imagerect(), True, False)

        if self.invincible:  # invincible
            if (pygame.time.get_ticks()//100) % 2 == 0:
                image = tint(image,  (245, 176, 65))

        if self.invulnerable:  # invulnerable
            if (pygame.time.get_ticks() // 100) % 2 == 0:
                return
        self.screen.blit(image, self.camera.apply(self))

    def draw(self):
        self.update_animation()
        self.screen.blit(self.current_anim.imagerect(), self.rect)
