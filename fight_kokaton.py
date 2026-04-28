import os
import random
import sys
import time
import math
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ

NUM_OF_BOMBS = 5

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:

    delta = {  # ここは def の外側！
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    
    # 画像の読み込み処理も def の外側！
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)
    imgs = { 
        (+5, 0): img,
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),# 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),   # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9), # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9), # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9), # 右下
    } 

    def __init__(self, xy: tuple[int, int]):
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5, 0)  # インスタンス変数として向きを保持

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)


    def update(self, key_lst: list[bool], screen: pg.Surface):
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.img = __class__.imgs[tuple(sum_mv)]
            self.dire = tuple(sum_mv)  # 向きを更新
        screen.blit(self.img, self.rct)


class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird: "Bird"):
        """
        こうかとんの向きに応じてビームを生成する
        """
        self.vx, self.vy = bird.dire  # birdインスタンスのdireを参照
        
        # 角度計算：atan2(y, x) だが画面座標系(y下向き)なので-vyとする
        theta = math.atan2(-self.vy, self.vx)
        angle = math.degrees(theta)
        
        # 画像の回転と読み込み
        self.img = pg.transform.rotozoom(pg.image.load("fig/beam.png"), angle, 1.0)
        self.rct = self.img.get_rect()
        
        # 初期配置：こうかとんの中心 + (サイズ * 向き/5)
        self.rct.centerx = bird.rct.centerx + bird.rct.width * self.vx / 5
        self.rct.centery = bird.rct.centery + bird.rct.height * self.vy / 5

    def update(self, screen: pg.Surface):
        # 画面外に出るまで移動
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)

class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        """
        引数に基づき爆弾円Surfaceを生成する
        引数1 color：爆弾円の色タプル
        引数2 rad：爆弾円の半径
        """
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    # bomb = Bomb((255, 0, 0), 10)

    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]
    # for i in range(NUM_OF_BOMBS):
    #     bomb = Bomb((255, 0, 0), 10)
    #     bombs.append(bomb)


    beam = None  # ゲーム初期化時にはビームは存在しない
    clock = pg.time.Clock()
    tmr = 0
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # スペースキー押下でBeamクラスのインスタンス生成
                beam = Beam(bird)          
        screen.blit(bg_img, [0, 0])

        
        for bomb in bombs:
            if bird.rct.colliderect(bomb.rct):
            # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                fonto = pg.font.Font(None, 80)
                txt = fonto.render("Game Over", True, (255, 0, 0))
                screen.blit(txt, [WIDTH//2-150, WIDTH//2-250])
                bird.change_img(8, screen)
                pg.display.update()
                time.sleep(1)
                return        


        for i, bomb in enumerate(bombs):
            if bomb is not None:
                if beam is not None:
                    if beam.rct.colliderect(bomb.rct): #練習2：爆弾とビームの衝突判定
                        beam = None
                        bombs[i] = None
                        bird.change_img(6, screen)# こうかとん喜びエフェクト
                        pg.display.update()
                        time.sleep(1)
                
        bombs = [bomb for bomb in bombs if bomb is not None]


        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        if beam is not None:
            beam.update(screen)   
        for bomb in bombs:
            bomb.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
