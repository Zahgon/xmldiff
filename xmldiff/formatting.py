import json
import re

from collections import namedtuple
from copy import deepcopy
from lxml import etree
from xmldiff.diff_match_patch import diff_match_patch
from xmldiff import utils


DIFF_NS = "http://namespaces.shoobx.com/diff"
DIFF_PREFIX = "diff"

INSERT_NAME = "{%s}insert" % DIFF_NS
DELETE_NAME = "{%s}delete" % DIFF_NS
REPLACE_NAME = "{%s}replace" % DIFF_NS
RENAME_NAME = "{%s}rename" % DIFF_NS

# Flags for whitespace handling in the text aware formatters:
WS_BOTH = 3  # Normalize ignorable whitespace and text whitespace
WS_TEXT = 2  # Normalize whitespace only inside text tags
WS_TAGS = 1  # Delete ignorable whitespace (between tags)
WS_NONE = 0  # Preserve all whitespace

# Placeholder tag type
T_OPEN = 0
T_CLOSE = 1
T_SINGLE = 2

# This is the start of the BMP(0) private use area.
# If you end up having more than 6400 different tags inside text tags
# this will bleed over to non private use area, but that's highly
# unlikely. However, once we have dropped support for Python versions
# that have narrow builds, we can change this to 0xf00000, which is
# the start of two 64,000 private use blocks.
# PY3: Once Python 2.7 support is dropped we should change this to 0xf00000
PLACEHOLDER_START = 0xE000


# These Bases can be abstract baseclasses, but it's a pain to support
# Python 2.7 in that case, because there is no abc.ABC. Right now this
# is just a description of the API.


class BaseFormatter:
    def __init__(self, normalize=WS_TAGS, pretty_print=False):
        """Formatters must as a minimum have a normalize parameter

        This is used by the main API to decide is whitespace between the
        tags should be stripped (the remove_blank_text flag in lxml) and
        if tags that are known texts tags should be normalized before
        comparing. String content in non-text tags will not be
        normalized with the included formatters.

        pretty_print is used to choose between a compact and a pretty output.
        This is currently only used by the XML and HTML formatters.

        Formatters may of course have more options than these, but these
        two are the ones that can be set from the command-line.
        """

    def prepare(self, left_tree, right_tree):
        """Allows the formatter to prepare the trees before diffing

        That preparing may need some "unpreparing", but it's then done
        by the formatters format() method, and is not a part of the
        public interface."""

    def format(self, diff, orig_tree):
        """Formats the diff and returns a unicode string

        A formatter that returns XML with diff markup will need the original
        tree available to do it's job, so there is an orig_tree parameter,
        but it may be ignored by differs that don't need it.
        """


PlaceholderEntry = namedtuple("PlaceholderEntry", "element ttype close_ph")


class PlaceholderMaker:
    """Replace tags with unicode placeholders

    This class searches for certain tags in an XML tree and replaces them
    with unicode placeholders. The idea is to replace structured content
    (in this case XML elements) with unicode characters which then
    participate in the regular text diffing algorithm. This makes text
    diffing easier and faster.

    The code can then unreplace the unicode placeholders with the tags.
    """

    def __init__(self, text_tags=(), formatting_tags=()):
        self.text_tags = text_tags
        self.formatting_tags = formatting_tags
        self.placeholder2tag = {}
        self.tag2placeholder = {}
        self.placeholder = PLACEHOLDER_START

        insert_elem = etree.Element(INSERT_NAME)
        insert_close = self.get_placeholder(insert_elem, T_CLOSE, None)
        insert_open = self.get_placeholder(insert_elem, T_OPEN, insert_close)

        delete_elem = etree.Element(DELETE_NAME)
        delete_close = self.get_placeholder(delete_elem, T_CLOSE, None)
        delete_open = self.get_placeholder(delete_elem, T_OPEN, delete_close)

        replace_elem = etree.Element(REPLACE_NAME)
        replace_close = self.get_placeholder(replace_elem, T_CLOSE, None)
        replace_open = self.get_placeholder(replace_elem, T_OPEN, replace_close)

        self.diff_tags = {
            "insert": (insert_open, insert_close),
            "delete": (delete_open, delete_close),
            "replace": (replace_open, replace_close),
        }

    def get_placeholder(self, element, ttype, close_ph):
        tag = etree.tounicode(element)
        ph = self.tag2placeholder.get((tag, ttype, close_ph))
        if ph is not None:
            return ph

        self.placeholder += 1
        ph = chr(self.placeholder)
        self.placeholder2tag[ph] = PlaceholderEntry(element, ttype, close_ph)
        self.tag2placeholder[tag, ttype, close_ph] = ph
        return ph

    def is_placeholder(self, char):
        pass

    def is_formatting(self, element):
        return element.tag in self.formatting_tags

    def do_element(self, element):
        for child in element:
            # Resolve all formatting text by allowing the inside text to
            # participate in the text diffing.
            tail = child.tail or ""
            child.tail = ""
            new_text = element.text or ""

            if self.is_formatting(child):
                ph_close = self.get_placeholder(child, T_CLOSE, None)
                ph_open = self.get_placeholder(child, T_OPEN, ph_close)
                # If it's known text formatting tags, do this hierarchically
                self.do_element(child)
                text = child.text or ""
                child.text = ""
                # Stick the placeholder in instead of the start and end tags:
                element.text = new_text + ph_open + text + ph_close + tail
            else:
                ph_single = self.get_placeholder(child, T_SINGLE, None)
                # Replace the whole tag including content:
                element.text = new_text + ph_single + tail

            # Remove the element from the tree now that we have inserted a
            # placeholder.
            element.remove(child)

    def do_tree(self, tree):
        if self.text_tags:
            for elem in tree.xpath("//" + "|//".join(self.text_tags)):
                self.do_element(elem)

    def split_string(self, text):
        pass

    def undo_string(self, text):
        pass

    def undo_element(self, elem):
        pass

    def undo_tree(self, tree):
        pass

    def mark_diff(self, ph, action, attributes=None):
        pass

    def wrap_diff(self, text, action, attributes=None):
        pass


class XMLFormatter(BaseFormatter):
    """A formatter that also replaces formatting tags with unicode characters

    The idea of this differ is to replace structured content (in this case XML
    elements) with unicode characters which then participate in the regular
    text diffing algorithm. This is done in the prepare() step.

    Each identical XML element will get a unique unicode character. If the
    node is changed for any reason, a new unicode character is assigned to the
    node. This allows identity detection of structured content between the
    two text versions while still allowing customization during diffing time,
    such as marking a new formatting node. The latter feature allows for
    granular style change detection independently of text changes.

    In order for the algorithm to not go crazy and convert entire XML
    documents to text (though that is perfectly doable), a few rules have been
    defined.

    - The `textTags` attribute lists all the XML nodes by name which can
      contain text. All XML nodes within those text nodes are converted to
      unicode placeholders. If you want better control over which parts of
      your XML document are considered text, you can simply override the
      ``insert_placeholders(tree)`` function. It is purposefully kept small to
      allow easy subclassing.

    - By default, all tags inside text tags are treated as immutable
      units. That means the node itself including its entire sub-structure is
      assigned one unicode character.

    - The ``formattingTags`` attribute is used to specify tags that format the
      text. For these tags, the opening and closing tags receive unique
      unicode characters, allowing for sub-structure change detection and
      formatting changes. During the diff markup phase, formatting notes are
      annotated to mark them as inserted or deleted allowing for markup
      specific to those formatting changes.

    The diffed version of the structural tree is passed into the
    ``finalize(tree)`` method to convert all the placeholders back into
    structural content before formatting.

    The ``normalize`` parameter decides how to normalize whitespace.
    WS_TEXT normalizes only inside text_tags, WS_TAGS will remove ignorable
    whitespace between tags, WS_BOTH do both, and WS_NONE will preserve
    all whitespace.

    The ``use_replace`` flag decides, if a replace tag (with the old text
    as an attribute) should be used instead of one delete and one insert tag.
    """

    def __init__(
        self,
        normalize=WS_NONE,
        pretty_print=True,
        text_tags=(),
        formatting_tags=(),
        use_replace=False,
    ):
        # Mapping from placeholders -> structural content and vice versa.
        self.normalize = normalize
        self.pretty_print = pretty_print
        self.text_tags = text_tags
        self.formatting_tags = formatting_tags
        self.use_replace = use_replace
        self.placeholderer = PlaceholderMaker(
            text_tags=text_tags, formatting_tags=formatting_tags
        )

    def prepare(self, left_tree, right_tree):
        """prepare() is run on the trees before diffing

        This is so the formatter can apply magic before diffing."""
        # We don't want to diff comments:
        self._remove_comments(left_tree)
        self._remove_comments(right_tree)

        self.placeholderer.do_tree(left_tree)
        self.placeholderer.do_tree(right_tree)

    def finalize(self, result_tree):
        """finalize() is run on the resulting tree before returning it

        This is so the formatter cab apply magic after diffing."""
        pass

    def format(self, diff, orig_tree, differ=None):
        # Make a new tree, both because we want to add the diff namespace
        # and also because we don't want to modify the original tree.
        pass

    def render(self, result):
        pass

    def handle_action(self, action, result):
        action_type = type(action)
        method = getattr(self, "_handle_" + action_type.__name__)
        method(action, result)

    def _remove_comments(self, tree):
        comments = tree.xpath("//comment()")

        for element in comments:
            parent = element.getparent()
            if parent is None:
                # We can't remove top level comments, but they won't
                # be iterated over anyway, so we just skip them.
                continue
            parent.remove(element)

    def _xpath(self, node, xpath):
        # This method finds an element with xpath and makes sure that
        # one and exactly one element is found. This is to protect against
        # formatting a diff on the wrong tree, or against using ambiguous
        # edit script xpaths.

        # First, make a namespace map that uses the left tree's URI's:
        pass

    def _extend_diff_attr(self, node, action, value):
        pass

    def _delete_attrib(self, node, name):
        pass

    def _handle_DeleteAttrib(self, action, tree):
        pass

    def _delete_node(self, node):
        pass

    def _handle_DeleteNode(self, action, tree):
        pass

    def _insert_attrib(self, node, name, value):
        pass

    def _handle_InsertAttrib(self, action, tree):
        pass

    def _insert_node(self, target, node, position):
        pass

    def _get_real_insert_position(self, target, position):
        # Find the real position:
        pass

    def _handle_InsertNode(self, action, tree):
        # Insert node as a child. However, position is the position in the
        # new tree, and the diff tree may have deleted children, so we must
        # adjust the position for that.
        pass

    def _rename_attrib(self, node, oldname, newname):
        pass

    def _handle_RenameAttrib(self, action, tree):
        pass

    def _handle_MoveNode(self, action, tree):
        pass

    def _handle_RenameNode(self, action, tree):
        pass

    def _update_attrib(self, node, name, value):
        pass

    def _handle_UpdateAttrib(self, action, tree):
        pass

    def _realign_placeholders(self, diff):
        # Since the differ always deletes first and insert second,
        # placeholders that represent XML open and close tags will get
        # misaligned. This method will fix that order.
        pass

    def _join_delete_insert(self, diffs):
        pass

    def _make_diff_tags(self, left_value, right_value, node, target=None):
        pass

    def _handle_UpdateTextIn(self, action, tree):
        pass

    def _handle_UpdateTextAfter(self, action, tree):
        pass

    def _handle_InsertNamespace(self, action, tree):
        # There is no way to mark this so it's visible, so we'll just update the tree
        pass

    def _handle_DeleteNamespace(self, action, tree):
        # This will be handled by the namespace cleanup
        pass

    # There is no InsertComment handler, as this formatter removes all comments


class DiffFormatter(BaseFormatter):
    def __init__(self, normalize=WS_TAGS, pretty_print=False):
        self.normalize = normalize
        # No pretty print support, nothing to be pretty about

    # Nothing to prepare or finalize (one-liners for code coverage)
    def prepare(self, left, right):
        return

    def finalize(self, left, right):
        pass

    def format(self, diff, orig_tree):
        # This Formatter don't need the left tree, but the XMLFormatter
        # does, so the parameter is required.
        pass

    def _format_action(
        self,
        action,
    ):
        pass

    def handle_action(self, action):
        action_type = type(action)
        method = getattr(self, "_handle_" + action_type.__name__)
        return ", ".join(method(action))

    def _handle_DeleteAttrib(self, action):
        pass

    def _handle_DeleteNode(self, action):
        pass

    def _handle_InsertAttrib(self, action):
        pass

    def _handle_InsertNode(self, action):
        pass

    def _handle_RenameAttrib(self, action):
        pass

    def _handle_MoveNode(self, action):
        pass

    def _handle_UpdateAttrib(self, action):
        pass

    def _handle_UpdateTextIn(self, action):
        pass

    def _handle_UpdateTextAfter(self, action):
        pass

    def _handle_RenameNode(self, action):
        pass

    def _handle_InsertComment(self, action):
        pass

    def _handle_InsertNamespace(self, action):
        pass

    def _handle_DeleteNamespace(self, action):
        pass


class XmlDiffFormatter(BaseFormatter):
    """A formatter for an output trying to be xmldiff 0.6 compatible"""

    def __init__(self, normalize=WS_TAGS, pretty_print=False):
        self.normalize = normalize
        # No pretty print support, nothing to be pretty about

    # Nothing to prepare or finalize (one-liners for code coverage)
    def prepare(self, left, right):
        return

    def finalize(self, left, right):
        pass

    def format(self, diff, orig_tree):
        # This Formatter don't need the left tree, but the XMLFormatter
        # does, so the parameter is required.
        pass

    def _format_action(self, action):
        pass

    def handle_action(self, action, orig_tree):
        action_type = type(action)
        method = getattr(self, "_handle_" + action_type.__name__)
        yield from method(action, orig_tree)

    def _handle_DeleteAttrib(self, action, orig_tree):
        pass

    def _handle_DeleteNode(self, action, orig_tree):
        pass

    def _handle_InsertAttrib(self, action, orig_tree):
        pass

    def _handle_InsertNode(self, action, orig_tree):
        pass

    def _handle_RenameAttrib(self, action, orig_tree):
        pass

    def _handle_MoveNode(self, action, orig_tree):
        pass

    def _handle_UpdateAttrib(self, action, orig_tree):
        pass

    def _handle_UpdateTextIn(self, action, orig_tree):
        pass

    def _handle_UpdateTextAfter(self, action, orig_tree):
        pass

    def _handle_RenameNode(self, action, orig_tree):
        pass

    def _handle_InsertComment(self, action, orig_tree):
        pass

    def _handle_InsertNamespace(self, action, orig_tree):
        pass

    def _handle_DeleteNamespace(self, action, orig_tree):
        pass
