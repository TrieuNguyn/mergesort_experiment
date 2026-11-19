import java.io.*;
import java.util.*;

/**
 * Experiment: Finding the Optimal CUTOFF for Mergesort
 * =====================================================
 *
 * This experiment measures the running time of mergesort with different
 * CUTOFF values to determine the optimal threshold for switching to
 * insertion sort on small subarrays.
 *
 * Methodology (based on 1.3 Algorithm Analysis):
 * - Test CUTOFF values: 0 (no cutoff), 1, 2, 3, ..., 50
 * - Array sizes: 1000, 5000, 10000, 50000, 100000, 500000, 1000000
 * - Data distributions: random, sorted, reverse-sorted, nearly-sorted, few-unique
 * - Each configuration is run TRIALS times; we report median time
 * - Warm-up runs before actual measurement (JIT compilation)
 */
public class MergesortExperiment {

  // ===== CONFIGURATION =====
  static final int[] CUTOFF_VALUES = {
      0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
      11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
      22, 25, 28, 30, 35, 40, 45, 50
  };

  static final int[] ARRAY_SIZES = {
      1_000, 5_000, 10_000, 50_000, 100_000, 500_000, 1_000_000
  };

  static final int TRIALS = 10;    // number of repetitions per configuration
  static final int WARMUP = 3;     // warm-up runs (not counted)

  // ===== DATA GENERATORS =====

  /** Uniformly random integers */
  static Integer[] generateRandom(int n, Random rng) {
    Integer[] a = new Integer[n];
    for (int i = 0; i < n; i++)
      a[i] = rng.nextInt(n);
    return a;
  }

  /** Already sorted */
  static Integer[] generateSorted(int n) {
    Integer[] a = new Integer[n];
    for (int i = 0; i < n; i++)
      a[i] = i;
    return a;
  }

  /** Reverse sorted */
  static Integer[] generateReverse(int n) {
    Integer[] a = new Integer[n];
    for (int i = 0; i < n; i++)
      a[i] = n - i;
    return a;
  }

  /** Nearly sorted: sorted array with ~5% elements swapped */
  static Integer[] generateNearlySorted(int n, Random rng) {
    Integer[] a = generateSorted(n);
    int swaps = n / 20; // 5% perturbation
    for (int s = 0; s < swaps; s++) {
      int i = rng.nextInt(n);
      int j = rng.nextInt(n);
      Integer tmp = a[i];
      a[i] = a[j];
      a[j] = tmp;
    }
    return a;
  }

  /** Few unique values: only 10 distinct values */
  static Integer[] generateFewUnique(int n, Random rng) {
    Integer[] a = new Integer[n];
    for (int i = 0; i < n; i++)
      a[i] = rng.nextInt(10);
    return a;
  }

  // ===== TIMING =====

  /** Time one sort; returns elapsed time in milliseconds */
  static double timeSort(Integer[] original, int cutoff) {
    Integer[] a = Arrays.copyOf(original, original.length);
    Merge.setCutoff(cutoff);

    long start = System.nanoTime();
    Merge.sort(a);
    long end = System.nanoTime();

    // Verify correctness
    for (int i = 1; i < a.length; i++) {
      if (a[i].compareTo(a[i - 1]) < 0) {
        System.err.println("ERROR: Array not sorted with cutoff=" + cutoff);
        System.exit(1);
      }
    }

    return (end - start) / 1_000_000.0; // ms
  }

  /** Run TRIALS and return median time */
  static double medianTime(Integer[] original, int cutoff) {
    double[] times = new double[TRIALS];
    for (int t = 0; t < TRIALS; t++) {
      times[t] = timeSort(original, cutoff);
    }
    Arrays.sort(times);
    // Return median
    if (TRIALS % 2 == 0)
      return (times[TRIALS / 2 - 1] + times[TRIALS / 2]) / 2.0;
    else
      return times[TRIALS / 2];
  }

  // ===== MAIN EXPERIMENT =====
  public static void main(String[] args) throws Exception {
    Random rng = new Random(42); // fixed seed for reproducibility

    // Output files
    PrintWriter csvWriter = new PrintWriter(new FileWriter("data/results.csv"));
    csvWriter.println("array_size,distribution,cutoff,median_time_ms");

    String[] distributions = {"random", "sorted", "reverse", "nearly_sorted", "few_unique"};

    System.out.println("=== Mergesort CUTOFF Experiment ===");
    System.out.println("Trials per config: " + TRIALS);
    System.out.println("Warm-up runs: " + WARMUP);
    System.out.println("Array sizes: " + Arrays.toString(ARRAY_SIZES));
    System.out.println("CUTOFF values: " + Arrays.toString(CUTOFF_VALUES));
    System.out.println();

    // Warm up JVM
    System.out.println("Warming up JVM...");
    Integer[] warmupArray = generateRandom(100_000, rng);
    for (int w = 0; w < WARMUP; w++) {
      for (int cutoff : CUTOFF_VALUES) {
        timeSort(warmupArray, cutoff);
      }
    }
    System.out.println("Warm-up complete.\n");

    for (int size : ARRAY_SIZES) {
      System.out.println("--- Array size: " + size + " ---");

      for (String dist : distributions) {
        // Generate test data
        Integer[] original;
        switch (dist) {
          case "random":        original = generateRandom(size, rng); break;
          case "sorted":        original = generateSorted(size); break;
          case "reverse":       original = generateReverse(size); break;
          case "nearly_sorted": original = generateNearlySorted(size, rng); break;
          case "few_unique":    original = generateFewUnique(size, rng); break;
          default: throw new RuntimeException("Unknown distribution: " + dist);
        }

        // Save first dataset of each type for reproducibility
        if (size <= 10_000) {
          saveDataset(original, "data/dataset_" + dist + "_" + size + ".txt");
        }

        System.out.printf("  Distribution: %-15s ", dist);

        double bestTime = Double.MAX_VALUE;
        int bestCutoff = 0;

        for (int cutoff : CUTOFF_VALUES) {
          double medTime = medianTime(original, cutoff);
          csvWriter.println(size + "," + dist + "," + cutoff + "," +
              String.format("%.4f", medTime));

          if (medTime < bestTime) {
            bestTime = medTime;
            bestCutoff = cutoff;
          }
        }

        System.out.printf("Best CUTOFF = %2d  (%.4f ms)\n", bestCutoff, bestTime);
      }
      System.out.println();
      csvWriter.flush();
    }

    csvWriter.close();

    System.out.println("Results saved to data/results.csv");
    System.out.println("Done!");
  }

  static void saveDataset(Integer[] a, String filename) throws Exception {
    PrintWriter pw = new PrintWriter(new FileWriter(filename));
    for (int val : a) {
      pw.println(val);
    }
    pw.close();
  }
}
