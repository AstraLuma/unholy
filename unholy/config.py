"""
Handle Unholyfile parsing
"""
import io
import re
import tomlkit


def parse(text) -> tuple[dict, str]:
    """
    Given a text blob, pull out the head matter and parse it.
    """
    head, tail = _split_headmatter(text)
    head = tomlkit.parse(head)
    return head, tail


_DIVIDER = re.compile('^-{3,}$')


def _split_headmatter(text):
    head = ""
    tail = ""
    fobj = io.StringIO(text)
    first = next(fobj)
    if _DIVIDER.match(first.strip()):
        # We have headmatter
        for line in fobj:
            if _DIVIDER.match(line.strip()):
                break
            else:
                head += line
        else:
            return head, tail

    tail += fobj.read()
    return head, tail
