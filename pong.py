import tkinter as tk
import pygame
import random
import math

# Initialize pygame for sound
pygame.init()
collision_sound = pygame.mixer.Sound("collision.wav")  # Add a collision sound file
brick_hit_sound = pygame.mixer.Sound("brick_hit.wav")  # Add a brick hit sound file


class Game(tk.Frame):
    def __init__(self, master):
        super(Game, self).__init__(master)
        self.lives = 30
        self.width = 800
        self.height = 600
        self.canvas = tk.Canvas(self, width=self.width, height=self.height, highlightthickness=0)
        self.canvas.pack()
        self.pack()

        # Add gradient background
        self.draw_gradient_background()

        self.items = {}
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width // 2, self.height - 30)
        self.items[self.paddle.item] = self.paddle
        for x in range(5, self.width - 5, 75):
            self.add_brick(x + 37.5, 50, 2)
            self.add_brick(x + 37.5, 70, 2)
            self.add_brick(x + 37.5, 90, 2)

        self.hud = None
        self.setup_game()
        self.canvas.focus_set()
        self.canvas.bind('<Left>', lambda _: self.paddle.start_moving(-10))
        self.canvas.bind('<Right>', lambda _: self.paddle.start_moving(10))

        # Particles
        self.particles = []

    def draw_gradient_background(self):
        for i in range(self.height):
            color = f"#{int(200 - (i / self.height) * 100):02x}aa{255 - int((i / self.height) * 100):02x}"
            self.canvas.create_line(0, i, self.width, i, fill=color)

    def setup_game(self):
        self.add_ball()
        self.update_lives_text()
        self.text = self.draw_text(self.width // 2, self.height // 2, 'Press Space to Start')
        self.canvas.bind('<space>', lambda _: self.start_game())

    def add_ball(self):
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) / 2
        self.ball = Ball(self.canvas, x, paddle_coords[1] - 10)
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def draw_text(self, x, y, text, size=40):
        font = ('Helvetica', size)
        return self.canvas.create_text(x, y, text=text, font=font, fill="white")

    def update_lives_text(self):
        text = f'Lives: {self.lives}'
        if self.hud is None:
            self.hud = self.draw_text(50, 20, text, 15)
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def start_game(self):
        self.canvas.unbind('<space>')
        self.canvas.delete(self.text)
        self.paddle.ball = None
        self.game_loop()

    def game_loop(self):
        self.check_collisions()
        num_bricks = len(self.canvas.find_withtag('brick'))
        if num_bricks == 0:
            self.ball.speed = None
            self.draw_text(self.width // 2, self.height // 2, 'You win!')
        elif self.ball.get_position()[3] >= self.height:
            self.ball.speed = None
            self.lives -= 1
            if self.lives < 0:
                self.draw_text(self.width // 2, self.height // 2, 'Game Over')
            else:
                self.after(1000, self.setup_game)
        else:
            self.ball.update()
            self.paddle.update()
            self.update_particles()
            self.after(16, self.game_loop)

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        overlapping_items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items.get(item) for item in overlapping_items if item in self.items]
        if objects:
            collision_sound.play()  # Play collision sound
        self.ball.collide(objects)

    def update_particles(self):
        for particle in self.particles:
            particle.update()
        self.particles = [p for p in self.particles if not p.is_dead()]

    def spawn_particles(self, x, y):
        for _ in range(10):  # Spawn 10 particles per collision
            self.particles.append(Particle(self.canvas, x, y))


class Particle:
    def __init__(self, canvas, x, y):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.size = random.randint(2, 6)
        self.color = f"#{random.randint(100, 255):02x}{random.randint(100, 255):02x}{random.randint(100, 255):02x}"
        self.lifetime = random.randint(20, 40)
        self.dx = random.uniform(-2, 2)
        self.dy = random.uniform(-2, 2)
        self.item = self.canvas.create_oval(x - self.size, y - self.size, x + self.size, y + self.size, fill=self.color)

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.lifetime -= 1
        self.canvas.move(self.item, self.dx, self.dy)
        if self.lifetime <= 0:
            self.canvas.delete(self.item)

    def is_dead(self):
        return self.lifetime <= 0


class GameObject:
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)


class Ball(GameObject):
    def __init__(self, canvas, x, y):
        self.radius = 10
        self.direction = [random.choice([-1, 1]), -1]
        self.speed = 5
        item = canvas.create_oval(x - self.radius, y - self.radius, x + self.radius, y + self.radius, fill="white")
        super().__init__(canvas, item)

    def update(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1
        if coords[1] <= 0:
            self.direction[1] *= -1
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def collide(self, game_objects):
        coords = self.get_position()
        ball_center = (coords[0] + coords[2]) / 2
        for game_object in game_objects:
            if isinstance(game_object, Brick):
                game_object.hit()
                game.spawn_particles(coords[0], coords[1])  # Add particle effect
                self.direction[1] *= -1
            elif isinstance(game_object, Paddle):
                paddle_coords = game_object.get_position()
                if ball_center < paddle_coords[0]:
                    self.direction[0] = -1
                elif ball_center > paddle_coords[2]:
                    self.direction[0] = 1
                self.direction[1] *= -1


class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 80
        self.height = 10
        self.ball = None
        item = canvas.create_rectangle(x - self.width // 2, y - self.height // 2, x + self.width // 2,
                                       y + self.height // 2, fill="blue", outline="white")
        super().__init__(canvas, item)
        self.moving = 0

    def set_ball(self, ball):
        self.ball = ball

    def start_moving(self, offset):
            self.moving = offset

    def update(self):
        if self.moving != 0:
            coords = self.get_position()
            width = self.canvas.winfo_width()
            
            # Ensure the paddle does not move out of bounds
            if (self.moving < 0 and coords[0] > 0) or (self.moving > 0 and coords[2] < width):
                self.move(self.moving, 0)
                if self.ball:
                    self.ball.move(self.moving, 0)

class Brick(GameObject):
    COLORS = {1: "#ff5555", 2: "#ffaa00", 3: "#55aa55"}

    def __init__(self, canvas, x, y, hits):
        self.width = 35
        self.height = 10
        self.hits = hits
        color = Brick.COLORS[hits]
        item = canvas.create_rectangle(x - self.width, y - self.height, x + self.width, y + self.height,
                                       fill=color, outline="white", tag="brick")
        super().__init__(canvas, item)

    def hit(self):
        self.hits -= 1
        brick_hit_sound.play()  # Play brick hit sound
        if self.hits == 0:
            self.delete()
        else:
            self.canvas.itemconfig(self.item, fill=Brick.COLORS[self.hits])


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Enhanced Pong Game")
    game = Game(root)
    game.mainloop()
