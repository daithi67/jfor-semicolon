# jfor-semi

A compact interpreter for **Johnson’s semicolon FOR loop**, written in Python.  
This toy language supports two loop styles side by side:

## Counter (ALGOL/BASIC style)

```jfor
for i = 1 to 5 by 2 do
    print i
end
```

## Iterator

```jfor
for w in ["Hello","Bonjour","Hola"] do
    print w + " World!"
end
```

## Johnson’s semicolon FOR (C-style)

```jfor
for (j = 0; j < 5; j = j + 1) do
    print j
end
```

## While-style (omit init/step)

```jfor
x = 3
for (; x > 0; ) do
    print x
    x = x - 1
end
```

## Usage

Run the demo program:

```bash
python jfor_semicolons.py demo
```

Run your own script:

```bash
python jfor_semicolons.py myprog.jfor
```

---

MIT License
