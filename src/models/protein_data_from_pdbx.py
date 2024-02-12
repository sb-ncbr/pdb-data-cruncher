from dataclasses import dataclass
from typing import Optional


# pylint: disable=too-many-instance-attributes
@dataclass(slots=True)
class ProteinDataFromPDBx:
    """
    Class holding data about protein extracted from pdbx files.
    """

    pdb_id: Optional[str] = None
    # general counts
    atom_count_without_hetatms: int = 0
    aa_count: int = 0
    all_atom_count: Optional[int] = None
    all_atom_count_ln: Optional[float] = None
    # hetero atom counts
    hetatm_count: int = 0
    hetatm_count_no_water: int = 0
    hetatm_count_metal: int = 0
    hetatm_count_no_metal: Optional[int] = None
    hetatm_count_no_water_no_metal: Optional[int] = None
    # ligand counts
    ligand_count: int = 0
    ligand_count_no_water: int = 0
    ligand_count_metal: int = 0
    ligand_count_no_metal: Optional[int] = None
    ligand_count_no_water_no_metal: Optional[int] = None
    # ligand ratios
    ligand_ratio: Optional[float] = None
    ligand_ratio_no_water: Optional[float] = None
    ligand_ratio_metal: Optional[float] = None
    ligand_ratio_no_metal: Optional[float] = None
    ligand_ratio_no_water_no_metal: Optional[float] = None
    # weights
    structure_weight_kda: Optional[float] = None
    polymer_weight_kda: float = 0.0
    nonpolymer_weight_no_water_da: float = 0.0
    water_weight_da: float = 0.0
    nonpolymer_weight_da: Optional[float] = None
    # other
    resolution: Optional[float] = None
    # additional data for future processing
    struct_keywords_text: Optional[list[str]] = None  # _struct_keywords.text
    struct_keywords_pdbx: Optional[str] = None  # _struct_keywords.pdbx_keywords
    experimental_method: Optional[str] = None  # _exptl.method
    citation_journal_abbreviation: Optional[str] = None  # _citation.journal_abbrev
    crystal_grow_methods: Optional[list[str]] = None  # _exptl_crystal_grow.method
    crystal_grow_temperatures: Optional[list[float]] = None  # _exptl_crystal_grow.temp
    crystal_grow_ph: Optional[float] = None  # _exptl_crystal_grow.pH
    diffraction_ambient_temperature: Optional[float] = None  # _diffrn.ambient_temp
    software_name: Optional[list[str]] = None  # _software.name
    gene_source_scientific_name: Optional[list[str]] = None  # _entity_src_gen.pdbx_gene_src_scientific_name
    host_organism_scientific_name: Optional[list[str]] = None  # _entity_src_gen.pdbx_host_org_scientific_name
    # TODO these three are used for calculating resolution - they may not be used for anything else though
    em_3d_reconstruction_resolution: Optional[float] = None  # _em_3d_reconstruction.resolution
    refinement_resolution_high: Optional[float] = None  # _refine.ls_d_res_high
    reflections_resolution_high: Optional[float] = None  # _reflns.d_resolution_high

