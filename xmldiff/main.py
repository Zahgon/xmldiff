"""All major API points and command-line tools"""

from importlib import metadata

from argparse import ArgumentParser, ArgumentTypeError
from lxml import etree
from xmldiff import diff, formatting, patch

__version__ = metadata.version("xmldiff")

FORMATTERS = {
    "diff": formatting.DiffFormatter,
    "xml": formatting.XMLFormatter,
    "old": formatting.XmlDiffFormatter,
}


def diff_trees(left, right, diff_options=None, formatter=None):
    """Takes two lxml root elements or element trees"""
    if formatter is not None:
        formatter.prepare(left, right)
    if diff_options is None:
        diff_options = {}
    differ = diff.Differ(**diff_options)
    diffs = differ.diff(left, right)

    if formatter is None:
        return list(diffs)

    return formatter.format(diffs, left)


def _diff(parse_method, left, right, diff_options=None, formatter=None):
    normalize = bool(getattr(formatter, "normalize", 1) & formatting.WS_TAGS)
    parser = etree.XMLParser(remove_blank_text=normalize)
    left_tree = parse_method(left, parser)
    right_tree = parse_method(right, parser)
    return diff_trees(
        left_tree, right_tree, diff_options=diff_options, formatter=formatter
    )


def diff_texts(left, right, diff_options=None, formatter=None):
    """Takes two Unicode strings containing XML"""
    return _diff(
        etree.fromstring, left, right, diff_options=diff_options, formatter=formatter
    )


def diff_files(left, right, diff_options=None, formatter=None):
    """Takes two filenames or streams, and diffs the XML in those files"""
    return _diff(
        etree.parse, left, right, diff_options=diff_options, formatter=formatter
    )


def validate_F(arg):
    """Type function for argparse - a float within some predefined bounds"""
    pass


def make_diff_parser():
    pass


def _parse_uniqueattrs(uniqueattrs):
    pass


def _parse_ignored_attrs(ignored_attrs):
    pass


def diff_command(args=None):
    pass


def patch_tree(actions, tree):
    """Takes an lxml root element or element tree, and a list of actions"""
    patcher = patch.Patcher()
    return patcher.patch(actions, tree)


def patch_text(actions, tree):
    """Takes a string with XML and a string with actions"""
    tree = etree.fromstring(tree)
    actions = patch.DiffParser().parse(actions)
    tree = patch_tree(actions, tree)
    return etree.tounicode(tree)


def patch_file(actions, tree, diff_encoding=None):
    """Takes two filenames or streams, one with XML the other a diff"""
    tree = etree.parse(tree)

    if isinstance(actions, str):
        # It's a string, so it's a filename
        with open(actions, "rt", encoding=diff_encoding) as f:
            actions = f.read()
    else:
        # We assume it's a stream
        actions = actions.read()

    actions = patch.DiffParser().parse(actions)
    tree = patch_tree(actions, tree)
    return etree.tounicode(tree)


def make_patch_parser():
    pass


def patch_command(args=None):
    pass
