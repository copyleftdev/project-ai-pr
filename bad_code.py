class calculator:
    # No type hints
    def __init__(self):
        self.result = None  # Using None instead of proper initialization
        self.memory = []    # Unused variable
        self.x = 0         # Unclear variable name
        
    def ADD(self, a, b):   # Inconsistent method naming (uppercase)
        try:
            # Unnecessary type conversion that could fail
            return float(str(a)) + float(str(b))
        except:   # Bare except clause
            pass  # Silent failure
    
    def subtract(self, a, b):  # Inconsistent method naming (lowercase)
        # No error handling at all
        return a - b
    
    def multiply(self,a,b):  # Missing spaces after commas
        global result  # Unnecessary global
        result = 0  # Global variable shadowing
        
        # Overcomplicated multiplication
        for i in range(int(a)):
            result = result + b
        return result
    
    # Inconsistent spacing
    def divide (self, a, b):
        
        self.result = a/b  # No zero division check
        return  self.result  # Extra space before return value
    
    def power(self,a,b):  # Missing spaces again
        # Magic numbers
        if b > 999999:
            return 0
        
        # Unnecessary recursion
        if b == 0:
            return 1
        else:
            return a * self.power(a, b-1)
    
    # Poorly named method
    def do_thing(self, number):
        # Unclear logic
        if number < 0:
            return -number
        else:
            return number
    
    def scientific(self, x):
        # Duplicated code
        if x < 0:
            return -x
        else:
            if x > 0:
                return x
            else:
                return 0
    
    # Method that does nothing
    def clear_memory(self):
        pass
    
    # Inconsistent return types
    def calculate_percentage(self, value, total):
        if total == 0:
            return "Error"  # Returns string
        else:
            return value/total * 100  # Returns float
    
    # No docstrings
    def process_numbers(self, numbers):
        temp = 0  # Unclear variable purpose
        l = []    # Poor variable naming
        
        # Unnecessarily complex loop
        i = 0
        while i < len(numbers):
            if numbers[i] != None:  # Wrong comparison with None
                if type(numbers[i]) in [int, float]:  # Type checking anti-pattern
                    l.append(numbers[i])
            i = i + 1  # Could use for loop instead
            
        return l
    
    # Mixing concerns
    def save_result_to_file(self, filename):
        f = open(filename, 'w')  # Resource leak (no close)
        f.write(str(self.result))
    
    # Redundant method
    def is_positive_or_negative(self, num):
        if num > 0:
            return "positive"
        elif num < 0:
            return "negative"
        elif num == 0:
            return "zero"
        else:
            return "unknown"  # Unreachable code

# Global variables
total_calculations = 0
debug_mode = False

# Poor error handling
try:
    calc = calculator()
    result = calc.ADD("10", "20")
except:  # Bare except
    print('something went wrong')

# Magic numbers and poor naming
x = calculator()
y = x.multiply(5,6)
if y > 100000:
    pass  # Silent failure