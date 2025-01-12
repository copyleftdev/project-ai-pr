## 1. Basic Syntax

```bash
grep [OPTIONS] PATTERN [FILE...]
```

- **PATTERN**: A (basic) regular expression unless using extended mode (e.g., with `-E`).
- **FILE...**: One or more files to be searched. If no files are specified, **grep** reads from standard input.

### Common Variants

- **grep**: Uses Basic Regular Expressions (BRE) by default.
- **egrep** (or `grep -E`): Uses Extended Regular Expressions (ERE).  
- **fgrep** (or `grep -F`): Interprets pattern as a fixed string, not a regex.

> **POSIX Note**: The official POSIX standard only specifies **grep** with basic regex. Using `-E` for extended syntax and `-F` for fixed strings are allowed as extensions but are widely supported.

---

## 2. Pattern Basics

### 2.1. Anchors
- `^` : Match start of line
- `$` : Match end of line

Example:
```bash
grep "^abc" file.txt
```
Search lines starting with **abc**.

### 2.2. Special Characters (BRE)
- `.` : Match any single character (except newline in most implementations)
- `[ ]` : Match any single character within brackets
- `[^ ]` : Match any single character **not** in brackets
- `*` : Match **zero or more** of the preceding element

> **POSIX Tip**: In basic regex, `+`, `?`, and `|` are not available unless escaped or used in ERE mode (`-E`).  
> - `\+` : Match one or more (BRE)  
> - `\?` : Match zero or one (BRE)  
> - `\|` : Alternation (OR) (BRE)

### 2.3. Extended Regex (ERE)
When using `grep -E` or `egrep`, you get:
- `+` : One or more
- `?` : Zero or one
- `|` : Alternation (OR)
- `()` : Grouping without backslash

Example ERE:
```bash
grep -E "(abc|xyz)+" file.txt
```
Matches lines containing one or more occurrences of either `abc` or `xyz`.

---

## 3. Common Options

### 3.1. Matching Options
- **-i** : Ignore case
- **-v** : Invert match (show lines **not** matching)
- **-x** : Match whole lines only (line must match the pattern entirely)
- **-F** : Interpret pattern as a fixed string (no regex)
- **-E** : Use Extended Regular Expressions

#### Example
```bash
grep -i "hello" file.txt       # case-insensitive match
grep -v "ERROR" logfile.txt    # lines without "ERROR"
grep -x "foobar" file.txt      # lines that are exactly "foobar"
grep -F "literal string" file.txt
```

### 3.2. Output Control
- **-n** : Prefix each matching line with the line number
- **-l** : Print only names of files with matches, not the lines
- **-L** : Print only names of files **without** matches
- **-c** : Print only a count of matching lines
- **-H** : Print file name with each match (on by default when searching multiple files)
- **-h** : Do not print file names
- **-s** : Suppress error messages about nonexistent or unreadable files

#### Example
```bash
grep -n "pattern" file.txt       # line numbers
grep -l "TODO" *.c               # just file names that have "TODO"
grep -L "TODO" *.c               # file names that don't have "TODO"
grep -c "foobar" file1 file2     # count matches in each file
```

### 3.3. Context Control
*(Not strictly defined in older POSIX specs, but typically available in modern grep)*  
- **-A N** : Print **N** lines **After** each match  
- **-B N** : Print **N** lines **Before** each match  
- **-C N** : Print **N** lines of context (before & after) for each match

#### Example
```bash
grep -C 2 "ERROR" logfile.txt    # 2 lines before & after
grep -B 3 "Segmentation" syslog  # 3 lines before
grep -A 1 "TODO" mycode.c        # 1 line after
```

### 3.4. File Recursion
*(This is not strictly in POSIX, but supported by many `grep` implementations.)*  
- **-r or -R** : Recursively search directories for matches
- **--exclude** : Exclude files/directories that match a pattern
- **--include** : Search only files that match a pattern

#### Example
```bash
# Recursively search for "main" in all .c and .h files
grep -r --include='*.{c,h}' "main" src/

# Recursively search all files but exclude *.md
grep -r --exclude='*.md' "TODO" .
```

---

## 4. Basic vs Extended Regular Expressions

| Feature               | Basic (BRE)        | Extended (ERE)             |
|-----------------------|---------------------|-----------------------------|
| `.`                   | Any single char     | Same                        |
| `[...]`              | Character class     | Same                        |
| `[^...]`             | Negated char class  | Same                        |
| `*`                   | Zero or more        | Same                        |
| `\+`                  | One or more         | `+` (no backslash)          |
| `\?`                  | Zero or one         | `?` (no backslash)          |
| `\|`                  | Alternation (OR)    | `|` (no backslash)          |
| `\(`, `\)`           | Grouping            | `(`, `)` (no backslash)     |

**Examples:**

- **BRE**: `grep "fo\+bar" file.txt` matches `foobar`, `foooobar`, etc.  
- **ERE**: `grep -E "fo+bar" file.txt` does the same.

---

## 5. Useful Patterns & Tricks

1. **Search for lines beginning with a digit**:
   ```bash
   grep '^[0-9]' file.txt
   ```
2. **Search for lines ending with a period**:
   ```bash
   grep '\.$' file.txt
   ```
3. **Match lines containing either 'cat' or 'dog' (BRE)**:
   ```bash
   grep "cat\|dog" file.txt
   ```
   *(ERE: `grep -E "cat|dog" file.txt`)*
4. **Search for an empty line**:
   ```bash
   grep '^$' file.txt
   ```
5. **Count matches across multiple files**:
   ```bash
   grep -c "TODO" *.txt
   ```
6. **Show line numbers with matches**:
   ```bash
   grep -n "ERROR" logfile.txt
   ```
7. **Search ignoring case**:
   ```bash
   grep -i "hello" file.txt
   ```
8. **Invert search (find lines that do *not* match)**:
   ```bash
   grep -v "WARN" logfile.txt
   ```

---

## 6. Performance Tips

1. **Fixed-String Search** (`-F`):  
   If you don’t need regex power, `grep -F` is often faster (implementation-dependent).

2. **Small Pattern Files** (`-f file`):  
   If you have many patterns to match, store them in a file and use `-f`.

3. **Binary Data** (`-a` or `-I` in some implementations):  
   Forcibly treat files as text, preventing some greps from bailing on binary matches.  
   *Not strictly POSIX but widely available.*

---

## 7. Quick Reference Table

| **Option**    | **Meaning**                                         |
|---------------|-----------------------------------------------------|
| `-i`          | Case-insensitive search                              |
| `-v`          | Invert the match                                    |
| `-c`          | Print only count of matching lines                  |
| `-n`          | Show line numbers for matches                       |
| `-l`          | Show filenames with matches                         |
| `-L`          | Show filenames without matches                      |
| `-h`          | Hide filename from output                           |
| `-H`          | Always show filename in output                      |
| `-s`          | Silent mode (suppress error messages)               |
| `-x`          | Force pattern to match entire line                  |
| `-F`          | Pattern is a fixed string, not a regex              |
| `-E`          | Use extended regex (like `egrep`)                   |
| `-f FILE`     | Take patterns from a file                           |
| `-A NUM`      | Print NUM lines after a match                       |
| `-B NUM`      | Print NUM lines before a match                      |
| `-C NUM`      | Print NUM lines before & after a match              |
| `-r / -R`     | Recursive search through directories (not POSIX)    |
| `--exclude`   | Exclude files by pattern (extension)                |
| `--include`   | Include only files matching pattern                 |

---

## 8. Common Workflows

1. **Searching inside compressed logs** (using a pipe):
   ```bash
   zcat /var/log/messages*.gz | grep "somepattern"
   ```
2. **Combining with `find` for custom recursion** (POSIX-friendly way):
   ```bash
   find . -type f -exec grep "pattern" {} +
   ```
3. **Filtering system logs**:
   ```bash
   tail -f /var/log/syslog | grep --line-buffered "ERROR"
   ```
4. **Multiple patterns** (store them in a file):
   ```bash
   grep -f patterns.txt biglogfile
   ```

---

# Final Words

- **Know Your Implementation**: While **grep** is standardized by POSIX, many options (like `-r`, `-A`, `-B`, `-C`) are widespread extensions.  
- **When in Doubt**: Stick to the core options (`-i`, `-v`, `-c`, `-n`, etc.) and basic/extended regex constructs that are guaranteed across Unix-like systems.  
- **Extended vs Basic**: Use `grep -E` (or `egrep`) if you need plus signs (`+`), question marks (`?`), or alternation without escaping.  

This covers the main use cases and commands you’ll rely on for effective text searching with **grep** in a POSIX-compliant manner (plus a few commonly available extensions). Happy searching!