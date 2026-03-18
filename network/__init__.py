"""
Copyright (C) 2024 Alexander "Naxela" Kleemann.
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

# file: network/__init__.py
# brief: Distributed rendering network package

from . import protocol
from .coordinator import TLM_Coordinator
from .worker import TLM_Worker
