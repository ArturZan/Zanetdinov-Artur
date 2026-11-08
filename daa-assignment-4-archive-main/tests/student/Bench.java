import java.util.*;

/**
 * Search comparison naive / KMP / exact Rabin-Karp (base 31, mod 101) on identical inputs.
 * Build and run from the repository root (after `python tools/run.py --setup` has created Java/build):
 *   javac --release 17 -d /tmp/benchout -cp Java/build tests/student/Bench.java
 *   java -Xmx384m -cp /tmp/benchout:Java/build Bench > tests/student/bench_results.md
 * Timing scope: one call of Algorithms.naive/kmp/rk on an already parsed request map (no JSON, no JVM start,
 * no compilation). Warm-up: 300 discarded calls per algorithm/input (JIT). A "run" is the mean of REPS
 * consecutive calls, reported in microseconds per call. Three runs per algorithm/size/case; median reported.
 */
public class Bench {
    static final int REPS = 300, RUNS = 3, WARM = 500;

    static Map<String, Object> req(String t, String p) {
        Map<String, Object> m = new HashMap<>();
        m.put("text", t);
        m.put("pattern", p);
        return m;
    }

    static String random(Random r, int n, String alpha) {
        StringBuilder b = new StringBuilder();
        for (int i = 0; i < n; i++) b.append(alpha.charAt(r.nextInt(alpha.length())));
        return b.toString();
    }

    static List<Integer> oracle(String t, String p) {          // independent reference (library search, only here)
        List<Integer> res = new ArrayList<>();
        for (int i = t.indexOf(p); i != -1; i = t.indexOf(p, i + 1)) res.add(i);
        return res;
    }

    static List<Integer> asInts(Object o) {
        List<Integer> res = new ArrayList<>();
        for (Object x : (List<?>) ((Map<?, ?>) o).get("positions")) res.add(((Number) x).intValue());
        return res;
    }

    interface Algo { Map<String, Object> run(Map<String, Object> in); }

    public static void main(String[] a) {
        int[][] sizes = {{500, 10}, {1500, 30}, {3000, 100}};
        String[] names = {"naive", "kmp", "rk"};
        Algo[] algos = {Algorithms::naive, Algorithms::kmp, Algorithms::rk};
        System.out.println("|Case|n|m|Seed/generator|Algorithm|Run 1 (us/call)|Run 2|Run 3|Median|Correct outputs checked|");
        System.out.println("|---|---:|---:|---|---|---:|---:|---:|---:|---|");
        for (String kind : new String[]{"random", "repetitive"}) {
            for (int[] sz : sizes) {
                int n = sz[0], m = sz[1];
                String text, pat, gen;
                if (kind.equals("random")) {
                    Random r = new Random(4242L + n);
                    text = random(r, n, "abcd");
                    int at = n / 3;
                    pat = text.substring(at, at + m);      // pattern copied from the text: >=1 true match
                    gen = "Random(" + (4242L + n) + "), alphabet abcd, pattern = text[n/3, n/3+m)";
                } else {
                    text = "a".repeat(n);
                    pat = "a".repeat(m - 1) + "b";         // almost matches everywhere, never matches
                    gen = "text a^n, pattern a^(m-1)b";
                }
                Map<String, Object> in = req(text, pat);
                List<Integer> ref = oracle(text, pat);
                for (int ai = 0; ai < 3; ai++) {
                    boolean ok = asInts(algos[ai].run(in)).equals(ref);
                    for (int w = 0; w < WARM; w++) algos[ai].run(in);
                    double[] t = new double[RUNS];
                    for (int run = 0; run < RUNS; run++) {
                        long t0 = System.nanoTime();
                        for (int k = 0; k < REPS; k++) algos[ai].run(in);
                        t[run] = (System.nanoTime() - t0) / 1e3 / REPS;
                    }
                    double[] s = t.clone();
                    Arrays.sort(s);
                    System.out.printf(Locale.ROOT, "|%s|%d|%d|%s|%s|%.1f|%.1f|%.1f|%.1f|%s (%d starts)|%n",
                            kind, n, m, gen, names[ai], t[0], t[1], t[2], s[1], ok ? "yes, = reference" : "NO", ref.size());
                }
            }
        }
    }
}
