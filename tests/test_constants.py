import os.path

BASIC_TEST_PDB_IDS = [
    "1dey",
    "1i4c",
    "1vcr",
    "2dh1",
    "2pde",
    "2qz5",
    "3p4a",
    "3rec",
    "4v4a",
    "4v43",
    "5dh6",
    "5j7v",
    "5qej",
    "5zck",
    "7pin",
    "8ucv",
    "103d",
]
EXTENDED_TEST_PDB_IDS = [
    "1htq",
    "3zpm",
    "5tga",
    "6dwu",
    "7as5",
    "7y7a",
    "8ckb",
]
CRUNCHED_RESULTS_CSV_PATH = os.path.join(os.path.curdir, "tests", "test_data", "crunched_results.csv")
TEST_DATA_PATH = os.path.join(os.path.curdir, "tests", "test_data")