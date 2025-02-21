import turtle
import math
import random
import pygame
from pygame import mixer
import os
from pathlib import Path

pygame.mixer.init()

SOUND_DIR = Path("sounds")
SOUND_DIR.mkdir(exist_ok=True)

screen = turtle.Screen()
screen.bgcolor("black")
screen.title("Space Invaders")
screen.setup(800, 600)
screen.tracer(0)

screen.register_shape("spaceship", ((-10, -10), (0, 10), (10, -10)))
screen.register_shape("alien", ((0, 10), (-10, -10), (10, -10)))

class SoundManager:
    def __init__(self):
        self.sounds = {
            'shoot': pygame.mixer.Sound('sounds/shoot.wav') if os.path.exists('sounds/shoot.wav') else None,
            'explosion': pygame.mixer.Sound('sounds/explosion.wav') if os.path.exists('sounds/explosion.wav') else None,
            'gameover': pygame.mixer.Sound('sounds/gameover.wav') if os.path.exists('sounds/gameover.wav') else None
        }
    
    def play(self, sound_name):
        if self.sounds.get(sound_name):
            self.sounds[sound_name].play()

class Player:
    def __init__(self):
        self.turtle = turtle.Turtle()
        self.turtle.shape("spaceship")
        self.turtle.color("white")
        self.turtle.penup()
        self.turtle.speed(0)
        self.turtle.setposition(0, -250)
        self.turtle.setheading(90)
        self.speed = 15
        self.respawn_pos = (0, -250)
        self.invincible_time = 60  # 1 second of invincibility after respawn
        self.respawn_position = (0, -250)
        self.blink_timer = 0
        self.flash_timer = 0  # Add this line
        self.score = 0
        self.invulnerable = False
        self.invulnerable_timer = 0
        self.reset()
    
    def reset(self):
        self.lives = 3
        self.score = 0
        self.turtle.showturtle()
        self.turtle.setposition(0, -250)
        self.invulnerable = False
        self.invulnerable_timer = 0
        self.blink_timer = 0
        self.flash_timer = 0  # Add this line

    def move_left(self):
        x = self.turtle.xcor()
        x -= self.speed
        if x < -380:
            x = -380
        self.turtle.setx(x)

    def move_right(self):
        x = self.turtle.xcor()
        x += self.speed
        if x > 380:
            x = 380
        self.turtle.setx(x)

    def hit(self):
        if not self.invulnerable:
            self.lives -= 1
            self.invulnerable = True
            self.invulnerable_timer = 60
            return True
        return False
        
    def reset_position(self):
        self.turtle.setposition(*self.respawn_pos)
        self.invulnerable = True
        self.invulnerable_timer = 120  # 2 seconds of invulnerability
        self.flash_timer = 0
        self.turtle.showturtle()

    def respawn(self):
        self.turtle.setposition(0, -250)
        self.invulnerable = True
        self.invulnerable_timer = 60  # 1 second invincibility
        self.blink_timer = 0
        self.flash_timer = 0  # Add this line
        self.turtle.showturtle()

    def update(self):
        if self.invulnerable:
            self.invulnerable_timer -= 1
            self.blink_timer += 1
            
            # Simplified blinking effect
            if self.blink_timer % 6 == 0:
                if self.turtle.isvisible():
                    self.turtle.hideturtle()
                else:
                    self.turtle.showturtle()
                    
            if self.invulnerable_timer <= 0:
                self.invulnerable = False
                self.turtle.showturtle()

class Bullet:
    def __init__(self):
        self.turtle = turtle.Turtle()
        self.turtle.shape("circle")
        self.turtle.color("yellow")
        self.turtle.penup()
        self.turtle.speed(0)
        self.turtle.hideturtle()
        self.turtle.setheading(90)
        self.speed = 20
        self.state = "ready"

    def fire(self, x, y):
        if self.state == "ready":
            self.state = "fired"
            self.turtle.setposition(x, y + 10)
            self.turtle.showturtle()

    def move(self):
        if self.state == "fired":
            y = self.turtle.ycor()
            y += self.speed
            self.turtle.sety(y)
            if y > 275:
                self.turtle.hideturtle()
                self.state = "ready"

class Alien:
    def __init__(self, x, y):
        self.turtle = turtle.Turtle()
        self.turtle.shape("alien")
        self.turtle.color("green")
        self.turtle.penup()
        self.turtle.speed(0)
        self.turtle.setposition(x, y)
        self.speed = 2
        self.direction = 1

class Game:
    def __init__(self):
        self.player = Player()
        self.bullet = Bullet()
        self.aliens = []
        self.sound_manager = SoundManager()
        self.game_over = False
        self.game_over_text = None  # Add this line to track game over text
        self.game_over_pen = None  # Add this to track game over message
        
        self.setup_display()
        self.setup_lives_display()
        
        self.setup_aliens()
        self.setup_controls()
        self.reset_game()

    def reset_game(self):
        # Clear game over messages
        if self.game_over_text is not None:
            self.game_over_text.clear()
            self.game_over_text.hideturtle()
            self.game_over_text = None

        # Clear all aliens
        for alien in self.aliens[:]:  # Use slice copy to avoid modification issues
            alien.turtle.hideturtle()
        self.aliens.clear()
        
        # Reset score display
        self.score_pen.clear()
        self.lives_pen.clear()
        
        # Reset player and bullet
        self.player = Player()
        self.bullet.turtle.hideturtle()
        self.bullet.state = "ready"
        
        # Reset game state
        self.game_over = False
        
        # Setup new game
        self.setup_aliens()
        self.update_score()
        self.update_lives_display()
        
        # Ensure controls are active
        self.setup_controls()

    def setup_display(self):
        self.score_pen = turtle.Turtle()
        self.score_pen.speed(0)
        self.score_pen.color("white")
        self.score_pen.penup()
        self.score_pen.hideturtle()
        self.score_pen.goto(-380, 260)
        
        self.lives_pen = turtle.Turtle()
        self.lives_pen.speed(0)
        self.lives_pen.color("white")
        self.lives_pen.penup()
        self.lives_pen.hideturtle()
        self.lives_pen.goto(280, 260)
        
        self.update_score()

    def setup_lives_display(self):
        self.life_icons = []
        for i in range(3):
            life = turtle.Turtle()
            life.shape("spaceship")
            life.color("green")
            life.penup()
            life.hideturtle()
            life.goto(280 + i * 30, 260)
            life.setheading(90)
            life.showturtle()
            self.life_icons.append(life)

    def update_lives_display(self):
        for i, life in enumerate(self.life_icons):
            if i < self.player.lives:
                life.showturtle()
            else:
                life.hideturtle()

    def setup_aliens(self):
        for i in range(5):
            for j in range(11):
                alien = Alien(-250 + j * 50, 200 - i * 40)
                self.aliens.append(alien)

    def setup_controls(self):
        screen.onkey(self.player.move_left, "Left")
        screen.onkey(self.player.move_right, "Right")
        screen.onkey(self.fire_bullet, "space")
        screen.onkey(self.handle_restart, "r")
        screen.listen()

    def handle_restart(self):
        if self.game_over:
            self.reset_game()

    def fire_bullet(self):
        if self.bullet.state == "ready":
            self.sound_manager.play('shoot')
            self.bullet.fire(self.player.turtle.xcor(), self.player.turtle.ycor())

    def check_collision(self, t1, t2, threshold=20):
        distance = math.sqrt(
            math.pow(t1.xcor() - t2.xcor(), 2) +
            math.pow(t1.ycor() - t2.ycor(), 2)
        )
        return distance < threshold

    def update_score(self):
        self.score_pen.clear()
        self.score_pen.write(
            f"Score: {self.player.score}", 
            font=("Arial", 14, "normal")
        )
        self.lives_pen.clear()
        self.lives_pen.write(
            f"Lives: {self.player.lives}", 
            font=("Arial", 14, "normal")
        )

    def show_game_over(self):
        self.sound_manager.play('gameover')
        
        # Clear previous game over text if it exists
        if self.game_over_text is not None:
            self.game_over_text.clear()
            self.game_over_text.hideturtle()
        
        # Create new game over text
        self.game_over_text = turtle.Turtle()
        self.game_over_text.speed(0)
        self.game_over_text.color("white")
        self.game_over_text.penup()
        self.game_over_text.hideturtle()
        self.game_over_text.goto(0, 0)
        self.game_over_text.write("GAME OVER\nPRESS R TO RESTART", 
                                 align="center", 
                                 font=("Arial", 30, "bold"))

    def handle_collision(self):
        if not self.player.invulnerable:
            self.player.lives -= 1
            self.update_lives_display()
            self.sound_manager.play('explosion')
            
            if self.player.lives <= 0:
                self.game_over = True
                self.show_game_over()
            else:
                # Just respawn player, keep aliens in current position
                self.player.respawn()
                self.bullet.state = "ready"
                self.bullet.turtle.hideturtle()
            return True
        return False

    def update(self):
        if self.game_over:
            return

        screen.update()
        
        self.player.update()
        self.bullet.move()

        # Check collisions in a safe way
        aliens_to_remove = []
        for alien in self.aliens:
            x = alien.turtle.xcor()
            x += alien.speed * alien.direction
            alien.turtle.setx(x)

            # Check for wall collision
            if x > 380 or x < -380:
                for a in self.aliens:
                    y = a.turtle.ycor()
                    y -= 40
                    a.turtle.sety(y)
                    a.direction *= -1
                    if y < -230:
                        # Remove game over here - just take away a life
                        if not self.player.invulnerable:
                            self.handle_collision()
                        return

            # Check collision with player
            if self.check_collision(self.player.turtle, alien.turtle, 30):
                if self.handle_collision():
                    continue  # Continue playing if lives remain

            # Check collision with bullet
            if self.bullet.state == "fired" and self.check_collision(self.bullet.turtle, alien.turtle):
                self.sound_manager.play('explosion')
                self.bullet.turtle.hideturtle()
                self.bullet.state = "ready"
                aliens_to_remove.append(alien)
                self.player.score += 10

        # Remove destroyed aliens and update score
        for alien in aliens_to_remove:
            alien.turtle.hideturtle()
            self.aliens.remove(alien)
        
        if aliens_to_remove:
            self.update_score()
            if not self.aliens:
                self.setup_aliens()

def main():
    game = Game()
    
    # Main game loop
    while True:
        screen.onkey(game.handle_restart, "r")  # Changed to handle_restart
        screen.listen()
        game.update()

if __name__ == "__main__":
    main()
