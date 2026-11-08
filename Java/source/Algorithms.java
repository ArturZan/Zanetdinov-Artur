import java.util.*;

/** Implementations of all A4 algorithms. docs/guide/CONTRACTS.md defines each field and limit. */
public final class Algorithms {

    private static String str(Map<String, Object> in, String key) {
        return (String) in.get(key);
    }

    private static int toInt(Object o) {
        return ((Number) o).intValue();
    }

    private static long toLong(Object o) {
        return ((Number) o).longValue();
    }

    // ------------------------------------------------------------------ Part 1: LCS

    /** Prefix DP: dp[i][j] = LCS length of a[0..i) and b[0..j). */
    static Map<String, Object> lcs(Map<String, Object> input) {
        String a = str(input, "a"), b = str(input, "b");
        int n = a.length(), m = b.length();
        Map<String, Object> out = new LinkedHashMap<>();
        if (n == 0 || m == 0) {
            out.put("length", 0L);
            out.put("sequence", "");
            return out;
        }
        int[][] dp = new int[n + 1][m + 1];
        for (int i = 1; i <= n; i++) {
            char ca = a.charAt(i - 1);
            for (int j = 1; j <= m; j++) {
                if (ca == b.charAt(j - 1)) dp[i][j] = dp[i - 1][j - 1] + 1;
                else dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
        int len = dp[n][m];
        char[] res = new char[len];
        int i = n, j = m, p = len;
        while (i > 0 && j > 0) {
            if (a.charAt(i - 1) == b.charAt(j - 1)) {
                res[--p] = a.charAt(i - 1);
                i--;
                j--;
            } else if (dp[i - 1][j] >= dp[i][j - 1]) {
                i--;
            } else {
                j--;
            }
        }
        out.put("length", (long) len);
        out.put("sequence", new String(res));
        return out;
    }

    // ------------------------------------------------------------------ Part 2: ordered merging

    /** All state is passed explicitly: split table in, plan out. Nothing is kept between calls. */
    private static void emitMerge(int[][] split, List<Object> plan, int l, int r) {
        if (l >= r) return;
        int k = split[l][r];
        emitMerge(split, plan, l, k);        // children first (chronological order)
        emitMerge(split, plan, k + 1, r);
        plan.add(Arrays.asList((long) l, (long) k, (long) r));
    }

    /** Interval DP: f[l][r] = min over k of f[l][k] + f[k+1][r] + sum(l..r). */
    static Map<String, Object> merge(Map<String, Object> input) {
        List<?> list = (List<?>) input.get("sizes");
        int n = list.size();
        Map<String, Object> out = new LinkedHashMap<>();
        if (n <= 1) {
            out.put("cost", 0L);
            out.put("plan", new ArrayList<Object>());
            return out;
        }
        long[] pre = new long[n + 1];
        for (int i = 0; i < n; i++) pre[i + 1] = pre[i] + toLong(list.get(i));
        long[][] f = new long[n][n];
        int[][] split = new int[n][n];
        for (int len = 2; len <= n; len++) {
            for (int l = 0; l + len - 1 < n; l++) {
                int r = l + len - 1;
                long best = Long.MAX_VALUE;
                int bk = l;
                for (int k = l; k < r; k++) {
                    long c = f[l][k] + f[k + 1][r];
                    if (c < best) {
                        best = c;
                        bk = k;
                    }
                }
                f[l][r] = best + pre[r + 1] - pre[l];
                split[l][r] = bk;
            }
        }
        List<Object> plan = new ArrayList<>();
        emitMerge(split, plan, 0, n - 1);     // recursion depth <= n-1 <= 199
        out.put("cost", f[0][n - 1]);
        out.put("plan", plan);
        return out;
    }

    // ------------------------------------------------------------------ Part 3: tree MWIS

    /** Iterative take/skip DP over a BFS order; reconstruction top-down. */
    static Map<String, Object> tree(Map<String, Object> input) {
        int n = toInt(input.get("n"));
        Map<String, Object> out = new LinkedHashMap<>();
        if (n == 0) {
            out.put("weight", 0L);
            out.put("selected", new ArrayList<Object>());
            return out;
        }
        List<?> wl = (List<?>) input.get("weights");
        List<?> el = (List<?>) input.get("edges");
        long[] w = new long[n];
        for (int i = 0; i < n; i++) w[i] = toLong(wl.get(i));
        int[] head = new int[n], nxt = new int[2 * el.size()], to = new int[2 * el.size()];
        Arrays.fill(head, -1);
        int ec = 0;
        for (Object eo : el) {
            List<?> e = (List<?>) eo;
            int u = toInt(e.get(0)), v = toInt(e.get(1));
            to[ec] = v; nxt[ec] = head[u]; head[u] = ec++;
            to[ec] = u; nxt[ec] = head[v]; head[v] = ec++;
        }
        int[] parent = new int[n], order = new int[n];
        Arrays.fill(parent, -1);
        boolean[] seen = new boolean[n];
        int qh = 0, qt = 0;
        order[qt++] = 0;
        seen[0] = true;
        while (qh < qt) {
            int v = order[qh++];
            for (int e = head[v]; e != -1; e = nxt[e]) {
                int u = to[e];
                if (!seen[u]) {
                    seen[u] = true;
                    parent[u] = v;
                    order[qt++] = u;
                }
            }
        }
        long[] take = new long[n], skip = new long[n];
        for (int i = 0; i < n; i++) take[i] = w[i];
        for (int idx = qt - 1; idx >= 0; idx--) {   // children before parents
            int v = order[idx];
            int p = parent[v];
            if (p >= 0) {
                take[p] += skip[v];
                skip[p] += Math.max(take[v], skip[v]);
            }
        }
        boolean[] chosen = new boolean[n];
        List<Object> selected = new ArrayList<>();
        for (int idx = 0; idx < qt; idx++) {         // parents before children
            int v = order[idx];
            int p = parent[v];
            boolean parentTaken = p >= 0 && chosen[p];
            if (!parentTaken && take[v] > skip[v]) {
                chosen[v] = true;
                selected.add((long) v);
            }
        }
        out.put("weight", Math.max(take[0], skip[0]));
        out.put("selected", selected);
        return out;
    }

    // ------------------------------------------------------------------ Part 4: string search

    private static Map<String, Object> positions(List<Object> pos) {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("positions", pos);
        return out;
    }

    private static List<Object> allBoundaries(int n) {
        List<Object> pos = new ArrayList<>(n + 1);
        for (int i = 0; i <= n; i++) pos.add((long) i);
        return pos;
    }

    static Map<String, Object> naive(Map<String, Object> input) {
        String t = str(input, "text"), p = str(input, "pattern");
        int n = t.length(), m = p.length();
        if (m == 0) return positions(allBoundaries(n));
        List<Object> pos = new ArrayList<>();
        for (int s = 0; s + m <= n; s++) {
            int j = 0;
            while (j < m && t.charAt(s + j) == p.charAt(j)) j++;
            if (j == m) pos.add((long) s);
        }
        return positions(pos);
    }

    /** pi[i] = length of the longest proper prefix of p[0..i] that is also its suffix. */
    static Map<String, Object> kmp(Map<String, Object> input) {
        String t = str(input, "text"), p = str(input, "pattern");
        int n = t.length(), m = p.length();
        if (m == 0) return positions(allBoundaries(n));
        List<Object> pos = new ArrayList<>();
        if (m > n) return positions(pos);
        int[] pi = new int[m];
        for (int i = 1, k = 0; i < m; i++) {
            while (k > 0 && p.charAt(i) != p.charAt(k)) k = pi[k - 1];
            if (p.charAt(i) == p.charAt(k)) k++;
            pi[i] = k;
        }
        int k = 0;
        for (int i = 0; i < n; i++) {
            while (k > 0 && (k == m || t.charAt(i) != p.charAt(k))) k = pi[k - 1];
            if (t.charAt(i) == p.charAt(k)) k++;
            if (k == m) pos.add((long) (i - m + 1));
        }
        return positions(pos);
    }

    /** Polynomial rolling hash, base 31, modulus 101; every equal-hash window is verified. */
    static Map<String, Object> rk(Map<String, Object> input) {
        final int BASE = 31, MOD = 101;
        String t = str(input, "text"), p = str(input, "pattern");
        int n = t.length(), m = p.length();
        if (m == 0) return positions(allBoundaries(n));
        List<Object> pos = new ArrayList<>();
        if (m > n) return positions(pos);
        long pow = 1;                                   // BASE^(m-1) mod MOD
        for (int i = 1; i < m; i++) pow = pow * BASE % MOD;
        long hp = 0, ht = 0;
        for (int i = 0; i < m; i++) {
            hp = (hp * BASE + p.charAt(i)) % MOD;
            ht = (ht * BASE + t.charAt(i)) % MOD;
        }
        for (int s = 0; ; s++) {
            if (hp == ht) {
                int j = 0;
                while (j < m && t.charAt(s + j) == p.charAt(j)) j++;
                if (j == m) pos.add((long) s);
            }
            if (s + m >= n) break;
            ht = ((ht - t.charAt(s) * pow) % MOD + MOD) % MOD;   // drop leftmost, normalise
            ht = (ht * BASE + t.charAt(s + m)) % MOD;             // append next char
        }
        return positions(pos);
    }

    // ------------------------------------------------------------------ Part 5: suffix array + Kasai

    /** Prefix doubling with counting sort on rank pairs (O(n log n)), then Kasai LCP. */
    static Map<String, Object> suffix(Map<String, Object> input) {
        String t = str(input, "text");
        int n = t.length();
        Map<String, Object> out = new LinkedHashMap<>();
        if (n == 0) {
            out.put("sa", new ArrayList<Object>());
            out.put("lcp", new ArrayList<Object>());
            out.put("repeated", "");
            return out;
        }
        int[] sa = new int[n], rank = new int[n], tmp = new int[n], sa2 = new int[n];
        int size = Math.max(n, 128) + 1;
        int[] cnt = new int[size];
        for (int i = 0; i < n; i++) cnt[t.charAt(i)]++;
        for (int i = 1; i < 128; i++) cnt[i] += cnt[i - 1];
        for (int i = n - 1; i >= 0; i--) sa[--cnt[t.charAt(i)]] = i;
        int classes = 1;
        rank[sa[0]] = 0;
        for (int i = 1; i < n; i++) {
            if (t.charAt(sa[i]) != t.charAt(sa[i - 1])) classes++;
            rank[sa[i]] = classes - 1;
        }
        for (int k = 1; classes < n; k <<= 1) {
            int p = 0;
            for (int i = n - k; i < n; i++) if (i >= 0) sa2[p++] = i;   // second key = "empty"
            for (int i = 0; i < n; i++) if (sa[i] >= k) sa2[p++] = sa[i] - k;
            Arrays.fill(cnt, 0, classes + 1, 0);
            for (int i = 0; i < n; i++) cnt[rank[i]]++;
            for (int i = 1; i < classes; i++) cnt[i] += cnt[i - 1];
            for (int i = n - 1; i >= 0; i--) sa[--cnt[rank[sa2[i]]]] = sa2[i];
            tmp[sa[0]] = 0;
            int c = 1;
            for (int i = 1; i < n; i++) {
                int x = sa[i - 1], y = sa[i];
                int x2 = x + k < n ? rank[x + k] : -1;
                int y2 = y + k < n ? rank[y + k] : -1;
                if (rank[x] != rank[y] || x2 != y2) c++;
                tmp[y] = c - 1;
            }
            int[] sw = rank; rank = tmp; tmp = sw;
            classes = c;
        }
        // Kasai: lcp[r] = LCP(sa[r-1], sa[r]); h drops by at most 1 between consecutive text positions.
        int[] lcp = new int[n];
        int h = 0;
        for (int i = 0; i < n; i++) {
            int r = rank[i];
            if (r > 0) {
                int j = sa[r - 1];
                while (i + h < n && j + h < n && t.charAt(i + h) == t.charAt(j + h)) h++;
                lcp[r] = h;
                if (h > 0) h--;
            } else {
                h = 0;
            }
        }
        int best = 0, bi = -1;
        for (int i = 1; i < n; i++) if (lcp[i] > best) { best = lcp[i]; bi = i; }
        List<Object> saL = new ArrayList<>(n), lcpL = new ArrayList<>(n);
        for (int i = 0; i < n; i++) {
            saL.add((long) sa[i]);
            lcpL.add((long) lcp[i]);
        }
        out.put("sa", saL);
        out.put("lcp", lcpL);
        out.put("repeated", best == 0 ? "" : t.substring(sa[bi], sa[bi] + best));
        return out;
    }

    // ------------------------------------------------------------------ Part 6: Aho-Corasick

    /** Trie + failure links (full goto automaton); counts by visit propagation along failure links. */
    static Map<String, Object> aho(Map<String, Object> input) {
        final int ALPHA = 95;   // printable ASCII 32..126 (local constant, not state)
        List<?> pats = (List<?>) input.get("patterns");
        List<?> texts = (List<?>) input.get("texts");
        int p = pats.size();
        int total = 1;
        for (Object o : pats) total += ((String) o).length();
        int[] go = new int[total * ALPHA];
        Arrays.fill(go, -1);
        int[] term = new int[p];            // dictionary position -> terminal state (duplicates share)
        int states = 1;
        for (int i = 0; i < p; i++) {
            String s = (String) pats.get(i);
            int v = 0;
            for (int j = 0; j < s.length(); j++) {
                int c = s.charAt(j) - 32;
                if (go[v * ALPHA + c] == -1) go[v * ALPHA + c] = states++;
                v = go[v * ALPHA + c];
            }
            term[i] = v;
        }
        int[] fail = new int[states], order = new int[states];
        int qh = 0, qt = 0;
        for (int c = 0; c < ALPHA; c++) {
            int u = go[c];
            if (u == -1) go[c] = 0;
            else { fail[u] = 0; order[qt++] = u; }
        }
        while (qh < qt) {
            int v = order[qh++];
            for (int c = 0; c < ALPHA; c++) {
                int u = go[v * ALPHA + c];
                if (u == -1) go[v * ALPHA + c] = go[fail[v] * ALPHA + c];
                else {
                    fail[u] = go[fail[v] * ALPHA + c];
                    order[qt++] = u;
                }
            }
        }
        List<Object> rows = new ArrayList<>();
        long[] visit = new long[states];
        for (Object to : texts) {
            String t = (String) to;
            Arrays.fill(visit, 0);                    // independent text: fresh counts
            int v = 0;
            for (int i = 0; i < t.length(); i++) {
                v = go[v * ALPHA + (t.charAt(i) - 32)];
                visit[v]++;
            }
            for (int i = qt - 1; i >= 0; i--) {       // BFS order reversed: deeper states first
                int u = order[i];
                visit[fail[u]] += visit[u];
            }
            long[] row = new long[p];
            for (int i = 0; i < p; i++) row[i] = visit[term[i]];
            rows.add(row);
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("counts", rows);
        return out;
    }
}
