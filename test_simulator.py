import random
import unittest
from airplane_simulator import (
    generate_passengers,
    generate_stow_times,
    assign_families,
    apply_family_grouping,
    order_random,
    order_back_to_front,
    order_wilma,
    order_steffen,
    simulate,
    parse_args,
)


class TestAirplaneSimulator(unittest.TestCase):
    def setUp(self):
        self.rows = 10
        self.seats_per_row = 6
        self.passengers = generate_passengers(self.rows, self.seats_per_row)
        self.rng = random.Random(42)

    def test_generate_passengers(self):
        total = self.rows * self.seats_per_row
        self.assertEqual(len(self.passengers), total)
        pids = [p[0] for p in self.passengers]
        self.assertEqual(len(set(pids)), total)
        for pid, r, s in self.passengers:
            self.assertTrue(0 <= r < self.rows)
            self.assertTrue(0 <= s < self.seats_per_row)

    def test_generate_stow_times(self):
        stow_times = generate_stow_times(self.passengers, 5, 25, self.rng)
        self.assertEqual(len(stow_times), len(self.passengers))
        for pid, t in stow_times.items():
            self.assertTrue(5 <= t <= 25)

    def test_assign_families(self):
        fmap = assign_families(self.rows, self.seats_per_row, 0.5, self.rng)
        for pid, (gid, group_pids) in fmap.items():
            self.assertIn(pid, group_pids)
            self.assertIn(len(group_pids), (2, 3))
            # Todos os passageiros da mesma família devem estar na mesma fileira
            rows = {p // self.seats_per_row for p in group_pids}
            self.assertEqual(len(rows), 1)

    def test_apply_family_grouping_integrity(self):
        fmap = assign_families(self.rows, self.seats_per_row, 0.4, self.rng)
        shuffled = order_random(self.passengers, self.rng)
        grouped = apply_family_grouping(shuffled, fmap)

        self.assertEqual(len(grouped), len(self.passengers))
        self.assertEqual(set(p[0] for p in grouped), set(p[0] for p in self.passengers))

        # Verifica se membros da mesma família estão contíguos na fila
        seen_pids = set()
        i = 0
        while i < len(grouped):
            pid = grouped[i][0]
            if pid in fmap:
                gid, group_pids = fmap[pid]
                family_slice = [grouped[j][0] for j in range(i, i + len(group_pids))]
                self.assertEqual(set(family_slice), set(group_pids))
                i += len(group_pids)
            else:
                i += 1

    def test_order_methods_completeness(self):
        methods = {
            "Random": order_random(self.passengers, self.rng),
            "Back to front": order_back_to_front(self.passengers, self.rows, self.rng),
            "Wilma": order_wilma(self.passengers, self.rng),
            "Steffen": order_steffen(self.passengers),
        }
        for name, order in methods.items():
            self.assertEqual(len(order), len(self.passengers), f"Falha no tamanho de {name}")
            self.assertEqual(
                set(p[0] for p in order),
                set(p[0] for p in self.passengers),
                f"Passageiros ausentes em {name}",
            )

    def test_simulate_completes_all_passengers(self):
        stow_times = generate_stow_times(self.passengers, 5, 10, self.rng)
        order = order_random(self.passengers, self.rng)
        ticks, frames = simulate(
            order,
            rows=self.rows,
            passenger_stow_time=stow_times,
            seat_delay=5,
            entry_delay=1,
            capture=True,
        )
        self.assertGreater(ticks, 0)
        self.assertEqual(len(frames), ticks)
        # Último frame deve ter todos os assentos ocupados
        last_seated = frames[-1][1]
        self.assertEqual(len(last_seated), len(self.passengers))

    def test_reproducibility_with_seed(self):
        rng1 = random.Random(123)
        p1 = generate_passengers(6, 6)
        stow1 = generate_stow_times(p1, 5, 25, rng1)
        o1 = order_random(p1, rng1)
        t1, _ = simulate(o1, rows=6, passenger_stow_time=stow1, seat_delay=10, entry_delay=1)

        rng2 = random.Random(123)
        p2 = generate_passengers(6, 6)
        stow2 = generate_stow_times(p2, 5, 25, rng2)
        o2 = order_random(p2, rng2)
        t2, _ = simulate(o2, rows=6, passenger_stow_time=stow2, seat_delay=10, entry_delay=1)

        self.assertEqual(t1, t2)

    def test_cli_args_parsing(self):
        args = parse_args(["--trials", "15", "--rows", "25", "--seed", "99", "--no-gif"])
        self.assertEqual(args.trials, 15)
        self.assertEqual(args.rows, 25)
        self.assertEqual(args.seed, 99)
        self.assertTrue(args.no_gif)


if __name__ == "__main__":
    unittest.main()
