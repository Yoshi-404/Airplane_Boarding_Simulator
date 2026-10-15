*[Leia em Português](README.md)*

# Boarding Order Simulator

![Boarding Simulation Demo](embarque_animado.gif)

A Python simulation that compares different airplane boarding methods, measuring the total time (in "ticks") each method takes until every passenger is seated. Generates comparative charts (bar and boxplot) and a GIF animation showing all four methods boarding simultaneously side by side.

---

## How to run

### 1. Prerequisites and Installation

Python 3.8+ is recommended. Install dependencies from [requirements.txt](requirements.txt):

```bash
pip install -r requirements.txt
```

### 2. Running the Simulation

Run the simulator with default settings:

```bash
python airplane_simulator.py
```

### 3. Command-Line Arguments

You can customize simulation parameters using CLI arguments:

| Argument | Description | Default |
|---|---|---|
| `--rows` | Number of rows in the airplane | `30` |
| `--seats-per-row` | Number of seats per row | `6` |
| `--trials` | Number of simulations per method | `20` |
| `--seed` | Random seed for reproducibility | `42` |
| `--entry-delay` | Gate boarding pass scan interval / external queue (ticks) | `1` |
| `--family-ratio` | Proportion of passengers in family groups | `0.15` |
| `--min-stow` | Minimum carry-on stow time | `5` |
| `--max-stow` | Maximum carry-on stow time | `25` |
| `--seat-delay` | Extra delay when a seated passenger must yield | `10` |
| `--no-gif` | Skip GIF animation generation (fast run) | `False` |
| `--output-dir` | Output directory for generated files | Script directory |

**Fast run example (only statistics and charts):**

```bash
python airplane_simulator.py --trials 50 --rows 30 --no-gif
```

### 4. Running Tests

To run the automated unit test suite:

```bash
python -m unittest test_simulator.py
```

---

## What the script does

1. **Aircraft setup**: Builds a plane with `rows` rows × `seats_per_row` seats (default: 30 rows, 6 seats per row, in a `Window | Middle | Aisle || Aisle | Middle | Window` layout).
2. **Fixed luggage stow time per passenger**: Draws a fixed stow time (`min_stow` to `max_stow`) once using a fixed seed. This isolates the effect of the **boarding order**.
3. **External queue and gate delay**: Models gate boarding pass scan delays (`--entry-delay`), controlling passenger inflow rate into the aisle.
4. **Family groups**: Models passengers traveling together in adjacent seats (`--family-ratio`). Family members board in sequence when the first member is called.
5. **Aisle dynamics**: Simulates a single-file aisle tick by tick. When someone stows luggage, the aisle blocks, with an extra delay (`seat_delay`) if seated passengers must stand to let them pass.
6. **Statistical reliability**: Runs each method over multiple trials (`--trials`, default 20) with a controlled seed (`--seed`, default 42).
7. **Output files**:
   - `comparacao_metodos.png`: bar chart displaying the mean (± standard deviation) for each method.
   - `boxplot_metodos.png`: boxplot displaying the distribution of boarding times.
   - `embarque_animado.gif`: side-by-side animated visualization of all four methods.

---

## Simulated boarding methods

| Method | Description |
|---|---|
| **Random** | Completely random boarding order. |
| **Back to front** | Zone-based boarding from rear rows to front rows. |
| **Wilma** | Grouped by seat type: Window first, then Middle, then Aisle. |
| **Steffen** | Deterministic method inspired by physicist Jason Steffen: alternates odd/even rows across window, middle, and aisle seats to minimize passenger interference. |

---

## Results

### Summary Table

Results obtained with default parameters (30 rows, 180 passengers, 20 trials, seed 42):

| Rank | Method | Mean (ticks) | Std Dev | Min (ticks) | Max (ticks) |
|:---:|---|:---:|:---:|:---:|:---:|
| 1st | **Steffen** | 602.0 | 0.0 | 602 | 602 |
| 2nd | **Wilma** | 968.7 | 36.1 | 925 | 1059 |
| 3rd | **Random** | 1231.8 | 45.1 | 1116 | 1316 |
| 4th | **Back to front** | 1907.5 | 61.6 | 1796 | 2030 |

### Console Output

```
Configuração:
  - Fileiras: 30 | Assentos/fileira: 6 | Total passageiros: 180
  - Repetições (trials): 20 | Seed: 42
  - Fila externa (entry delay): 1 tick(s)
  - Grupos familiares: 10 famílias (24 passageiros, ~15%)

Rodando 20 simulações por método...

Random          media= 1231.8  desvio_padrao=  45.1  min= 1116  max= 1316  (20 trials)
Back to front   media= 1907.5  desvio_padrao=  61.6  min= 1796  max= 2030  (20 trials)
Wilma           media=  968.7  desvio_padrao=  36.1  min=  925  max= 1059  (20 trials)
Steffen         media=  602.0  desvio_padrao=   0.0  min=  602  max=  602  (20 trials)

Arquivos gerados: comparacao_metodos.png, boxplot_metodos.png, embarque_animado.gif
```

### Generated Visualizations

#### Mean Comparison
![Comparison of boarding methods](comparacao_metodos.png)

#### Distribution (Boxplot)
![Boarding time distribution (Boxplot)](boxplot_metodos.png)

---

## License

This project is licensed under the [MIT License](LICENSE).
