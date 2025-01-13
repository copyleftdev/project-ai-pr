# Ubuntu Grep Best Practices Cheatsheet

## Basic Syntax
```bash
grep [options] pattern [file...]
```

## Essential Options
| Option | Description | Example |
|--------|-------------|---------|
| `-i` | Case insensitive search | `grep -i "error" log.txt` |
| `-r` or `-R` | Recursive search | `grep -r "TODO" /path/to/dir` |
| `-n` | Show line numbers | `grep -n "pattern" file.txt` |
| `-w` | Match whole words only | `grep -w "class" *.java` |
| `-l` | Show only filenames | `grep -l "pattern" *.txt` |
| `-c` | Count matches | `grep -c "error" log.txt` |
| `-v` | Invert match (show non-matching) | `grep -v "^#" config.txt` |
| `-E` | Extended regex support | `grep -E "word1|word2" file.txt` |

## Best Practices

### 1. Using Context Options
```bash
# Show 3 lines before match
grep -B 3 "error" log.txt

# Show 3 lines after match
grep -A 3 "error" log.txt

# Show 3 lines before and after
grep -C 3 "error" log.txt
```

### 2. Color Output
```bash
# Enable color output
grep --color=auto "pattern" file.txt

# Add to ~/.bashrc for permanent color:
export GREP_OPTIONS='--color=auto'
```

### 3. Excluding Directories
```bash
# Exclude specific directories
grep -r "pattern" --exclude-dir={.git,node_modules,vendor} .

# Exclude by pattern
grep -r "pattern" --exclude-dir=".*" .
```

### 4. File Type Filtering
```bash
# Search only specific file types
grep -r "pattern" --include="*.php" .

# Multiple file types
grep -r "pattern" --include="*.{js,jsx,ts,tsx}" .
```

### 5. Advanced Pattern Matching

#### Regular Expressions
```bash
# Match start of line
grep "^start" file.txt

# Match end of line
grep "end$" file.txt

# Match any single character
grep "h.t" file.txt

# Match zero or more occurrences
grep "wo*rd" file.txt

# Match specific number of occurrences
grep "o\{2\}" file.txt
```

#### Extended Regular Expressions (-E or egrep)
```bash
# Match either pattern
grep -E "pattern1|pattern2" file.txt

# Match one or more occurrences
grep -E "o+" file.txt

# Match zero or one occurrence
grep -E "colou?r" file.txt
```

### 6. Performance Optimization

#### For Large Files
```bash
# Stop after first match
grep -m 1 "pattern" large_file.txt

# Use binary grep for faster search
grep -a "pattern" binary_file

# Count matches without printing
grep -c "pattern" large_file.txt
```

#### For Multiple Files
```bash
# Process files in parallel
parallel "grep 'pattern' {}" ::: *.txt

# Use find with grep
find . -type f -exec grep "pattern" {} +
```

### 7. Error Handling
```bash
# Suppress error messages
grep -s "pattern" /path/to/files/*

# Show only error messages
grep -q "pattern" file.txt 2>&1 >/dev/null
```

### 8. Common Use Cases

#### Finding IP Addresses
```bash
grep -E "([0-9]{1,3}\.){3}[0-9]{1,3}" log.txt
```

#### Finding Email Addresses
```bash
grep -E "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}" file.txt
```

#### Finding URLs
```bash
grep -E "https?://[A-Za-z0-9./]+" file.txt
```

## Tips for Daily Use

1. **Use ripgrep (rg) for Better Performance**
   - Install: `sudo apt install ripgrep`
   - Usage: `rg "pattern"`

2. **Create Aliases for Common Operations**
   ```bash
   # Add to ~/.bashrc
   alias grepjs='grep -r --include="*.js"'
   alias grepphp='grep -r --include="*.php"'
   alias greperr='grep -i -r "error|warning|critical"'
   ```

3. **Use Process Substitution**
   ```bash
   # Search in command output
   grep "pattern" <(command)
   ```

4. **Combine with Other Commands**
   ```bash
   # Find and grep
   find . -type f -name "*.log" -exec grep "error" {} +

   # Pipe with grep
   ps aux | grep "[n]ginx"
   ```

## Common Pitfalls to Avoid

1. Don't use grep without -r for directory searches
2. Avoid using GREP_OPTIONS (deprecated)
3. Remember to escape special characters in patterns
4. Don't forget to use quotes around patterns with spaces
5. Be careful with -R vs -r (symbolic links)

## Debugging Tips

1. Use `-v` to see what's being excluded
2. Use `--debug` to see detailed matching information
3. Use `-h` to suppress filenames in multi-file searches
4. Add `-n` to show line numbers for easier reference