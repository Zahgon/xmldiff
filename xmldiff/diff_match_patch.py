#!/usr/bin/python3

"""Diff Match and Patch
Copyright 2018 The diff-match-patch Authors.
https://github.com/google/diff-match-patch

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

"""Functions for diff, match and patch.

Computes the difference between two texts to create a patch.
Applies the patch onto another text, allowing for errors.
"""

__author__ = "fraser@google.com (Neil Fraser)"

import re
import sys
import time
import urllib.parse


class diff_match_patch:
    """Class containing the diff, match and patch methods.

    Also contains the behaviour settings.
    """

    def __init__(self):
        """Inits a diff_match_patch object with default settings.
        Redefine these in your program to override the defaults.
        """

        # Number of seconds to map a diff before giving up (0 for infinity).
        self.Diff_Timeout = 1.0
        # Cost of an empty edit operation in terms of edit characters.
        self.Diff_EditCost = 4
        # At what point is no match declared (0.0 = perfection, 1.0 = very loose).
        self.Match_Threshold = 0.5
        # How far to search for a match (0 = exact location, 1000+ = broad match).
        # A match this many characters away from the expected location will add
        # 1.0 to the score (0.0 is a perfect match).
        self.Match_Distance = 1000
        # When deleting a large block of text (over ~64 characters), how close do
        # the contents have to be to match the expected contents. (0.0 = perfection,
        # 1.0 = very loose).  Note that Match_Threshold controls how closely the
        # end points of a delete need to match.
        self.Patch_DeleteThreshold = 0.5
        # Chunk size for context length.
        self.Patch_Margin = 4

        # The number of bits in an int.
        # Python has no maximum, thus to disable patch splitting set to 0.
        # However to avoid long patches in certain pathological cases, use 32.
        # Multiple short patches (using native ints) are much faster than long ones.
        self.Match_MaxBits = 32

    #  DIFF FUNCTIONS

    # The data structure representing a diff is an array of tuples:
    # [(DIFF_DELETE, "Hello"), (DIFF_INSERT, "Goodbye"), (DIFF_EQUAL, " world.")]
    # which means: delete "Hello", add "Goodbye" and keep " world."
    DIFF_DELETE = -1
    DIFF_INSERT = 1
    DIFF_EQUAL = 0
    DIFF_REPLACE = 2

    def diff_main(self, text1, text2, checklines=True, deadline=None):
        """Find the differences between two texts.  Simplifies the problem by
          stripping any common prefix or suffix off the texts before diffing.

        Args:
          text1: Old string to be diffed.
          text2: New string to be diffed.
          checklines: Optional speedup flag.  If present and false, then don't run
            a line-level diff first to identify the changed areas.
            Defaults to true, which does a faster, slightly less optimal diff.
          deadline: Optional time when the diff should be complete by.  Used
            internally for recursive calls.  Users should set DiffTimeout instead.

        Returns:
          Array of changes.
        """
        pass

    def diff_compute(self, text1, text2, checklines, deadline):
        """Find the differences between two texts.  Assumes that the texts do not
          have any common prefix or suffix.

        Args:
          text1: Old string to be diffed.
          text2: New string to be diffed.
          checklines: Speedup flag.  If false, then don't run a line-level diff
            first to identify the changed areas.
            If true, then run a faster, slightly less optimal diff.
          deadline: Time when the diff should be complete by.

        Returns:
          Array of changes.
        """
        pass

    def diff_lineMode(self, text1, text2, deadline):
        """Do a quick line-level diff on both strings, then rediff the parts for
          greater accuracy.
          This speedup can produce non-minimal diffs.

        Args:
          text1: Old string to be diffed.
          text2: New string to be diffed.
          deadline: Time when the diff should be complete by.

        Returns:
          Array of changes.
        """
        pass

    def diff_bisect(self, text1, text2, deadline):
        """Find the 'middle snake' of a diff, split the problem in two
          and return the recursively constructed diff.
          See Myers 1986 paper: An O(ND) Difference Algorithm and Its Variations.

        Args:
          text1: Old string to be diffed.
          text2: New string to be diffed.
          deadline: Time at which to bail if not yet complete.

        Returns:
          Array of diff tuples.
        """
        pass

    def diff_bisectSplit(self, text1, text2, x, y, deadline):
        """Given the location of the 'middle snake', split the diff in two parts
        and recurse.

        Args:
          text1: Old string to be diffed.
          text2: New string to be diffed.
          x: Index of split point in text1.
          y: Index of split point in text2.
          deadline: Time at which to bail if not yet complete.

        Returns:
          Array of diff tuples.
        """
        pass

    def diff_linesToChars(self, text1, text2):
        """Split two texts into an array of strings.  Reduce the texts to a string
        of hashes where each Unicode character represents one line.

        Args:
          text1: First string.
          text2: Second string.

        Returns:
          Three element tuple, containing the encoded text1, the encoded text2 and
          the array of unique strings.  The zeroth element of the array of unique
          strings is intentionally blank.
        """
        pass

    def diff_charsToLines(self, diffs, lineArray):
        """Rehydrate the text in a diff from a string of line hashes to real lines
        of text.

        Args:
          diffs: Array of diff tuples.
          lineArray: Array of unique strings.
        """
        pass

    def diff_commonPrefix(self, text1, text2):
        """Determine the common prefix of two strings.

        Args:
          text1: First string.
          text2: Second string.

        Returns:
          The number of characters common to the start of each string.
        """
        pass

    def diff_commonSuffix(self, text1, text2):
        """Determine the common suffix of two strings.

        Args:
          text1: First string.
          text2: Second string.

        Returns:
          The number of characters common to the end of each string.
        """
        pass

    def diff_commonOverlap(self, text1, text2):
        """Determine if the suffix of one string is the prefix of another.

        Args:
          text1 First string.
          text2 Second string.

        Returns:
          The number of characters common to the end of the first
          string and the start of the second string.
        """
        pass

    def diff_halfMatch(self, text1, text2):
        """Do the two texts share a substring which is at least half the length of
        the longer text?
        This speedup can produce non-minimal diffs.

        Args:
          text1: First string.
          text2: Second string.

        Returns:
          Five element Array, containing the prefix of text1, the suffix of text1,
          the prefix of text2, the suffix of text2 and the common middle.  Or None
          if there was no match.
        """
        pass

    def diff_cleanupSemantic(self, diffs):
        """Reduce the number of edits by eliminating semantically trivial
        equalities.

        Args:
          diffs: Array of diff tuples.
        """
        pass

    def diff_cleanupSemanticLossless(self, diffs):
        """Look for single edits surrounded on both sides by equalities
        which can be shifted sideways to align the edit to a word boundary.
        e.g: The c<ins>at c</ins>ame. -> The <ins>cat </ins>came.

        Args:
          diffs: Array of diff tuples.
        """
        pass

    # Define some regex patterns for matching boundaries.
    BLANKLINEEND = re.compile(r"\n\r?\n$")
    BLANKLINESTART = re.compile(r"^\r?\n\r?\n")

    def diff_cleanupEfficiency(self, diffs):
        """Reduce the number of edits by eliminating operationally trivial
        equalities.

        Args:
          diffs: Array of diff tuples.
        """
        pass

    def diff_cleanupMerge(self, diffs):
        """Reorder and merge like edit sections.  Merge equalities.
        Any edit section can move as long as it doesn't cross an equality.

        Args:
          diffs: Array of diff tuples.
        """
        pass

    def diff_xIndex(self, diffs, loc):
        """loc is a location in text1, compute and return the equivalent location
        in text2.  e.g. "The cat" vs "The big cat", 1->1, 5->8

        Args:
          diffs: Array of diff tuples.
          loc: Location within text1.

        Returns:
          Location within text2.
        """
        pass

    def diff_prettyHtml(self, diffs):
        """Convert a diff array into a pretty HTML report.

        Args:
          diffs: Array of diff tuples.

        Returns:
          HTML representation.
        """
        pass

    def diff_text1(self, diffs):
        """Compute and return the source text (all equalities and deletions).

        Args:
          diffs: Array of diff tuples.

        Returns:
          Source text.
        """
        pass

    def diff_text2(self, diffs):
        """Compute and return the destination text (all equalities and insertions).

        Args:
          diffs: Array of diff tuples.

        Returns:
          Destination text.
        """
        pass

    def diff_levenshtein(self, diffs):
        """Compute the Levenshtein distance; the number of inserted, deleted or
        substituted characters.

        Args:
          diffs: Array of diff tuples.

        Returns:
          Number of changes.
        """
        pass

    def diff_toDelta(self, diffs):
        """Crush the diff into an encoded string which describes the operations
        required to transform text1 into text2.
        E.g. =3\t-2\t+ing  -> Keep 3 chars, delete 2 chars, insert 'ing'.
        Operations are tab-separated.  Inserted text is escaped using %xx notation.

        Args:
          diffs: Array of diff tuples.

        Returns:
          Delta text.
        """
        pass

    def diff_fromDelta(self, text1, delta):
        """Given the original text1, and an encoded string which describes the
        operations required to transform text1 into text2, compute the full diff.

        Args:
          text1: Source string for the diff.
          delta: Delta text.

        Returns:
          Array of diff tuples.

        Raises:
          ValueError: If invalid input.
        """
        pass

    #  MATCH FUNCTIONS

    def match_main(self, text, pattern, loc):
        """Locate the best instance of 'pattern' in 'text' near 'loc'.

        Args:
          text: The text to search.
          pattern: The pattern to search for.
          loc: The location to search around.

        Returns:
          Best match index or -1.
        """
        pass

    def match_bitap(self, text, pattern, loc):
        """Locate the best instance of 'pattern' in 'text' near 'loc' using the
        Bitap algorithm.

        Args:
          text: The text to search.
          pattern: The pattern to search for.
          loc: The location to search around.

        Returns:
          Best match index or -1.
        """
        pass

    def match_alphabet(self, pattern):
        """Initialise the alphabet for the Bitap algorithm.

        Args:
          pattern: The text to encode.

        Returns:
          Hash of character locations.
        """
        pass

    #  PATCH FUNCTIONS

    def patch_addContext(self, patch, text):
        """Increase the context until it is unique,
        but don't let the pattern expand beyond Match_MaxBits.

        Args:
          patch: The patch to grow.
          text: Source text.
        """
        pass

    def patch_make(self, a, b=None, c=None):
        """Compute a list of patches to turn text1 into text2.
        Use diffs if provided, otherwise compute it ourselves.
        There are four ways to call this function, depending on what data is
        available to the caller:
        Method 1:
        a = text1, b = text2
        Method 2:
        a = diffs
        Method 3 (optimal):
        a = text1, b = diffs
        Method 4 (deprecated, use method 3):
        a = text1, b = text2, c = diffs

        Args:
          a: text1 (methods 1,3,4) or Array of diff tuples for text1 to
              text2 (method 2).
          b: text2 (methods 1,4) or Array of diff tuples for text1 to
              text2 (method 3) or undefined (method 2).
          c: Array of diff tuples for text1 to text2 (method 4) or
              undefined (methods 1,2,3).

        Returns:
          Array of Patch objects.
        """
        pass

    def patch_deepCopy(self, patches):
        """Given an array of patches, return another array that is identical.

        Args:
          patches: Array of Patch objects.

        Returns:
          Array of Patch objects.
        """
        pass

    def patch_apply(self, patches, text):
        """Merge a set of patches onto the text.  Return a patched text, as well
        as a list of true/false values indicating which patches were applied.

        Args:
          patches: Array of Patch objects.
          text: Old text.

        Returns:
          Two element Array, containing the new text and an array of boolean values.
        """
        pass

    def patch_addPadding(self, patches):
        """Add some padding on text start and end so that edges can match
        something.  Intended to be called only from within patch_apply.

        Args:
          patches: Array of Patch objects.

        Returns:
          The padding string added to each side.
        """
        pass

    def patch_splitMax(self, patches):
        """Look through the patches and break up any which are longer than the
        maximum limit of the match algorithm.
        Intended to be called only from within patch_apply.

        Args:
          patches: Array of Patch objects.
        """
        pass

    def patch_toText(self, patches):
        """Take a list of patches and return a textual representation.

        Args:
          patches: Array of Patch objects.

        Returns:
          Text representation of patches.
        """
        pass

    def patch_fromText(self, textline):
        """Parse a textual representation of patches and return a list of patch
        objects.

        Args:
          textline: Text representation of patches.

        Returns:
          Array of Patch objects.

        Raises:
          ValueError: If invalid input.
        """
        pass


class patch_obj:
    """Class representing one patch operation."""

    def __init__(self):
        """Initializes with an empty list of diffs."""
        self.diffs = []
        self.start1 = None
        self.start2 = None
        self.length1 = 0
        self.length2 = 0

    def __str__(self):
        """Emulate GNU diff's format.
        Header: @@ -382,8 +481,9 @@
        Indices are printed as 1-based, not 0-based.

        Returns:
          The GNU diff string.
        """
        if self.length1 == 0:
            coords1 = str(self.start1) + ",0"
        elif self.length1 == 1:
            coords1 = str(self.start1 + 1)
        else:
            coords1 = str(self.start1 + 1) + "," + str(self.length1)
        if self.length2 == 0:
            coords2 = str(self.start2) + ",0"
        elif self.length2 == 1:
            coords2 = str(self.start2 + 1)
        else:
            coords2 = str(self.start2 + 1) + "," + str(self.length2)
        text = ["@@ -", coords1, " +", coords2, " @@\n"]
        # Escape the body of the patch with %xx notation.
        for op, data in self.diffs:
            if op == diff_match_patch.DIFF_INSERT:
                text.append("+")
            elif op == diff_match_patch.DIFF_DELETE:
                text.append("-")
            elif op == diff_match_patch.DIFF_EQUAL:
                text.append(" ")
            # High ascii will raise UnicodeDecodeError.  Use Unicode instead.
            data = data.encode("utf-8")
            text.append(urllib.parse.quote(data, "!~*'();/?:@&=+$,# ") + "\n")
        return "".join(text)
