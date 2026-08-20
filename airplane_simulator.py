import math
import random
import statistics
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Patch

# salva os arquivos de saida na mesma pasta onde este script esta
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

rows = 30  # fileira
seats_per_row = 6  # assento por fileiras; J|0|1|2|C|3|4|5|J (J: Janela, C: Corredor)
min_stow_time = 5  # tempo para guardar bagagem de mao minimo
max_stow_time = 25  # tempo para guardar bagagem de mao maximo
Seat_deley = 10  # tempo para troca de assentos
TRIALS = 20  # numero de execucoes por metodo, para media/desvio padrao

random.seed(42)

# ---------------------------------------------------------------
# Passageiros base
# ---------------------------------------------------------------
base_passengers = []
pid = 0
for r in range(rows):
    for s in range(seats_per_row):
        base_passengers.append((pid, r, s))
        pid += 1

# MELHORIA 2 (parte a): tempo de guardar bagagem fixado POR PASSAGEIRO
# (gerado uma unica vez, antes de qualquer embaralhamento). Assim a
# "lentidao" de cada pessoa e sempre a mesma, nao importa em qual
# metodo/trial ela embarca -- isso isola o efeito da ORDEM de embarque,
# que e o que realmente queremos comparar entre os metodos.
passenger_stow_time = {p[0]: random.randint(min_stow_time, max_stow_time) for p in base_passengers}


def simulate(passengers, capture=False):
    """Simulacao original. 'passengers' e uma lista de tuplas (id, row, seat)."""
    aisle = [None] * rows
    seated = set()
    queue = list(passengers)
    ticks = 0
    frames = []  # cada frame: (aisle_status, seated_snapshot)

    while len(seated) < len(passengers):
        ticks += 1
        for r in range(rows - 1, -1, -1):
            p = aisle[r]
            if p is not None:
                if p['row'] == r:
                    if p['timer'] == 0:
                        delay = passenger_stow_time[p['id']]
                        seats_to_check = []
                        if p['seat'] == 0: seats_to_check = [1, 2]
                        elif p['seat'] == 1: seats_to_check = [2]
                        elif p['seat'] == 5: seats_to_check = [3, 4]
                        elif p['seat'] == 4: seats_to_check = [3]
                        for s in seats_to_check:
                            if (r, s) in seated:
                                delay += Seat_deley
                        p['timer'] = delay
                    else:
                        p['timer'] -= 1
                        if p['timer'] <= 0:
                            seated.add((p['row'], p['seat']))
                            aisle[r] = None
                else:
                    if r + 1 < rows and aisle[r + 1] is None:
                        aisle[r + 1] = p
                        aisle[r] = None
        if aisle[0] is None and queue:
            nxt = queue.pop(0)
            aisle[0] = {'id': nxt[0], 'row': nxt[1], 'seat': nxt[2], 'timer': 0}

        if capture:
            aisle_status = [None] * rows
            for r in range(rows):
                p = aisle[r]
                if p is not None:
                    aisle_status[r] = 'stow' if p['row'] == r else 'walk'
            frames.append((aisle_status, set(seated)))

    return ticks, frames


# ---------------------------------------------------------------
# Geradores de ordem de embarque -- uma funcao por metodo, para poder
# rechamar e reembaralhar em cada trial (necessario para a MELHORIA 2b)
# ---------------------------------------------------------------
def order_random():
    order = list(base_passengers)
    random.shuffle(order)
    return order


def order_back_to_front():
    # MELHORIA 1: antes era 'range(rows // 5 - 1, -1, -1)', que descartava
    # silenciosamente as ultimas fileiras quando 'rows' nao era multiplo de 5
    # (ex.: rows=32 perdia as fileiras 30 e 31). Agora usamos math.ceil e
    # limitamos cada bloco a 'rows', garantindo que todo passageiro
    # sempre entre em algum bloco.
    n_blocks = math.ceil(rows / 5)
    order = []
    for block in range(n_blocks - 1, -1, -1):
        start = block * 5
        end = min(start + 5, rows)
        block_pass = [p for p in base_passengers if start <= p[1] < end]
        random.shuffle(block_pass)
        order.extend(block_pass)
    assert len(order) == len(base_passengers), "algum passageiro ficou de fora do embarque!"
    return order


def order_wilma():
    windows = [p for p in base_passengers if p[2] in (0, 5)]
    middles = [p for p in base_passengers if p[2] in (1, 4)]
    aisles = [p for p in base_passengers if p[2] in (2, 3)]
    random.shuffle(windows); random.shuffle(middles); random.shuffle(aisles)
    return windows + middles + aisles


def order_steffen():
    order = []
    for seat_group in [(0, 5), (1, 4), (2, 3)]:
        for even_odd in [1, 0]:
            group = [p for p in base_passengers if p[2] in seat_group and p[1] % 2 == even_odd]
            group.sort(key=lambda x: x[1], reverse=True)
            order.extend(group)
    return order


methods = {
    "Random": order_random,
    "Back to front": order_back_to_front,
    "Wilma": order_wilma,
    "Steffen": order_steffen,
}

# ---------------------------------------------------------------
# MELHORIA 2 (parte b): roda TRIALS simulacoes por metodo (reembaralhando
# a ordem a cada vez) e reporta media + desvio padrao, em vez de um
# unico numero que pode ser so "sorte" de uma execucao.
# ---------------------------------------------------------------
print(f"Rodando {TRIALS} simulacoes por metodo "
      f"(mesma 'lentidao' de bagagem por passageiro em todos os metodos/trials)...\n")

stats = {}
for name, order_fn in methods.items():
    trial_ticks = [simulate(order_fn(), capture=False)[0] for _ in range(TRIALS)]
    mean = statistics.mean(trial_ticks)
    std = statistics.stdev(trial_ticks) if len(trial_ticks) > 1 else 0.0
    stats[name] = {"mean": mean, "std": std, "min": min(trial_ticks), "max": max(trial_ticks)}
    print(f"{name:15s} media={mean:7.1f}  desvio_padrao={std:6.1f}  "
          f"min={min(trial_ticks):5d}  max={max(trial_ticks):5d}  ({TRIALS} trials)")

# ---------------------------------------------------------------
# 1) Grafico de barras: media +/- desvio padrao de cada metodo
# ---------------------------------------------------------------
fig_bar, ax_bar = plt.subplots(figsize=(7, 4.5), facecolor="#0A0D12")
ax_bar.set_facecolor("#0A0D12")

names_sorted = sorted(stats.keys(), key=lambda n: stats[n]["mean"])
means_sorted = [stats[n]["mean"] for n in names_sorted]
stds_sorted = [stats[n]["std"] for n in names_sorted]
colors = ["#34D399" if i == 0 else "#FFB020" for i in range(len(names_sorted))]

bars = ax_bar.barh(names_sorted, means_sorted, xerr=stds_sorted, color=colors,
                    edgecolor="#2A3441", capsize=4,
                    error_kw=dict(ecolor="#E7EAEE", lw=1.2))
ax_bar.invert_yaxis()
ax_bar.set_xlabel(f"Ticks (media de {TRIALS} execucoes, +/- desvio padrao)", color="#E7EAEE")
ax_bar.set_title("Comparacao entre metodos de embarque", color="#E7EAEE", fontsize=13, fontweight="bold")
ax_bar.tick_params(colors="#E7EAEE")
for spine in ax_bar.spines.values():
    spine.set_color("#2A3441")
for bar, val in zip(bars, means_sorted):
    ax_bar.text(val + max(means_sorted) * 0.02, bar.get_y() + bar.get_height() / 2,
                f"{val:.0f}", va="center", color="#E7EAEE", fontsize=10)

fig_bar.tight_layout()
fig_bar.savefig(os.path.join(OUT_DIR, "comparacao_metodos.png"), dpi=150, facecolor=fig_bar.get_facecolor())
plt.close(fig_bar)

# ---------------------------------------------------------------
# 2) Animacao: 4 mapas de assento lado a lado, avancando juntos
#    (usa UMA execucao dedicada por metodo, com capture=True,
#    separada dos trials estatisticos acima)
# ---------------------------------------------------------------
anim_results = {name: simulate(order_fn(), capture=True) for name, order_fn in methods.items()}

COL_SEAT_EMPTY = np.array([27, 34, 44]) / 255      # painel escuro
COL_SEAT_TAKEN = np.array([52, 211, 153]) / 255    # verde (sentado)
COL_AISLE_BG = np.array([20, 24, 32]) / 255        # corredor vazio
COL_AISLE_WALK = np.array([69, 217, 224]) / 255    # ciano (andando)
COL_AISLE_STOW = np.array([255, 138, 61]) / 255    # laranja (guardando bagagem)

GRID_COLS = 7  # 0,1,2 = assentos esquerda | 3 = corredor | 4,5,6 = assentos direita
SEAT_TO_COL = {0: 0, 1: 1, 2: 2, 3: 4, 4: 5, 5: 6}

SKIP = 6  # subamostragem para manter o gif leve
max_len = max(len(frames) for _, frames in anim_results.values())
frame_indices = list(range(0, max_len, SKIP))
if frame_indices[-1] != max_len - 1:
    frame_indices.append(max_len - 1)

fig, axes = plt.subplots(1, 4, figsize=(15, 7), facecolor="#0A0D12")
fig.suptitle("Simulador de ordem de embarque", color="#FFB020", fontsize=16, fontweight="bold")

images = []
titles = []
for ax, name in zip(axes, anim_results.keys()):
    ax.set_facecolor("#0A0D12")
    grid = np.tile(COL_SEAT_EMPTY, (rows, GRID_COLS, 1))
    grid[:, 3, :] = COL_AISLE_BG
    im = ax.imshow(grid, aspect="equal")
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#2A3441")
    title = ax.set_title(name, color="#E7EAEE", fontsize=11, fontweight="bold")
    images.append(im)
    titles.append(title)

legend_elems = [
    Patch(facecolor=COL_SEAT_TAKEN, label="Sentado"),
    Patch(facecolor=COL_AISLE_WALK, label="Andando no corredor"),
    Patch(facecolor=COL_AISLE_STOW, label="Guardando bagagem"),
]
fig.legend(handles=legend_elems, loc="lower center", ncol=3, facecolor="#131820",
           labelcolor="#E7EAEE", edgecolor="#2A3441", bbox_to_anchor=(0.5, -0.02))
fig.tight_layout(rect=[0, 0.04, 1, 0.93])


def make_grid(aisle_status, seated_snapshot):
    grid = np.tile(COL_SEAT_EMPTY, (rows, GRID_COLS, 1))
    grid[:, 3, :] = COL_AISLE_BG
    for (r, s) in seated_snapshot:
        grid[r, SEAT_TO_COL[s]] = COL_SEAT_TAKEN
    for r, status in enumerate(aisle_status):
        if status == 'walk':
            grid[r, 3] = COL_AISLE_WALK
        elif status == 'stow':
            grid[r, 3] = COL_AISLE_STOW
    return grid


def update(frame_i):
    t = frame_indices[frame_i]
    artists = []
    for im, title, name in zip(images, titles, anim_results.keys()):
        total_ticks, frames = anim_results[name]
        idx = min(t, len(frames) - 1)
        aisle_status, seated_snapshot = frames[idx]
        grid = make_grid(aisle_status, seated_snapshot)
        im.set_data(grid)
        done = idx >= len(frames) - 1
        label = f"{name}  —  {idx+1}s" + ("  CONCLUIDO" if done else "")
        title.set_text(label)
        title.set_color("#34D399" if done else "#E7EAEE")
        artists.append(im)
        artists.append(title)
    return artists


anim = animation.FuncAnimation(fig, update, frames=len(frame_indices), interval=90, blit=False)
anim.save(os.path.join(OUT_DIR, "embarque_animado.gif"), writer=animation.PillowWriter(fps=11))
plt.close(fig)

print("\nArquivos gerados: comparacao_metodos.png, embarque_animado.gif")