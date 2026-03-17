from typing import List, Tuple


# ------------------------------------------------------------------------------
# constants


train_sequence_length = 10
test_sequence_length = 10
target_complexity = 20
element_min = 0
element_max = 9


# ------------------------------------------------------------------------------
# utilities


def levenshtein_distance(list1: List[int], list2: List[int]) -> int:
    """
    Calculates the Levenshtein distance between two lists of integers.
    Uses a dynamic programming approach (Wagner-Fischer algorithm).
    """
    # Get the lengths of both input lists
    len1 = len(list1)
    len2 = len(list2)

    # Initialize a 2D matrix (list of lists) with dimensions (len1 + 1) x (len2 + 1)
    # The matrix will store the distances between prefixes of list1 and list2
    dp = [[0 for _ in range(len2 + 1)] for _ in range(len1 + 1)]

    # Populate the first column: cost of deleting elements from list1 to match an empty list2
    for i in range(len1 + 1):
        dp[i][0] = i

    # Populate the first row: cost of inserting elements into an empty list1 to match list2
    for j in range(len2 + 1):
        dp[0][j] = j

    # Iterate through each element of list1
    for i in range(1, len1 + 1):
        # Iterate through each element of list2
        for j in range(1, len2 + 1):
            # If the current elements match, no new operation is needed
            # The cost is the same as the cost without these two elements
            if list1[i - 1] == list2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                # If they do not match, take the minimum of three possible operations + 1:
                # 1. dp[i - 1][j] + 1 : Deletion
                # 2. dp[i][j - 1] + 1 : Insertion
                # 3. dp[i - 1][j - 1] + 1 : Substitution
                dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + 1)

    # The bottom-right cell contains the final Levenshtein distance
    return dp[len1][len2]


def validate_sequence(xs: List[int]) -> Tuple[bool, str]:
    out_of_range_elements = list(
        filter(lambda x: not (element_min <= x <= element_max), xs)
    )

    if not (len(out_of_range_elements) == 0):
        return (
            False,
            f"Some of the first elements of the generated sequence are not in the range {element_min}-{element_max}. The elements of the sequence are: {xs}. The particular elements that are not in the range {element_min}-{element_max} are: {out_of_range_elements}.",
        )

    nonintegral_elements = list(filter(lambda x: not (isinstance(x, int)), xs))

    if not (len(nonintegral_elements) == 0):
        return (
            False,
            f"Some of the elements of the generated sequence are not integers. The elements of the sequence are: {xs}. The particular elements that are not integers are: {nonintegral_elements}.",
        )

    return True, "The generated sequence is valid."
