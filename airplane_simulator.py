import argparse
import math
import os
import random
import statistics
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Patch


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description="Simulador comparativo de métodos de embarque de aeronaves."
    )
    parser.add_argument("--rows", type=int, default=30, help="Número de fileiras do avião (padrão: 30)")
    parser.add_argument("--seats-per-row", type=int, default=6, help="Número de assentos por fileira (padrão: 6)")
    parser.add_argument("--trials", type=int, default=20, help="Número de repetições por método (padrão: 20)")
    parser.add_argument("--seed", type=int, default=42, help="Seed fixa para reprodutibilidade (padrão: 42)")
    parser.add_argument("--min-stow", type=int, default=5, help="Tempo mínimo para guardar bagagem (padrão: 5)")
    parser.add_argument("--max-stow", type=int, default=25, help="Tempo máximo para guardar bagagem (padrão: 25)")
    parser.add_argument("--seat-delay", type=int, default=10, help="Atraso para dar passagem a assento ocupado (padrão: 10)")
    parser.add_argument("--entry-delay", type=int, default=1, help="Intervalo de leitura de cartão no portão/fila externa (padrão: 1 tick)")
    parser.add_argument("--family-ratio", type=float, default=0.15, help="Proporção de passageiros em grupos familiares (padrão: 0.15)")
    parser.add_argument("--no-gif", action="store_true", help="Desativa a geração do arquivo GIF de animação")
    parser.add_argument("--output-dir", type=str, default=None, help="Diretório de saída para gráficos e animações")
    return parser.parse_args(args)


def generate_passengers(rows, seats_per_row):
    """Gera lista base de tuplas de passageiros: (id, row, seat)."""
    passengers = []
    pid = 0
    for r in range(rows):
        for s in range(seats_per_row):
            passengers.append((pid, r, s))
            pid += 1
    return passengers


def generate_stow_times(passengers, min_stow, max_stow, rng):
    """Gera tempo fixo de guardar bagagem por passageiro para isolar efeito da ordem."""
    return {p[0]: rng.randint(min_stow, max_stow) for p in passengers}


def assign_families(rows, seats_per_row, family_ratio, rng):
    """
    Agrupa assentos adjacentes na mesma fileira em grupos familiares (2 a 3 pessoas).
    Retorna dicionário: pid -> (group_id, [pids_da_familia]).
    """
    if family_ratio <= 0.0:
        return {}
    family_map = {}
    next_group_id = 1
    for r in range(rows):
        for side_seats in [(0, 1, 2), (3, 4, 5)]:
            valid_side = [s for s in side_seats if s < seats_per_row]
            if len(valid_side) >= 2 and rng.random() < family_ratio:
                if len(valid_side) == 3:
                    size = rng.choice([2, 3])
                    sub = valid_side if size == 3 else (valid_side[:2] if rng.random() < 0.5 else valid_side[1:])
                else:
                    sub = valid_side
                pids = [r * seats_per_row + s for s in sub]
                gid = next_group_id
                next_group_id += 1
                for pid in pids:
                    family_map[pid] = (gid, pids)
    return family_map


def apply_family_grouping(order, family_map):
    """
    Mantém passageiros de um mesmo grupo familiar juntos no embarque.
    Quando o primeiro membro é chamado, os demais entram em sequência logo atrás.
    """
    if not family_map:
        return list(order)
    new_order = []
    seen_groups = set()
    pid_to_p = {p[0]: p for p in order}
    for p in order:
        pid = p[0]
        if pid in family_map:
            gid, group_pids = family_map[pid]
            if gid not in seen_groups:
                seen_groups.add(gid)
                for g_pid in group_pids:
                    if g_pid in pid_to_p:
                        new_order.append(pid_to_p[g_pid])
        else:
            new_order.append(p)
    return new_order


def order_random(base_passengers, rng):
    order = list(base_passengers)
    rng.shuffle(order)
    return order


def order_back_to_front(base_passengers, rows, rng):
    n_blocks = math.ceil(rows / 5)
    order = []
    for block in range(n_blocks - 1, -1, -1):
        start = block * 5
        end = min(start + 5, rows)
        block_pass = [p for p in base_passengers if start <= p[1] < end]
        rng.shuffle(block_pass)
        order.extend(block_pass)
    assert len(order) == len(base_passengers), "algum passageiro ficou de fora do embarque!"
    return order


def order_wilma(base_passengers, rng):
    windows = [p for p in base_passengers if p[2] in (0, 5)]
    middles = [p for p in base_passengers if p[2] in (1, 4)]
    aisles = [p for p in base_passengers if p[2] in (2, 3)]
    rng.shuffle(windows)
    rng.shuffle(middles)
    rng.shuffle(aisles)
    return windows + middles + aisles


def order_steffen(base_passengers):
    order = []
    for seat_group in [(0, 5), (1, 4), (2, 3)]:
        for even_odd in [1, 0]:
            group = [p for p in base_passengers if p[2] in seat_group and p[1] % 2 == even_odd]
            group.sort(key=lambda x: x[1], reverse=True)
            order.extend(group)
    return order


def simulate(passengers, rows, passenger_stow_time, seat_delay=10, entry_delay=1, capture=False):
    """
    Executa a simulação tick a tick.
    'passengers' é uma lista de tuplas (id, row, seat).
    'entry_delay' simula o intervalo de leitura de cartão no portão (fila externa).
    """
    aisle = [None] * rows
    seated = set()
    queue = list(passengers)
    ticks = 0
    gate_timer = 0
    frames = []

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
                                delay += seat_delay
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

        if gate_timer > 0:
            gate_timer -= 1
        if gate_timer == 0 and aisle[0] is None and queue:
            nxt = queue.pop(0)
            aisle[0] = {'id': nxt[0], 'row': nxt[1], 'seat': nxt[2], 'timer': 0}
            gate_timer = entry_delay

        if capture:
            aisle_status = [None] * rows
            for r in range(rows):
                p = aisle[r]
                if p is not None:
                    aisle_status[r] = 'stow' if p['row'] == r else 'walk'
            frames.append((aisle_status, set(seated)))

    return ticks, frames


def plot_bar_chart(stats, trials, output_path):
    fig_bar, ax_bar = plt.subplots(figsize=(7, 4.5), facecolor="#0A0D12")
    ax_bar.set_facecolor("#0A0D12")

    names_sorted = sorted(stats.keys(), key=lambda n: stats[n]["mean"])
    means_sorted = [stats[n]["mean"] for n in names_sorted]
    stds_sorted = [stats[n]["std"] for n in names_sorted]
    colors = ["#34D399" if i == 0 else "#FFB020" for i in range(len(names_sorted))]

    bars = ax_bar.barh(
        names_sorted,
        means_sorted,
        xerr=stds_sorted,
        color=colors,
        edgecolor="#2A3441",
        capsize=4,
        error_kw=dict(ecolor="#E7EAEE", lw=1.2),
    )
    ax_bar.invert_yaxis()
    ax_bar.set_xlabel(f"Ticks (média de {trials} execuções, ± desvio padrão)", color="#E7EAEE")
    ax_bar.set_title("Comparação entre métodos de embarque", color="#E7EAEE", fontsize=13, fontweight="bold")
    ax_bar.tick_params(colors="#E7EAEE")
    for spine in ax_bar.spines.values():
        spine.set_color("#2A3441")
    for bar, val in zip(bars, means_sorted):
        ax_bar.text(
            val + max(means_sorted) * 0.02,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.0f}",
            va="center",
            color="#E7EAEE",
            fontsize=10,
        )

    fig_bar.tight_layout()
    fig_bar.savefig(output_path, dpi=150, facecolor=fig_bar.get_facecolor())
    plt.close(fig_bar)


def plot_boxplot(raw_results, output_path):
    fig, ax = plt.subplots(figsize=(7.5, 4.5), facecolor="#0A0D12")
    ax.set_facecolor("#0A0D12")

    names_sorted = sorted(raw_results.keys(), key=lambda n: statistics.mean(raw_results[n]))
    data_sorted = [raw_results[n] for n in names_sorted]

    box = ax.boxplot(
        data_sorted,
        vert=False,
        tick_labels=names_sorted,
        patch_artist=True,
        medianprops=dict(color="#FFFFFF", linewidth=2),
        whiskerprops=dict(color="#E7EAEE", linewidth=1.2),
        capprops=dict(color="#E7EAEE", linewidth=1.2),
        flierprops=dict(marker='o', markerfacecolor='#E7EAEE', markeredgecolor='#2A3441', markersize=5),
    )

    for i, patch in enumerate(box['boxes']):
        color = "#34D399" if i == 0 else "#FFB020"
        patch.set_facecolor(color)
        patch.set_edgecolor("#2A3441")
        patch.set_alpha(0.85)

    ax.invert_yaxis()
    ax.set_xlabel("Ticks (distribuição por método)", color="#E7EAEE")
    ax.set_title("Distribuição do Tempo de Embarque (Boxplot)", color="#E7EAEE", fontsize=13, fontweight="bold")
    ax.tick_params(colors="#E7EAEE")
    for spine in ax.spines.values():
        spine.set_color("#2A3441")

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def generate_animation(anim_results, rows, output_path, skip=6):
    COL_SEAT_EMPTY = np.array([27, 34, 44]) / 255
    COL_SEAT_TAKEN = np.array([52, 211, 153]) / 255
    COL_AISLE_BG = np.array([20, 24, 32]) / 255
    COL_AISLE_WALK = np.array([69, 217, 224]) / 255
    COL_AISLE_STOW = np.array([255, 138, 61]) / 255

    GRID_COLS = 7
    SEAT_TO_COL = {0: 0, 1: 1, 2: 2, 3: 4, 4: 5, 5: 6}

    max_len = max(len(frames) for _, frames in anim_results.values())
    frame_indices = list(range(0, max_len, skip))
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
        ax.set_xticks([])
        ax.set_yticks([])
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
    fig.legend(
        handles=legend_elems,
        loc="lower center",
        ncol=3,
        facecolor="#131820",
        labelcolor="#E7EAEE",
        edgecolor="#2A3441",
        bbox_to_anchor=(0.5, -0.02),
    )
    fig.tight_layout(rect=[0, 0.04, 1, 0.93])

    def make_grid(aisle_status, seated_snapshot):
        grid = np.tile(COL_SEAT_EMPTY, (rows, GRID_COLS, 1))
        grid[:, 3, :] = COL_AISLE_BG
        for (r, s) in seated_snapshot:
            col = SEAT_TO_COL.get(s, s if s < 3 else s + 1)
            grid[r, col] = COL_SEAT_TAKEN
        for r, status in enumerate(aisle_status):
            if status == "walk":
                grid[r, 3] = COL_AISLE_WALK
            elif status == "stow":
                grid[r, 3] = COL_AISLE_STOW
        return grid

    def update(frame_i):
        t = frame_indices[frame_i]
        artists = []
        for im, title, name in zip(images, titles, anim_results.keys()):
            _, frames = anim_results[name]
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
    anim.save(output_path, writer=animation.PillowWriter(fps=11))
    plt.close(fig)


def print_results_table(stats, trials):
    names_sorted = sorted(stats.keys(), key=lambda n: stats[n]["mean"])
    print("\n" + "=" * 70)
    print(f"TABELA DE RESULTADOS ({trials} trials por método)")
    print("=" * 70)
    print(f"{'Método':<16} | {'Média (ticks)':<13} | {'Desvio Padrão':<13} | {'Mínimo':<7} | {'Máximo':<7}")
    print("-" * 70)
    for name in names_sorted:
        s = stats[name]
        print(f"{name:<16} | {s['mean']:<13.1f} | {s['std']:<13.1f} | {s['min']:<7} | {s['max']:<7}")
    print("=" * 70 + "\n")


def main():
    args = parse_args()
    out_dir = args.output_dir if args.output_dir else os.path.dirname(os.path.abspath(__file__))
    os.makedirs(out_dir, exist_ok=True)

    rng = random.Random(args.seed)

    base_passengers = generate_passengers(args.rows, args.seats_per_row)
    passenger_stow_time = generate_stow_times(base_passengers, args.min_stow, args.max_stow, rng)
    family_map = assign_families(args.rows, args.seats_per_row, args.family_ratio, rng)

    num_family_passengers = len(family_map)
    num_families = len(set(g[0] for g in family_map.values())) if family_map else 0

    print("Configuração:")
    print(f"  - Fileiras: {args.rows} | Assentos/fileira: {args.seats_per_row} | Total passageiros: {len(base_passengers)}")
    print(f"  - Repetições (trials): {args.trials} | Seed: {args.seed}")
    print(f"  - Fila externa (entry delay): {args.entry_delay} tick(s)")
    print(f"  - Grupos familiares: {num_families} famílias ({num_family_passengers} passageiros, ~{args.family_ratio*100:.0f}%)")
    print(f"\nRodando {args.trials} simulações por método...\n")

    raw_results = {}
    stats = {}

    method_generators = {
        "Random": lambda: apply_family_grouping(order_random(base_passengers, rng), family_map),
        "Back to front": lambda: apply_family_grouping(order_back_to_front(base_passengers, args.rows, rng), family_map),
        "Wilma": lambda: apply_family_grouping(order_wilma(base_passengers, rng), family_map),
        "Steffen": lambda: apply_family_grouping(order_steffen(base_passengers), family_map),
    }

    for name, order_fn in method_generators.items():
        trial_ticks = [
            simulate(
                order_fn(),
                rows=args.rows,
                passenger_stow_time=passenger_stow_time,
                seat_delay=args.seat_delay,
                entry_delay=args.entry_delay,
                capture=False,
            )[0]
            for _ in range(args.trials)
        ]
        mean = statistics.mean(trial_ticks)
        std = statistics.stdev(trial_ticks) if len(trial_ticks) > 1 else 0.0
        raw_results[name] = trial_ticks
        stats[name] = {
            "mean": mean,
            "std": std,
            "min": min(trial_ticks),
            "max": max(trial_ticks),
        }
        print(
            f"{name:15s} media={mean:7.1f}  desvio_padrao={std:6.1f}  "
            f"min={min(trial_ticks):5d}  max={max(trial_ticks):5d}  ({args.trials} trials)"
        )

    print_results_table(stats, args.trials)

    bar_path = os.path.join(out_dir, "comparacao_metodos.png")
    plot_bar_chart(stats, args.trials, bar_path)

    box_path = os.path.join(out_dir, "boxplot_metodos.png")
    plot_boxplot(raw_results, box_path)

    generated = ["comparacao_metodos.png", "boxplot_metodos.png"]

    if not args.no_gif:
        print("Gerando animação comparativa (embarque_animado.gif)...")
        anim_results = {}
        for name, order_fn in method_generators.items():
            ticks, frames = simulate(
                order_fn(),
                rows=args.rows,
                passenger_stow_time=passenger_stow_time,
                seat_delay=args.seat_delay,
                entry_delay=args.entry_delay,
                capture=True,
            )
            anim_results[name] = (ticks, frames)
        gif_path = os.path.join(out_dir, "embarque_animado.gif")
        generate_animation(anim_results, args.rows, gif_path)
        generated.append("embarque_animado.gif")

    print(f"\nArquivos gerados: {', '.join(generated)}")


if __name__ == "__main__":
    main()