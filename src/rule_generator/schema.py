"""
Konveyor Analyzer Rule Schema

Pydantic models for Konveyor analyzer-lsp rule format.
Based on: https://github.com/konveyor/analyzer-lsp/blob/main/docs/rules.md
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum


class Category(str, Enum):
    """Rule category indicating migration impact."""
    MANDATORY = "mandatory"
    POTENTIAL = "potential"
    OPTIONAL = "optional"


class LocationType(str, Enum):
    """Java provider location types."""
    IMPORT = "IMPORT"
    PACKAGE = "PACKAGE"
    CONSTRUCTOR_CALL = "CONSTRUCTOR_CALL"
    METHOD_CALL = "METHOD_CALL"
    TYPE = "TYPE"
    INHERITANCE = "INHERITANCE"
    ANNOTATION = "ANNOTATION"


class JavaReferenced(BaseModel):
    """Java provider condition for referenced code."""
    pattern: str = Field(..., description="Pattern to match (supports wildcards)")
    location: Optional[LocationType] = Field(None, description="Where to look for the pattern")


class JavaDependency(BaseModel):
    """Java provider condition for dependencies."""
    name: str = Field(..., description="Dependency name (e.g., 'junit.junit')")
    upperbound: Optional[str] = Field(None, description="Upper version bound")
    lowerbound: Optional[str] = Field(None, description="Lower version bound")


class BuiltinFileContent(BaseModel):
    """Builtin provider for file content search."""
    pattern: str = Field(..., description="Regex pattern to search for")
    filePattern: Optional[str] = Field(None, description="File pattern (e.g., '*.properties')")


class BuiltinFile(BaseModel):
    """Builtin provider for file pattern matching."""
    pattern: str = Field(..., description="File pattern to match")


class BuiltinXML(BaseModel):
    """Builtin provider for XML content."""
    xpath: str = Field(..., description="XPath expression")
    filepaths: Optional[List[str]] = Field(None, description="File paths to search")


# When condition can be a provider condition or logical operator
WhenCondition = Union[
    Dict[str, Union['JavaReferenced', 'JavaDependency', 'BuiltinFileContent', 'BuiltinFile', 'BuiltinXML', List['WhenCondition']]],
    List['WhenCondition']
]


class Link(BaseModel):
    """Reference link for additional information."""
    url: str = Field(..., description="URL to documentation")
    title: str = Field(..., description="Link title/description")


class AnalyzerRule(BaseModel):
    """Konveyor analyzer rule definition."""
    ruleID: str = Field(..., description="Unique rule identifier")
    description: str = Field(..., description="Short problem description")
    effort: int = Field(..., ge=1, le=10, description="Migration effort (1-10)")
    category: Category = Field(default=Category.POTENTIAL)
    labels: List[str] = Field(default_factory=list, description="Rule labels (e.g., 'konveyor.io/source=java-ee')")
    when: Dict[str, Any] = Field(..., description="Condition for rule application")
    message: str = Field(..., description="Violation message with migration guidance")
    links: Optional[List[Link]] = Field(default=None, description="Reference documentation links")
    customVariables: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Custom variable definitions")
    tag: Optional[List[str]] = Field(default=None, description="Tags to add when rule matches")


class AnalyzerRuleset(BaseModel):
    """Collection of analyzer rules (YAML list format)."""
    rules: List[AnalyzerRule] = Field(default_factory=list)


class MigrationPattern(BaseModel):
    """
    Extracted migration pattern from documentation.

    This is the intermediate representation used during LLM extraction,
    before converting to AnalyzerRule format.
    """
    # Core pattern info
    source_pattern: str = Field(..., description="What to look for (e.g., '@Stateless')")
    target_pattern: Optional[str] = Field(None, description="What to replace with (e.g., '@ApplicationScoped'). May be null for removals.")
    rationale: str = Field(..., description="Why this change is needed")

    # For generating 'when' conditions
    source_fqn: Optional[str] = Field(None, description="Fully qualified name (e.g., 'javax.ejb.Stateless')")
    location_type: Optional[LocationType] = Field(None, description="Where to look (ANNOTATION, IMPORT, etc.)")

    # Alternative FQNs (for or conditions - javax vs jakarta)
    alternative_fqns: Optional[List[str]] = Field(default_factory=list, description="Alternative FQNs (e.g., jakarta.ejb.Stateless)")

    # Metadata
    complexity: str = Field(..., description="Migration complexity (trivial, low, medium, high, expert)")
    category: str = Field(..., description="Rule category")

    # Optional context
    example_before: Optional[str] = Field(None, description="Example code before migration")
    example_after: Optional[str] = Field(None, description="Example code after migration")
    documentation_url: Optional[str] = Field(None, description="Reference documentation URL")
