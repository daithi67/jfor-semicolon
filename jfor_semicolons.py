#!/usr/bin/env python3
# jfor_semicolons.py — tiny Johnson-style FOR interpreter (both ALGOL-ish and C-ish)
# Features:
#   for i = A to B [by S] do ... end        # inclusive, S defaults to 1 (can be negative)
#   for v in EXPR do ... end                 # iterate over any iterable
#   for (init; cond; step) do ... end        # C/Johnson semicolon form; any of the 3 parts may be empty
#   print EXPR,  NAME = EXPR                 # simple statements inside blocks
#
# NOTE: Expressions are evaluated via eval() with empty globals and a shared env dict.
#       This is a toy; don't feed it untrusted code.

import re
from typing import List, Dict, Any, Tuple, Optional

# --- regexes for the three for-forms ---
RX_FOR_COUNTER = re.compile(r"^\s*for\s+([A-Za-z_]\w*)\s*=\s*(.+?)\s+to\s+(.+?)(?:\s+by\s+(.+?))?\s+do\s*$", re.I)
RX_FOR_ITER    = re.compile(r"^\s*for\s+([A-Za-z_]\w*)\s+in\s+(.+?)\s+do\s*$", re.I)
RX_FOR_CSTYLE  = re.compile(r"^\s*for\s*\(\s*(.*?)\s*;\s*(.*?)\s*;\s*(.*?)\s*\)\s+do\s*$", re.I)
RX_END         = re.compile(r"^\s*end\s*$", re.I)
RX_PRINT       = re.compile(r"^\s*print\s+(.+)\s*$", re.I)
RX_ASSIGN      = re.compile(r"^\s*([A-Za-z_]\w*)\s*=\s*(.+)\s*$")

class JFOR:
    def __init__(self):
        self.env: Dict[str, Any] = {}

    # safe-ish eval: no builtins, only our env; allow common names if you want (e.g., range)
    def _eval(self, expr: str) -> Any:
        return eval(expr, {}, self.env)

    def _exec_lines(self, lines: List[str], i: int) -> int:
        """Execute from lines[i], return next index to run after finishing this (sub)block."""
        while i < len(lines):
            line = lines[i].rstrip()

            # blank or comment
            if not line.strip() or line.lstrip().startswith("#"):
                i += 1
                continue

            # --- for: counter form ---
            m = RX_FOR_COUNTER.match(line)
            if m:
                var, start_s, end_s, step_s = m.groups()
                start = self._eval(start_s)
                end   = self._eval(end_s)
                step  = self._eval(step_s) if step_s else 1
                if step == 0:
                    raise ValueError("by step cannot be 0")
                # collect block
                block, i = self._collect_block(lines, i + 1)
                # run loop (inclusive end)
                if step > 0:
                    n = start
                    while n <= end:
                        self.env[var] = n
                        self._run_block(block)
                        n += step
                else:
                    n = start
                    while n >= end:
                        self.env[var] = n
                        self._run_block(block)
                        n += step
                continue

            # --- for: iterator form ---
            m = RX_FOR_ITER.match(line)
            if m:
                var, expr = m.groups()
                it = self._eval(expr)
                block, i = self._collect_block(lines, i + 1)
                for v in it:
                    self.env[var] = v
                    self._run_block(block)
                continue

            # --- for: C/semicolon form ---
            m = RX_FOR_CSTYLE.match(line)
            if m:
                init_s, cond_s, step_s = m.groups()

                # parse init/step as optional assignment lines (or empty)
                def do_assign(s: str):
                    s = s.strip()
                    if not s:
                        return None
                    am = RX_ASSIGN.match(s)
                    if not am:
                        # allow expression-only init/step too
                        return ("expr", s)
                    return ("assign", am.group(1), am.group(2))

                init = do_assign(init_s)
                step = do_assign(step_s)
                cond = cond_s.strip()

                block, i = self._collect_block(lines, i + 1)

                # run: init once
                if init:
                    if init[0] == "assign":
                        name, rhs = init[1], init[2]
                        self.env[name] = self._eval(rhs)
                    else:
                        self._eval(init[1])

                # loop: while cond (or True if empty)
                while True:
                    ok = True if cond == "" else bool(self._eval(cond))
                    if not ok:
                        break
                    self._run_block(block)
                    if step:
                        if step[0] == "assign":
                            name, rhs = step[1], step[2]
                            self.env[name] = self._eval(rhs)
                        else:
                            self._eval(step[1])
                continue

            # --- end (should be handled by _collect_block) ---
            if RX_END.match(line):
                # returning here lets outer _collect_block finish
                return i

            # --- print ---
            m = RX_PRINT.match(line)
            if m:
                val = self._eval(m.group(1))
                print(val)
                i += 1
                continue

            # --- assignment ---
            m = RX_ASSIGN.match(line)
            if m:
                self.env[m.group(1)] = self._eval(m.group(2))
                i += 1
                continue

            raise SyntaxError(f"Unrecognized line {i+1}: {line}")

        return i

    def _collect_block(self, lines: List[str], i: int) -> Tuple[List[str], int]:
        """Collect lines until matching 'end' (no nesting tracking needed beyond counting)."""
        block: List[str] = []
        depth = 1
        while i < len(lines):
            if RX_FOR_COUNTER.match(lines[i]) or RX_FOR_ITER.match(lines[i]) or RX_FOR_CSTYLE.match(lines[i]):
                depth += 1
            if RX_END.match(lines[i]):
                depth -= 1
                if depth == 0:
                    return block, i + 1
            block.append(lines[i])
            i += 1
        raise SyntaxError("missing 'end'")

    def _run_block(self, block_lines: List[str]):
        j = 0
        while j < len(block_lines):
            j = self._exec_lines(block_lines, j) + 1  # jump past any 'end' consumed

    def run(self, src: str):
        lines = src.splitlines()
        i = 0
        while i < len(lines):
            i = self._exec_lines(lines, i) + 1

# --- CLI demo ---
DEMO = """# Demo: both FOR styles

print "Counter (ALGOL/BASIC style):"
for i = 1 to 5 by 2 do
    print i
end

print "Iterator:"
for w in ["Hello","Bonjour","Hola"] do
    print w + " World!"
end

print "Johnson/C-style semicolon loop:"
for (j = 0; j < 5; j = j + 1) do
    print j
end

print "While-style using semicolons (omit init/step):"
x = 3
for (; x > 0; ) do
    print x
    x = x - 1
end
"""

if __name__ == "__main__":
    import sys
    vm = JFOR()
    if len(sys.argv) == 2 and sys.argv[1] == "demo":
        vm.run(DEMO)
    elif len(sys.argv) == 2:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            vm.run(f.read())
    else:
        print("Usage:")
        print("  python jfor_semicolons.py demo")
        print("  python jfor_semicolons.py yourfile.jfor")
