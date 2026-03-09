# Starters

A collection of beginner Python scripts written while working through **Learn Python the Hard Way** by Zed Shaw. These were my first programs — written on March 6, 2026 — covering the fundamentals of printing, variables, math, string formatting, escape characters, and user input.

Nothing here is complex. That's the point. Every concept practiced in these scripts is a building block that shows up in every larger project I've built since.

Built by **GhostWhoWalkz** — follow the journey from trailer park kid, to air force pilot, to burnt out trial attorney teaching herself to code.
- GitHub: https://www.github.com/GhostWhoWalkz67
- Blog: https://forgottenfieldnotes.blogspot.com/

---

## How to Run Any of These

All scripts require only Python 3 — no libraries, no installs, no dependencies of any kind.

**Install Python 3 if you don't have it (macOS):**
```bash
brew install python
```

**Run any script:**
```bash
python3 scriptname.py
```

That's it.

---

## The Scripts

### `first.py`
**Concept: Basic printing**

The classic Hello World and nothing more. Seven `print()` statements, each outputting a line of text. The very first thing you learn — how to make Python say something.

```bash
python3 first.py
```

---

### `moreprint.py`
**Concept: String repetition and string concatenation**

Prints a nursery rhyme, then demonstrates two things: repeating a string using the `*` operator (`"." * 10` prints ten dots in a row), and building a word by storing individual letters as variables and joining them with `+`. Spells out "Cheese" and "Burger" one character at a time.

```bash
python3 moreprint.py
```

---

### `printprint.py`
**Concept: String formatting with `%r`**

Introduces the `%r` format specifier — a way to insert values into a string template. The same formatter is used to print integers, strings, booleans, the formatter string itself, and even a short poem. Shows that `%r` works with any data type.

```bash
python3 printprint.py
```

---

### `printprintprint.py`
**Concept: Lists and multi-line strings**

Creates two lists — all seven days of the week and all twelve months of the year — and prints them. Also demonstrates triple-quoted strings (`"""`) which let you write text across multiple lines without any special characters.

```bash
python3 printprintprint.py
```

---

### `escape.py`
**Concept: Escape characters**

Demonstrates the most common escape sequences in Python strings — `\t` for tab indentation, `\n` for a new line, `\\` for a literal backslash, and `"""` triple quotes for multi-line strings. Uses cat-themed variable names straight from the textbook.

```bash
python3 escape.py
```

---

### `varname.py`
**Concept: Variables and math**

A carpool calculator. Stores numbers in named variables (cars, drivers, passengers) and uses basic arithmetic to figure out how many empty cars there will be, total carpool capacity, and average passengers per car. First real example of variables doing useful work.

```bash
python3 varname.py
```

---

### `morvar.py`
**Concept: Mixed variable types and string interpolation**

Stores personal details — name, age, height, weight, eye color, hair color, teeth status — as variables of different types (strings and integers) and prints them out in natural sentences. Also demonstrates adding numeric variables together inline inside a print statement.

```bash
python3 morvar.py
```

---

### `farmcount.py`
**Concept: Math operators and boolean expressions**

A farm-themed math exercise. Demonstrates arithmetic operators including addition, subtraction, multiplication, division, and modulo (`%`). Then introduces boolean expressions — comparing values with `<`, `>`, `>=`, and `<=` — and shows that Python prints `True` or `False` as the result.

```bash
python3 farmcount.py
```

---

### `askq.py`
**Concept: User input**

The first interactive script. Asks the user three questions — age, height, and weight — using `input()` to capture their responses, stores each answer in a variable, and prints a summary sentence using `%r` string formatting. First example of a program that responds to the person running it.

```bash
python3 askq.py
```

---

## Concepts Covered Across This Folder

| Concept | Files |
|---------|-------|
| `print()` basics | `first.py`, `moreprint.py` |
| String repetition (`*`) | `moreprint.py` |
| String concatenation (`+`) | `moreprint.py` |
| Format strings (`%r`) | `printprint.py`, `askq.py` |
| Lists | `printprintprint.py` |
| Triple-quoted strings (`"""`) | `printprintprint.py`, `escape.py` |
| Escape characters (`\t`, `\n`, `\\`) | `escape.py` |
| Variables (strings and integers) | `varname.py`, `morvar.py` |
| Arithmetic operators | `varname.py`, `farmcount.py` |
| Boolean expressions | `farmcount.py` |
| User input (`input()`) | `askq.py` |

---

## No Dependencies Required

Every script in this folder uses only Python's built-in capabilities. No `pip install`, no Homebrew packages, no external libraries of any kind. If Python 3 is installed, everything here runs.
