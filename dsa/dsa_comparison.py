"""Compare linear search against dictionary lookup on the parsed transactions."""

import os
import statistics
import sys
import timeit

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dsa.parse_xml import load_transactions  # noqa: E402

REPEATS = 1000


def linear_search(transactions, target_id):
    """Scan the list one record at a time. O(n)."""
    for record in transactions:
        if record["id"] == target_id:
            return record
    return None


def dict_lookup(index, target_id):
    """Hash the key straight to its bucket. O(1) on average."""
    return index.get(target_id)


def build_index(transactions):
    """Build the id -> transaction dictionary. O(n), done once."""
    return {record["id"]: record for record in transactions}


def benchmark(transactions, sample_size=20):
    """Time both strategies over `sample_size` ids spread across the dataset."""
    index = build_index(transactions)
    ids = [record["id"] for record in transactions]
    step = max(1, len(ids) // sample_size)
    targets = ids[::step][:sample_size]

    rows = []
    for target_id in targets:
        linear = timeit.timeit(lambda: linear_search(transactions, target_id), number=REPEATS)
        lookup = timeit.timeit(lambda: dict_lookup(index, target_id), number=REPEATS)
        assert linear_search(transactions, target_id) == dict_lookup(index, target_id)
        rows.append({
            "id": target_id,
            "position": ids.index(target_id) + 1,
            "linear_us": linear / REPEATS * 1e6,
            "dict_us": lookup / REPEATS * 1e6,
        })
    return rows


def report(transactions, rows):
    print(f"Dataset: {len(transactions)} transactions | {REPEATS} repeats per measurement\n")
    print(f"{'ID':>6} {'Position':>9} {'Linear (us)':>13} {'Dict (us)':>11} {'Speed-up':>10}")
    print("-" * 54)
    for row in rows:
        speedup = row["linear_us"] / row["dict_us"] if row["dict_us"] else float("inf")
        print(f"{row['id']:>6} {row['position']:>9} {row['linear_us']:>13.3f} "
              f"{row['dict_us']:>11.3f} {speedup:>9.1f}x")

    mean_linear = statistics.mean(r["linear_us"] for r in rows)
    mean_dict = statistics.mean(r["dict_us"] for r in rows)
    print("-" * 54)
    print(f"{'AVERAGE':>16} {mean_linear:>13.3f} {mean_dict:>11.3f} "
          f"{mean_linear / mean_dict:>9.1f}x")

    print(f"\nLinear search  : O(n)  - average {mean_linear:.3f} us per lookup")
    print(f"Dictionary     : O(1)  - average {mean_dict:.3f} us per lookup")
    print(f"Dictionary lookup is about {mean_linear / mean_dict:.1f}x faster on this dataset.")


if __name__ == "__main__":
    data = load_transactions()
    report(data, benchmark(data))
