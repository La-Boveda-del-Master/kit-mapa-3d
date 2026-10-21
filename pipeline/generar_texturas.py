"""Genera las texturas repetibles (tileables) del mapa: pisos, cubiertas, fachadas, madera, agua, follaje, pantallas LED.

Uso: python pipeline/generar_texturas.py [carpeta_salida]      Salida por defecto: texturas/*.jpg  (+ *_n.jpg normales)
Todo es procedural (numpy), sin descargas ni derechos de terceros. El tamano real de cada baldosa (en metros)
esta en MATERIALES dentro de construir_modelo.py.
"""
import pathlib, sys
import numpy as np
from PIL import Image

OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent.parent / 'texturas'
OUT.mkdir(exist_ok=True)
N = 512
rng = np.random.default_rng(2026)


def fnoise(n=N, beta=1.6, seed=0):
    """Ruido fractal periodico (filtrado en frecuencia) en 0..1."""
    r = np.random.default_rng(seed)
    f = np.fft.fft2(r.standard_normal((n, n)))
    fx = np.fft.fftfreq(n)[:, None]; fy = np.fft.fftfreq(n)[None, :]
    k = np.sqrt(fx * fx + fy * fy); k[0, 0] = 1
    a = np.real(np.fft.ifft2(f / k ** beta))
    a -= a.min(); a /= a.max()
    return a


def save(name, rgb):
    Image.fromarray(np.clip(rgb * 255, 0, 255).astype(np.uint8)).save(OUT / f'{name}.jpg', quality=88)


def normal_from_height(h, strength=2.0):
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * strength
    dy = (np.roll(h, 1, 0) - np.roll(h, -1, 0)) * strength      # filas hacia abajo -> v hacia arriba
    nz = np.ones_like(h); l = np.sqrt(dx * dx + dy * dy + 1)
    return np.dstack(((-dx / l) * .5 + .5, (-dy / l) * .5 + .5, (nz / l) * .5 + .5))


def col(c):
    return np.array(c, float)[None, None, :]


def bricks(cols, rows, base, var=.06, joint=2, joint_col=(.45, .42, .38), stagger=True, seed=1, grain=.05, hue=.10):
    """Aparejo trabado: devuelve (albedo, altura)."""
    r = np.random.default_rng(seed)
    img = np.zeros((N, N, 3)); h = np.ones((N, N))
    bw, bh = N / cols, N / rows
    for j in range(rows):
        off = (bw / 2 if (stagger and j % 2) else 0)
        for i in range(cols + 1):
            c = np.array(base) * (1 + r.uniform(-var, var)) + np.array((1, .55, -.9)) * r.uniform(-var, var) * hue * 4
            x0 = int(round(i * bw - off)); x1 = int(round((i + 1) * bw - off)); y0 = int(round(j * bh)); y1 = int(round((j + 1) * bh))
            xs = np.arange(x0, x1) % N
            img[y0:y1][:, xs] = c
            h[y0:y0 + joint][:, xs] = 0; h[y0:y1][:, xs[:joint]] = 0
    m = h < .5
    img[m] = np.array(joint_col)
    g = fnoise(seed=seed + 50, beta=1.0)[..., None]
    return img * (1 - grain + 2 * grain * g), h


# ---------------------------------------------------------------- pisos
a, h = bricks(4, 8, (.70, .68, .63), .06, joint_col=(.52, .50, .46), seed=1, hue=.07); save('pav_arenisca', a); save('pav_arenisca_n', normal_from_height(h, 1.2))
a, h = bricks(4, 8, (.74, .71, .64), .055, joint_col=(.56, .53, .48), seed=2, hue=.09); save('pav_plaza', a); save('pav_plaza_n', normal_from_height(h, 1.2))
a, h = bricks(16, 32, (.40, .35, .30), .10, joint_col=(.26, .24, .22), seed=3); save('pav_oscuro', a)
n1, n2 = fnoise(seed=4, beta=.6), fnoise(seed=5, beta=1.8)
asf = .19 + .10 * n1 + .05 * n2
save('asfalto', np.dstack((asf, asf * 1.01, asf * 1.04))); save('asfalto_n', normal_from_height(n1, 3.0))
asb = .40 + .10 * n1 + .05 * n2
save('asfalto_brt', np.dstack((asb * 1.05, asb, asb * .93)))
g1, g2, g3 = fnoise(seed=6, beta=1.2), fnoise(seed=7, beta=2.2), fnoise(seed=8, beta=.5)
gr = col((.30, .50, .15)) * (.8 + .4 * g1[..., None]) + col((.10, .14, .02)) * g2[..., None] + (g3[..., None] - .5) * .10
save('cesped', gr)
c1, c2 = fnoise(seed=9, beta=1.4), fnoise(seed=10, beta=.4)
cc = .70 + .08 * c1 + .03 * c2
conc = np.dstack((cc, cc * .99, cc * .96)); conc[::N // 2, :, :] *= .82; conc[:, ::N // 2, :] *= .82
save('concreto', conc)
a, h = bricks(4, 12, (.76, .67, .52), .08, joint=2, seed=11); save('arenisca_muro', a); save('arenisca_muro_n', normal_from_height(h, 1.0))
a, h = bricks(8, 28, (.60, .28, .17), .12, joint=2, joint_col=(.62, .58, .52), seed=12); save('ladrillo', a); save('ladrillo_n', normal_from_height(h, 1.5))

# ---------------------------------------------------------------- cubiertas y paneles metalicos (tintados por pabellon)
x = np.arange(N)
seam = np.ones(N); hs = np.zeros(N)
for k in range(8):                                   # 8 juntas alzadas por baldosa
    c = int(k * N / 8)
    for d in range(-3, 4):
        seam[(c + d) % N] = .72 + .06 * abs(d); hs[(c + d) % N] = 1 - abs(d) / 3
streak = fnoise(seed=13, beta=2.0); streak = np.repeat(streak[:, :8].mean(1, keepdims=True), N, 1)   # vetas a lo largo
roof_g = seam[None, :] * (.93 + .09 * streak + .03 * fnoise(seed=14, beta=.5))
save('techo_n', normal_from_height(np.repeat(hs[None, :], N, 0), 3.0))
rib = .86 + .14 * (np.sin(x * 2 * np.pi * 16 / N) > .2)          # panel nervado vertical
panel_g = rib[None, :] * (.94 + .08 * fnoise(seed=15, beta=1.6))
save('panel_n', normal_from_height(np.repeat((np.sin(x * 2 * np.pi * 16 / N))[None, :], N, 0), 1.5))
TINTES = {'amarillo': (.96, .72, .08), 'blanco': (.90, .91, .92), 'azul': (.10, .40, .82), 'verde': (.42, .68, .18),
          'rojo': (.78, .12, .10), 'hall': (.72, .70, .70), 'gs': (.62, .56, .48), 'gris': (.60, .62, .64),
          'verde_osc': (.30, .52, .12), 'multi': (.70, .56, .25)}
for k, c in TINTES.items():
    save('techo_' + k, roof_g[..., None] * col(c)); save('panel_' + k, panel_g[..., None] * col(c))

# ---------------------------------------------------------------- madera (celosia de la Caja)
w = fnoise(seed=16, beta=1.8); w = np.repeat(w[:1, :], N, 0) * .6 + np.repeat(fnoise(seed=17, beta=2.2)[:, :1], N, 1) * .25 + fnoise(seed=18, beta=.8) * .15
save('madera', col((.11, .075, .055)) + col((.15, .10, .07)) * w[..., None])

# ---------------------------------------------------------------- fachadas de ciudad (ventanas), 9 x 9 m
def fachada(wall, seed):
    r = np.random.default_rng(seed)
    img = np.ones((N, N, 3)) * col(wall) * (.92 + .12 * fnoise(seed=seed, beta=1.5)[..., None])
    fw, fh = N / 4, N / 3
    for j in range(3):
        for i in range(4):
            x0 = int(i * fw + fw * .18); x1 = int(i * fw + fw * .82); y0 = int(j * fh + fh * .22); y1 = int(j * fh + fh * .72)
            t = r.uniform(.75, 1.15)
            grad = np.linspace(1.15, .8, y1 - y0)[:, None, None]
            img[y0:y1, x0:x1] = col((.20, .27, .34)) * t * grad
            img[y0:y1, (x0 + x1) // 2 - 1:(x0 + x1) // 2 + 1] = col(wall) * .8
        img[int(j * fh):int(j * fh) + 3] *= .8
    return img


for k, c in {'1': (.84, .82, .78), '2': (.74, .70, .64), '3': (.68, .44, .32), '4': (.88, .88, .86)}.items():
    save('fachada_' + k, fachada(c, 20 + int(k)))

# ---------------------------------------------------------------- fachada real de pabellon (12 x 12 m): vidrio abajo, panel gris arriba
fp = np.ones((N, N, 3)) * col((.66, .67, .68)) * (.95 + .08 * fnoise(seed=40, beta=1.6)[..., None])
for k in range(1, 5):
    fp[int(N * (1 - .38 - k * .155)) - 1:int(N * (1 - .38 - k * .155)) + 1] *= .82          # juntas horizontales del panel
for i in range(8):
    fp[:int(N * .62), int(i * N / 8):int(i * N / 8) + 2] *= .86
g0 = int(N * .62)
grad = np.linspace(.85, 1.15, N - g0)[:, None, None]
fp[g0:] = col((.34, .50, .56)) * grad * (.9 + .2 * fnoise(seed=41, beta=2.2)[g0:, :, None])
for i in range(8):
    fp[g0:, int(i * N / 8):int(i * N / 8) + 3] = col((.80, .82, .84))
fp[g0:g0 + 4] = col((.80, .82, .84)); fp[int(N * .81):int(N * .81) + 3] = col((.80, .82, .84))
save('fachada_pab', fp)
sp = np.ones((N, N, 3)) * col((.07, .11, .22))                                             # paneles solares
for i in range(8):
    sp[:, int(i * N / 8):int(i * N / 8) + 3] = col((.55, .58, .62)); sp[int(i * N / 8):int(i * N / 8) + 3, :] = col((.55, .58, .62))
for i in range(32):
    sp[:, int(i * N / 32)] *= 1.5; sp[int(i * N / 32), :] *= 1.5
save('solar', sp)

# ---------------------------------------------------------------- interiores (recorrido 360)
cp1, cp2 = fnoise(seed=50, beta=1.3), fnoise(seed=51, beta=.5)
cpv = .58 + .12 * cp1 + .04 * cp2
conc_p = np.dstack((cpv, cpv, cpv * .98)); conc_p[::N // 2, :, :] *= .78; conc_p[:, ::N // 2, :] *= .78   # losas de 3 m con juntas
save('concreto_pulido', conc_p)
a, h = bricks(3, 6, (.56, .57, .50), .09, joint=1, joint_col=(.40, .40, .36), stagger=False, seed=52, hue=.12)
save('piedra_pulida', a * (.9 + .25 * fnoise(seed=53, beta=2.4)[..., None]))
ca = fnoise(seed=54, beta=.3)
save('alfombra', col((.40, .44, .50)) * (.85 + .3 * ca[..., None]))
wd = np.repeat(fnoise(seed=55, beta=1.8)[:1, :], N, 0) * .5 + fnoise(seed=56, beta=.9) * .2
mc = col((.62, .46, .28)) + col((.25, .18, .10)) * wd[..., None]
for i in range(6):
    mc[:, int(i * N / 6):int(i * N / 6) + 2] *= .7
save('madera_clara', mc)

# ---------------------------------------------------------------- pantallas LED (contenido generico: anillos violeta/magenta). Para el arte real del evento, reemplaza led_*.jpg
def led(name, W, H, rings=True):
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    cx, cy = W / 2, H * .55
    r = np.sqrt((xx - cx) ** 2 + ((yy - cy) * 1.15) ** 2) / (H * .62)
    base = np.dstack((.06 + .10 * (1 - r).clip(0), .02 + .03 * (1 - r).clip(0), .20 + .25 * (1 - r).clip(0)))
    if rings:
        ring = (np.sin(r * 22) ** 24) * (r < 1.25)
        glow = np.exp(-((r - .55) ** 2) / .02) * .9 + np.exp(-((r - .95) ** 2) / .006) * .6
        base += np.dstack((ring * .9 + glow * .55, ring * .25 + glow * .15, ring * 1.0 + glow * .95))
    rr = np.random.default_rng(3).random((H, W))
    stars = (rr > .9985)[..., None] * np.array([1.0, .9, 1.0])
    base += stars
    # figura central (astronauta estilizado: silueta clara)
    fig = (np.abs(xx - cx) < H * .05) & (yy > cy - H * .18) & (yy < cy + H * .22)
    head = ((xx - cx) ** 2 + (yy - (cy - H * .22)) ** 2) < (H * .07) ** 2
    base[fig | head] = np.array([.95, .93, 1.0]) * .85
    # halo del logo
    base += np.dstack([np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2)) / (H * .25) ** 2) * c for c in (.35, .10, .55)])
    base *= .9 + .2 * fnoise(H, seed=77, beta=1.2)[:, :W] if H == W else 1.0
    save(name, base.clip(0, 1))


led('led_main', 1024, 272)            # pantalla central 15 x 4 m (3.75:1)
led('led_wide', 1024, 410)            # pantalla 10 x 4 / portico 10 x 5
led('led_lateral', 512, 288)          # laterales 16:9
led('led_portal_pata', 256, 640)      # patas del portico 2 x 5

w1, w2 = fnoise(seed=30, beta=1.4), fnoise(seed=31, beta=2.4)
save('agua', col((.16, .30, .30)) * (.8 + .4 * w2[..., None]) + col((.06, .10, .08)) * w1[..., None])
save('agua_n', normal_from_height(fnoise(seed=32, beta=1.0), 2.5))
l1, l2 = fnoise(seed=33, beta=.9), fnoise(seed=34, beta=1.8)
save('follaje', col((.22, .46, .13)) * (.7 + .6 * l1[..., None]) + col((.12, .16, .03)) * l2[..., None])
print('texturas:', len(list(OUT.glob('*.jpg'))), 'archivos,', round(sum(f.stat().st_size for f in OUT.glob('*.jpg')) / 1e6, 2), 'MB')
