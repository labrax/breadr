"""Breadr is a pipeline helper"""
__version__ = "0.1"
__all__ = ['crumb', 'CrumbRepository']
__slice_serializer_version__ = 2

from crumb.decorator import crumb
from crumb.repository import CrumbRepository
