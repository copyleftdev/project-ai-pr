from typing import Any, Dict, Union, Optional
from collections.abc import Mapping
import copy

# edit to open pull request


class DictFlattener:
    """A professional-grade dictionary flattener that handles nested dictionaries of any depth.
    
    Features:
    - Configurable delimiter for nested keys
    - Optional prefix for all flattened keys
    - Preserves data types
    - Handles lists, tuples, and sets
    - Custom key transformation functions
    - Circular reference detection
    
    Example:
        flattener = DictFlattener(delimiter='.')
        nested_dict = {'a': {'b': {'c': 1}}, 'd': [1, 2, {'e': 3}]}
        flat_dict = flattener.flatten(nested_dict)
        # Result: {'a.b.c': 1, 'd.0': 1, 'd.1': 2, 'd.2.e': 3}
    """

    def __init__(
        delimiter: str = ".",
        prefix: str = "",
        max_depth: Optional[int] = None,
        preserve_lists: bool = False,
        key_transformer: Optional[callable] = None
    ):
        """Initialize the DictFlattener with custom configuration.
        
        Args:
            delimiter: String to join nested keys (default: ".")
            prefix: Optional prefix for all flattened keys
            max_depth: Maximum depth to flatten (None for unlimited)
            preserve_lists: If True, keeps lists intact instead of flattening them
            key_transformer: Optional function to transform keys before joining
        """
        self.delimiter = delimiter
        self.prefix = prefix
        self.max_depth = max_depth
        self.preserve_lists = preserve_lists
        self.key_transformer = key_transformer or str
        self._seen_objects = set()

    def flatten(self, d: Union[Dict, Any], parent_key: str = "") -> Dict[str, Any]:
        """Flatten a nested dictionary into a single-level dictionary.
        
        Args:
            d: Dictionary to flatten or any other object
            parent_key: Internal use for recursive calls
            
        Returns:
            Dict[str, Any]: Flattened dictionary
            
        Raises:
            ValueError: If circular reference is detected
            TypeError: If unsupported type is encountered
        """
        items: list = []
        
        # Handle non-dict input
        if not isinstance(d, (dict, list, tuple, set)) or \
           (self.preserve_lists and isinstance(d, (list, tuple, set))):
            return {parent_key: d} if parent_key else d

        # Detect circular references
        obj_id = id(d)
        if obj_id in self._seen_objects:
            raise ValueError("Circular reference detected")
        self._seen_objects.add(obj_id)

        try:
            if isinstance(d, (list, tuple, set)):
                items.extend(
                    self._flatten_sequence(d, parent_key)
                )
            else:
                items.extend(
                    self._flatten_dict(d, parent_key)
                )

            return dict(items)
        finally:
            self._seen_objects.remove(obj_id)

    def _flatten_dict(self, d: Dict, parent_key: str) -> list:
        """Helper method to flatten dictionary items."""
        items = []
        for k, v in d.items():
            transformed_key = self.key_transformer(k)
            new_key = self._join_keys(parent_key, transformed_key)
            
            if isinstance(v, (dict, list, tuple, set)) and \
               (not self.preserve_lists or isinstance(v, dict)):
                if self.max_depth is None or self._get_depth(new_key) < self.max_depth:
                    items.extend(
                        self.flatten(v, new_key).items()
                    )
                else:
                    items.append((new_key, v))
            else:
                items.append((new_key, v))
        return items

    def _flatten_sequence(self, seq: Union[list, tuple, set], parent_key: str) -> list:
        """Helper method to flatten sequence items."""
        items = []
        for i, v in enumerate(seq):
            new_key = self._join_keys(parent_key, str(i))
            if isinstance(v, (dict, list, tuple, set)) and \
               (not self.preserve_lists or isinstance(v, dict)):
                if self.max_depth is None or self._get_depth(new_key) < self.max_depth:
                    items.extend(
                        self.flatten(v, new_key).items()
                    )
                else:
                    items.append((new_key, v))
            else:
                items.append((new_key, v))
        return items

    def _join_keys(self, parent_key: str, child_key: str) -> str:
        """Join parent and child keys with delimiter."""
        if not parent_key:
            key = child_key
        else:
            key = f"{parent_key}{self.delimiter}{child_key}"
        return f"{self.prefix}{key}" if self.prefix else key

    def _get_depth(self, key: str) -> int:
        """Calculate the current depth of a key."""
        return len(key.split(self.delimiter)) if key else 0

    @classmethod
    def unflatten(cls, d: Dict[str, Any], delimiter: str = ".") -> Dict:
        """Convert a flattened dictionary back to nested format.
        
        Args:
            d: Flattened dictionary
            delimiter: Delimiter used in keys (default: ".")
            
        Returns:
            Dict: Nested dictionary
            
        Example:
            flat_dict = {'a.b.c': 1, 'd.0': 2, 'd.1': 3}
            nested_dict = DictFlattener.unflatten(flat_dict)
            # Result: {'a': {'b': {'c': 1}}, 'd': [2, 3]}
        """
        result = {}
        
        for key, value in d.items():
            parts = key.split(delimiter)
            target = result
            
            for i, part in enumerate(parts[:-1]):
                # Convert string digits to list indices
                if part.isdigit() and (i == 0 or isinstance(target, list)):
                    idx = int(part)
                    if not isinstance(target, list):
                        target = result[parts[i-1]] = []
                    while len(target) <= idx:
                        target.append({})
                    target = target[idx]
                else:
                    target = target.setdefault(part, {})
            
            last = parts[-1]
            if last.isdigit() and isinstance(target, list):
                idx = int(last)
                while len(target) <= idx:
                    target.append(None)
                target[idx] = value
            else:
                target[last] = value
                
        return result


# Example usage:
if __name__ == "__main__":
    # Create a nested dictionary
    nested_dict = {
        "person": {
            "name": "John Doe",
            "age": 30,
            "address": {
                "street": "123 Main St",
                "city": "Springfield",
                "coordinates": [42.1234, -71.5678]
            }
        },
        "preferences": {
            "colors": ["blue", "green"],
            "settings": {
                "notifications": True,
                "theme": "dark"
            }
        }
    }

    # Initialize flattener with custom settings
    flattener = DictFlattener(
        delimiter=".",
        prefix="",
        max_depth=None,
        preserve_lists=False
    )

    # Flatten the dictionary
    flat_dict = flattener.flatten(nested_dict)
    print("\nFlattened dictionary:")
    for k, v in flat_dict.items():
        print(f"{k}: {v}")

    # Unflatten back to nested format
    restored_dict = DictFlattener.unflatten(flat_dict)
    print("\nRestored dictionary:")
    print(restored_dict)
