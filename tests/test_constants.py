from os import path

BASIC_TEST_PDB_IDS = [
    "1dey",
    "1i4c",
    "1vcr",
    "2dh1",
    "2pde",
    "2qz5",
    "3p4a",
    "3rec",
    "5dh6",
    "5j7v",
    "5qej",
    "5zck",
    "8ucv",
    "103d",
]
EXTENDED_TEST_PDB_IDS = [
    "1kvp",
    "1htq",
    "3zpm",
    "5tga",
    "6dwu",
    "7as5",
    "7y7a",
    "8ckb",
    "4v4a",
    "4v43",
    "7pin",
]
CRUNCHED_RESULTS_CSV_PATH = path.join(path.curdir, "tests", "test_data", "crunched_results.csv")
TEST_DATA_PATH = path.join(path.curdir, "tests", "test_data")
BASIC_TEST_DATA_PATH = path.join(TEST_DATA_PATH, "basic")
EXTENDED_TEST_DATA_PATH = path.join(TEST_DATA_PATH, "extended")
