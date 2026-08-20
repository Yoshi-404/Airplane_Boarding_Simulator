*[Leia em Português](README.md)*


# Boarding Order Simulator

A Python simulation that compares different airplane boarding methods, measuring the total time (in "ticks") each method takes until every passenger is seated. It produces a comparison chart and an animated GIF showing all four methods boarding side by side.

## What the script does

1. Builds a plane with `rows` rows × `seats_per_row` seats (default: 30 rows, 6 seats per row, in a `Window | Middle | Aisle || Aisle | Middle | Window` layout).
2. Draws, **once**, a fixed "stow luggage" time for every passenger (between `min_stow_time` and `max_stow_time`). This time is identical across all methods and all repetitions, so the comparison isolates the effect of **boarding order** rather than the luck of who happens to have a small or large bag.
3. Simulates a single-file aisle tick by tick (no one can overtake anyone else). When a passenger reaches their row, they "block" the aisle for their stow time — plus an extra delay (`Seat_deley`) if they need to ask someone already seated in the middle/aisle seat to get up and let them through.
4. Runs each method **multiple times** (`TRIALS`, default 20), reshuffling the order on every run, and reports the mean, standard deviation, min, and max number of ticks.
5. Generates two output files:
   - `comparacao_metodos.png`: a bar chart with the mean (± standard deviation) for each method, fastest to slowest.
   - `embarque_animado.gif`: an animation showing all four methods boarding simultaneously, side by side, for visual comparison.

## Simulated boarding methods

| Method | Description |
|---|---|
| **Random** | Fully random order, with no organization by zone or seat type. |
| **Back to front** | Zone-based boarding, from the rear rows to the front rows (how most airlines board today). Order within each zone is random. |
| **Wilma** | Groups passengers by seat type: all window-seat passengers board first, then middle, then aisle. Greatly reduces how often a seated passenger has to stand up to let someone through. |
| **Steffen** | A deterministic method (no randomness) inspired by physicist Jason Steffen's research: window → middle → aisle, alternating even and odd rows on both sides of the plane, minimizing interference between neighboring passengers. |

## Requirements

```
python >= 3.8
numpy
matplotlib
pillow
```

Install with:

```bash
pip install numpy matplotlib pillow
```

## How to run

```bash
python sim_visual.py
```

`comparacao_metodos.png` and `embarque_animado.gif` are automatically saved in the **same folder as the script**, regardless of where you run it from.

## Sample console output

```
Rodando 20 simulacoes por metodo (mesma 'lentidao' de bagagem por passageiro em todos os metodos/trials)...

Random          media= 1250.5  desvio_padrao=  92.2  min= 1115  max= 1414  (20 trials)
Back to front   media= 1904.2  desvio_padrao=  81.6  min= 1765  max= 2041  (20 trials)
Wilma           media=  940.9  desvio_padrao=  32.1  min=  875  max=  995  (20 trials)
Steffen         media=  400.0  desvio_padrao=   0.0  min=  400  max=  400  (20 trials)

Arquivos gerados: comparacao_metodos.png, embarque_animado.gif
```

> A standard deviation of **0** for the Steffen method is not a bug: since that method is fully deterministic and each passenger's stow time is now fixed, every run produces exactly the same result.

## Configurable parameters (top of the file)

| Parameter | Description | Default |
|---|---|---|
| `rows` | Number of rows in the plane | 30 |
| `seats_per_row` | Seats per row | 6 |
| `min_stow_time` / `max_stow_time` | Range (in ticks) for stowing carry-on luggage | 5 / 25 |
| `Seat_deley` | Extra time needed when asking a seated passenger to move | 10 |
| `TRIALS` | Number of repetitions per method used to compute mean/standard deviation | 20 |
| `SKIP` | Frame subsampling for the animation (higher = lighter but choppier GIF) | 6 |

## Known limitations / next steps

- The animation uses a single dedicated run per method, separate from the `TRIALS` used for statistics — it may not represent the average case exactly, especially for methods with higher standard deviation (Random, Back to front).
- The model does not simulate an outside queue with boarding-pass scan delays, families/priority groups boarding together, or oversized luggage blocking rows other than the owner's own.
- With a low `TRIALS` count, the distribution may be skewed; a boxplot/histogram would represent the data better than mean ± standard deviation alone.

## License

Free to use for educational and study purposes.
