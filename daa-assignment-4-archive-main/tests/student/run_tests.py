#!/usr/bin/env python3
"""Own tests for Assignment 4 (Java).

Usage (from repository root):  python tests/student/run_tests.py
Compiles Java/source into Java/build (same flags as tools/run.py), sends JSON-lines
batches to `java Main`, and checks every answer against *independent* oracles written
here (brute force on small inputs, simple reference code on large ones).
Exit code 0 = all passed. A log is printed to stdout.
"""
import itertools
import json
import pathlib
import random
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / 'Java' / 'source'
BUILD = ROOT / 'Java' / 'build'
PRINTABLE = ''.join(chr(c) for c in range(32, 127))


def build():
    BUILD.mkdir(exist_ok=True)
    subprocess.run(['javac', '--release', '17', '-encoding', 'UTF-8', '-d', str(BUILD),
                    *map(str, sorted(SRC.glob('*.java')))], check=True, timeout=60)


def run(requests, timeout=20):
    data = ''.join(json.dumps(r, separators=(',', ':')) + '\n' for r in requests)
    t0 = time.perf_counter()
    res = subprocess.run(['java', '-Xmx384m', '-cp', str(BUILD), 'Main'], input=data,
                         capture_output=True, text=True, encoding='utf-8', timeout=timeout)
    dt = time.perf_counter() - t0
    assert res.returncode == 0, res.stderr[:2000]
    lines = res.stdout.splitlines()
    assert len(lines) == len(requests), f'{len(lines)} lines for {len(requests)} requests'
    return [json.loads(l) for l in lines], dt


# ----------------------------------------------------------------------------- oracles
def is_subseq(s, t):
    it = iter(t)
    return all(c in it for c in s)


def lcs_len_bruteforce(a, b):
    """Longest subsequence of a (by subset enumeration) that is also a subsequence of b."""
    best = 0
    for mask in range(1 << len(a)):
        s = ''.join(a[i] for i in range(len(a)) if mask >> i & 1)
        if len(s) > best and is_subseq(s, b):
            best = len(s)
    return best


def merge_bruteforce(sizes):
    """Minimum cost over ALL orders of adjacent merges (memoised on the block tuple)."""
    from functools import lru_cache

    @lru_cache(None)
    def go(blocks):
        if len(blocks) <= 1:
            return 0
        return min(blocks[i] + blocks[i + 1] + go(blocks[:i] + (blocks[i] + blocks[i + 1],) + blocks[i + 2:])
                   for i in range(len(blocks) - 1))
    return go(tuple(sizes))


def check_merge_plan(sizes, plan, cost):
    blocks = [(i, i) for i in range(len(sizes))]
    total = 0
    for l, k, r in plan:
        if (l, k) not in blocks:
            return False
        j = blocks.index((l, k))
        if j + 1 >= len(blocks) or blocks[j + 1] != (k + 1, r):
            return False
        blocks[j:j + 2] = [(l, r)]
        total += sum(sizes[l:r + 1])
    return len(plan) == max(0, len(sizes) - 1) and total == cost and len(blocks) <= 1


def mwis_bruteforce(n, w, edges):
    best = 0
    for mask in range(1 << n):
        if any(mask >> u & 1 and mask >> v & 1 for u, v in edges):
            continue
        best = max(best, sum(w[i] for i in range(n) if mask >> i & 1))
    return best


def random_tree(n, rng, chain=False):
    edges = []
    for v in range(1, n):
        u = v - 1 if chain else rng.randrange(v)
        edges.append([u, v] if rng.random() < .5 else [v, u])
    perm = list(range(n))
    rng.shuffle(perm)                       # relabel so that vertex 0 is not always the root
    edges = [[perm[u], perm[v]] for u, v in edges]
    rng.shuffle(edges)
    return edges


def tree_ok(req, ans, expected):
    sel = ans['selected']
    chosen = set(sel)
    return (len(chosen) == len(sel) and all(0 <= v < req['n'] for v in sel)
            and not any(u in chosen and v in chosen for u, v in req['edges'])
            and sum(req['weights'][v] for v in sel) == ans['weight'] == expected)


def search_oracle(text, pat):
    return [i for i in range(len(text) + 1) if text.startswith(pat, i)]


def suffix_oracle(text):
    n = len(text)
    sa = sorted(range(n), key=lambda i: text[i:])
    lcp = [0] * n
    for r in range(1, n):
        a, b = sa[r - 1], sa[r]
        h = 0
        while a + h < n and b + h < n and text[a + h] == text[b + h]:
            h += 1
        lcp[r] = h
    return sa, lcp


def suffix_oracle_doubling(text):
    """Different algorithm (tuple-sort doubling) for large n, plus plain-LCP via rank array."""
    n = len(text)
    rank = [ord(c) for c in text]
    k = 1
    while True:
        key = [(rank[i], rank[i + k] if i + k < n else -1) for i in range(n)]
        sa = sorted(range(n), key=key.__getitem__)
        new = [0] * n
        for r in range(1, n):
            new[sa[r]] = new[sa[r - 1]] + (key[sa[r]] != key[sa[r - 1]])
        rank = new
        if rank[sa[-1]] == n - 1:
            break
        k *= 2
    lcp = [0] * n
    inv = [0] * n
    for r, s in enumerate(sa):
        inv[s] = r
    h = 0
    for i in range(n):
        if inv[i]:
            j = sa[inv[i] - 1]
            while i + h < n and j + h < n and text[i + h] == text[j + h]:
                h += 1
            lcp[inv[i]] = h
            h = max(h - 1, 0)
        else:
            h = 0
    return sa, lcp


def aho_oracle(patterns, texts):
    return [[sum(t.startswith(p, i) for i in range(len(t))) for p in patterns] for t in texts]


# ----------------------------------------------------------------------------- harness
FAILS = []
COUNT = 0


def expect(cond, name, detail=''):
    global COUNT
    COUNT += 1
    if not cond:
        FAILS.append(name)
        print(f'FAIL {name} {detail}'[:600])


def rstr(rng, n, alpha):
    return ''.join(rng.choice(alpha) for _ in range(n))


def test_lcs(rng):
    reqs, exps = [], []
    fixed = [('', ''), ('', 'abc'), ('abc', ''), ('tea_time', 'team'), ('axbyc', 'abc'), ('ABC', 'BAC'),
             ('aaaa', 'aa'), ('abcdef', 'fedcba'), ('Aa Bb', 'aA bB'), ('x', 'x'), ('x', 'y')]
    for a, b in fixed:
        reqs.append({'task': 'lcs', 'a': a, 'b': b})
    for _ in range(150):
        a, b = rstr(rng, rng.randint(0, 9), 'ab c'), rstr(rng, rng.randint(0, 9), 'ab c')
        reqs.append({'task': 'lcs', 'a': a, 'b': b})
    ans, _ = run(reqs)
    for r, a in zip(reqs, ans):
        exp = lcs_len_bruteforce(r['a'], r['b'])
        s = a['sequence']
        expect(a['length'] == exp == len(s) and is_subseq(s, r['a']) and is_subseq(s, r['b']),
               'lcs small', json.dumps(r))


def test_merge(rng):
    reqs = [{'task': 'merge', 'sizes': s} for s in
            ([], [5], [0, 0, 0], [2, 3, 4], [1, 1, 1, 1], [10 ** 9] * 3, [5, 1, 1, 5], [0, 7, 0, 7, 0])]
    for _ in range(150):
        reqs.append({'task': 'merge', 'sizes': [rng.choice([0, 1, 2, 3, 10, 1000]) for _ in range(rng.randint(0, 7))]})
    ans, _ = run(reqs)
    for r, a in zip(reqs, ans):
        exp = merge_bruteforce(r['sizes'])
        expect(a['cost'] == exp and check_merge_plan(r['sizes'], a['plan'], a['cost']), 'merge small', json.dumps(r))
    # the dominant cost: 200 blocks of 10^9
    big = {'task': 'merge', 'sizes': [10 ** 9] * 200}
    (a,), dt = run([big])
    expect(check_merge_plan(big['sizes'], a['plan'], a['cost']) and a['cost'] > 2 ** 32, 'merge large cost')
    # equal blocks: balanced tree cost = sum over levels; independent oracle via heap-free formula
    # (n equal blocks of size s: optimal = s * sum of the Huffman-like depth -> compare with O(n^3) python DP)
    sizes = [rng.randint(0, 10 ** 9) for _ in range(60)]
    n = len(sizes)
    pre = [0]
    for x in sizes:
        pre.append(pre[-1] + x)
    f = [[0] * n for _ in range(n)]
    for ln in range(2, n + 1):
        for l in range(n - ln + 1):
            r = l + ln - 1
            f[l][r] = min(f[l][k] + f[k + 1][r] for k in range(l, r)) + pre[r + 1] - pre[l]
    (a,), _ = run([{'task': 'merge', 'sizes': sizes}])
    expect(a['cost'] == f[0][n - 1] and check_merge_plan(sizes, a['plan'], a['cost']), 'merge n=60 vs python DP')


def test_tree(rng):
    reqs, exps = [], []
    reqs.append({'task': 'tree', 'n': 0, 'weights': [], 'edges': []}); exps.append(0)
    reqs.append({'task': 'tree', 'n': 1, 'weights': [-3], 'edges': []}); exps.append(0)
    reqs.append({'task': 'tree', 'n': 1, 'weights': [7], 'edges': []}); exps.append(7)
    reqs.append({'task': 'tree', 'n': 3, 'weights': [4, 9, 6], 'edges': [[0, 1], [1, 2]]}); exps.append(10)
    reqs.append({'task': 'tree', 'n': 3, 'weights': [-4, -1, -5], 'edges': [[0, 1], [1, 2]]}); exps.append(0)
    reqs.append({'task': 'tree', 'n': 2, 'weights': [5, 5], 'edges': [[0, 1]]}); exps.append(5)
    for _ in range(200):
        n = rng.randint(1, 12)
        w = [rng.randint(-5, 9) for _ in range(n)]
        reqs.append({'task': 'tree', 'n': n, 'weights': w, 'edges': random_tree(n, rng, rng.random() < .3)})
        exps.append(None)
    for r, e in zip(reqs, exps):
        if e is None:
            e = mwis_bruteforce(r['n'], r['weights'], r['edges'])
        r['_e'] = e
    ans, _ = run([{k: v for k, v in r.items() if k != '_e'} for r in reqs])
    for r, a in zip(reqs, ans):
        expect(tree_ok(r, a, r['_e']), 'tree small', json.dumps(r)[:200])


def test_tree_large(rng):
    n = 100000
    # deep chain (would overflow a recursive DFS), weights 1e9 -> sum up to 5e13 (> 32 bit)
    chain = {'task': 'tree', 'n': n, 'weights': [10 ** 9] * n, 'edges': [[i, i + 1] for i in range(n - 1)]}
    # random tree with mixed weights; oracle: independent iterative DP using parent array + topological order
    edges = random_tree(n, rng)
    w = [rng.randint(-10 ** 9, 10 ** 9) for _ in range(n)]
    star = {'task': 'tree', 'n': n, 'weights': [1] + [-1] * (n - 1), 'edges': [[0, i] for i in range(1, n)]}
    rand = {'task': 'tree', 'n': n, 'weights': w, 'edges': edges}
    ans, dt = run([chain, rand, star])
    expect(tree_ok(chain, ans[0], (n // 2) * 10 ** 9), 'tree chain 1e5')
    expect(tree_ok(star, ans[2], 1), 'tree star 1e5')
    # reference DP for rand
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v); adj[v].append(u)
    par = [-1] * n
    order = [0]
    seen = [False] * n; seen[0] = True
    for v in order:
        for u in adj[v]:
            if not seen[u]:
                seen[u] = True; par[u] = v; order.append(u)
    tk, sk = list(w), [0] * n
    for v in reversed(order):
        if par[v] >= 0:
            tk[par[v]] += sk[v]; sk[par[v]] += max(tk[v], sk[v])
    expect(tree_ok(rand, ans[1], max(tk[0], sk[0])), 'tree random 1e5')
    print(f'  tree n=1e5 x3 in one batch: {dt:.2f}s')


def test_search(rng):
    fixed = [('', ''), ('ab', ''), ('', 'a'), ('a', 'aaa'), ('aaaaa', 'aaa'), ('abababa', 'aba'), ('A a A', 'A'),
             ('abdj', 'ab'), ('bcek', 'bc'), ('Hello, World! hello', 'hello'), ('x y  z', '  '), ('aaaa', 'aa')]
    reqs = []
    for text, pat in fixed:
        for t in ('naive', 'kmp', 'rk'):
            reqs.append({'task': t, 'text': text, 'pattern': pat})
    for _ in range(300):
        alpha = rng.choice(['a', 'ab', 'abc', 'ab '])
        text, pat = rstr(rng, rng.randint(0, 25), alpha), rstr(rng, rng.randint(0, 5), alpha)
        for t in ('naive', 'kmp', 'rk'):
            reqs.append({'task': t, 'text': text, 'pattern': pat})
    ans, _ = run(reqs)
    for r, a in zip(reqs, ans):
        expect(a['positions'] == search_oracle(r['text'], r['pattern']), 'search small', json.dumps(r))
    # all printable chars, base-31 / mod-101 collisions: brute-force-find many colliding strings
    def h(s):
        v = 0
        for c in s:
            v = (v * 31 + ord(c)) % 101
        return v
    reqs = []
    for _ in range(200):
        pat = rstr(rng, rng.randint(1, 4), PRINTABLE)
        text = ''.join(rng.choice(PRINTABLE) if rng.random() < .7 else pat for _ in range(60))
        for t in ('naive', 'kmp', 'rk'):
            reqs.append({'task': t, 'text': text, 'pattern': pat})
    ans, _ = run(reqs)
    for r, a in zip(reqs, ans):
        expect(a['positions'] == search_oracle(r['text'], r['pattern']), 'search printable', json.dumps(r)[:200])
    expect(h('ab') == h('dj') == 75, 'hash fact ab/dj = 75')


def test_search_large(rng):
    n = 200000
    cases = []
    cases.append({'text': 'a' * n, 'pattern': 'a' * 100000})                      # many overlaps, deep fallback
    cases.append({'text': 'ab' * (n // 2), 'pattern': 'ab' * 50000})
    cases.append({'text': rstr(rng, n, 'ab'), 'pattern': rstr(rng, 17, 'ab')})
    cases.append({'text': 'a' * (n - 1) + 'b', 'pattern': 'a' * 99999 + 'b'})
    cases.append({'text': 'x' * n, 'pattern': ''})                                  # n+1 boundaries
    reqs = [{'task': 'kmp', **c} for c in cases]
    ans, dt = run(reqs)
    # independent oracle: Z-function-free approach using str.find loop (overlap-aware)
    for c, a in zip(cases, ans):
        exp, i = [], c['text'].find(c['pattern'])
        if c['pattern'] == '':
            exp = list(range(len(c['text']) + 1))
        else:
            while i != -1:
                exp.append(i); i = c['text'].find(c['pattern'], i + 1)
        expect(a['positions'] == exp, 'kmp large')
    print(f'  kmp n=2e5 x5 in one batch: {dt:.2f}s')
    # rk and naive at their maximum domains
    rk = [{'task': 'rk', 'text': 'a' * 10000, 'pattern': 'a' * 2000},              # 8001 candidates x 2000 chars = 1.6e7
          {'task': 'rk', 'text': rstr(rng, 10000, PRINTABLE), 'pattern': rstr(rng, 2000, PRINTABLE)},
          {'task': 'rk', 'text': rstr(rng, 10000, 'ab'), 'pattern': rstr(rng, 3, 'ab')}]
    ans, dt = run(rk)
    for r, a in zip(rk, ans):
        exp, i = [], r['text'].find(r['pattern'])
        while i != -1:
            exp.append(i); i = r['text'].find(r['pattern'], i + 1)
        expect(a['positions'] == exp, 'rk large')
    print(f'  rk n=1e4, worst candidate load: {dt:.2f}s')
    nv = [{'task': 'naive', 'text': 'a' * 3000, 'pattern': 'a' * 1500},
          {'task': 'naive', 'text': 'a' * 3000, 'pattern': 'a' * 1499 + 'b'}]
    ans, dt = run(nv)
    expect(ans[0]['positions'] == list(range(1501)) and ans[1]['positions'] == [], 'naive large')
    print(f'  naive n=3000 worst case: {dt:.2f}s')


def test_suffix(rng):
    fixed = ['', 'a', '$', 'banana', 'aaaa', 'caba', 'abcd', 'abab', 'mississippi', 'a a a', 'zyx', 'aab' * 5]
    texts = fixed + [rstr(rng, rng.randint(0, 30), rng.choice(['a', 'ab', 'abc', PRINTABLE])) for _ in range(300)]
    reqs = [{'task': 'suffix', 'text': t} for t in texts]
    ans, _ = run(reqs)
    for t, a in zip(texts, ans):
        sa, lcp = suffix_oracle(t)
        mx = max(lcp, default=0)
        rep = a['repeated']
        occ = sum(t.startswith(rep, i) for i in range(len(t))) if rep else 0
        expect(a['sa'] == sa and a['lcp'] == lcp and len(rep) == mx and (mx == 0 or occ >= 2),
               'suffix small', repr(t))


def test_suffix_large(rng):
    n = 50000
    texts = [rstr(rng, n, 'ab'), 'a' * n, rstr(rng, n, PRINTABLE), ('abc' * n)[:n], ('ab' * 100 + 'c') * (n // 201) + 'a' * (n % 201)]
    reqs = [{'task': 'suffix', 'text': t} for t in texts]
    ans, dt = run(reqs)
    for t, a in zip(texts, ans):
        sa, lcp = suffix_oracle_doubling(t)
        mx = max(lcp)
        rep = a['repeated']
        ok = (a['sa'] == sa and a['lcp'] == lcp and len(rep) == mx)
        if rep:
            ok = ok and t.count(rep) >= 1 and sum(1 for i in range(len(t)) if t.startswith(rep, i)) >= 2 if len(t) < 5000 else ok
        expect(ok, 'suffix large', t[:20])
    print(f'  suffix n=5e4 x5 in one batch: {dt:.2f}s')


def test_aho(rng):
    fixed = [
        ([], ['a', '']), (['a'], []), (['a', 'aa', 'a'], ['aaa', '', 'aaa']), (['cat', 'at'], ['cat', 'cat']),
        (['he', 'she', 'he'], ['sheshe', 'sheshe', '']), (['a'], ['']), ([' ', '  '], ['a  b ']),
        (['abc', 'bc', 'c', 'abcd'], ['abcabcd']),
    ]
    reqs = [{'task': 'aho', 'patterns': p, 'texts': t} for p, t in fixed]
    for _ in range(200):
        alpha = rng.choice(['a', 'ab', 'abc'])
        pats = [rstr(rng, rng.randint(1, 4), alpha) for _ in range(rng.randint(0, 6))]
        texts = [rstr(rng, rng.randint(0, 20), alpha) for _ in range(rng.randint(0, 4))]
        reqs.append({'task': 'aho', 'patterns': pats, 'texts': texts})
    ans, _ = run(reqs)
    for r, a in zip(reqs, ans):
        expect(a['counts'] == aho_oracle(r['patterns'], r['texts']), 'aho small', json.dumps(r)[:200])


def test_aho_large(rng):
    # dense: 'a'-chain dictionary, 1e4 patterns a^1..a^~440 (total length <= 1e5) + duplicates, 100 texts of 2000 'a'
    pats = ['a' * k for k in range(1, 440)]
    pats += ['a'] * 10
    while sum(map(len, pats)) < 99000:
        pats.append('a' * rng.randint(1, 50))
    pats = pats[:10000]
    assert sum(map(len, pats)) <= 100000
    texts = ['a' * 2000 for _ in range(100)]
    req1 = {'task': 'aho', 'patterns': pats, 'texts': texts}
    # 10000 patterns of length ~10, random over small alphabet, 100 texts
    pats2 = [rstr(rng, rng.randint(1, 10), 'abc') for _ in range(10000)]
    while sum(map(len, pats2)) > 100000:
        pats2.pop()
    texts2 = [rstr(rng, 2000, 'abc') for _ in range(100)]
    req2 = {'task': 'aho', 'patterns': pats2, 'texts': texts2}
    ans, dt = run([req1, req2])
    # oracle for req1: count of a^k in a^L is max(0, L-k+1)
    exp1 = [[max(0, 2000 - len(p) + 1) for p in pats] for _ in texts]
    expect(ans[0]['counts'] == exp1, 'aho dense')
    # oracle for req2: dictionary of (pattern -> count) via sliding hash map of all substrings up to length 10
    from collections import Counter
    ok = True
    for t, row in zip(texts2, ans[1]['counts']):
        c = Counter(t[i:i + L] for L in range(1, 11) for i in range(len(t) - L + 1))
        if row != [c[p] for p in pats2]:
            ok = False
    expect(ok, 'aho random large')
    print(f'  aho (10^4 patterns, 100 texts x 2000) x2 in one batch: {dt:.2f}s')
    big = {'task': 'aho', 'patterns': ['ab' * 5] * 10000, 'texts': ['ab' * 1000] * 100}
    (a,), dt = run([big])
    expect(a['counts'] == [[996] * 10000 for _ in range(100)], 'aho duplicates')
    print(f'  aho 10^4 duplicate patterns: {dt:.2f}s')
    long1 = {'task': 'aho', 'patterns': ['b' * 100000], 'texts': ['b' * 200000]}
    (a,), dt = run([long1])
    expect(a['counts'] == [[100001]], 'aho single long pattern')
    print(f'  aho single 1e5 pattern, 2e5 text: {dt:.2f}s')


def test_mixed_state(rng):
    """Consecutive requests of different tasks in ONE process: no stale state."""
    base = [{'task': 'merge', 'sizes': [1, 2, 3, 4]}, {'task': 'aho', 'patterns': ['a'], 'texts': ['aa']},
            {'task': 'suffix', 'text': 'banana'}, {'task': 'aho', 'patterns': ['b'], 'texts': ['aa', 'b']},
            {'task': 'lcs', 'a': 'abc', 'b': 'ac'}, {'task': 'tree', 'n': 2, 'weights': [1, 2], 'edges': [[0, 1]]},
            {'task': 'rk', 'text': 'abdj', 'pattern': 'dj'}, {'task': 'kmp', 'text': 'aaa', 'pattern': 'aa'},
            {'task': 'naive', 'text': 'aaa', 'pattern': ''}, {'task': 'merge', 'sizes': []}]
    single = [run([r])[0][0] for r in base]
    both, _ = run(base + base[::-1] + base)
    n = len(base)
    expect(both[:n] == single and both[n:2 * n] == single[::-1] and both[2 * n:] == single, 'mixed state reset')


def main():
    build()
    rng = random.Random(20261108)
    t0 = time.time()
    for fn in (test_lcs, test_merge, test_tree, test_search, test_suffix, test_aho, test_mixed_state,
               test_tree_large, test_search_large, test_suffix_large, test_aho_large):
        before = len(FAILS)
        c0 = COUNT
        fn(rng)
        print(f'{"PASS" if len(FAILS) == before else "FAIL"} {fn.__name__} ({COUNT - c0} checks)')
    print(f'total checks: {COUNT}, failures: {len(FAILS)}, wall time {time.time() - t0:.1f}s')
    return 1 if FAILS else 0


if __name__ == '__main__':
    sys.exit(main())
