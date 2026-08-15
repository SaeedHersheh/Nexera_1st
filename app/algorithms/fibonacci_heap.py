from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class FibonacciNode:
    key: float
    value: Any

    degree: int = 0
    mark: bool = False

    parent: "FibonacciNode | None" = None
    child: "FibonacciNode | None" = None

    left: "FibonacciNode | None" = None
    right: "FibonacciNode | None" = None

    def __post_init__(self):
        self.left = self
        self.right = self


class FibonacciHeap:
    def __init__(self):
        self.min_node: FibonacciNode | None = None
        self.total_nodes = 0

    def is_empty(self) -> bool:
        return self.min_node is None

    def insert(
        self,
        key: float,
        value: Any,
    ) -> FibonacciNode:

        node = FibonacciNode(
            key=key,
            value=value,
        )

        self._add_to_root_list(node)

        if (
            self.min_node is None
            or node.key < self.min_node.key
        ):
            self.min_node = node

        self.total_nodes += 1

        return node

    def minimum(self) -> FibonacciNode | None:
        return self.min_node

    def extract_min(self) -> FibonacciNode | None:
        z = self.min_node

        if z is None:
            return None

        # Move all children of min to root list.
        if z.child is not None:
            children = list(
                self._iterate(z.child)
            )

            for child in children:
                self._remove_from_list(child)

                child.parent = None
                child.mark = False

                self._add_to_root_list(child)

            z.child = None

        next_root = z.right

        self._remove_from_list(z)

        if z == next_root:
            self.min_node = None
        else:
            self.min_node = next_root
            self._consolidate()

        self.total_nodes -= 1

        z.left = z
        z.right = z

        return z

    def decrease_key(
        self,
        node: FibonacciNode,
        new_key: float,
    ):
        if new_key > node.key:
            raise ValueError(
                "New key is greater than current key."
            )

        node.key = new_key

        parent = node.parent

        if (
            parent is not None
            and node.key < parent.key
        ):
            self._cut(
                node,
                parent,
            )

            self._cascading_cut(
                parent
            )

        if (
            self.min_node is None
            or node.key < self.min_node.key
        ):
            self.min_node = node

    def _add_to_root_list(
        self,
        node: FibonacciNode,
    ):
        node.parent = None

        if self.min_node is None:
            node.left = node
            node.right = node
            self.min_node = node

            return

        node.left = self.min_node
        node.right = self.min_node.right

        self.min_node.right.left = node
        self.min_node.right = node

    def _remove_from_list(
        self,
        node: FibonacciNode,
    ):
        node.left.right = node.right
        node.right.left = node.left

    def _iterate(
        self,
        start: FibonacciNode,
    ):
        current = start

        while True:
            yield current

            current = current.right

            if current == start:
                break

    def _link(
        self,
        child: FibonacciNode,
        parent: FibonacciNode,
    ):
        self._remove_from_list(child)

        child.left = child
        child.right = child

        child.parent = parent
        child.mark = False

        if parent.child is None:
            parent.child = child
        else:
            first_child = parent.child

            child.left = first_child
            child.right = first_child.right

            first_child.right.left = child
            first_child.right = child

        parent.degree += 1

    def _consolidate(self):
        if self.min_node is None:
            return

        degree_table = {}

        roots = list(
            self._iterate(
                self.min_node
            )
        )

        for node in roots:

            # Node might already have been linked
            # under another root.
            if node.parent is not None:
                continue

            x = node
            degree = x.degree

            while degree in degree_table:
                y = degree_table[degree]

                if x.key > y.key:
                    x, y = y, x

                self._link(
                    y,
                    x,
                )

                del degree_table[degree]

                degree += 1

            degree_table[degree] = x

        # Rebuild root list.
        self.min_node = None

        for node in degree_table.values():
            node.left = node
            node.right = node
            node.parent = None

            if self.min_node is None:
                self.min_node = node
            else:
                self._add_to_root_list(
                    node
                )

                if (
                    node.key
                    < self.min_node.key
                ):
                    self.min_node = node

    def _cut(
        self,
        node: FibonacciNode,
        parent: FibonacciNode,
    ):
        if (
            parent.child == node
        ):
            if node.right == node:
                parent.child = None
            else:
                parent.child = node.right

        self._remove_from_list(node)

        parent.degree -= 1

        node.left = node
        node.right = node

        node.parent = None
        node.mark = False

        self._add_to_root_list(node)

    def _cascading_cut(
        self,
        node: FibonacciNode,
    ):
        parent = node.parent

        if parent is None:
            return

        if not node.mark:
            node.mark = True

            return

        self._cut(
            node,
            parent,
        )

        self._cascading_cut(
            parent
        )
