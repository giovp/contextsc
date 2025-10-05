"""Registry of core scverse packages."""

from dataclasses import dataclass
from enum import Enum


class PackageCategory(str, Enum):
    """Category of scverse package."""

    DATA_FORMAT = "data_format"
    ANALYSIS = "analysis"


@dataclass(frozen=True)
class ScversePackage:
    """Metadata for a scverse package.

    Attributes
    ----------
    name : str
        Package name (import name).
    display_name : str
        Human-readable display name.
    description : str
        Brief description of the package.
    category : PackageCategory
        Package category (data format or analysis).
    github_url : str
        URL to the GitHub repository.
    docs_url : str
        URL to the documentation.
    """

    name: str
    display_name: str
    description: str
    category: PackageCategory
    github_url: str
    docs_url: str


@dataclass(frozen=True)
class ScverseDataFormatPackage(ScversePackage):
    """Scverse data format package.

    Data format packages provide data structures for storing and manipulating
    single-cell and spatial omics data.
    """

    def __init__(self, name: str, display_name: str, description: str, github_url: str, docs_url: str):
        """Initialize data format package."""
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "display_name", display_name)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "category", PackageCategory.DATA_FORMAT)
        object.__setattr__(self, "github_url", github_url)
        object.__setattr__(self, "docs_url", docs_url)


@dataclass(frozen=True)
class ScverseAnalysisPackage(ScversePackage):
    """Scverse analysis package.

    Analysis packages provide tools and algorithms for analyzing single-cell
    and spatial omics data.
    """

    def __init__(self, name: str, display_name: str, description: str, github_url: str, docs_url: str):
        """Initialize analysis package."""
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "display_name", display_name)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "category", PackageCategory.ANALYSIS)
        object.__setattr__(self, "github_url", github_url)
        object.__setattr__(self, "docs_url", docs_url)


# Core scverse data format packages
DATA_FORMAT_PACKAGES = [
    ScverseDataFormatPackage(
        name="anndata",
        display_name="AnnData",
        description="Annotated data matrices for single-cell analysis",
        github_url="https://github.com/scverse/anndata",
        docs_url="https://anndata.readthedocs.io/",
    ),
    ScverseDataFormatPackage(
        name="mudata",
        display_name="MuData",
        description="Multimodal omics data structure",
        github_url="https://github.com/scverse/mudata",
        docs_url="https://mudata.readthedocs.io/",
    ),
    ScverseDataFormatPackage(
        name="spatialdata",
        display_name="SpatialData",
        description="Spatial omics data framework",
        github_url="https://github.com/scverse/spatialdata",
        docs_url="https://spatialdata.scverse.org/",
    ),
]

# Core scverse analysis packages
ANALYSIS_PACKAGES = [
    ScverseAnalysisPackage(
        name="scanpy",
        display_name="Scanpy",
        description="Scalable toolkit for analyzing single-cell gene expression data",
        github_url="https://github.com/scverse/scanpy",
        docs_url="https://scanpy.readthedocs.io/",
    ),
    ScverseAnalysisPackage(
        name="squidpy",
        display_name="Squidpy",
        description="Spatial molecular data analysis and visualization",
        github_url="https://github.com/scverse/squidpy",
        docs_url="https://squidpy.readthedocs.io/",
    ),
    ScverseAnalysisPackage(
        name="muon",
        display_name="Muon",
        description="Multimodal omics analysis framework",
        github_url="https://github.com/scverse/muon",
        docs_url="https://muon.readthedocs.io/",
    ),
    ScverseAnalysisPackage(
        name="scvi-tools",
        display_name="scvi-tools",
        description="Deep learning models for single-cell omics data analysis",
        github_url="https://github.com/yoseflab/scvi-tools",
        docs_url="https://docs.scvi-tools.org/",
    ),
    ScverseAnalysisPackage(
        name="scirpy",
        display_name="Scirpy",
        description="Single-cell TCR and BCR analysis toolkit",
        github_url="https://github.com/scverse/scirpy",
        docs_url="https://scirpy.scverse.org/",
    ),
    ScverseAnalysisPackage(
        name="snapatac2",
        display_name="SnapATAC2",
        description="Single-cell ATAC-seq analysis pipeline",
        github_url="https://github.com/scverse/SnapATAC2",
        docs_url="https://scverse.org/SnapATAC2/",
    ),
    ScverseAnalysisPackage(
        name="rapids_singlecell",
        display_name="rapids-singlecell",
        description="GPU-accelerated single-cell analysis",
        github_url="https://github.com/scverse/rapids_singlecell",
        docs_url="https://rapids-singlecell.readthedocs.io/",
    ),
    ScverseAnalysisPackage(
        name="pertpy",
        display_name="pertpy",
        description="Perturbation analysis for single-cell experiments",
        github_url="https://github.com/scverse/pertpy",
        docs_url="https://pertpy.readthedocs.io/",
    ),
    ScverseAnalysisPackage(
        name="decoupler",
        display_name="decoupler",
        description="Enrichment analysis from omics data",
        github_url="https://github.com/scverse/decoupler",
        docs_url="https://decoupler.readthedocs.io/",
    ),
]

# All core scverse packages
CORE_SCVERSE_PACKAGES = DATA_FORMAT_PACKAGES + ANALYSIS_PACKAGES


def get_package_by_name(name: str) -> ScversePackage | None:
    """Get package metadata by name.

    Parameters
    ----------
    name : str
        Package name to look up.

    Returns
    -------
    ScversePackage | None
        Package metadata if found, None otherwise.
    """
    for package in CORE_SCVERSE_PACKAGES:
        if package.name.lower() == name.lower():
            return package
    return None
