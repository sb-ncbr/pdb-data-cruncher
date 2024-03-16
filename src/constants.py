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
The string shorthand for unknown ligand type in rest or xml files.
"""
UNKNOWN_LIGAND_NAME = "unl"

"""
Max bucket count. High values may cause significant increase in run time while resulting in similarly sized
buckets because the fewer buckets had too little structures in them to be valid.
"""
DEFAULT_PLOT_SETTINGS_MAX_BUCKET_COUNT = 50


"""
Minimal structures needed in a bucket to be valid. When invalid buckets are found, lower bucket count is tried,
thus prolonging the calculation and resulting in fewer final buckets. Beware, higher value in combination with
lower/zero exclude quantile may result in one-bucket-captures-all result.
"""
DEFAULT_PLOT_SETTINGS_MIN_STRUCTURE_COUNT_IN_BUCKET = 50


"""
For the base x minimum and maximum value for creating the bucket size, only the min/max value that isn't outlier
is counted. The outlier threshold is based on mean value +- this multiplier times standard deviation.
Increasing this will result in larger interval being considered and wider buckets (but if the data is too sparse on
the sides to fullfill min structure count in buckets, it may result in smaller bucket count and even wider buckets).
"""
DEFAULT_PLOT_SETTINGS_STD_OUTLIER_MULTIPLIER = 2


"""
Bucket sizes will be allowed values only from this list multiplied by 10^n. The values need to be from interval <10,99>.
"""
DEFAULT_PLOT_SETTINGS_ALLOWED_BUCKET_BASE_SIZES = [10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90]
