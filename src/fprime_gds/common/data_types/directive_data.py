"""
@brief Directive Data class

Instances of this class define a specific instance of a sequence directive
(LABEL, JCF, EXIT, JCS, ERROR_MODE) with specific argument values.

@date Created 2026
@author Generated

@bug No known bugs
"""

from fprime_gds.common.models.serialize.numerical_types import U8Type
from fprime_gds.common.models.serialize.string_type import StringType
from fprime_gds.common.data_types import sys_data


class DirectiveData(sys_data.SysData):
    """The DirectiveData class stores a specific sequence directive"""

    # Directive ID mapping
    DIRECTIVE_IDS = {
        "LABEL": 0,
        "JCF": 1,
        "EXIT": 2,
        "JCS": 3,
        "ERROR_MODE": 4,
    }

    def __init__(self, directive_name, directive_args=None):
        """
        Constructor.

        Args:
            directive_name: The name of the directive (LABEL, JCF, EXIT, JCS, ERROR_MODE)
            directive_args: The arguments for the directive:
                           - LABEL: label name (string)
                           - JCF: target label name (string)
                           - EXIT: status code (0 or 1)
                           - JCS: target label name (string)
                           - ERROR_MODE: mode (0 = OFF, 1 = ON)

        Returns:
            An initialized DirectiveData object
        """
        super().__init__()

        if directive_name not in self.DIRECTIVE_IDS:
            raise ValueError(f"Unknown directive: {directive_name}")

        self.directive_name = directive_name
        self.directive_id = self.DIRECTIVE_IDS[directive_name]
        self.raw_args = directive_args or []

        # Validate and process arguments
        self._validate_args()

    def _validate_args(self):
        """Validate directive arguments based on directive type."""
        if self.directive_name in ("LABEL", "JCF", "JCS"):
            # These directives require a string argument (label name)
            if not self.raw_args or len(self.raw_args) != 1:
                raise ValueError(f"{self.directive_name} requires exactly one argument (label name)")
            if not isinstance(self.raw_args[0], str):
                raise ValueError(f"{self.directive_name} argument must be a string")
            # Check label length (max 20 characters)
            if len(self.raw_args[0]) > 20:
                raise ValueError(f"{self.directive_name} label name must be 20 characters or less")

        elif self.directive_name == "EXIT":
            # EXIT requires a numeric argument (0 or 1)
            if not self.raw_args or len(self.raw_args) != 1:
                raise ValueError(f"EXIT requires exactly one argument (status code 0 or 1)")
            if not isinstance(self.raw_args[0], (int, float)):
                raise ValueError(f"EXIT argument must be a number")
            status = int(self.raw_args[0])
            if status not in (0, 1):
                raise ValueError(f"EXIT status code must be 0 or 1, got {status}")

        elif self.directive_name == "ERROR_MODE":
            # ERROR_MODE requires a numeric argument (0 or 1)
            if not self.raw_args or len(self.raw_args) != 1:
                raise ValueError(f"ERROR_MODE requires exactly one argument (mode 0 or 1)")
            if not isinstance(self.raw_args[0], (int, float)):
                raise ValueError(f"ERROR_MODE argument must be a number")
            mode = int(self.raw_args[0])
            if mode not in (0, 1):
                raise ValueError(f"ERROR_MODE must be 0 or 1, got {mode}")

    def get_directive_name(self):
        """Get the directive name"""
        return self.directive_name

    def get_directive_id(self):
        """Get the directive ID (0-4)"""
        return self.directive_id

    def get_args(self):
        """Get the raw arguments"""
        return self.raw_args

    def serialize_directive_buffer(self):
        """
        Serialize the directive buffer (directive ID + arguments).

        Returns:
            bytes: The serialized directive buffer
        """
        # Start with directive ID
        buffer = U8Type(self.directive_id).serialize()

        if self.directive_name in ("LABEL", "JCF", "JCS"):
            # Serialize string argument: length + string bytes
            label_name = self.raw_args[0]
            label_bytes = label_name.encode('utf-8')
            buffer += U8Type(len(label_bytes)).serialize()
            buffer += label_bytes

        elif self.directive_name in ("EXIT", "ERROR_MODE"):
            # Serialize numeric argument
            value = int(self.raw_args[0])
            buffer += U8Type(value).serialize()

        return buffer

    def __str__(self):
        """String representation"""
        args_str = ", ".join(str(arg) for arg in self.raw_args) if self.raw_args else ""
        return f"{self.directive_name}({args_str})"
