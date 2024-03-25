# turning off black formatter to keep the elements more readable
# fmt: off
METAL_ELEMENT_NAMES = {
        "li", "na", "k", "rb", "cs", "fr",
        "be", "mg", "ca", "sr", "ba", "ra",
        "lu", "la", "ce", "pr", "nd", "pm", "sm", "eu", "gd", "tb", "dy", "ho", "er", "tm", "yb",
        "lr", "ac", "th", "pa", "u", "np", "pu", "am", "cm", "bk", "cf", "es", "fm", "md", "no",
        "sc", "ti", "v", "cr", "mn", "fe", "co", "ni", "cu", "zn",
        "y", "zr", "nb", "mo", "tc", "ru", "rh", "pd", "ag", "cd",
        "hf", "ta", "w", "re", "os", "ir", "pt", "au", "hg",
        "rf", "db", "sg", "bh", "hs", "cn",
        "al", "ga", "in", "sn", "tl", "pb", "bi", "po", "fl"
}
# fmt: on


"""
Holds all molecule types that are considered biopolymers for parsing rest molecules.
The comparison ignores upper/lower case differences.
"""
BIOPOLYMER_MOLECULE_TYPES = [
    "carbohydrate polymer",
    "polypeptide(l)",
    "polypeptide(d)",
    "polyribonucleotide",
    "polydeoxyribonucleotide",
    "polysaccharide(d)",
    "polysaccharide(l)",
    "polydeoxyribonucleotide/polyribonucleotide hybrid",
    "cyclic-pseudo-peptide",
    "peptide nucleic acid",
]


"""
The string shorthand for unknown ligand type in rest or xml files.
"""
UNKNOWN_LIGAND_NAME = "unl"
