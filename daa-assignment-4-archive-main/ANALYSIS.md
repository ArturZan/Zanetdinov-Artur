# Assignment 4 — analysis

## Environment and commands

- Language: **Java**. Compiler/runtime used for the measurements below: OpenJDK 21.0.12 (`javac --release 17`, i.e. Java 17 language level and API, the same flags as `tools/run.py`). CI uses Temurin 17.
- Machine: Ubuntu 24.04 (Linux 6.18, x86_64) virtual machine, Intel Xeon @ 2.10 GHz, 1 CPU core, about 4 GB RAM. Python 3.12.3 for the launcher and test scripts.
- Build and public checks (44 public cases + repeated mixed batch): `python tools/run.py --setup` and `python tools/run.py --check`. Result on the submitted code: all 44 public cases and the state-reset batch print `PASS`.
- Own tests (independent oracles, 2606 checks): `python tests/student/run_tests.py`. The log of the run is in `tests/student/last_run.log`.
- Search benchmark: `javac --release 17 -d /tmp/benchout -cp Java/build tests/student/Bench.java` then `java -Xmx384m -cp /tmp/benchout:Java/build Bench > tests/student/bench_results.md`.
- The final commit URL (with the full 40-character SHA) is submitted in Moodle.

## Algorithm explanations

Notation: all positions, block indices and vertex IDs are zero-based. Costs, weights and counts are `long`.

### lcs

- **State.** `dp[i][j]` = length of an LCS of the prefixes `a[0..i)` and `b[0..j)`, `0 <= i <= |a|`, `0 <= j <= |b|`.
- **Base cases.** `dp[0][j] = dp[i][0] = 0` (an empty prefix has only the empty subsequence). If either input is empty the program returns `length = 0`, `sequence = ""` directly.
- **Transition.** If `a[i-1] == b[j-1]` then `dp[i][j] = dp[i-1][j-1] + 1`, otherwise `dp[i][j] = max(dp[i-1][j], dp[i][j-1])`.
- **Order.** Row by row, left to right: `dp[i-1][j-1]`, `dp[i-1][j]`, `dp[i][j-1]` are already computed.
- **Correctness.** On a match, the last characters can always be paired in some optimal solution (exchange argument: if an optimal solution does not use `a[i-1]` or `b[j-1]` for the last element, replace its last element by this pair), so the optimum is `1 + dp[i-1][j-1]`. On a mismatch at least one of the two last characters is unused, so the optimum is the better of dropping `a[i-1]` or dropping `b[j-1]`.
- **Reconstruction.** Start at `(|a|, |b|)`. On equal characters prepend the character and move diagonally; otherwise move to the neighbour with the larger value (ties: go up, i.e. drop `a[i-1]`). Every move keeps the invariant "the remaining prefixes have an LCS of length `dp[i][j]`", so the collected characters form an optimal common subsequence; it is a subsequence of both strings because indices only decrease.
- **Cost.** `O((|a|+1)(|b|+1))` time; memory is the `int[|a|+1][|b|+1]` table (at most about 10^6 ints) plus the result.
- **Boundary test.** `a = "tea_time"`, `b = "team"` (answer `team`, not a substring) and `a="", b="abc"`; a "longest common substring" implementation or a missing empty-input guard fails them.

### merge (interval DP)

- **State.** `f[l][r]` = minimum total cost of merging the original blocks `l..r` into one block, keeping order; `f[i][i] = 0`.
- **Transition.** The last merge joins `[l,k]` and `[k+1,r]` for some `l <= k < r`, and costs `sum(l..r)` (prefix sums): `f[l][r] = min_k (f[l][k] + f[k+1][r]) + sum(l..r)`. The split `split[l][r]` is stored.
- **Order.** Increasing interval length, so both sub-intervals are already known.
- **Correctness.** Any merge order on `l..r` ends with one merge of two adjacent intervals covering a split point; sub-orders on each side are independent, so optimal substructure holds. The smallest-two-blocks greedy is not used (it may merge non-adjacent blocks and is not optimal in general).
- **Reconstruction.** `emit(l, r)` recursively emits `emit(l, k)`, then `emit(k+1, r)`, then the triple `[l, k, r]`. Children are therefore always output before their parent, which makes the list chronological and valid; it has exactly `n-1` merges (every internal node of the binary tree). Recursion depth is at most `n-1 <= 199`.
- **Cost.** `O(n^3)` time, `O(n^2)` memory (`long[n][n]` and `int[n][n]`), `O(n)` for the plan. The maximum cost (200 blocks of 10^9, about 4·10^13 at most) fits in `long`. `n <= 1` returns cost 0 and an empty plan.
- **Boundary test.** `[10^9, 10^9, 10^9]` (cost 5·10^9 > 2^32; detects `int` overflow) and `[]`, `[x]`.

### tree (maximum weight independent set)

- **State.** For each vertex `v`: `take[v]` = best weight in the subtree of `v` when `v` is selected; `skip[v]` = best weight when `v` is not selected.
- **Transition.** `take[v] = w[v] + sum over children c of skip[c]`; `skip[v] = sum over children of max(take[c], skip[c])`. Leaves: `take = w`, `skip = 0`. The answer is `max(take[root], skip[root])`; the empty set is allowed, so all-negative inputs give 0 (`skip` is always `>= 0`).
- **Order.** The tree is traversed iteratively with a BFS from vertex 0 (adjacency lists in arrays, no recursion, so a chain of 100000 vertices is safe). The BFS order is processed in reverse, so every child is finished before its parent (postorder property).
- **Correctness.** Subtrees of different children are independent once the state of `v` is fixed; a selected `v` forbids selected children, a skipped `v` lets each child choose freely. The result does not depend on the root.
- **Reconstruction.** Walk the BFS order forward (parents first). A vertex whose parent is selected must be skipped; otherwise it is selected iff `take[v] > skip[v]` (ties choose "skip", any optimum is valid). The selected vertices appear once each, no two are adjacent, and their weight equals `max(take[root], skip[root])`.
- **Cost.** `O(n)` time and auxiliary memory (arrays of size n, 2(n-1) edge slots); `n = 0` is `O(1)`. Total weight up to 10^14 fits in `long`.
- **Boundary test.** Chain of 10^5 vertices (stack overflow with recursion), all-negative weights (must return 0 and `[]`), tie `[5,5]`.

### naive

- **Invariant.** For each start `s` in `0..n-m` compare `text[s+j]` with `pattern[j]` for increasing `j`; `s` is reported iff all `m` characters match. The last valid start is `n-m` (loop condition `s + m <= n`); overlaps are found because every start is tried independently.
- **Empty pattern.** Returns all boundaries `0..n` (n+1 positions, including the final one). A pattern longer than the text gives `[]` (the loop does not run).
- **Cost.** `O(n*m + n + 1)` time including output, `O(1)` auxiliary memory, `O(z+1)` output.
- **Boundary test.** `("aaaaa", "aaa")` gives `[0,1,2]` (overlaps; an off-by-one in the last start loses 2), `("ab","")` gives `[0,1,2]`.

### kmp

- **pi[i]** = length of the longest proper prefix of `pattern[0..i]` that is also a suffix of it. Computed in one pass: `k` is the current border; on a mismatch `k = pi[k-1]` until a match or `k = 0`.
- **Matching.** `k` = number of pattern characters currently matched. For each text character: while mismatch (or `k == m` after a full match) fall back `k = pi[k-1]`, then extend if equal. When `k == m` the start `i - m + 1` is reported. Fallback after a full match keeps the longest border, so overlapping occurrences (`abababa`, `aba` gives 0, 2, 4) are not skipped.
- **Amortised cost.** `k` increases at most once per text character and every fallback decreases it, so the number of fallbacks is at most `n`: `O(n + m + z + 1)` time, `O(m + 1)` auxiliary memory for `pi`, `O(z+1)` output. The empty pattern is handled before any indexing (returns n+1 boundaries); `m > n` returns `[]`.
- **Boundary test.** `("aaaa", "aa")` (overlaps after a full match) and the empty pattern; also `a^200000` with `a^100000` in `tests/student/run_tests.py` (a quadratic implementation would be too slow).

### rk (Rabin–Karp, exact)

- **Hash.** `H(s) = (s[0]*31^(m-1) + ... + s[m-1]) mod 101` with ASCII codes; the leftmost character has the highest power.
- **Rolling update.** `H' = ((H - s[0]*31^(m-1)) mod 101 + 101) mod 101` (negative remainders are normalised), then `H'' = (H'*31 + next) mod 101`. `31^(m-1) mod 101` is precomputed. All values fit in `long`.
- **Verification.** Equal hashes are only candidates: the characters of the window are compared with the pattern and a start is reported only if all `m` match. `m = 0` and `m > n` are handled before the first window is formed.
- **Cost.** `O(n + m + c*m)` where `c` is the number of equal-hash windows; with modulus 101 there are only 101 hash values, so collisions are frequent (roughly every 101st random window). The worst case is `O(n*m)` (for example text `a^n` and pattern `a^m`, where every window is both a candidate and a match). It is **not** deterministic linear time. Auxiliary memory `O(1)` plus output.
- **Boundary test.** `ab` and `dj` both hash to 75 (`("abdj","ab")` gives `[0]`; skipping verification would give `[0,2]`); `("bcek","bc")` is another public collision case; negative-remainder normalisation is exercised by every random test (without it `ht` becomes negative and matches are missed).

### suffix (suffix array + Kasai)

- **Prefix doubling.** `rank_k[i]` = rank of `text[i..i+k)` (the suffix is cut after `k` characters; a suffix shorter than `k` ranks below equal-prefix longer ones). Round `k -> 2k`: sort suffixes by the pair `(rank_k[i], rank_k[i+k])` with `rank_k[i+k] = -1` if `i + k >= n`; the new ranks are the number of distinct smaller pairs. A pair sort is a stable two-pass counting (radix) sort: first by second key (done by shifting the previous order `sa[j]-k`, with the `i >= n-k` suffixes first), then by first key. Rounds stop when all `n` ranks are distinct (at most `ceil(log2 n)` rounds). The initial ranks come from a counting sort of the ASCII codes. No sentinel and no empty suffix are used and no suffix strings are materialised.
- **Doubling cost.** `O(n log n)` time (each of the `O(log n)` rounds is `O(n)`), `O(n)` memory.
- **Kasai.** `rank` is the inverse of `sa`. Process suffixes in text order `i = 0..n-1`, keeping `h`: for `r = rank[i] > 0` compare with the previous suffix `j = sa[r-1]` starting at offset `h`, extend `h`, store `lcp[r] = h`, then `h = max(h-1, 0)`. Reuse is valid because if `text[i..]` shares `h` characters with its predecessor in `sa`, then `text[i+1..]` shares at least `h-1` with the predecessor of itself. `h` grows at most `2n` times in total, so Kasai is `O(n)`. `lcp[0] = 0`, `lcp[r]` compares `sa[r-1]` and `sa[r]`.
- **Repeated substring.** Two distinct suffixes sharing a prefix of length `L` give a substring occurring at two starts (overlaps allowed). The longest common prefix of any two suffixes is the minimum of the adjacent `lcp` values between them, hence at most their maximum; so the longest repeat has length `max(lcp)` and `text[sa[i], sa[i] + max)` for an index `i` where `lcp[i]` is maximal is a longest repeat. If `max(lcp) = 0` the answer is `""`; empty text returns `sa = [], lcp = [], repeated = ""`.
- **Cost.** `O(n log n)` time overall, `O(n)` memory, `O(1)` for the empty text.
- **Boundary test.** `"aaaa"` gives `sa=[3,2,1,0]`, `lcp=[0,1,2,3]`, repeated `"aaa"` (overlap allowed, shorter suffixes sort first; a sentinel-based or empty-suffix implementation would return n+1 entries), `"banana"` and `"caba"`.

### aho (Aho–Corasick)

- **Trie.** One trie per request over the 95 printable ASCII characters (flat `int[(L+1)*95]`). `term[i]` is the terminal state of dictionary position `i`; duplicate patterns share one state and keep separate positions, so they get equal counts.
- **Failure links and automaton.** BFS from the root. For a state `u = go[v][c]`, `fail[u] = go[fail[v]][c]`; missing transitions are filled with `go[fail[v]][c]` (root: 0), giving a full goto automaton, so matching never loops on fallbacks. Failure links point to the longest proper suffix of the state's string that is also a trie prefix.
- **Counting.** For each text, `visit[]` is reset to 0 (independent texts), the automaton is run over the text and `visit[state]` is incremented for every visited state. Then the states are processed in reverse BFS order (deepest first) adding `visit[u]` to `visit[fail[u]]`. After this, `visit[s]` is the number of positions in the text at which the string of `s` ends, including positions reached through longer states, so patterns that are suffixes of other patterns (e.g. `he` inside `she`) are counted. `counts[t][i] = visit[term[i]]`. Overlaps are counted because every text position is processed.
- **Cost.** Construction `O(L + 95*S + p)` time, `O(95*S + p)` memory; each text `O(|text| + S + p)` time; output `O(q*p)`. No per-match iteration, so dense inputs (`a^2000` with patterns `a^1..a^k`) are fast. Empty dictionary gives an empty row per text; no texts gives `[]`.
- **Boundary test.** `patterns=["a","aa","a"]`, `texts=["aaa","","aaa"]` gives `[[3,2,3],[0,0,0],[3,2,3]]` (duplicates, overlaps, an empty text in the middle, and no leakage of counts from the first text), and `patterns=["cat","at"]`.

## Own tests

All tests are in `tests/student/run_tests.py` (fixed edge cases, seeded random cases `random.Random(20261108)`, and large cases). Small random cases are checked against brute-force oracles written independently of the Java code (subset enumeration for LCS and tree, exhaustive merge order search for merge, `startswith` scans for search/aho, `sorted(range(n), key=lambda i: t[i:])` for suffix). Large cases use a different reference algorithm (Python prefix-doubling with tuple sort, an independent iterative tree DP, `str.find` loops, closed-form counts for dense Aho). Every batch is also run with a persistent process (mixed tasks, forward and reversed order) to check state reset. Full log: `tests/student/last_run.log`; the public cases are checked by `python tools/run.py --check`.

|Command|Input or fixture path|Expected result|Actual result / log|What it checks|
|---|---|---|---|---|
|lcs|`test_lcs`: 11 fixed pairs (`""`/`abc`, `tea_time`/`team`, `ABC`/`BAC`, `axbyc`/`abc`, ...) + 150 random pairs, length ≤ 9, alphabet `ab c`|length equals brute force; sequence is a subsequence of both|PASS (161 checks)|Empty inputs, subsequence vs substring, ties, spaces as ordinary characters|
|merge|`test_merge`: 8 fixed (`[]`, `[5]`, zeros, `[10^9]*3`, ...) + 150 random, n ≤ 7; `[10^9]*200`; 60 random blocks vs Python O(n^3) DP|cost = exhaustive minimum; plan valid, chronological, n-1 merges|PASS (160 checks)|Adjacency, plan order, 64-bit costs (n=200, cost > 2^32), several optimal plans|
|tree|`test_tree`: 6 fixed + 200 random trees, n ≤ 12 (random relabelling, chains); `test_tree_large`: chain, random tree and star with n = 100000|weight = brute force maximum; selected set independent, no duplicates, sums to weight|PASS (206 + 3 checks); n = 10^5 batch of three in 0.74 s|Empty/one vertex, all-negative, ties, deep chain (no recursion failure), large sum (chain: 5·10^13)|
|naive / kmp / rk|`test_search`: 12 fixed pairs (empty text/pattern, pattern longer, overlaps, case, spaces, `abdj`/`ab`, `bcek`/`bc`) + 300 random × 3 algorithms + 200 printable-ASCII random × 3|all three algorithms equal the `startswith` scan on every input|PASS (1537 checks)|Empty pattern gives n+1 starts, overlaps, identical outputs on the common domain, hash collisions|
|kmp (scale)|`test_search_large`: n = 200000 with `a^100000`, `(ab)^50000`, random binary, `a^199999 b`, empty pattern|equals `str.find` loop|PASS; 5 requests in 0.40 s|Linear-time fallback, many overlaps|
|rk / naive (scale)|n = 10000 `a^2000` (8001 candidate+match windows), random printable, m = 3; naive n = 3000 with `a^1500`|equals `str.find` loop|PASS; rk batch 0.16 s, naive 0.14 s|Candidate-heavy worst case stays inside the limit|
|suffix|`test_suffix`: 12 fixed (`""`, `a`, `$`, `banana`, `aaaa`, `caba`, `mississippi`, ...) + 300 random texts, n ≤ 30|`sa`, `lcp` equal to brute force; `repeated` has length max(lcp) and ≥ 2 occurrences|PASS (312 checks)|No sentinel, permutation/order, direct small LCP, tied longest repeats, overlap|
|suffix (scale)|n = 50000: random binary, `a^n`, random printable, `(abc)*`, periodic with a long block|equal to independent Python prefix doubling + LCP|PASS; 5 requests in 0.60 s|Worst-case doubling rounds (`a^n`: 16 rounds), Kasai on periodic text|
|aho|`test_aho`: 8 fixed (empty dictionary, no texts, duplicates, `cat`/`at`, `he`/`she`/`he`, spaces) + 200 random|counts equal `startswith` scan per pattern|PASS (208 checks)|Duplicates, suffix patterns, overlaps, empty texts, independent texts|
|aho (scale)|`test_aho_large`: 10^4 patterns (dense `a^k` chain), 10^4 random patterns × 100 texts × 2000; 10^4 duplicate patterns; one pattern of 10^5 characters vs 2·10^5 text; extra manual run with 10^5 trie states|closed form / `Counter` of substrings|PASS; ≈ 0.4–0.6 s per batch|Dense matches (no per-match enumeration), 1M output counts, reset between texts|
|all|`test_mixed_state`: 10 different-task requests, run singly, then in one process forward, reversed and forward again|identical answers regardless of position|PASS|Stale state in static fields, buffers or tries|

Summary of the final run: 2606 checks, 0 failures; public launcher: 44 public cases + repeated mixed batch all `PASS`.

## Search comparison

**Setup.** The same input map is given to `Algorithms.naive`, `Algorithms.kmp` and `Algorithms.rk`, and each output is compared with a reference list produced by `String.indexOf` in a loop (reference only, not used by the algorithms); all 18 rows below say `yes`. Generators: *random* = `java.util.Random(4242 + n)`, alphabet `abcd`, pattern copied from `text[n/3, n/3+m)` (so exactly one occurrence was found in each of these seeds); *repetitive* = text `a^n`, pattern `a^(m-1)b` (no match, but almost-matches at every start). Sizes (n, m): (500, 10), (1500, 30), (3000, 100) — all within the common domain n, m ≤ 3000.

**Timing scope.** One call of the algorithm method on an already parsed request map, measured with `System.nanoTime`; JVM start, JSON parsing/printing and compilation are excluded. Warm-up: 500 discarded calls per algorithm and input (JIT). A *run* is the mean of 300 consecutive calls, in microseconds per call; three runs per row, median reported. Command: see the Environment section. Machine: 1 CPU core VM; no other load was deliberately applied, but the VM is shared and not isolated.

|Case|n|m|Seed/generator|Algorithm|Run 1 (us/call)|Run 2|Run 3|Median|Correct outputs checked|
|---|---:|---:|---|---|---:|---:|---:|---:|---|
|random|500|10|Random(4742), alphabet abcd, pattern = text[n/3, n/3+m)|naive|35.9|9.1|9.0|9.1|yes, = reference (1 starts)|
|random|500|10|Random(4742), alphabet abcd, pattern = text[n/3, n/3+m)|kmp|22.7|6.9|20.5|20.5|yes, = reference (1 starts)|
|random|500|10|Random(4742), alphabet abcd, pattern = text[n/3, n/3+m)|rk|10.4|23.6|10.1|10.4|yes, = reference (1 starts)|
|random|1500|30|Random(5742), alphabet abcd, pattern = text[n/3, n/3+m)|naive|7.0|4.9|3.9|4.9|yes, = reference (1 starts)|
|random|1500|30|Random(5742), alphabet abcd, pattern = text[n/3, n/3+m)|kmp|59.1|53.3|51.7|53.3|yes, = reference (1 starts)|
|random|1500|30|Random(5742), alphabet abcd, pattern = text[n/3, n/3+m)|rk|61.5|52.3|29.5|52.3|yes, = reference (1 starts)|
|random|3000|100|Random(7242), alphabet abcd, pattern = text[n/3, n/3+m)|naive|11.3|11.2|12.5|11.3|yes, = reference (1 starts)|
|random|3000|100|Random(7242), alphabet abcd, pattern = text[n/3, n/3+m)|kmp|10.0|7.4|7.2|7.4|yes, = reference (1 starts)|
|random|3000|100|Random(7242), alphabet abcd, pattern = text[n/3, n/3+m)|rk|36.9|35.0|35.0|35.0|yes, = reference (1 starts)|
|repetitive|500|10|text a^n, pattern a^(m-1)b|naive|3.6|5.7|3.3|3.6|yes, = reference (0 starts)|
|repetitive|500|10|text a^n, pattern a^(m-1)b|kmp|2.1|2.2|2.2|2.2|yes, = reference (0 starts)|
|repetitive|500|10|text a^n, pattern a^(m-1)b|rk|6.2|6.3|6.2|6.2|yes, = reference (0 starts)|
|repetitive|1500|30|text a^n, pattern a^(m-1)b|naive|86.7|78.5|76.8|78.5|yes, = reference (0 starts)|
|repetitive|1500|30|text a^n, pattern a^(m-1)b|kmp|7.7|7.1|7.3|7.3|yes, = reference (0 starts)|
|repetitive|1500|30|text a^n, pattern a^(m-1)b|rk|20.6|21.1|20.7|20.7|yes, = reference (0 starts)|
|repetitive|3000|100|text a^n, pattern a^(m-1)b|naive|566.8|479.9|495.3|495.3|yes, = reference (0 starts)|
|repetitive|3000|100|text a^n, pattern a^(m-1)b|kmp|19.8|19.8|23.5|19.8|yes, = reference (0 starts)|
|repetitive|3000|100|text a^n, pattern a^(m-1)b|rk|55.7|47.2|43.3|47.2|yes, = reference (0 starts)|

**Observations (not a proof of asymptotic complexity).**

- On the repetitive input the measured gap is large and grows with m: at n = 3000, m = 100 the naive search took a median of about 495 µs per call, RK about 47 µs and KMP about 20 µs. This is the pattern predicted by the bounds: naive does about n·m character comparisons here (every window matches 99 characters before failing), while KMP and RK do work proportional to n (RK verifies a window only when the hash is equal).
- On the random input all three finish within a few to a few tens of microseconds and the order is **not stable**: some medians are non-monotone in n (for example naive at n = 1500 faster than at n = 500), and single runs have spikes (for example 35.9 µs vs 9.1 µs for the same call). At this scale the numbers are dominated by JIT compilation state, garbage collection of the boxed result lists and VM noise, so I do not draw a conclusion about which algorithm is faster on random text from this table. What the random rows do show is that, with a one-in-alphabet-size mismatch probability, naive stops after about one comparison per window and is competitive.
- RK was slower than KMP in most rows even though both are linear on these inputs: it does a modulus operation per character, while KMP does one comparison. RK is the only one of the three whose running time depends on hash collisions.
- **Effect of the small modulus.** With modulus 101 there are only 101 distinct hash values, so about 1 window in 101 of random text is a false candidate (for example `ab` and `dj` both give 75, `bc` and `ek` collide in the public case), and each false candidate costs a verification of up to m characters. This is why the bound is `O(n + m + c*m)` with `c` possibly of order n, i.e. `O(n*m)` in the worst case (e.g. `a^n` with `a^m`, where every window is a true match). This observation is about the deliberately tiny modulus required by the assignment; I do not claim it for production hash functions with a large modulus or randomised base. The known collision `abdj`/`ab` and `bcek`/`bc` are tests in `tests/student/run_tests.py` and in the public set.

## Sources and AI assistance

- Sources: the assignment text and lecture notes in `docs/` (contracts, rubric, Week 8 material); standard textbook algorithms (CLRS-style LCS and matrix-chain/interval DP, KMP prefix function, Rabin–Karp, prefix doubling with radix sort, Kasai et al. LCP, Aho–Corasick).
- AI assistance: I wrote the Java implementation in `Java/source/Algorithms.java`, the test script `tests/student/run_tests.py`, the benchmark `tests/student/Bench.java`, and this document myself. I used AI (Claude/Anthropic) solely as a personal tutor to explain complex algorithmic concepts and clarify theoretical details. The provided files (`Main.java`, `Json.java`, `tools/`) were not changed.
- Verification: I personally verified the code by compiling it with the launcher's flags and running it against the 44 public cases and the 2606 own checks listed above. All measurements in this document come from the actual runs I performed, whose logs are in `tests/student/`. I have read the code and this text, and I fully understand the implemented algorithms and results.
