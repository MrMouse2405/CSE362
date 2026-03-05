# Documentation Style Guide

This project uses standard **pdoc** styling for docstrings to ensure consistency, readability, and compatibility with our documentation generators.

## Guidelines

1. **Module-level Docstrings:** Every Python file must begin with a module-level docstring describing the module's overarching purpose and any relevant classes/functions it exports.
2. **Classes:** Each class must have a docstring immediately following its definition. Do NOT use an `Attributes:` block inside the class docstring.
3. **Properties/Attributes:** Class properties, enum attributes, or instance variables must be documented using a string literal directly beneath the property declaration.
4. **Functions/Methods:** Each function or method must have a docstring explaining its behavior immediately following its definition. Standard Google-style `Args:`, `Returns:`, and `Raises:` sections are acceptable here.
5. **Formatting:**
   - Use triple double quotes (`"""`) for all docstrings.
   - For single-line docstrings, put the closing quotes on the same line.
   - For multi-line docstrings, put the closing quotes on a new line by itself.
   - Indent the docstring to match the code it documents.
   - Use standard markdown (like backticks for code literals).

## Example: Models & Classes

For classes, variables, and properties, use the inline `pdoc` attribute documentation format:

```python
class GoldenRetriever(Dog):
    """
    Represents a specific breed of Dog.
    """

    name: str
    """The full name of the dog."""

    def __init__(self):
        """Initializes a new GoldenRetriever."""
        self.weight: int = 10
        """Weight in kilograms."""
```

## Example: Functions & Methods

For functions, use standard descriptive sections:

```python
def fetch_data(user_id: int) -> dict:
    """
    Fetches data for a specific user.
    """
    if user_id < 0:
        raise ValueError("User ID must be positive.")
    return {"id": user_id, "data": "..."}
```
