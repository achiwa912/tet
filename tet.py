# Zen Tetris - Tetris clone with two-player battle mode
# Uses Python arcade library: https://arcade.academy/index.html
# Background images are from https://pixabay.com/
# Sound data are from 魔王魂 at https://maoudamashii.jokersounds.com/

import arcade
from arcade import Matrix3x3
import random
import os
import timeit

WIDTH = 800  # window width in pixel
HEIGHT = 600  # window height in pixel
ASPECT = 1  # background image aspect ratio
SPRITE_SCALING = 0.7

PLWIDTH = 10  # game area width in number of blocks
PLHEIGHT = 20  # game area height in number of blocks

PLLEFT = 320  # game area left edge location within window in pixel
PLBOTTOM = 80  # game area top edge location within window in pixel
PLLEFT1 = 120  # PLLEFT for player 1 in two-player game mode
PLLEFT2 = 480  # PLLEFT for player 2 in two-player game mode

# Tetris shape colors
BLUE = 1
RED = 2
PURPLE = 3
GREEN = 4
AQUA = 5
YELLOW = 6
ORANGE = 7
GRAY = 8  # for wall/frame


class TitleView(arcade.View):
    # Show game title
    def __init__(self):
        super().__init__()
        self.camera_x = 0

    def on_show(self):
        arcade.set_background_color(arcade.color.AMAZON)
        self.background = arcade.load_texture("images/buddha-4263091_1280.jpg")

    def on_update(self, delta_time: float):
        self.camera_x += 2

    def on_draw(self):
        arcade.start_render()

        for z in [300, 200]:
            opacity = 100
            scale = 150 / z
            translate = scale / 500
            self.background.draw_transformed(
                0, 0, WIDTH, HEIGHT, 0, opacity,
                Matrix3x3().scale(scale, scale).translate(-self.camera_x
                                                          * translate, 0))

        if self.window.game_over:
            arcade.draw_text("Game Over", WIDTH/2, HEIGHT/2,
                             arcade.color.WHITE, font_size=50,
                             anchor_x="center")
            arcade.draw_text(f"High Score: {self.window.high_score}",
                             WIDTH/2-40, HEIGHT-30, arcade.color.WHITE, 14)
        else:
            arcade.draw_text("Zen Tetris", WIDTH/2, HEIGHT/2,
                             arcade.color.WHITE, font_size=50,
                             anchor_x="center")

        arcade.draw_text("Push O (One player) or T (Two players) to play",
                         WIDTH/2, HEIGHT/2 - 72,
                         arcade.color.WHITE, font_size=16, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.O:
            self.window.game_over = False
            self.window.game_mode = 0  # one-player game
            game_view = GameView()
            game_view.window = self.window
            game_view.setup()
            self.window.show_view(game_view)
        if key == arcade.key.T:
            self.window.game_over = False
            self.window.game_mode = 1  # two-player game
            game_view = GameView()
            game_view.window = self.window
            game_view.setup()
            self.window.show_view(game_view)


class PauseView(arcade.View):
    """Switch from/to GameView temporalily"""
    def __init__(self, game_view):
        super().__init__()
        self.game_view = game_view

    def on_show(self):
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        arcade.start_render()
        arcade.draw_text("Press Space to return", WIDTH/2, HEIGHT/2,
                         arcade.color.WHITE, font_size=20, anchor_x="center")

    def on_key_press(self, key, _modifiers):
        if key == arcade.key.SPACE:
            self.window.show_view(self.game_view)


class GameView(arcade.View):
    """Tetris game main"""
    def __init__(self):
        super().__init__()

        # Tetris shapes
        # A shape consists of four blocks, each is assigned a location
        # number in 4x4 matrix.  The first line are 0-3, the 2nd: 4-7, etc.
        self.tetris_shapes = [
            [RED, [[2, 6, 10, 14], [4, 5, 6, 7]]],
            [YELLOW, [[1, 2, 5, 6]]],
            [AQUA, [[1, 4, 5, 6], [1, 4, 5, 9], [4, 5, 6, 9],
                    [1, 5, 6, 9]]],
            [BLUE, [[1, 2, 5, 9], [0, 4, 5, 6], [1, 5, 8, 9],
                    [4, 5, 6, 10]]],
            [ORANGE, [[0, 1, 5, 9], [4, 5, 6, 8], [1, 5, 9, 10],
                      [2, 4, 5, 6]]],
            [GREEN, [[1, 5, 6, 10], [1, 2, 4, 5]]],
            [PURPLE, [[1, 4, 5, 8], [0, 1, 5, 6]]],
            ]

        self.block_images = {
            BLUE: "images/blue32.png",
            RED: "images/red32.png",
            PURPLE: "images/purple32.png",
            GREEN: "images/green32.png",
            AQUA: "images/aqua32.png",
            YELLOW: "images/yellow32.png",
            ORANGE: "images/orange32.png",
            GRAY: "images/gray32.png",
            }

        # Load sounds
        self.bottom_sound = arcade.load_sound(
            "sounds/se_maoudamashii_se_sound16.wav")
        self.delete_sound = arcade.load_sound(
            "sounds/se_maoudamashii_battle07.wav")
        self.attacked_sound = arcade.load_sound(
            "sounds/se_maoudamashii_system26.wav")
        self.levelup_sound = arcade.load_sound(
            "sounds/se_maoudamashii_system29.wav")
        self.gameover_sound = arcade.load_sound(
            "sounds/se_maoudamashii_retro30.wav")

        # Fall speed by level (in sec)
        self.fall_counter_init = [60/60, 50/60, 40/60, 30/60,
                                  25/60, 20/60, 15/60, 10/60,
                                  7/60, 5/60, 3/60]

    def setup(self):
        # Setup player objects
        self.players = []
        if self.window.game_mode == 0:
            # 1-player mode
            player = Player()
            player.game_view = self
            player.left_edge = PLLEFT
            player.bottom_edge = PLBOTTOM
            player.setup()
            player.player_num = 0  # only player
            self.players.append(player)
        else:
            # 2-player mode
            player = Player()
            player.game_view = self
            player.left_edge = PLLEFT1
            player.bottom_edge = PLBOTTOM
            player.setup()
            player.player_num = 1  # player one
            self.players.append(player)

            player = Player()
            player.game_view = self
            player.left_edge = PLLEFT2
            player.bottom_edge = PLBOTTOM
            player.setup()
            player.player_num = 2  # player two
            self.players.append(player)

        # Setup background rotation
        self.time_passed = 0
        self.window.game_over = False
        self.loop_time = timeit.default_timer()
        self.tmp_block = arcade.Sprite(
            self.block_images[1], SPRITE_SCALING,
            0, 0, 32, 32)
        self.update_time = timeit.default_timer()
        self.background = None
        self.angle = 0
        self.update_counter = 0

    def on_show(self):
        arcade.set_background_color(arcade.color.BLACK)
        self.window.set_mouse_visible(False)
        if self.window.game_mode == 0:
            # image for 1-player mode
            self.background = arcade.load_texture(
                "images/mandala-1094811_1280.jpg")
        else:
            # image for 2-player mode
            self.background = arcade.load_texture(
                "images/fractal-1832617_1280.jpg")

    def on_draw(self):
        draw_time = timeit.default_timer()
        arcade.start_render()

        # Draw background texture
        self.update_counter += 1
        if self.window.game_mode == 0:
            ratio = 60  # rotation speed slow
        else:
            ratio = 5  # rotation speed a little faster
        if self.update_counter % 10 == 0:
            self.angle += 0.1
        self.background.draw_transformed(
            0, 0, WIDTH, HEIGHT, 0, 255, Matrix3x3().rotate(self.angle))

        # Display sprites
        for player in self.players:
            player.player_list.draw()
            player.wall_list.draw()
            player.block_list.draw()

        # Display scores
        arcade.draw_text(f"High Score: {self.window.high_score}", WIDTH/2-60,
                         HEIGHT-30, arcade.color.WHITE, 14)
        if self.window.game_mode == 0:
            for player in self.players:
                arcade.draw_text(f"Score: {player.score}", 10, HEIGHT-30,
                                 arcade.color.WHITE, 14)
                arcade.draw_text(f"Level: {player.level}", WIDTH-70,
                                 HEIGHT-30, arcade.color.WHITE, 14)
        else:
            for player in self.players:
                arcade.draw_text(f"Level: {player.level}", player.left_edge+50,
                                 HEIGHT-30, arcade.color.WHITE, 14)
                arcade.draw_text(f"Score: {player.score}", player.left_edge+50,
                                 HEIGHT-50, arcade.color.WHITE, 14)

        # Display game over
        for player in self.players:
            if player.game_over:
                arcade.draw_text(f"Game Over",
                                 player.left_edge+25,
                                 HEIGHT/2+20, arcade.color.WHITE, 24)
                arcade.draw_text(f"ESC to quit",
                                 player.left_edge+50,
                                 HEIGHT/2-20, arcade.color.WHITE, 16)
        # Display performance info (debug mode)
        if self.window.debug is True:
            now_time = timeit.default_timer()
            loop_time = now_time - self.loop_time
            self.loop_time = now_time
            draw_time = now_time - draw_time
            arcade.draw_text(
                f"Loop time: {loop_time * 1000:.3f} " +
                f"(Update time: {self.update_time * 1000:.3f}, " +
                f"Draw time: {draw_time * 1000:.3f})",
                60, 0, arcade.color.WHITE, 14)

    def on_update(self, delta_time):
        # If ESC key is pressed (eg, gameover), switch to TitleView
        if self.window.game_over:
            title_view = TitleView()
            self.window.show_view(title_view)

        update_time = timeit.default_timer()
        self.time_passed += delta_time

        for player in self.players:
            player.fall_counter -= delta_time

            if player.game_over is True:
                # Gameover effect (turn blocks to GRAY)
                player.player_game_over()
            elif player.delete_animation is True:
                # Delete animation
                player.delete_animation_counter -= delta_time
                player.animation()
            else:
                # Player key move and fall
                player.player_attacked()
                player.shape_move()
                player.shape_fall()

                if player.score > self.window.high_score:
                    self.window.high_score = player.score

            # Update player_list
            # Only when player tetris moves, rotates or is generated
            if player.player_moved:
                player.player_moved = False
                for i in range(len(player.player_list)):
                    player.player_list.pop()
                color = self.tetris_shapes[player.shape][0]
                for pos in (self.tetris_shapes[player.shape][1]
                            [player.shape_cnt]):
                    x = player.x + pos % 4
                    y = player.y - pos // 4
                    block = player.display_block(color, x, y)
                    player.player_list.append(block)

            # Update block_list
            # Only when in animation, added or deleted
            if player.block_changed:
                for i in range(len(player.block_list)):
                    player.block_list.pop()
                for y in range(0, PLHEIGHT):
                    for x in range(0, PLWIDTH):
                        if player.game_area[y][x] != 0:
                            block = player.display_block(
                                player.game_area[y][x], x, y)
                            player.block_list.append(block)

        self.update_time = timeit.default_timer() - update_time

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            # Switch to TitleView
            self.window.game_over = True
        if key == arcade.key.SPACE:
            # Temporalily switch to PauseView
            pause = PauseView(self)
            self.window.show_view(pause)

        if key == arcade.key.UP or key == arcade.key.W:
            for player in self.players:
                if player.player_num != 2 and \
                   player.delete_animation is False:
                    player.up_pressed = True
        if key == arcade.key.LEFT or key == arcade.key.A:
            for player in self.players:
                if player.player_num != 2 and \
                   player.delete_animation is False:
                    player.left_pressed = True
        if key == arcade.key.RIGHT or key == arcade.key.D:
            for player in self.players:
                if player.player_num != 2 and player.delete_animation is False:
                    player.right_pressed = True
        if key == arcade.key.DOWN or key == arcade.key.S:
            for player in self.players:
                if player.player_num != 2 and player.delete_animation is False:
                    player.down_pressed = True

        if key == arcade.key.I:
            for player in self.players:
                if player.player_num == 2 and player.delete_animation is False:
                    player.up_pressed = True
        if key == arcade.key.J:
            for player in self.players:
                if player.player_num == 2 and player.delete_animation is False:
                    player.left_pressed = True
        if key == arcade.key.L:
            for player in self.players:
                if player.player_num == 2 and player.delete_animation is False:
                    player.right_pressed = True
        if key == arcade.key.K:
            for player in self.players:
                if player.player_num == 2 and player.delete_animation is False:
                    player.down_pressed = True


class Player():
    """Represents a player to achieve two-player game battle"""
    def __init__(self):
        # Initialized in GameView
        # player_num - 0: only player, 1: right player, 2: left player
        self.player_num = 0
        self.left_edge = 0
        self.bottom_edge = 0
        self.game_view = None
        self.game_over = False

    def setup(self):
        # Sprite lists
        self.wall_list = arcade.SpriteList(is_static=True)
        self.player_list = arcade.SpriteList(is_static=True)
        self.block_list = arcade.SpriteList(is_static=True)

        self.score = 0
        self.fall_counter = 0
        self.level = 0
        self.delete_counter = 0
        self.x = 4
        self.y = PLHEIGHT-1
        self.shape = random.randint(0, 6)
        self.shape_cnt = 0
        self.fall_flag = False
        self.generate_tetris = True
        self.delete_animation = False
        self.delete_animation_counter = 0
        self.delete_animation_index = 0
        self.delete_animation_lines = []
        self.player_moved = True  # player_list is updated only when it's True
        self.block_changed = True  # block_list is updated only when it's True
        self.up_pressed = False
        self.down_pressed = False
        self.right_pressed = False
        self.left_pressed = False
        self.damage_lines = 0  # Num of lines to be added by the other player

        # Wall/frame surrounding the game area
        for x in range(-1, PLWIDTH+1):
            wall = self.display_block(GRAY, x, -1)
            self.wall_list.append(wall)
            wall = self.display_block(GRAY, x, PLHEIGHT)
            self.wall_list.append(wall)
        for y in range(0, PLHEIGHT):
            wall = self.display_block(GRAY, -1, y)
            self.wall_list.append(wall)
            wall = self.display_block(GRAY, PLWIDTH, y)
            self.wall_list.append(wall)

        # Initialize game area
        # 0: no block, color: block of color is there
        self.game_area = []
        for y in range(0, PLHEIGHT):
            area_line = []
            for x in range(0, PLWIDTH):
                area_line.append(0)
            self.game_area.append(area_line)

    def display_block(self, color, x, y):
        # Create a block sprite with the specified color and
        # position (in num of blocks) within game area window,
        # and return the sprite
        if self.delete_animation is True and y in self.delete_animation_lines:
            block = arcade.Sprite(self.game_view.block_images[color],
                                  SPRITE_SCALING,
                                  32*self.delete_animation_index, 0, 32, 32)
        else:
            block = arcade.Sprite(self.game_view.block_images[color],
                                  SPRITE_SCALING, 0, 0, 32, 32)
            block.alpha = 255
        block.center_x = int(self.left_edge + 32*SPRITE_SCALING*x)
        block.center_y = int(self.bottom_edge + 32*SPRITE_SCALING*y)
        return block

    def can_move(self):
        """Check if shape can be located in current x, y, rotation count"""
        for pos in self.game_view.tetris_shapes[self.shape][1][self.shape_cnt]:
            x = int(self.x + pos % 4)
            y = int(self.y - pos // 4)
            if x < 0 or x >= PLWIDTH:
                return False
            if y < 0:
                return False
            if self.game_area[y][x] != 0:
                return False
        return True

    def animation(self):
        """Delete animation"""
        # Animate to-be-deleted lines before actually delete them
        if self.delete_animation_counter <= 0:
            self.block_changed = True
            self.delete_animation_counter = 0.1  # 0.1 sec/frame
            self.delete_animation_index += 1
            if self.delete_animation_index > 7:
                # Animation done
                self.delete_animation = False
                self.generate_tetris = True
                self.delete_animation_index = 0
                self.delete_counter += len(self.delete_animation_lines)
                # delete 4 lines -> level up
                if self.delete_counter >= 4:
                    self.delete_counter = 0
                    if self.level < len(self.game_view.fall_counter_init):
                        self.level += 1
                        arcade.play_sound(self.game_view.levelup_sound)
                self.score += 10 * (2**(len(self.delete_animation_lines)-1))
                # Attack the other player
                if self.game_view.window.game_mode == 1:
                    for player in self.game_view.players:
                        if self != player:
                            player.damage_lines = \
                                len(self.delete_animation_lines) - 1

                # Delete lines and append new lines
                for y in self.delete_animation_lines:
                    del self.game_area[y]
                    area_line = []
                    for x in range(0, PLWIDTH):
                        area_line.append(0)
                    self.game_area.append(area_line)
                self.delete_animation_lines = []
                arcade.play_sound(self.game_view.delete_sound)

    def shape_move(self):
        """Move player shape based on key input"""
        if self.up_pressed:
            self.player_moved = True
            prev_cnt = self.shape_cnt
            self.shape_cnt += 1
            if self.shape_cnt >= \
               len(self.game_view.tetris_shapes[self.shape][1]):
                self.shape_cnt = 0
            if not self.can_move():
                self.shape_cnt = prev_cnt
            self.up_pressed = False
        if self.left_pressed:
            self.player_moved = True
            prev_x = self.x
            self.x -= 1
            if not self.can_move():
                self.x = prev_x
            self.left_pressed = False
        if self.right_pressed:
            self.player_moved = True
            prev_x = self.x
            self.x += 1
            if not self.can_move():
                self.x = prev_x
            self.right_pressed = False
        if self.down_pressed:
            self.player_moved = True
            self.fall_flag = True
            self.down_pressed = False

    def shape_fall(self):
        """Drop player shape one line or reach the bottom"""
        if self.fall_counter <= 0 or self.fall_flag is True:
            self.fall_counter = self.game_view.fall_counter_init[self.level]
            self.player_moved = True
            if self.generate_tetris is True:
                # Generate new shape at top of game area
                self.shape = random.randint(0, 6)
                self.shape_cnt = 0
                self.x = PLWIDTH/2 - 2
                self.y = PLHEIGHT - 1
                self.fall_flag = False
                self.generate_tetris = False
                # Gameover check
                if not self.can_move():
                    self.game_over = True
                    self.gameover_counter = 0
                    self.player_moved = True
                    arcade.play_sound(self.game_view.gameover_sound)
            else:
                # Fall one line
                prev_y = self.y
                self.y -= 1
                self.score += 2
                if not self.can_move():
                    # Stuck at bottom and can't move anymore
                    arcade.play_sound(self.game_view.bottom_sound)
                    self.y = prev_y
                    color = self.game_view.tetris_shapes[self.shape][0]
                    for pos in (self.game_view.tetris_shapes
                                [self.shape][1][self.shape_cnt]):
                        x = int(self.x + pos % 4)
                        y = int(self.y - pos // 4)
                        self.game_area[y][x] = color

                    # Delete line check (and delete)
                    for y in range(0, PLHEIGHT):
                        if 0 not in self.game_area[PLHEIGHT-y-1]:
                            # Start delete animation
                            self.delete_animation = True
                            self.delete_animation_counter = 0.1  # 0.1 sec
                            self.delete_animation_index = 1
                            self.delete_animation_lines.append(PLHEIGHT-y-1)
                    if self.delete_animation is False:
                        # No delete line
                        self.generate_tetris = True

    def player_attacked(self):
        """The other player deleted two or more lines and incurred
        additional lines to me"""
        for i in range(self.damage_lines):
            del self.game_area[PLHEIGHT-1]
            area_line = []
            for x in range(PLWIDTH):
                if random.randint(0, 99) < 50:  # 50%
                    area_line.append(0)
                else:
                    area_line.append(GRAY)
            self.game_area.insert(0, area_line)
        if self.damage_lines != 0:
            arcade.play_sound(self.game_view.attacked_sound)
            self.damage_lines = 0

    def player_game_over(self):
        """Change block color to GRAY from bottom to top"""
        if self.gameover_counter == 0:
            # Move player sprites to block_list
            # Without this, player sprites doesn't turn to GRAY
            for sprite in self.player_list:
                self.block_list.append(sprite)
            self.player_list = arcade.SpriteList()
        elif self.gameover_counter >= PLHEIGHT:
            return

        for x in range(PLWIDTH):
            if self.game_area[self.gameover_counter][x] != 0:
                self.game_area[self.gameover_counter][x] = GRAY
        self.gameover_counter += 1
        self.block_changed = True


def main():
    window = arcade.Window(WIDTH, HEIGHT, "Tetris")
    window.high_score = 0
    window.game_over = False
    window.game_mode = 0  # game mode dummy number
    window.debug = False  # Show performamce info
    width, height = window.get_size()
    window.set_viewport(0, width, 0, height)
    title_view = TitleView()
    title_view.window = window
    window.show_view(title_view)
    arcade.run()


file_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(file_path)

if __name__ == "__main__":
    main()
