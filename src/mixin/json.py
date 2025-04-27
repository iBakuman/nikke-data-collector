import os
from typing import runtime_checkable, Protocol


@runtime_checkable
class JSONSerializable(Protocol):
    """Protocol defining the interface for JSON serializable objects."""

    def to_json(self, **kwargs) -> str:
        """Convert the object to a JSON string."""
        ...


class JSONSerializableMixin:
    """
    Mixin class that provides JSON serialization functionality.

    Can be used with any class that implements the to_json method (e.g., JSONWizard).
    """

    def save_as_json(self, filename: str) -> None:
        """
        Save the object to a JSON file.

        Args:
            filename: Path to the output JSON file
        """
        # Using type checking to verify this class implements to_json
        if not isinstance(self, JSONSerializable):
            raise TypeError(f"{self.__class__.__name__} does not implement to_json method")

        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(self.to_json(indent=2, ensure_ascii=False))
            # f.write(self.to_json(indent=2))
