from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
from collections.abc import Iterator


@dataclass
class _Element:
    tag: str
    classes: frozenset[str] = frozenset()
    children: list[_Element | str] = field(default_factory=list)
    parent: _Element | None = field(default=None, repr=False)

    def select(self, class_name: str, tag: str | None = None) -> Iterator[_Element]:
        for child in self.children:
            if isinstance(child, _Element):
                if class_name in child.classes and (tag is None or child.tag == tag):
                    yield child
                yield from child.select(class_name, tag)

    def strings(self) -> Iterator[str]:
        for child in self.children:
            if isinstance(child, str):
                if text := child.strip():
                    yield text
            elif child.tag not in {"script", "style", "template"}:
                yield from child.strings()

    def ancestor(self, tag: str) -> _Element | None:
        node = self.parent
        while node is not None and node.tag != tag:
            node = node.parent
        return node


class CalendarHTMLParser(HTMLParser):
    """Minimal tree for the selectors used by the SAVNO calendar."""

    _VOID = frozenset("area base br col embed hr img input link meta param source track wbr".split())

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Element("")
        self._stack = [self.root]

    def _append(self, tag: str, attrs: list[tuple[str, str | None]]) -> _Element:
        parent = self._stack[-1]
        node = _Element(tag, frozenset((dict(attrs).get("class") or "").split()), parent=parent)
        parent.children.append(node)
        return node

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = self._append(tag, attrs)
        if tag not in self._VOID:
            self._stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._append(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self._stack) - 1, 0, -1):
            if self._stack[index].tag == tag:
                del self._stack[index:]
                break

    def handle_data(self, data: str) -> None:
        self._stack[-1].children.append(data)
