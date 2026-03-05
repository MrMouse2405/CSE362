# Documentation Style Guide

This project uses the **Google Python Style Guide** for all docstrings. It ensures consistency, readability, and compatibility with standard documentation generators like `pdoc`, `Sphinx`, and IDE tooltips.

## Guidelines

1. **Module-level Docstrings:** Every Python file should begin with a module-level docstring describing the module's purpose.
2. **Classes:** Each class must have a docstring right below its definition. Document attributes and usage if necessary.
3. **Functions/Methods:** Each function or method must have a docstring explaining its behavior. It should include:
   - A brief summary.
   - `Args:` section describing the parameters (name, type, description).
   - `Returns:` section describing the return value and type.
   - `Raises:` section if any specific exceptions are raised.
4. **Formatting:**
   - Use triple double quotes (`"""`) for all docstrings.
   - For single-line docstrings, put the closing quotes on the same line.
   - For multi-line docstrings, put the closing quotes on a new line by itself.
   - Indent the docstring to match the code it documents.

## Example

```python
def fetch_data(user_id: int) -> dict:
    """
    Fetches data for a specific user.

    Args:
        user_id (int): The unique identifier of the user.

    Returns:
        dict: A dictionary containing the user's data.

    Raises:
        ValueError: If the user_id is negative.
    """
    if user_id < 0:
        raise ValueError("User ID must be positive.")
    return {"id": user_id, "data": "..."}
```
