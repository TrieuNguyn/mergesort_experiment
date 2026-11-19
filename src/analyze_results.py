"""
analyze_results.py - Phân tích kết quả thí nghiệm Mergesort CUTOFF
===================================================================

Đọc kết quả từ data/results.csv, tạo:
1. Bảng thống kê tóm tắt
2. Đồ thị thời gian theo CUTOFF cho mỗi kích thước mảng
3. Đồ thị tổng hợp tìm CUTOFF tốt nhất
4. Heatmap tối ưu
"""

import csv
import os
import sys
from collections import defaultdict

# Try to import matplotlib
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("WARNING: matplotlib not found. Install with: pip install matplotlib")
    print("Will generate text-based analysis only.\n")

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


def read_results(csv_path):
    """Read CSV results into structured dict"""
    data = defaultdict(lambda: defaultdict(dict))
    # data[size][dist][cutoff] = time

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            size = int(row['array_size'])
            dist = row['distribution']
            cutoff = int(row['cutoff'])
            time = float(row['median_time_ms'])
            data[size][dist][cutoff] = time

    return data


def find_best_cutoffs(data):
    """Find the best CUTOFF for each (size, distribution) pair"""
    results = {}
    for size in sorted(data.keys()):
        for dist in sorted(data[size].keys()):
            times = data[size][dist]
            best_cutoff = min(times, key=times.get)
            best_time = times[best_cutoff]
            # Also get time for cutoff=0 (pure mergesort) for comparison
            baseline = times.get(0, times.get(1, best_time))
            improvement = (baseline - best_time) / baseline * 100 if baseline > 0 else 0
            results[(size, dist)] = {
                'best_cutoff': best_cutoff,
                'best_time': best_time,
                'baseline_time': baseline,
                'improvement_pct': improvement
            }
    return results


def print_summary_table(data, best_cutoffs):
    """Print a formatted summary table"""
    sizes = sorted(data.keys())
    distributions = sorted(next(iter(data.values())).keys())

    print("\n" + "=" * 80)
    print("SUMMARY: Best CUTOFF values")
    print("=" * 80)

    # Header
    header = f"{'Size':>10}"
    for dist in distributions:
        header += f" | {dist:>15}"
    print(header)
    print("-" * len(header))

    for size in sizes:
        row = f"{size:>10}"
        for dist in distributions:
            bc = best_cutoffs.get((size, dist))
            if bc:
                row += f" | {bc['best_cutoff']:>7} ({bc['improvement_pct']:>4.1f}%)"
            else:
                row += f" | {'N/A':>15}"
        print(row)

    # Overall best cutoff
    cutoff_counts = defaultdict(int)
    cutoff_scores = defaultdict(float)
    for key, val in best_cutoffs.items():
        c = val['best_cutoff']
        cutoff_counts[c] += 1
        cutoff_scores[c] += val['improvement_pct']

    print("\n" + "=" * 80)
    print("CUTOFF frequency (how often each value was best):")
    print("=" * 80)
    for c in sorted(cutoff_counts.keys()):
        bar = "█" * cutoff_counts[c]
        print(f"  CUTOFF {c:>3}: {cutoff_counts[c]:>3} times  {bar}")

    # Weighted best
    print("\n" + "=" * 80)
    print("OVERALL BEST CUTOFF (most frequently optimal):")
    overall_best = max(cutoff_counts, key=cutoff_counts.get)
    print(f"  >>> CUTOFF = {overall_best} <<<")
    print("=" * 80)

    return overall_best


def print_detailed_table(data):
    """Print detailed timing table for key CUTOFF values"""
    sizes = sorted(data.keys())
    key_cutoffs = [0, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 30]

    print("\n" + "=" * 80)
    print("DETAILED: Median time (ms) for key CUTOFF values - RANDOM distribution")
    print("=" * 80)

    header = f"{'CUTOFF':>8}"
    for size in sizes:
        header += f" | {size:>10}"
    print(header)
    print("-" * len(header))

    for cutoff in key_cutoffs:
        row = f"{cutoff:>8}"
        for size in sizes:
            t = data[size].get('random', {}).get(cutoff, None)
            if t is not None:
                row += f" | {t:>10.4f}"
            else:
                row += f" | {'N/A':>10}"
        print(row)


def plot_results(data, output_dir):
    """Generate all plots"""
    if not HAS_MATPLOTLIB:
        print("Skipping plots (matplotlib not available)")
        return

    sizes = sorted(data.keys())
    distributions = sorted(next(iter(data.values())).keys())

    # Color map for distributions
    colors = {
        'random': '#2196F3',
        'sorted': '#4CAF50',
        'reverse': '#F44336',
        'nearly_sorted': '#FF9800',
        'few_unique': '#9C27B0'
    }

    # ========== PLOT 1: Time vs CUTOFF for each array size (random only) ==========
    fig, axes = plt.subplots(2, 4, figsize=(20, 10))
    axes = axes.flatten()

    for idx, size in enumerate(sizes):
        ax = axes[idx]
        cutoffs = sorted(data[size]['random'].keys())
        times = [data[size]['random'][c] for c in cutoffs]

        ax.plot(cutoffs, times, 'b.-', linewidth=1.5, markersize=4)

        # Mark minimum
        min_idx = times.index(min(times))
        ax.plot(cutoffs[min_idx], times[min_idx], 'r*', markersize=15,
                label=f'Best: CUTOFF={cutoffs[min_idx]}')

        ax.set_title(f'N = {size:,}', fontsize=12, fontweight='bold')
        ax.set_xlabel('CUTOFF')
        ax.set_ylabel('Time (ms)')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    # Hide empty subplots
    for idx in range(len(sizes), len(axes)):
        axes[idx].set_visible(False)

    fig.suptitle('Mergesort: Median Time vs CUTOFF (Random Data)',
                 fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'plot1_time_vs_cutoff_random.png'), dpi=150)
    plt.close()
    print(f"  Saved: plot1_time_vs_cutoff_random.png")

    # ========== PLOT 2: All distributions for large N ==========
    large_sizes = [s for s in sizes if s >= 50_000]

    fig, axes = plt.subplots(1, len(large_sizes), figsize=(6 * len(large_sizes), 5))
    if len(large_sizes) == 1:
        axes = [axes]

    for idx, size in enumerate(large_sizes):
        ax = axes[idx]
        for dist in distributions:
            cutoffs = sorted(data[size][dist].keys())
            times = [data[size][dist][c] for c in cutoffs]
            ax.plot(cutoffs, times, '.-', color=colors.get(dist, 'gray'),
                    linewidth=1.5, markersize=3, label=dist)

        ax.set_title(f'N = {size:,}', fontsize=12, fontweight='bold')
        ax.set_xlabel('CUTOFF')
        ax.set_ylabel('Time (ms)')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    fig.suptitle('Mergesort: Time vs CUTOFF (All Distributions)',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'plot2_all_distributions.png'), dpi=150)
    plt.close()
    print(f"  Saved: plot2_all_distributions.png")

    # ========== PLOT 3: Normalized performance (relative to CUTOFF=0) ==========
    fig, ax = plt.subplots(figsize=(12, 6))

    for size in [s for s in sizes if s >= 10_000]:
        cutoffs = sorted(data[size]['random'].keys())
        baseline = data[size]['random'].get(0, data[size]['random'].get(1))
        if baseline and baseline > 0:
            normalized = [data[size]['random'][c] / baseline for c in cutoffs]
            ax.plot(cutoffs, normalized, '.-', linewidth=1.5, markersize=4,
                    label=f'N={size:,}')

    ax.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='Baseline (no cutoff)')
    ax.set_xlabel('CUTOFF Value', fontsize=12)
    ax.set_ylabel('Relative Time (1.0 = no cutoff)', fontsize=12)
    ax.set_title('Normalized Performance: Mergesort with CUTOFF / Mergesort without CUTOFF',
                 fontsize=13, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'plot3_normalized_performance.png'), dpi=150)
    plt.close()
    print(f"  Saved: plot3_normalized_performance.png")

    # ========== PLOT 4: Heatmap of best CUTOFFs ==========
    if HAS_NUMPY:
        fig, ax = plt.subplots(figsize=(10, 6))

        matrix = []
        y_labels = []
        for size in sizes:
            row = []
            for dist in distributions:
                times = data[size][dist]
                best = min(times, key=times.get)
                row.append(best)
            matrix.append(row)
            y_labels.append(f'{size:,}')

        matrix = np.array(matrix)
        im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto')

        ax.set_xticks(range(len(distributions)))
        ax.set_xticklabels(distributions, rotation=45, ha='right')
        ax.set_yticks(range(len(sizes)))
        ax.set_yticklabels(y_labels)
        ax.set_xlabel('Distribution')
        ax.set_ylabel('Array Size')
        ax.set_title('Best CUTOFF Value (Heatmap)', fontsize=14, fontweight='bold')

        # Add text annotations
        for i in range(len(sizes)):
            for j in range(len(distributions)):
                ax.text(j, i, str(int(matrix[i, j])),
                        ha='center', va='center', fontsize=11, fontweight='bold')

        plt.colorbar(im, label='CUTOFF value')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'plot4_heatmap_best_cutoff.png'), dpi=150)
        plt.close()
        print(f"  Saved: plot4_heatmap_best_cutoff.png")

    # ========== PLOT 5: Zoomed in on CUTOFF 5-20 for the largest N ==========
    fig, ax = plt.subplots(figsize=(10, 6))
    largest = max(sizes)

    cutoffs_zoom = [c for c in sorted(data[largest]['random'].keys()) if 0 <= c <= 30]

    for dist in distributions:
        times = [data[largest][dist].get(c, float('nan')) for c in cutoffs_zoom]
        ax.plot(cutoffs_zoom, times, '.-', color=colors.get(dist, 'gray'),
                linewidth=2, markersize=6, label=dist)

    ax.set_xlabel('CUTOFF Value', fontsize=12)
    ax.set_ylabel('Time (ms)', fontsize=12)
    ax.set_title(f'Zoomed View: CUTOFF 0-30 for N={largest:,}',
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # Add vertical lines at classic values
    ax.axvline(x=7, color='gray', linestyle=':', alpha=0.7, label='_Java 6 (7)')
    ax.axvline(x=10, color='gray', linestyle='--', alpha=0.7, label='_Textbook (10)')
    ax.text(7, ax.get_ylim()[1] * 0.95, 'Java 6\n(7)', ha='center', fontsize=9, color='gray')
    ax.text(10, ax.get_ylim()[1] * 0.90, 'Textbook\n(10)', ha='center', fontsize=9, color='gray')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'plot5_zoomed_largest.png'), dpi=150)
    plt.close()
    print(f"  Saved: plot5_zoomed_largest.png")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    csv_path = os.path.join(project_root, 'data', 'results.csv')
    output_dir = os.path.join(project_root, 'data')

    if not os.path.exists(csv_path):
        print(f"ERROR: {csv_path} not found. Run the Java experiment first.")
        sys.exit(1)

    print("Reading results...")
    data = read_results(csv_path)

    print("Computing best CUTOFFs...")
    best_cutoffs = find_best_cutoffs(data)

    # Print tables
    overall_best = print_summary_table(data, best_cutoffs)
    print_detailed_table(data)

    # Generate plots
    print("\nGenerating plots...")
    plot_results(data, output_dir)

    print(f"\n{'=' * 80}")
    print(f"CONCLUSION: The optimal CUTOFF value for this machine is approximately {overall_best}")
    print(f"{'=' * 80}")


if __name__ == '__main__':
    main()

