from __future__ import annotations
from typing import Union, Optional, List, Any, Final
from decimal import Decimal, InvalidOperation, getcontext
from dataclasses import dataclass
from enum import Enum, auto
import logging
import math
from abc import ABC, abstractmethod
import threading
from functools import wraps
import contextlib
import hashlib
import hmac
import os

# Configure Decimal precision
getcontext().prec = 28

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CalculatorError(Exception):
    """Base exception class for calculator errors."""
    pass

class DivisionByZeroError(CalculatorError):
    """Raised when attempting to divide by zero."""
    pass

class OverflowError(CalculatorError):
    """Raised when result exceeds maximum allowed value."""
    pass

class InvalidInputError(CalculatorError):
    """Raised when input validation fails."""
    pass

class SecurityError(CalculatorError):
    """Raised when a security check fails."""
    pass

class Operation(Enum):
    """Enumeration of supported calculator operations."""
    ADD = auto()
    SUBTRACT = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    POWER = auto()
    ROOT = auto()

@dataclass(frozen=True)
class CalculationResult:
    """Immutable class to store calculation results with metadata."""
    value: Decimal
    operation: Operation
    timestamp: float
    precision: int
    hash: str

    def verify(self) -> bool:
        """Verify the integrity of the calculation result."""
        return self.hash == self._calculate_hash()

    def _calculate_hash(self) -> str:
        """Calculate cryptographic hash of the result."""
        data = f"{self.value}{self.operation.name}{self.timestamp}{self.precision}"
        return hashlib.sha256(data.encode()).hexdigest()

class InputValidator:
    """Validates and sanitizes calculator inputs."""
    
    # Constants for input validation
    MAX_VALUE: Final[Decimal] = Decimal('1e1000')
    MIN_VALUE: Final[Decimal] = Decimal('-1e1000')
    
    @classmethod
    def validate_number(cls, value: Any) -> Decimal:
        """Validate and convert input to Decimal."""
        try:
            if isinstance(value, (int, float, str, Decimal)):
                decimal_value = Decimal(str(value))
                if not cls._is_within_bounds(decimal_value):
                    raise InvalidInputError("Value exceeds allowed range")
                return decimal_value
            raise InvalidInputError("Invalid numeric input type")
        except (InvalidOperation, ValueError) as e:
            raise InvalidInputError(f"Invalid numeric input: {e}")

    @classmethod
    def _is_within_bounds(cls, value: Decimal) -> bool:
        """Check if value is within allowed bounds."""
        return cls.MIN_VALUE <= value <= cls.MAX_VALUE

class SecurityManager:
    """Manages security aspects of calculations."""
    
    def __init__(self):
        """Initialize security manager with a secure key."""
        self._key = os.urandom(32)
        self._lock = threading.Lock()

    def secure_operation(self, func):
        """Decorator to add security measures to operations."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self._lock:
                # Verify inputs
                self._verify_inputs(args[1:])
                
                # Execute operation
                result = func(*args, **kwargs)
                
                # Sign result
                return self._sign_result(result)
        return wrapper

    def _verify_inputs(self, inputs: tuple) -> None:
        """Verify input integrity."""
        for value in inputs:
            if not isinstance(value, Decimal):
                raise SecurityError("Input verification failed")

    def _sign_result(self, result: Decimal) -> Decimal:
        """Sign calculation result."""
        signature = hmac.new(self._key, str(result).encode(), hashlib.sha256)
        logger.debug(f"Result signed with signature: {signature.hexdigest()}")
        return result

class CalculatorBase(ABC):
    """Abstract base class defining calculator interface."""
    
    @abstractmethod
    def add(self, a: Union[int, float, str, Decimal], b: Union[int, float, str, Decimal]) -> CalculationResult:
        pass

    @abstractmethod
    def subtract(self, a: Union[int, float, str, Decimal], b: Union[int, float, str, Decimal]) -> CalculationResult:
        pass

    @abstractmethod
    def multiply(self, a: Union[int, float, str, Decimal], b: Union[int, float, str, Decimal]) -> CalculationResult:
        pass

    @abstractmethod
    def divide(self, a: Union[int, float, str, Decimal], b: Union[int, float, str, Decimal]) -> CalculationResult:
        pass

class SecureCalculator(CalculatorBase):
    """Thread-safe, secure calculator implementation with comprehensive error handling."""

    def __init__(self):
        """Initialize calculator with security manager."""
        self._security_manager = SecurityManager()
        self._operation_count = 0
        self._lock = threading.Lock()
        logger.info("Secure calculator initialized")

    @contextlib.contextmanager
    def _operation_context(self, operation: Operation) -> None:
        """Context manager for calculator operations."""
        import time
        start_time = time.time()
        try:
            yield
        finally:
            with self._lock:
                self._operation_count += 1
            duration = time.time() - start_time
            logger.debug(f"{operation.name} operation completed in {duration:.4f} seconds")

    def _create_result(self, value: Decimal, operation: Operation) -> CalculationResult:
        """Create a secure calculation result."""
        import time
        result = CalculationResult(
            value=value,
            operation=operation,
            timestamp=time.time(),
            precision=getcontext().prec,
            hash=''
        )
        # Create new result with proper hash
        return CalculationResult(
            value=result.value,
            operation=result.operation,
            timestamp=result.timestamp,
            precision=result.precision,
            hash=result._calculate_hash()
        )

    @SecurityManager.secure_operation
    def add(self, a: Union[int, float, str, Decimal], b: Union[int, float, str, Decimal]) -> CalculationResult:
        """
        Securely add two numbers.
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            CalculationResult containing the sum
            
        Raises:
            InvalidInputError: If inputs are invalid
            OverflowError: If result exceeds maximum value
        """
        with self._operation_context(Operation.ADD):
            # Validate inputs
            a_dec = InputValidator.validate_number(a)
            b_dec = InputValidator.validate_number(b)
            
            # Perform calculation
            try:
                result = a_dec + b_dec
                if not InputValidator._is_within_bounds(result):
                    raise OverflowError("Addition result exceeds maximum value")
                return self._create_result(result, Operation.ADD)
            except Exception as e:
                logger.error(f"Addition failed: {e}")
                raise

    @SecurityManager.secure_operation
    def subtract(self, a: Union[int, float, str, Decimal], b: Union[int, float, str, Decimal]) -> CalculationResult:
        """Securely subtract two numbers."""
        with self._operation_context(Operation.SUBTRACT):
            a_dec = InputValidator.validate_number(a)
            b_dec = InputValidator.validate_number(b)
            
            try:
                result = a_dec - b_dec
                if not InputValidator._is_within_bounds(result):
                    raise OverflowError("Subtraction result exceeds maximum value")
                return self._create_result(result, Operation.SUBTRACT)
            except Exception as e:
                logger.error(f"Subtraction failed: {e}")
                raise

    @SecurityManager.secure_operation
    def multiply(self, a: Union[int, float, str, Decimal], b: Union[int, float, str, Decimal]) -> CalculationResult:
        """Securely multiply two numbers."""
        with self._operation_context(Operation.MULTIPLY):
            a_dec = InputValidator.validate_number(a)
            b_dec = InputValidator.validate_number(b)
            
            try:
                result = a_dec * b_dec
                if not InputValidator._is_within_bounds(result):
                    raise OverflowError("Multiplication result exceeds maximum value")
                return self._create_result(result, Operation.MULTIPLY)
            except Exception as e:
                logger.error(f"Multiplication failed: {e}")
                raise

    @SecurityManager.secure_operation
    def divide(self, a: Union[int, float, str, Decimal], b: Union[int, float, str, Decimal]) -> CalculationResult:
        """Securely divide two numbers."""
        with self._operation_context(Operation.DIVIDE):
            a_dec = InputValidator.validate_number(a)
            b_dec = InputValidator.validate_number(b)
            
            try:
                if b_dec == 0:
                    raise DivisionByZeroError("Division by zero")
                result = a_dec / b_dec
                if not InputValidator._is_within_bounds(result):
                    raise OverflowError("Division result exceeds maximum value")
                return self._create_result(result, Operation.DIVIDE)
            except Exception as e:
                logger.error(f"Division failed: {e}")
                raise

    def get_operation_count(self) -> int:
        """Safely get the total number of operations performed."""
        with self._lock:
            return self._operation_count

def main():
    """Example usage with error handling."""
    calculator = SecureCalculator()
    
    try:
        # Perform calculations
        result1 = calculator.add("123.456", "789.012")
        print(f"Addition result: {result1.value}")
        assert result1.verify(), "Result verification failed"
        
        result2 = calculator.difrom __future__ import annotations
from typing import Union, Optional, List, Any, Final
from decimal import Decimal, InvalidOperation, getcontext
from dataclasses import dataclass
from enum import Enum, auto
import logging
import math
from abc import ABC, abstractmethod
import threading
from functools import wraps
import contextlib
import hashlib
import hmac
import os

# Configure Decimal precision
getcontext().prec = 28

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CalculatorError(Exception):
    """Base exception class for calculator errors."""
    pass

class DivisionByZeroError(CalculatorError):
    """Raised when attempting to divide by zero."""
    pass

class OverflowError(CalculatorError):
    """Raised when result exceeds maximum allowed value."""
    pass

class InvalidInputError(CalculatorError):
    """Raised when input validation fails."""
    pass

class SecurityError(CalculatorError):
    """Raised when a security check fails."""
    pass

class Operation(Enum):
    """Enumeration of supported calculator operations."""
    ADD = auto()
    SUBTRACT = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    POWER = auto()
    ROOT = auto()

@dataclass(frozen=True)
class CalculationResult:
    """Immutable class to store calculation results with metadata."""
    value: Decimal
    operation: Operation
    timestamp: float
    precision: int
    hash: str

    def verify(self) -> bool:
        """Verify the integrity of the calculation result."""
        return self.hash == self._calculate_hash()

    def _calculate_hash(self) -> str:
        """Calculate cryptographic hash of the result."""
        data = f"{self.value}{self.operation.name}{self.timestamp}{self.precision}"
        return hashlib.sha256(data.encode()).hexdigest()

class InputValidator:
    """Validates and sanitizes calculator inputs."""
    
    # Constants for input validation
    MAX_VALUE: Final[Decimal] = Decimal('1e1000')
    MIN_VALUE: Final[Decimal] = Decimal('-1e1000')
    
    @classmethod
    def validate_number(cls, value: Any) -> Decimal:
        """Validate and convert input to Decimal."""
        try:
            if isinstance(value, (int, float, str, Decimal)):
                decimal_value = Decimal(str(value))
                if not cls._is_within_bounds(decimal_value):
                    raise InvalidInputError("Value exceeds allowed range")
                return decimal_value
            raise InvalidInputError("Invalid numeric input type")
        except (InvalidOperation, ValueError) as e:
            raise InvalidInputError(f"Invalid numeric input: {e}")

    @classmethod
    def _is_within_bounds(cls, value: Decimal) -> bool:
        """Check if value is within allowed bounds."""
        return cls.MIN_VALUE <= value <= cls.MAX_VALUE

class SecurityManager:
    """Manages security aspects of calculations."""
    
    def __init__(self):
        """Initialize security manager with a secure key."""
        self._key = os.urandom(32)
        self._lock = threading.Lock()

    def secure_operation(self, func):
        """Decorator to add security measures to operations."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self._lock:
                # Verify inputs
                self._verify_inputs(args[1:])
                
                # Execute operation
                result = func(*args, **kwargs)
                
                # Sign result
                return self._sign_result(result)
        return wrapper

    def _verify_inputs(self, inputs: tuple) -> None:
        """Verify input integrity."""
        for value in inputs:
            if not isinstance(value, Decimal):
                raise SecurityError("Input verification failed")

    def _sign_result(self, result: Decimal) -> Decimal:
        """Sign calculation result."""
        signature = hmac.new(self._key, str(result).encode(), hashlib.sha256)
        logger.debug(f"Result signed with signature: {signature.hexdigest()}")
        return result

class CalculatorBase(ABC):
    """Abstract base class defining calculator interface."""
    
    @abstractmethod
    def add(self, a: Union[int, float, str, Decimal], b: Union[int, float, str, Decimal]) -> CalculationResult:
        pass

    @abstractmethod
    def subtract(self, a: Union[int, float, str, Decimal], b: Union[int, float, str, Decimal]) -> CalculationResult:
        pass

    @abstractmethod
    def multiply(self, a: Union[int, float, str, Decimal], b: Union[int, float, str, Decimal]) -> CalculationResult:
        pass

    @abstractmethod
    def divide(self, a: Union[int, float, str, Decimal], b: Union[int, float, str, Decimal]) -> CalculationResult:
        pass

class SecureCalculator(CalculatorBase):
    """Thread-safe, secure calculator implementation with comprehensive error handling."""

    def __init__(self):
        """Initialize calculator with security manager."""
        self._security_manager = SecurityManager()
        self._operation_count = 0
        self._lock = threading.Lock()
        logger.info("Secure calculator initialized")

    @contextlib.contextmanager
    def _operation_context(self, operation: Operation) -> None:
        """Context manager for calculator operations."""
        import time
        start_time = time.time()
        try:
            yield
        finally:
            with self._lock:
                self._operation_count += 1
            duration = time.time() - start_time
            logger.debug(f"{operation.name} operation completed in {duration:.4f} seconds")

    def _create_result(self, value: Decimal, operation: Operation) -> CalculationResult:
        """Create a secure calculation result."""
        import time
        result = CalculationResult(
            value=value,
            operation=operation,
            timestamp=time.time(),
            precision=getcontext().prec,
            hash=''
        )
        # Create new result with proper hash
        return CalculationResult(
            value=result.value,
            operation=result.operation,
            timestamp=result.timestamp,
            precision=result.precision,
            hash=result._calculate_hash()
        )

    @SecurityManager.secure_operation
    def add(self, a: Union[int, float, str, Decimal], b: Union[int, float, str, Decimal]) -> CalculationResult:
        """
        Securely add two numbers.
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            CalculationResult containing the sum
            
        Raises:
            InvalidInputError: If inputs are invalid
            OverflowError: If result exceeds maximum value
        """
        with self._operation_context(Operation.ADD):
            # Validate inputs
            a_dec = InputValidator.validate_number(a)
            b_dec = InputValidator.validate_number(b)
            
            # Perform calculation
            try:
                result = a_dec + b_dec
                if not InputValidator._is_within_bounds(result):
                    raise OverflowError("Addition result exceeds maximum value")
                return self._create_result(result, Operation.ADD)
            except Exception as e:
                logger.error(f"Addition failed: {e}")
                raise

    @SecurityManager.secure_operation
    def subtract(self, a: Union[int, float, str, Decimal], b: Union[int, float, str, Decimal]) -> CalculationResult:
        """Securely subtract two numbers."""
        with self._operation_context(Operation.SUBTRACT):
            a_dec = InputValidator.validate_number(a)
            b_dec = InputValidator.validate_number(b)
            
            try:
                result = a_dec - b_dec
                if not InputValidator._is_within_bounds(result):
                    raise OverflowError("Subtraction result exceeds maximum value")
                return self._create_result(result, Operation.SUBTRACT)
            except Exception as e:
                logger.error(f"Subtraction failed: {e}")
                raise

    @SecurityManager.secure_operation
    def multiply(self, a: Union[int, float, str, Decimal], b: Union[int, float, str, Decimal]) -> CalculationResult:
        """Securely multiply two numbers."""
        with self._operation_context(Operation.MULTIPLY):
            a_dec = InputValidator.validate_number(a)
            b_dec = InputValidator.validate_number(b)
            
            try:
                result = a_dec * b_dec
                if not InputValidator._is_within_bounds(result):
                    raise OverflowError("Multiplication result exceeds maximum value")
                return self._create_result(result, Operation.MULTIPLY)
            except Exception as e:
                logger.error(f"Multiplication failed: {e}")
                raise

    @SecurityManager.secure_operation
    def divide(self, a: Union[int, float, str, Decimal], b: Union[int, float, str, Decimal]) -> CalculationResult:
        """Securely divide two numbers."""
        with self._operation_context(Operation.DIVIDE):
            a_dec = InputValidator.validate_number(a)
            b_dec = InputValidator.validate_number(b)
            
            try:
                if b_dec == 0:
                    raise DivisionByZeroError("Division by zero")
                result = a_dec / b_dec
                if not InputValidator._is_within_bounds(result):
                    raise OverflowError("Division result exceeds maximum value")
                return self._create_result(result, Operation.DIVIDE)
            except Exception as e:
                logger.error(f"Division failed: {e}")
                raise

    def get_operation_count(self) -> int:
        """Safely get the total number of operations performed."""
        with self._lock:
            return self._operation_count

def main():
    """Example usage with error handling."""
    calculator = SecureCalculator()
    
    try:
        # Perform calculations
        result1 = calculator.add("123.456", "789.012")
        print(f"Addition result: {result1.value}")
        assert result1.verify(), "Result verification failed"
        
        result2 = calculator.divide(100, "5")
        print(f"Division result: {result2.value}")
        assert result2.verify(), "Result verification failed"
        
    except InvalidInputError as e:
        print(f"Invalid input: {e}")
    except DivisionByZeroError as e:
        print(f"Division error: {e}")
    except OverflowError as e:
        print(f"Overflow error: {e}")
    except SecurityError as e:
        print(f"Security error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        print(f"Total operations performed: {calculator.get_operation_count()}")

if __name__ == "__main__":
    main()vide(100, "5")
        print(f"Division result: {result2.value}")
        assert result2.verify(), "Result verification failed"
        
    except InvalidInputError as e:
        print(f"Invalid input: {e}")
    except DivisionByZeroError as e:
        print(f"Division error: {e}")
    except OverflowError as e:
        print(f"Overflow error: {e}")
    except SecurityError as e:
        print(f"Security error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        print(f"Total operations performed: {calculator.get_operation_count()}")

if __name__ == "__main__":
    main()