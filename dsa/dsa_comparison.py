"""Compare linear search against dictionary lookup on the parsed transactions.

Two things are measured for each target id:

* wall-clock time, averaged over many repetitions with ``timeit``; and
* the number of record comparisons each strategy needs.

The comparison count matters because it is independent of how fast this
particular machine happens to be: linear search needs one comparison per record
it walks past (O(n)), while a dictionary hashes the key straight to its bucket
and needs only one (O(1)).
"""

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


def count_linear_comparisons(transactions, target_id):
    """How many id comparisons linear search needs to reach `target_id`.

    Counted in a separate pass so the counter never slows down the timed run.
    """
    comparisons = 0
    for record in transactions:
        comparisons += 1
        if record["id"] == target_id:
            break
    return comparisons


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
            "linear_cmps": count_linear_comparisons(transactions, target_id),
            # One hash of the key, then one bucket probe - constant regardless of size.
            "dict_cmps": 1,
        })
    return rows


def report(transactions, rows):
    print(f"Dataset: {len(transactions)} transactions | {REPEATS} repeats per measurement\n")
    header = (f"{'ID':>6} {'Position':>9} {'Linear (us)':>13} {'Dict (us)':>11} "
              f"{'Speed-up':>10} {'Lin cmps':>10} {'Dict cmps':>10}")
    print(header)
    print("-" * len(header))
    for row in rows:
        speedup = row["linear_us"] / row["dict_us"] if row["dict_us"] else float("inf")
        print(f"{row['id']:>6} {row['position']:>9} {row['linear_us']:>13.3f} "
              f"{row['dict_us']:>11.3f} {speedup:>9.1f}x {row['linear_cmps']:>10} "
              f"{row['dict_cmps']:>10}")

    mean_linear = statistics.mean(r["linear_us"] for r in rows)
    mean_dict = statistics.mean(r["dict_us"] for r in rows)
    mean_lin_cmps = statistics.mean(r["linear_cmps"] for r in rows)
    mean_dict_cmps = statistics.mean(r["dict_cmps"] for r in rows)
    print("-" * len(header))
    print(f"{'AVERAGE':>16} {mean_linear:>13.3f} {mean_dict:>11.3f} "
          f"{mean_linear / mean_dict:>9.1f}x {mean_lin_cmps:>10.1f} {mean_dict_cmps:>10.1f}")

    print(f"\nLinear search  : O(n)  - average {mean_linear:.3f} us, "
          f"{mean_lin_cmps:.1f} comparisons per lookup")
    print(f"Dictionary     : O(1)  - average {mean_dict:.3f} us, "
          f"{mean_dict_cmps:.1f} comparison per lookup")
    print(f"Dictionary lookup is about {mean_linear / mean_dict:.1f}x faster on this dataset.")
    print("\nThe comparison counts show the difference is structural, not just machine speed:")
    print("linear search walks the list until it finds the record, so its cost grows with the")
    print("record's position, while the dictionary hashes the key straight to its bucket and")
    print("does the same single probe no matter how large the dataset gets.")


if __name__ == "__main__":
    data = load_transactions()
    report(data, benchmark(data))
