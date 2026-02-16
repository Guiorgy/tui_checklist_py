# tui_checklist_py

A simple crossplatform scrollable TUI checklist selection in pure Python.

> [!WARNING]
> This is a simple-ish implementation of a checklist TUI.
> It assumes the terminal supports ANSI escape sequences.
> It does not attempt to render items that are too large in either dimension, only rendering an error requesting for a larger terminal window.
> At most, you may enable the `truncate_lines` option to truncate lines that don't fit horizontally.
> It's best to ensure that the checklist items are small enough to fit the terminal yourself.

## Usage

The `tui_checklist` accepts 3 arguments:

- `items`: The items to render
- `header`: The header text to render at the top if the checklist
- `item_margin`: The number of empty lines to render between each item
- `truncate_lines`: Truncates lines that don't fit into the terminal

The items in the checklist are defined as a list of `ChecklistItem(label: str, checked: bool, tag: Any)`, where `label` is the text to render next to the checkbox, `checked` is whether the item should be initially checked, and `tag` is anything user defined that will be returned when selection is made. If `tag` is not defined, it default to the item index in the list.

The items can also be passed as a list of:

- `Tuple[str, bool, Any]`: Equivalent to `ChecklistItem(tuple[0], tuple[1], tuple[2])`
- `Tuple[str, bool]`: Equivalent to `ChecklistItem(tuple[0], tuple[1], None)`
- `Tuple[str, Any]`: Equivalent to `ChecklistItem(tuple[0], False, tuple[1])`
- `str`: Equivalent to `ChecklistItem(str, False, None)`

## Demo

```python
#!/usr/bin/env python

from tui_checklist import tui_checklist


def main() -> None:
    results = tui_checklist(
        header="Please select some of the following options",
        items=[(f"Option {i}\nSub-description {i}", i % 10 == 0) for i in range(1, 100)],
        item_margin=1,
        truncate_lines=False
    )
    if results is not None:
        print(f"Selection saved: {len(results)} items:")
        for tag in results:
            print(tag)
    else:
        print("Selection cancelled.")


if __name__ == '__main__':
    main()
```

```
Please select some of the following options
(Arrows: Move, Space: Toggle, PgUp/Dn: Scroll, Home/End: Jump, Enter: Save, Esc/Ctrl+C: Cancel)

> [ ] Option 1
      Sub-description 1

  [ ] Option 2
      Sub-description 2

  [ ] Option 3
      Sub-description 3

  [ ] Option 4
      Sub-description 4

  [ ] Option 5
      Sub-description 5

  [ ] Option 6
      Sub-description 6

  [ ] Option 7
      Sub-description 7

  [ ] Option 8
      Sub-description 8

  [ ] Option 9
      Sub-description 9

  [X] Option 10
      Sub-description 10

  [ ] Option 11
      Sub-description 11

  [ ] Option 12
      Sub-description 12

  [ ] Option 13
      Sub-description 13

  [ ] Option 14
      Sub-description 14

  [ ] Option 15
      Sub-description 15

  [ ] Option 16
      Sub-description 16


>1 1-16/99
```

```
Selection saved: 9 items:
9
19
29
39
49
59
69
79
89
```

## LICENSE

> Copyright (c) 2026 Guiorgy
>
> This Source Code Form is subject to the terms of the Mozilla Public
> License, v. 2.0. If a copy of the MPL was not distributed with this
> file, You can obtain one at http://mozilla.org/MPL/2.0/.
