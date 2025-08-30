"""Configuration management for direktiv."""

import json
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Manages user configuration for direktiv."""

    DEFAULT_CONFIG = {
        "theme": "dark",
        "default_category": "General",
        "auto_mark_read_after_seconds": 30,
        "show_hidden_files": False,
        "editor": None,
        "categories": {
            "General": {"icon": "📄", "color": None},
            "Personal": {"icon": "👤", "color": None},
            "Work": {"icon": "💼", "color": None},
        },
        "ui": {
            "tree_width": 50,
            "show_status_bar": True,
            "show_help_on_start": False,
        },
    }

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration.

        Args:
            config_path: Path to config file. Defaults to ~/.direktiv/config.json
        """
        if config_path is None:
            config_dir = Path.home() / ".direktiv"
            config_dir.mkdir(exist_ok=True)
            config_path = config_dir / "config.json"

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file.

        Returns:
            Configuration dictionary
        """
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    user_config = json.load(f)
                    # Merge with defaults
                    config = self.DEFAULT_CONFIG.copy()
                    self._deep_merge(config, user_config)
                    return config
            except (json.JSONDecodeError, IOError):
                # Fall back to defaults if config is invalid
                return self.DEFAULT_CONFIG.copy()
        else:
            # Create default config file
            config = self.DEFAULT_CONFIG.copy()
            self.save()
            return config

    def _deep_merge(self, base: Dict, update: Dict) -> None:
        """Deep merge update dictionary into base.

        Args:
            base: Base dictionary to update
            update: Dictionary with updates
        """
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def save(self) -> bool:
        """Save configuration to file.

        Returns:
            True if successful
        """
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=2)
            return True
        except IOError:
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value
        self.save()

    def add_category(
        self, name: str, icon: Optional[str] = None, color: Optional[str] = None
    ) -> None:
        """Add a category configuration.

        Args:
            name: Category name
            icon: Optional icon
            color: Optional color
        """
        if "categories" not in self.config:
            self.config["categories"] = {}

        self.config["categories"][name] = {"icon": icon or "📁", "color": color}
        self.save()

    def get_category_config(self, name: str) -> Dict[str, Optional[str]]:
        """Get configuration for a category.

        Args:
            name: Category name

        Returns:
            Category configuration
        """
        categories = self.get("categories", {})
        return categories.get(name, {"icon": "📁", "color": None})  # type: ignore[no-any-return]

    def reset(self) -> None:
        """Reset configuration to defaults."""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save()
