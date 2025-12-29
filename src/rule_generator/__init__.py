"""
Analyzer Rule Generator

Generate Konveyor analyzer rules from migration guides using LLMs.
"""

from .ingestion import GuideIngester
from .schema import AnalyzerRule, AnalyzerRuleset, Category, LocationType, MigrationPattern

__version__ = "0.1.0"
__all__ = [
    "GuideIngester",
    "AnalyzerRule",
    "AnalyzerRuleset",
    "MigrationPattern",
    "Category",
    "LocationType",
]
