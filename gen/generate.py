#!/usr/bin/env python3
"""Regenerate RE2 test results for test-cases/* with known options."""

import json, os, sys

import re2

TEST_CASES_DIR = "test-cases"
RESULTS_DIR = "test-results/re2"

def make_opts(name: str) -> re2.Options:
    opts = re2.Options()
    if "FoldCase" in name:
        opts.case_sensitive = False
    is_utf8 = "UTF8" in name or "InterestingUTF8" in name
    opts.encoding = re2.Options.Encoding.UTF8 if is_utf8 else re2.Options.Encoding.LATIN1
    return opts


def run_re2(pattern, input, opts, anchored, longest):
    lopts = re2.Options()
    lopts.case_sensitive = opts.case_sensitive
    lopts.encoding = opts.encoding
    lopts.longest_match = longest

    if opts.encoding == re2.Options.Encoding.LATIN1:
        try:
            pat = pattern.encode("latin-1")
            inp = input.encode("latin-1")
        except UnicodeEncodeError:
            return []
    else:
        pat, inp = pattern, input

    try:
        m = re2.fullmatch(pat, inp, lopts) if anchored else re2.search(pat, inp, lopts)
        if not m:
            return []
        result = []
        for i in range(len(m.groups()) + 1):  # group 0 + captures
            result += [m.start(i), m.end(i)]
        # match log2json: all -1 → [] (no match)
        if all(x == -1 for x in result):
            return []
        return result
    except Exception as e:
        print(f'ERROR: {e}')
        raise e
        return []

def main() -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)

    for fname in sorted(os.listdir(TEST_CASES_DIR)):
        if not fname.endswith(".json"):
            continue

        path = os.path.join(TEST_CASES_DIR, fname)
        with open(path) as f:
            tc = json.load(f)

        opts = make_opts(fname)
        results = []

        for pattern in tc["regexs"]:
            row = []
            for s in tc["strs"]:
                cols = [
                    run_re2(pattern, s, opts, anchored, longest)
                    for anchored, longest in [
                        (True, False),   # 0: anchored
                        (False, False),  # 1: unanchored
                        (True, True),    # 2: anchored longest
                        (False, True),   # 3: unanchored longest
                    ]
                ]
                row.append(cols)
            results.append(row)

        out_path = os.path.join(RESULTS_DIR, fname)
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)
        print(
            f"Generated {fname} "
            f"({len(tc['regexs'])} × {len(tc['strs'])})"
        )

if __name__ == "__main__":
    main()
