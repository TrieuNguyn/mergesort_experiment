/**
 * Mergesort with CUTOFF to Insertion Sort
 * ========================================
 * Cài đặt dựa trên slide bài giảng "2.2 Mergesort" 
 * (Sedgewick & Wayne, Algorithms 4th Edition)
 *
 * Slide 7  - merge() implementation
 * Slide 8  - sort() recursive implementation  
 * Slide 18 - CUTOFF improvement: use insertion sort for small subarrays
 * Slide 20 - Stop-if-already-sorted optimization
 *
 * CUTOFF value is configurable via command-line argument or constant.
 */
public class Merge {

  private static int CUTOFF = 7;

  private static void insertionSort(Comparable[] a, int lo, int hi) {
    for (int i = lo + 1; i <= hi; i++) {
      for (int j = i; j > lo && less(a[j], a[j - 1]); j--) {
        exch(a, j, j - 1);
      }
    }
  }

  private static void merge(Comparable[] a, Comparable[] aux, int lo, int mid, int hi) {
    // copy to aux[]
    for (int k = lo; k <= hi; k++)
      aux[k] = a[k];

    // merge back to a[]
    int i = lo, j = mid + 1;
    for (int k = lo; k <= hi; k++) {
      if      (i > mid)              a[k] = aux[j++];
      else if (j > hi)               a[k] = aux[i++];
      else if (less(aux[j], aux[i]))  a[k] = aux[j++];
      else                            a[k] = aux[i++];
    }
  }


  private static void sort(Comparable[] a, Comparable[] aux, int lo, int hi) {
    // Improvement 1
    if (hi <= lo + CUTOFF - 1 || hi <= lo) {
      insertionSort(a, lo, hi);
      return;
    }

    int mid = lo + (hi - lo) / 2;
    sort(a, aux, lo, mid);
    sort(a, aux, mid + 1, hi);

    // Improvement 2
    if (!less(a[mid + 1], a[mid])) return;

    merge(a, aux, lo, mid, hi);
  }

  public static void sort(Comparable[] a) {
    Comparable[] aux = new Comparable[a.length];
    sort(a, aux, 0, a.length - 1);
  }

  // ========== HELPER FUNCTIONS ==========
  @SuppressWarnings("unchecked")
  private static boolean less(Comparable v, Comparable w) {
    return v.compareTo(w) < 0;
  }

  private static void exch(Comparable[] a, int i, int j) {
    Comparable swap = a[i];
    a[i] = a[j];
    a[j] = swap;
  }

  // ========== SET CUTOFF ==========
  public static void setCutoff(int cutoff) {
    if (cutoff < 0) {
      throw new IllegalArgumentException("CUTOFF must be >= 0, got: " + cutoff);
    }
    CUTOFF = cutoff;
  }

  public static int getCutoff() {
    return CUTOFF;
  }
}
