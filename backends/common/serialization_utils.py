"""Utilities for serialization/deserialization of objects.
"""

import base64
import dill
from typing import Any


def serialize_obj(obj: Any) -> str:
    """Serialize given object with the following steps:
        1. Dump it using dill into a string.
        2. Encode it into base64 and obtain a bytes representation.
        3. Convert the bytes into an ASCII string.
    This serialized object can then be transferred in an HTTP request's parameters.
    """
    obj_dill = dill.dumps(obj)
    obj_base64 = base64.b64encode(obj_dill)
    obj_ascii = obj_base64.decode("ascii")
    return obj_ascii


def deserialize_obj(obj: str) -> str:
    """Deserialize given object with the following steps:
        1. Decode it using base64 to obtain bytes representation.
        2. Load it into an object using dill.
    """
    obj_dill = base64.b64decode(obj)
    obj_str = dill.loads(obj_dill)
    return obj_str
