"""
Secure Secret Generation and Management

This module handles secure generation of passwords, tokens, and other secrets,
as well as management of environment variable files.
"""

import os
import re
import secrets
import string
import hashlib
import base64
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from rich.console import Console

console = Console()


class SecretGenerationError(Exception):
    """Error in secret generation"""
    pass


def generate_password(
    length: int = 24,
    charset: Optional[str] = None,
    ensure_complexity: bool = True
) -> str:
    """
    Generate a cryptographically secure password
    
    Args:
        length: Password length
        charset: Custom character set (if None, uses default)
        ensure_complexity: Ensure password has variety of character types
        
    Returns:
        Generated password
        
    Raises:
        SecretGenerationError: If generation fails
    """
    try:
        if length < 1:
            raise SecretGenerationError("Password length must be at least 1")
        
        if ensure_complexity and length < 4:
            length = 4  # Minimum for complexity requirements
        
        if charset is None:
            if ensure_complexity:
                # Use full character set for complexity
                charset = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
            else:
                # Use alphanumeric for simpler passwords
                charset = string.ascii_letters + string.digits
        
        if ensure_complexity and length >= 4:
            # Ensure at least one character from each category
            password_chars = []
            
            # Add required character types
            password_chars.append(secrets.choice(string.ascii_uppercase))
            password_chars.append(secrets.choice(string.ascii_lowercase))
            password_chars.append(secrets.choice(string.digits))
            
            if "!" in charset:  # Has special characters
                special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
                password_chars.append(secrets.choice(special_chars))
            
            # Fill the rest randomly
            for _ in range(length - len(password_chars)):
                password_chars.append(secrets.choice(charset))
            
            # Shuffle to avoid predictable patterns
            secrets.SystemRandom().shuffle(password_chars)
            return ''.join(password_chars)
        else:
            # Simple random generation
            return ''.join(secrets.choice(charset) for _ in range(length))
            
    except Exception as e:
        raise SecretGenerationError(f"Failed to generate password: {e}")


def generate_api_key(length: int = 64) -> str:
    """
    Generate a secure API key
    
    Args:
        length: Key length in characters
        
    Returns:
        Base64-encoded API key
    """
    try:
        # Generate random bytes and encode as base64
        key_bytes = secrets.token_bytes(length // 2)  # Base64 expands by ~33%
        return base64.urlsafe_b64encode(key_bytes).decode('ascii').rstrip('=')[:length]
    except Exception as e:
        raise SecretGenerationError(f"Failed to generate API key: {e}")


def generate_uuid() -> str:
    """
    Generate a UUID-like string
    
    Returns:
        UUID string
    """
    try:
        return secrets.token_hex(16)
    except Exception as e:
        raise SecretGenerationError(f"Failed to generate UUID: {e}")


def generate_htpasswd_hash(username: str, password: str) -> str:
    """
    Generate htpasswd-compatible hash for HTTP basic auth
    
    Args:
        username: Username
        password: Password to hash
        
    Returns:
        htpasswd format string (username:hash)
    """
    try:
        import crypt
        # Use SHA-512 based hash (most secure)
        salt = secrets.token_hex(8)
        hashed = crypt.crypt(password, f"$6${salt}$")
        return f"{username}:{hashed}"
    except ImportError:
        # Fallback to bcrypt-style hash using hashlib
        try:
            import bcrypt
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return f"{username}:{{bcrypt}}{hashed.decode('ascii')}"
        except ImportError:
            # Final fallback to SHA256 (less secure but portable)
            salt = secrets.token_hex(16)
            hash_obj = hashlib.sha256(f"{salt}{password}".encode('utf-8'))
            hashed = hash_obj.hexdigest()
            return f"{username}:{{SHA256}}{salt}${hashed}"


def validate_env_key(key: str) -> bool:
    """
    Validate environment variable key format
    
    Args:
        key: Environment variable key
        
    Returns:
        True if valid format
    """
    return bool(re.match(r'^[A-Z][A-Z0-9_]*$', key))


def load_or_create_env(env_path: Path = Path('.env')) -> Dict[str, str]:
    """
    Load existing .env file or create new one
    
    Args:
        env_path: Path to .env file
        
    Returns:
        Dictionary of environment variables
    """
    env_vars = {}
    
    if env_path.exists():
        console.print(f"[dim]Loading existing environment from {env_path}[/dim]")
        
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse KEY=value format
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if (value.startswith('"') and value.endswith('"')) or \
                           (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                        
                        env_vars[key] = value
                    else:
                        console.print(f"[yellow]Warning: Invalid format in {env_path} line {line_num}: {line}[/yellow]")
        
        except Exception as e:
            console.print(f"[yellow]Warning: Error reading {env_path}: {e}[/yellow]")
    
    else:
        console.print(f"[dim]Creating new environment file: {env_path}[/dim]")
    
    return env_vars


def write_env(
    env_vars: Dict[str, Any], 
    env_path: Path = Path('.env'),
    comments: Optional[Dict[str, str]] = None
) -> None:
    """
    Write environment variables to .env file
    
    Args:
        env_vars: Environment variables to write
        env_path: Path to .env file
        comments: Optional comments for variables
    """
    try:
        # Ensure parent directory exists
        env_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(env_path, 'w', encoding='utf-8') as f:
            # Write header
            f.write("# Home Lab Environment Variables\n")
            f.write("# Generated automatically - do not edit manually\n")
            f.write(f"# File: {env_path.name}\n\n")
            
            # Sort keys for stable output
            sorted_keys = sorted(env_vars.keys())
            
            # Group variables by prefix for better organization
            groups = {}
            for key in sorted_keys:
                prefix = key.split('_')[0]
                if prefix not in groups:
                    groups[prefix] = []
                groups[prefix].append(key)
            
            # Write variables by group
            for group_name in sorted(groups.keys()):
                if len(groups) > 1:  # Only show group headers if multiple groups
                    f.write(f"# {group_name} Configuration\n")
                
                for key in groups[group_name]:
                    value = env_vars[key]
                    
                    # Add comment if provided
                    if comments and key in comments:
                        f.write(f"# {comments[key]}\n")
                    
                    # Quote values that contain spaces or special characters
                    if isinstance(value, str) and (' ' in value or any(c in value for c in '`$"\\')):
                        # Escape quotes and backslashes
                        escaped_value = value.replace('\\', '\\\\').replace('"', '\\"')
                        f.write(f'{key}="{escaped_value}"\n')
                    else:
                        f.write(f'{key}={value}\n')
                
                if len(groups) > 1:
                    f.write('\n')  # Blank line between groups
        
        console.print(f"[green]✓ Environment variables saved to {env_path}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error writing {env_path}: {e}[/red]")
        raise


def merge_env_vars(
    base_vars: Dict[str, str], 
    new_vars: Dict[str, Any],
    preserve_existing: bool = True
) -> Dict[str, str]:
    """
    Merge new environment variables with existing ones
    
    Args:
        base_vars: Existing environment variables
        new_vars: New environment variables to add
        preserve_existing: Whether to preserve existing values
        
    Returns:
        Merged environment variables
    """
    merged = base_vars.copy()
    
    for key, value in new_vars.items():
        if not validate_env_key(key):
            console.print(f"[yellow]Warning: Invalid environment variable key '{key}', skipping[/yellow]")
            continue
        
        # Convert value to string
        str_value = str(value) if value is not None else ""
        
        if preserve_existing and key in merged:
            console.print(f"[dim]Preserving existing value for {key}[/dim]")
        else:
            merged[key] = str_value
    
    return merged


def generate_service_secrets(
    service_id: str, 
    secret_types: List[str],
    existing_secrets: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """
    Generate secrets for a service
    
    Args:
        service_id: Service identifier
        secret_types: Types of secrets to generate ('password', 'api_key', 'uuid')
        existing_secrets: Existing secrets to preserve
        
    Returns:
        Dictionary of generated secrets
    """
    secrets_dict = {}
    existing = existing_secrets or {}
    
    for secret_type in secret_types:
        key = f"{service_id.upper()}_{secret_type.upper()}"
        
        # Preserve existing secrets
        if key in existing:
            secrets_dict[key] = existing[key]
            console.print(f"[dim]Preserved existing {secret_type} for {service_id}[/dim]")
            continue
        
        # Generate new secrets
        try:
            if secret_type == 'password':
                secrets_dict[key] = generate_password(32, ensure_complexity=True)
            elif secret_type == 'api_key':
                secrets_dict[key] = generate_api_key(64)
            elif secret_type == 'uuid':
                secrets_dict[key] = generate_uuid()
            elif secret_type == 'token':
                secrets_dict[key] = generate_api_key(48)
            else:
                console.print(f"[yellow]Warning: Unknown secret type '{secret_type}' for {service_id}[/yellow]")
                continue
            
            console.print(f"[green]✓ Generated {secret_type} for {service_id}[/green]")
            
        except SecretGenerationError as e:
            console.print(f"[red]Error generating {secret_type} for {service_id}: {e}[/red]")
    
    return secrets_dict


def redact_secrets(data: Any, redaction_text: str = "●●●●●●●●") -> Any:
    """
    Recursively redact sensitive data for display
    
    Args:
        data: Data structure to redact
        redaction_text: Text to use for redaction
        
    Returns:
        Data with secrets redacted
    """
    if isinstance(data, dict):
        redacted = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in ['password', 'token', 'secret', 'key', 'auth']):
                redacted[key] = redaction_text if value else "[not set]"
            else:
                redacted[key] = redact_secrets(value, redaction_text)
        return redacted
    
    elif isinstance(data, list):
        return [redact_secrets(item, redaction_text) for item in data]
    
    elif isinstance(data, str):
        # Check if the string itself looks like a secret
        if len(data) > 16 and any(c in data for c in string.ascii_letters + string.digits):
            return redaction_text
        return data
    
    else:
        return data


def validate_secret_strength(password: str) -> Tuple[bool, List[str]]:
    """
    Validate password strength
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_strong, list of issues)
    """
    issues = []
    
    if len(password) < 12:
        issues.append("Password should be at least 12 characters long")
    
    if not any(c.isupper() for c in password):
        issues.append("Password should contain uppercase letters")
    
    if not any(c.islower() for c in password):
        issues.append("Password should contain lowercase letters")
    
    if not any(c.isdigit() for c in password):
        issues.append("Password should contain numbers")
    
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        issues.append("Password should contain special characters")
    
    # Check for common patterns
    if password.lower() in ['password', 'admin', '123456', 'qwerty']:
        issues.append("Password is too common")
    
    return len(issues) == 0, issues


def create_backup_env(env_path: Path) -> Optional[Path]:
    """
    Create a backup of the environment file
    
    Args:
        env_path: Path to environment file
        
    Returns:
        Path to backup file if created, None otherwise
    """
    if not env_path.exists():
        return None
    
    try:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = env_path.with_suffix(f'.bak.{timestamp}')
        
        # Copy file content
        with open(env_path, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
        
        console.print(f"[dim]Created backup: {backup_path}[/dim]")
        return backup_path
        
    except Exception as e:
        console.print(f"[yellow]Warning: Could not create backup: {e}[/yellow]")
        return None