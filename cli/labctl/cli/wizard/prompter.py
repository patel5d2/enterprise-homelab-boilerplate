"""
Interactive Prompt Engine

This module provides beautiful, type-safe interactive prompts for service configuration
using Rich for UI and comprehensive validation.
"""

import re
import secrets
import string
from typing import Any, Dict, List, Optional, Union

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table
from rich.text import Text

from ...core.services.schema import FieldSchema, FieldType

console = Console()


class ValidationError(Exception):
    """Field validation error"""

    pass


class ConditionalExpressionEvaluator:
    """Safe evaluator for show_if/hidden_if expressions"""

    def __init__(self, context: Dict[str, Any]):
        self.context = context

    def evaluate(self, expression: str) -> bool:
        """
        Safely evaluate a conditional expression

        Args:
            expression: Expression like 'field_name == "value"' or 'field_name == true'

        Returns:
            Boolean result of evaluation
        """
        if not expression:
            return True

        try:
            # Simple expression parsing - supports basic comparisons
            # Format: field_name == "value" or field_name == true/false

            # Handle boolean comparisons
            if " == true" in expression:
                field_name = expression.split(" == true")[0].strip()
                return bool(self.context.get(field_name, False))

            if " == false" in expression:
                field_name = expression.split(" == false")[0].strip()
                return not bool(self.context.get(field_name, False))

            # Handle string comparisons
            if " == " in expression and ('"' in expression or "'" in expression):
                parts = expression.split(" == ", 1)
                if len(parts) == 2:
                    field_name = parts[0].strip()
                    value_part = parts[1].strip()

                    # Extract quoted value
                    if value_part.startswith('"') and value_part.endswith('"'):
                        expected_value = value_part[1:-1]
                    elif value_part.startswith("'") and value_part.endswith("'"):
                        expected_value = value_part[1:-1]
                    else:
                        expected_value = value_part

                    actual_value = str(self.context.get(field_name, ""))
                    return actual_value == expected_value

            # Handle != comparisons
            if " != " in expression and ('"' in expression or "'" in expression):
                parts = expression.split(" != ", 1)
                if len(parts) == 2:
                    field_name = parts[0].strip()
                    value_part = parts[1].strip()

                    # Extract quoted value
                    if value_part.startswith('"') and value_part.endswith('"'):
                        expected_value = value_part[1:-1]
                    elif value_part.startswith("'") and value_part.endswith("'"):
                        expected_value = value_part[1:-1]
                    else:
                        expected_value = value_part

                    actual_value = str(self.context.get(field_name, ""))
                    return actual_value != expected_value

            # If we can't parse the expression, default to showing the field
            console.print(
                f"[yellow]Warning: Could not parse expression '{expression}', defaulting to true[/yellow]"
            )
            return True

        except Exception as e:
            console.print(
                f"[yellow]Warning: Error evaluating expression '{expression}': {e}[/yellow]"
            )
            return True


def generate_password(length: int = 24, ensure_complexity: bool = True) -> str:
    """
    Generate a secure password

    Args:
        length: Password length
        ensure_complexity: Ensure password has uppercase, lowercase, digits, and symbols

    Returns:
        Generated password
    """
    if ensure_complexity and length < 4:
        length = 4  # Minimum for complexity requirements

    if ensure_complexity:
        # Ensure at least one character from each category
        password_chars = []
        password_chars.append(secrets.choice(string.ascii_uppercase))
        password_chars.append(secrets.choice(string.ascii_lowercase))
        password_chars.append(secrets.choice(string.digits))
        password_chars.append(secrets.choice("!@#$%^&*()_+-=[]{}|;:,.<>?"))

        # Fill the rest randomly
        all_chars = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
        for _ in range(length - 4):
            password_chars.append(secrets.choice(all_chars))

        # Shuffle to avoid predictable patterns
        secrets.SystemRandom().shuffle(password_chars)
        return "".join(password_chars)
    else:
        # Simple random generation
        all_chars = string.ascii_letters + string.digits
        return "".join(secrets.choice(all_chars) for _ in range(length))


def validate_field_value(field: FieldSchema, value: Any) -> Any:
    """
    Validate field value according to field schema

    Args:
        field: Field schema
        value: Value to validate

    Returns:
        Validated and potentially converted value

    Raises:
        ValidationError: If validation fails
    """
    # Handle empty values
    if value is None or value == "":
        if field.required:
            raise ValidationError(f"Field '{field.label}' is required")
        return None if field.type != FieldType.BOOLEAN else False

    # Type-specific validation
    if field.type == FieldType.STRING:
        value = str(value)

        if field.min_length and len(value) < field.min_length:
            raise ValidationError(f"Minimum length is {field.min_length} characters")

        if field.max_length and len(value) > field.max_length:
            raise ValidationError(f"Maximum length is {field.max_length} characters")

        if field.validate_regex:
            if not re.match(field.validate_regex, value):
                raise ValidationError(f"Value does not match required format")

    elif field.type == FieldType.PASSWORD:
        value = str(value)

        if field.min_length and len(value) < field.min_length:
            raise ValidationError(f"Minimum length is {field.min_length} characters")

        if field.max_length and len(value) > field.max_length:
            raise ValidationError(f"Maximum length is {field.max_length} characters")

    elif field.type == FieldType.INTEGER:
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValidationError("Value must be a valid integer")

        if field.min is not None and value < field.min:
            raise ValidationError(f"Minimum value is {field.min}")

        if field.max is not None and value > field.max:
            raise ValidationError(f"Maximum value is {field.max}")

    elif field.type == FieldType.BOOLEAN:
        if isinstance(value, str):
            value = value.lower() in ("true", "yes", "1", "on", "y")
        else:
            value = bool(value)

    elif field.type == FieldType.CHOICE:
        if field.choices and value not in field.choices:
            raise ValidationError(f"Value must be one of: {', '.join(field.choices)}")

    elif field.type == FieldType.MULTISELECT:
        if not isinstance(value, list):
            raise ValidationError("Value must be a list")

        if field.choices:
            invalid_choices = set(value) - set(field.choices)
            if invalid_choices:
                raise ValidationError(f"Invalid choices: {', '.join(invalid_choices)}")

        if field.min_selections and len(value) < field.min_selections:
            raise ValidationError(f"Minimum {field.min_selections} selections required")

        if field.max_selections and len(value) > field.max_selections:
            raise ValidationError(f"Maximum {field.max_selections} selections allowed")

    return value


def prompt_string(field: FieldSchema, default: Any = None) -> str:
    """Prompt for string input"""
    default_str = str(default) if default is not None else None
    prompt_text = field.label

    if default_str:
        prompt_text += f" [dim]\\[default: {default_str}][/dim]"

    while True:
        try:
            value = Prompt.ask(
                prompt_text, default=default_str, show_default=False, console=console
            )
            return validate_field_value(field, value)
        except ValidationError as e:
            console.print(f"[red]Error: {e}[/red]")


def prompt_password(field: FieldSchema, default: Any = None) -> str:
    """Prompt for password input with optional generation"""
    if field.generate and not default:
        if Confirm.ask(
            f"Generate secure password for {field.label}?",
            default=True,
            console=console,
        ):
            length = field.length or 24
            generated = generate_password(length, ensure_complexity=True)
            console.print(f"[green]✓[/green] Generated secure password")
            return generated

    prompt_text = field.label
    if field.generate:
        prompt_text += " [dim](leave empty to generate)[/dim]"

    while True:
        try:
            value = Prompt.ask(
                prompt_text,
                password=True,
                default="",
                show_default=False,
                console=console,
            )

            if not value and field.generate:
                length = field.length or 24
                value = generate_password(length, ensure_complexity=True)
                console.print(f"[green]✓[/green] Generated secure password")

            return validate_field_value(field, value)
        except ValidationError as e:
            console.print(f"[red]Error: {e}[/red]")


def prompt_boolean(field: FieldSchema, default: Any = None) -> bool:
    """Prompt for boolean input"""
    default_bool = bool(default) if default is not None else field.default
    return Confirm.ask(field.label, default=default_bool, console=console)


def prompt_integer(field: FieldSchema, default: Any = None) -> int:
    """Prompt for integer input"""
    default_int = int(default) if default is not None else field.default
    prompt_text = field.label

    if default_int is not None:
        prompt_text += f" [dim]\\[default: {default_int}][/dim]"

    while True:
        try:
            value = IntPrompt.ask(
                prompt_text, default=default_int, show_default=False, console=console
            )
            return validate_field_value(field, value)
        except ValidationError as e:
            console.print(f"[red]Error: {e}[/red]")


def prompt_choice(field: FieldSchema, default: Any = None) -> str:
    """Prompt for single choice selection"""
    if not field.choices:
        raise ValueError("Choice field must have choices defined")

    default_choice = str(default) if default is not None else field.default

    # Show choices in a nice format
    choices_text = " / ".join(field.choices)
    console.print(f"[cyan]Choices:[/cyan] {choices_text}")

    prompt_text = field.label
    if default_choice:
        prompt_text += f" [dim]\\[default: {default_choice}][/dim]"

    while True:
        try:
            value = Prompt.ask(
                prompt_text,
                choices=field.choices,
                default=default_choice,
                show_default=False,
                show_choices=False,
                console=console,
            )
            return validate_field_value(field, value)
        except ValidationError as e:
            console.print(f"[red]Error: {e}[/red]")


def prompt_multiselect(field: FieldSchema, default: Any = None) -> List[str]:
    """Prompt for multiple choice selection"""
    if not field.choices:
        raise ValueError("Multiselect field must have choices defined")

    default_selections = default if isinstance(default, list) else (field.default or [])

    console.print(f"\n[bold]{field.label}[/bold]")
    console.print(f"[dim]{field.description}[/dim]")

    # Create a table showing choices with selection status
    table = Table(show_header=False, show_lines=False, pad_edge=False)
    table.add_column("Select", width=3)
    table.add_column("Choice", style="cyan")
    table.add_column("Description", style="dim")

    selected = set(default_selections)

    for i, choice in enumerate(field.choices):
        status = "✓" if choice in selected else " "
        table.add_row(f"[{i+1}]", f"{status} {choice}", "")

    console.print(table)
    console.print(
        "\n[dim]Enter choice numbers (space-separated) or press Enter for defaults:[/dim]"
    )

    while True:
        try:
            user_input = Prompt.ask(
                "Selections", default="", show_default=False, console=console
            )

            if not user_input.strip():
                # Use defaults
                result = list(default_selections)
            else:
                # Parse user input
                try:
                    indices = [int(x.strip()) for x in user_input.split()]
                    result = []
                    for idx in indices:
                        if 1 <= idx <= len(field.choices):
                            choice = field.choices[idx - 1]
                            if choice not in result:
                                result.append(choice)
                        else:
                            raise ValidationError(f"Invalid choice number: {idx}")
                except ValueError:
                    raise ValidationError(
                        "Please enter valid choice numbers separated by spaces"
                    )

            return validate_field_value(field, result)

        except ValidationError as e:
            console.print(f"[red]Error: {e}[/red]")


def prompt_textarea(field: FieldSchema, default: Any = None) -> str:
    """Prompt for multi-line text input"""
    console.print(f"\n[bold]{field.label}[/bold]")
    console.print(f"[dim]{field.description}[/dim]")

    if field.placeholder:
        console.print(f"[dim]Example:[/dim]\n{field.placeholder}")

    console.print(
        "[dim]Enter text (press Ctrl+D when finished, or type 'END' on a new line):[/dim]"
    )

    lines = []
    try:
        while True:
            try:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)
            except EOFError:
                break
    except KeyboardInterrupt:
        console.print("\n[yellow]Input cancelled[/yellow]")
        return ""

    result = "\n".join(lines)

    if not result and default:
        result = str(default)

    try:
        return validate_field_value(field, result)
    except ValidationError as e:
        console.print(f"[red]Error: {e}[/red]")
        return ""


def ask_field(field: FieldSchema, context: Dict[str, Any]) -> Any:
    """
    Ask for field input with appropriate prompt type

    Args:
        field: Field schema definition
        context: Current context for conditional evaluation

    Returns:
        User input value, validated and converted to appropriate type
    """
    # Check conditional visibility
    if field.show_if:
        evaluator = ConditionalExpressionEvaluator(context)
        if not evaluator.evaluate(field.show_if):
            return field.default

    if field.hidden_if:
        evaluator = ConditionalExpressionEvaluator(context)
        if evaluator.evaluate(field.hidden_if):
            return field.default

    # Show field description if provided
    if field.description:
        console.print(f"\n[dim]{field.description}[/dim]")

    # Get default from context or field
    default = context.get(field.key, field.default)

    # Route to appropriate prompt function
    if field.type == FieldType.STRING:
        return prompt_string(field, default)
    elif field.type == FieldType.PASSWORD:
        return prompt_password(field, default)
    elif field.type == FieldType.BOOLEAN:
        return prompt_boolean(field, default)
    elif field.type == FieldType.INTEGER:
        return prompt_integer(field, default)
    elif field.type == FieldType.CHOICE:
        return prompt_choice(field, default)
    elif field.type == FieldType.MULTISELECT:
        return prompt_multiselect(field, default)
    elif field.type == FieldType.TEXTAREA:
        return prompt_textarea(field, default)
    else:
        raise ValueError(f"Unsupported field type: {field.type}")


def ask_custom_environment_variables() -> Dict[str, str]:
    """
    Ask for custom environment variables

    Returns:
        Dictionary of environment variable key-value pairs
    """
    if not Confirm.ask(
        "Add custom environment variables?", default=False, console=console
    ):
        return {}

    console.print("\n[bold]Custom Environment Variables[/bold]")
    console.print(
        "[dim]Enter KEY=value pairs. Press Enter with empty line to finish.[/dim]"
    )

    env_vars = {}

    while True:
        try:
            line = Prompt.ask(
                "Environment variable (KEY=value)", default="", console=console
            )

            if not line.strip():
                break

            if "=" not in line:
                console.print("[red]Error: Format must be KEY=value[/red]")
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            # Validate key format
            if not re.match(r"^[A-Z][A-Z0-9_]*$", key):
                console.print(
                    "[red]Error: Key must be uppercase letters, numbers, and underscores[/red]"
                )
                continue

            env_vars[key] = value
            console.print(f"[green]✓[/green] Added: {key}=***")

        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled[/yellow]")
            break

    return env_vars


def display_field_summary(fields_data: Dict[str, Any], service_name: str) -> None:
    """
    Display a summary of configured fields

    Args:
        fields_data: Dictionary of field values
        service_name: Name of the service being configured
    """
    console.print(f"\n[bold green]✓ {service_name} Configuration Summary[/bold green]")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Field", style="white", width=20)
    table.add_column("Value", style="green")

    for key, value in fields_data.items():
        if key == "enabled":
            continue  # Skip enabled field in summary

        # Mask passwords and sensitive data
        if (
            "password" in key.lower()
            or "token" in key.lower()
            or "secret" in key.lower()
        ):
            display_value = "●●●●●●●●" if value else "[dim]not set[/dim]"
        elif isinstance(value, list):
            display_value = ", ".join(value) if value else "[dim]none[/dim]"
        elif isinstance(value, bool):
            display_value = "✓ Yes" if value else "✗ No"
        else:
            display_value = str(value) if value is not None else "[dim]not set[/dim]"

        table.add_row(key.replace("_", " ").title(), display_value)

    console.print(table)
