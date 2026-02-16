# Copyright (c) 2026 Guiorgy
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import sys
import os
from enum import StrEnum
from dataclasses import dataclass, field
from typing import Self, Tuple, List, Dict, Optional, Union, Final, Type, Any


if sys.platform == 'win32':
    import msvcrt

    class _InputHandler:
        """Handle inputs on Windows"""

        Key = Optional[Union[str, bytes]]

        ASCII_ETX: Final[bytes] = b'\x03'
        ASCII_ESC: Final[bytes] = b'\x1b'

        WIN_CTRL_C: Final[bytes] = ASCII_ETX
        WIN_ESC_PREFIXES: Final[Tuple[bytes]] = (b'\x00', b'\xe0')
        WIN_ESCAPED_MAPPING: Final[Dict[bytes, str]] = {
            b'H': 'UP',
            b'P': 'DOWN',
            b'I': 'PGUP',
            b'Q': 'PGDN',
            b'G': 'HOME',
            b'O': 'END',
        }
        WIN_NORMAL_MAPPING: Final[Dict[bytes, str]] = {
            b' ': 'SPACE',
            b'\r': 'ENTER',
            ASCII_ESC: 'ESCAPE',
        }

        @classmethod
        def get_key(cls: Type) -> Key:
            key_code: bytes = msvcrt.getch()

            if key_code == cls.WIN_CTRL_C:
                raise KeyboardInterrupt

            if key_code in cls.WIN_ESC_PREFIXES:
                escape, key_code = key_code, msvcrt.getch()
                return cls.WIN_ESCAPED_MAPPING.get(key_code, escape + key_code)
            else:
                return cls.WIN_NORMAL_MAPPING.get(key_code, key_code)
else:
    import tty, termios

    class _InputHandler:
        """Handle inputs on Unix/Linux"""

        Key = Optional[Union[str, bytes]]

        ASCII_ETX: Final[str] = b'\x03'.decode('ascii')
        ASCII_ESC: Final[str] = b'\x1b'.decode('ascii')

        UNIX_CTRL_C: Final[str] = ASCII_ETX
        UNIX_ANSI_ESC: Final[str] = ASCII_ESC
        UNIX_CSI_PREFIX: Final[str] = '['
        UNIX_SS3_PREFIX: Final[str] = 'O'
        UNIX_VT_MAPPING: Final[Dict[str, Optional[str]]] = {
            '1~': 'HOME',
            '2~': 'INSERT',
            '3~': 'DELETE',
            '4~': 'END',
            '5~': 'PAGE_UP',
            '6~': 'PAGE_DOWN',
            '7~': 'HOME',
            '8~': 'END',
            '9~': None,
            '10~': 'F0',
            '11~': 'F1',
            '12~': 'F2',
            '13~': 'F3',
            '14~': 'F4',
            '15~': 'F5',
            '16~': None,
            '17~': 'F6',
            '18~': 'F7',
            '19~': 'F8',
            '20~': 'F9',
            '21~': 'F10',
            '22~': None,
            '23~': 'F11',
            '24~': 'F12',
            '25~': 'F13',
            '26~': 'F14',
            '27~': None,
            '28~': 'F15',
            '29~': 'F16',
            '30~': None,
            '31~': 'F17',
            '32~': 'F18',
            '33~': 'F19',
            '34~': 'F20',
            '35~': None,
        }
        UNIX_XTERM_MAPPING: Final[Dict[str, Optional[str]]] = {
            'A': 'UP',
            'B': 'DOWN',
            'C': 'RIGHT',
            'D': 'LEFT',
            'E': None,
            'F': 'END',
            'G': 'KEYPAD5',
            'H': 'HOME',
            'I': None,
            'J': None,
            'K': None,
            'L': None,
            'M': None,
            'N': None,
            'O': None,
            '1P': 'F1',
            '1Q': 'F2',
            '1R': 'F3',
            '1S': 'F4',
            'T': None,
            'U': None,
            'V': None,
            'W': None,
            'X': None,
            'Y': None,
            'Z': None,
        }
        UNIX_TERM_MAPPING: Final[Dict[str, Optional[str]]] = UNIX_VT_MAPPING | UNIX_XTERM_MAPPING
        UNIX_NORMAL_MAPPING: Final[Dict[str, str]] = {
            ' ': 'SPACE',
            '\r': 'ENTER',
            ASCII_ESC: 'ESCAPE',
        }

        @classmethod
        def get_key(cls: Type) -> Key:
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)

            try:
                tty.setraw(fd)
                char = sys.stdin.read(1)

                if char == cls.UNIX_CTRL_C:
                    raise KeyboardInterrupt

                if char == cls.UNIX_ANSI_ESC:
                    prefix = sys.stdin.read(1)

                    if prefix == cls.UNIX_CSI_PREFIX or prefix == cls.UNIX_SS3_PREFIX:
                        sequence: str = ''

                        for i in range(3):
                            sequence += sys.stdin.read(1)
                            key = cls.UNIX_TERM_MAPPING.get(sequence, '')
                            if key != '':
                                return key

                        return None
                    else:
                        return None
                else:
                    return cls.UNIX_NORMAL_MAPPING.get(char, char)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)


class _Term:
    """A collection of ANSI escape sequences for terminal control"""

    # Screen and Buffer
    ALT_SCREEN_ON: Final = '\033[?1049h'
    ALT_SCREEN_OFF: Final = '\033[?1049l'
    CLEAR_SCREEN: Final = '\033[2J'
    CLEAR_FROM_CURSOR: Final = '\033[J'
    CLEAR_LINE: Final = '\033[2K'
    HOME_CURSOR: Final = '\033[H'

    # Cursor Visibility
    HIDE_CURSOR: Final = '\033[?25l'
    SHOW_CURSOR: Final = '\033[?25h'

    # Formatting
    RESET: Final = '\033[0m'
    BOLD: Final = '\033[1m'
    class Color(StrEnum):
        DEFAULT: Final = ''
        BLACK: Final = '\033[30m'
        RED: Final = '\033[31m'
        GREEN: Final = '\033[32m'
        YELLOW: Final = '\033[33m'
        BLUE: Final = '\033[34m'
        PURPLE: Final = '\033[35m'
        CYAN: Final = '\033[36m'
        WHITE: Final = '\033[37m'

    @classmethod
    def enter_app_mode(cls: Type) -> None:
        """Sets up the terminal for a TUI (Alt screen, hidden cursor)"""

        sys.stdout.write(cls.ALT_SCREEN_ON + cls.HIDE_CURSOR + cls.HOME_CURSOR)
        cls.flush()

    @classmethod
    def exit_app_mode(cls: Type) -> None:
        """Restores the terminal to its original state"""

        sys.stdout.write(cls.SHOW_CURSOR + cls.ALT_SCREEN_OFF)
        cls.flush()

    @classmethod
    def move_home(cls: Type) -> None:
        """Moves the cursor to the home position"""

        sys.stdout.write(cls.HOME_CURSOR)

    @staticmethod
    def move_to(row: int, column: int = 0) -> None:
        """Moves the cursor to specific coordinates"""

        # The ANSI code is 1-based
        sys.stdout.write(f'\033[{row + 1};{column + 1}H')

    @classmethod
    def write(cls: Type, text: str, bold: bool = False, color: Color = Color.DEFAULT) -> None:
        """Write to stdout"""

        if not bold and color == cls.Color.DEFAULT:
            sys.stdout.write(text)
        else:
            sys.stdout.write(f'{(cls.BOLD if bold else '')}{color}{text}{cls.RESET}')

    @classmethod
    def write_line(cls: Type, text: str, bold: bool = False, color: Color = Color.DEFAULT) -> None:
        """A shorthand for write(f'{text}\n')"""

        cls.write(f'{text}\n', bold, color)

    @classmethod
    def overwrite_line(cls: Type, text: str = '', newline: bool = True, bold: bool = False, color: Color = Color.DEFAULT) -> None:
        """Writes text followed by a newline, clearing the line first to prevent ghosting"""

        sys.stdout.write(cls.CLEAR_LINE)
        cls.write(text, bold, color)
        if newline:
            sys.stdout.write('\n')

    @classmethod
    def clear_lines_after(cls: Type, row: Optional[int] = None) -> None:
        """Clears all lines below the current position, or from the given position"""

        if row is not None:
            cls.move_to(row + 1)

        cls.write(cls.CLEAR_FROM_CURSOR)

    @staticmethod
    def flush() -> None:
        """Flushes the stdout buffer"""

        sys.stdout.flush()


@dataclass(frozen=True)
class ChecklistItem:
    label: str
    checked: bool = False
    tag: Any = None

    label_lines: int = field(init=False)

    @property
    def height(self) -> int:
        return len(self.label_lines)

    def __post_init__(self) -> None:
        object.__setattr__(self, 'label_lines', self.label.split('\n'))

    def toggle(self, *, value: Optional[bool] = None) -> None:
        if value is None:
            value = not self.checked

        object.__setattr__(self, 'checked', value)

    def __len__(self) -> int:
        return len(self.label_lines)


_CHECKLIST_ITEM_LIKE_TYPES: Final[Type] = Union[Tuple[str, bool, Any], Tuple[str, bool], Tuple[str, Any], str]
def _make_checklist_item(obj: Union[ChecklistItem, _CHECKLIST_ITEM_LIKE_TYPES]) -> ChecklistItem:
    """Tries to convert an object to a ChecklistItem"""

    if isinstance(obj, ChecklistItem):
        return obj
    elif isinstance(obj, Tuple):
        if len(obj) >= 2 and isinstance(obj[0], str):
            if len(obj) == 3:
                if isinstance(obj[1], bool):
                    return ChecklistItem(label=obj[0], checked=obj[1], tag=obj[2])
            elif len(obj) == 2:
                if isinstance(obj[1], bool):
                    return ChecklistItem(label=obj[0], checked=obj[1], tag=None)
                else:
                    return ChecklistItem(label=obj[0], checked=False, tag=obj[1])
    elif isinstance(obj, str):
        return ChecklistItem(label=obj, checked=False, tag=None)

    raise TypeError(f'Can not make ChecklistItem from {obj}')


@dataclass(frozen=True)
class _ItemRange:
    first: int
    last: int
    height: int

    def __len__(self) -> int:
        return self.last - self.first + 1


def tui_checklist(
    items: List[Union[ChecklistItem, _CHECKLIST_ITEM_LIKE_TYPES]],
    header: Optional[str] = None,
    item_margin: int = 0,
    truncate_lines: bool = False
) -> Optional[List[str]]:
    """
    Renders a cross-platform TUI checkbox list.
    :param items: List of selection items.
    :param header: Optional description text to show above instructions.
    :param item_margin: Number of empty lines between items.
    :param truncate_lines: Truncates lines that don't fit into the current viewport.
    """

    items = [_make_checklist_item(item) for item in items]
    items = [ChecklistItem(item.label, item.checked, i if item.tag is None else item.tag) for i, item in enumerate(items)]

    _Term.enter_app_mode()
    try:
        terminal_width: int = 0
        terminal_height: int = 0
        usable_height: int = 0
        visible_range: Optional[_ItemRange] = None
        scroll_max: int = 0

        current_position: int = 0

        def truncate(line: str, offset: int = 0) -> str:
            """Truncates and adds ellipsis to a line if truncate_lines is True"""

            if truncate_lines and offset + len(line) > terminal_width:
                line = line[:(terminal_width - offset - 3)] + '...'

            return line

        def render_error(message: str) -> None:
            """Renders a red error message at the top of the viewport"""

            _Term.move_home()
            _Term.overwrite_line(message, bold=True, color=_Term.Color.RED)
            _Term.overwrite_line('Press any key to continue', color=_Term.Color.YELLOW)
            _Term.overwrite_line()
            key = _InputHandler.get_key()
            if key == 'ESCAPE':
                raise KeyboardInterrupt

        def render_viewport_too_small_error() -> None:
            render_error('The viewport is too small to render the list\nResize the terminal before continuing')

        def get_visible_range(position: int, to: bool = False) -> Optional[_ItemRange]:
            """Determines which items can fit in the viewport starting from or up to the given position"""

            visible_last: int = -1
            visible_height: int = -item_margin # the first item doesn't need any margin

            check_range = range(position, len(items)) if not to else range(position, -1, -1)
            for i in check_range:
                next_height = visible_height + item_margin + items[i].height

                if next_height > usable_height:
                    break

                visible_last = i
                visible_height = next_height

            if visible_last != -1:
                if not to:
                    return _ItemRange(first=position, last=visible_last, height=visible_height)
                else:
                    return _ItemRange(first=visible_last, last=position, height=visible_height)

            return None

        def scroll_to(new_position: int) -> None:
            """Scrolls to the given position and recalculates the visible range"""

            nonlocal visible_range

            if new_position < 0 or scroll_max < new_position:
                raise ValueError(f'Can only scroll between 0 and {scroll_max}, but tried to scroll to {new_position}')

            visible_range = get_visible_range(new_position)

            if not visible_range:
                render_viewport_too_small_error()

        def scroll_up() -> None:
            """Scrolls up by 1 item (with wrap around)"""

            nonlocal visible_range

            if visible_range.first == 0:
                scroll_to(scroll_max)
            else:
                visible_height = visible_range.height + item_margin + items[visible_range.first - 1].height
                visible_first = visible_range.first - 1
                visible_last = visible_range.last

                # Hide as many items as needed to show the newly scrolled item
                while visible_first <= visible_last and visible_height > usable_height:
                    visible_height -= item_margin + items[visible_last].height
                    visible_last -= 1

                if visible_height > usable_height:
                    visible_range = None
                    render_viewport_too_small_error()

                visible_range = _ItemRange(first=visible_first, last=visible_last, height=visible_height)

                if not visible_range:
                    render_viewport_too_small_error()

        def scroll_down() -> None:
            """Scrolls up by 1 item (with wrap around)"""

            nonlocal visible_range

            if visible_range.first == scroll_max:
                scroll_to(0)
            else:
                visible_height = visible_range.height + item_margin + items[visible_range.last + 1].height
                visible_first = visible_range.first
                visible_last = visible_range.last + 1

                # Hide as many items as needed to show the newly scrolled item
                while visible_first <= visible_last and visible_height > usable_height:
                    visible_height -= item_margin + items[visible_first].height
                    visible_first += 1

                if visible_height > usable_height:
                    visible_range = None
                    render_viewport_too_small_error()

                # We may be able to show more items
                for i in range(visible_last + 1, len(items)):
                    next_height = visible_height + item_margin + items[i].height

                    if next_height > usable_height:
                        break

                    visible_last = i
                    visible_height = next_height

                visible_range = _ItemRange(first=visible_first, last=visible_last, height=visible_height)

                if not visible_range:
                    render_viewport_too_small_error()

        def render_item(item_position: int, max_lines: Optional[int] = None) -> None:
            """Renders the given ChecklistItem, optionally limiting the number of rencered lines"""

            if max_lines is not None and max_lines < 1:
                raise ValueError('max_lines can not be less than 1')

            SELECTION_MARKER: Final[str] = '>'
            NO_MARKER: Final[str] = ' ' * len(SELECTION_MARKER)
            SELECTION_MARKER_SEPARATOR: Final[str] = ' '
            UNCHECKED_CHECKBOX: Final[str] = '[ ]' # must be same length as CHECKED_CHECKBOX
            CHECKED_CHECKBOX: Final[str] = '[X]' # must be same length as UNCHECKED_CHECKBOX
            CHECKBOX_SEPARATOR: Final[str] = ' '
            OTHER_LINES_INDENTATION: Final[str] = ' ' * (len(SELECTION_MARKER) + len(SELECTION_MARKER_SEPARATOR) + len(CHECKED_CHECKBOX) + len(CHECKBOX_SEPARATOR))

            item = items[item_position]

            marker = (SELECTION_MARKER + SELECTION_MARKER_SEPARATOR) if item_position == current_position else (NO_MARKER + SELECTION_MARKER_SEPARATOR)
            _Term.overwrite_line(marker, newline=False)
            if item.checked:
                _Term.write(CHECKED_CHECKBOX + CHECKBOX_SEPARATOR, color=_Term.Color.GREEN)
            else:
                _Term.write(UNCHECKED_CHECKBOX + CHECKBOX_SEPARATOR)
            _Term.write_line(truncate(item.label_lines[0], len(OTHER_LINES_INDENTATION)))

            for line in item.label_lines[1:(len(item) if max_lines is None else max_lines - 1)]:
                _Term.overwrite_line(truncate(f'{OTHER_LINES_INDENTATION}{line}'))

        def render_item_margin() -> None:
            """Renders the margin between list items"""

            for _ in range(item_margin):
                _Term.overwrite_line()

        instructions: Final = '(Arrows: Move, Space: Toggle, PgUp/Dn: Scroll, Home/End: Jump, Enter: Save, Esc/Ctrl+C: Cancel)'
        header_lines: Final[List[str]] = header.split('\n') + [instructions]

        while True:
            # Redraw the header and recalculate the viewport if terminal dimensions change (or it's the first time)
            _terminal_width, _terminal_height = os.get_terminal_size()
            if terminal_width != _terminal_width or terminal_height != _terminal_height:
                if not truncate_lines and _terminal_width < max(max(len(line) for line in header_lines), max(len(item) for item in items)):
                    render_viewport_too_small_error()
                    continue

                terminal_width, terminal_height = _terminal_width, _terminal_height

                # Render the header
                _Term.move_home()
                for line in header_lines:
                    _Term.overwrite_line(truncate(line), bold=True, color=_Term.Color.CYAN)
                _Term.overwrite_line()

                # Reserve 3 lines for header/footer margins and status bar in the footer
                usable_height = terminal_height - len(header_lines) - 3

                # Precalculate the furthest scrollable position while keeping the last item visible
                scroll_max_vr = get_visible_range(to=True, position=len(items) - 1)
                if scroll_max_vr:
                    scroll_max = scroll_max_vr.first
                else:
                    render_viewport_too_small_error()
                    terminal_width, terminal_height = 0, 0
                    continue

                visible_range = get_visible_range(visible_range.first if visible_range is not None else current_position)

            # Scroll to ensure current selection is within view bounds
            if not visible_range or current_position < visible_range.first or visible_range.last < current_position:
                scroll_to(current_position)

            if not visible_range:
                render_viewport_too_small_error()
                continue

            # Move cursor to the start of the list viewport
            _Term.move_to(len(header_lines) + 1)

            # Render the fully visible list items
            render_item(visible_range.first)
            for i in range(visible_range.first + 1, visible_range.last + 1):
                render_item_margin()
                render_item(i)

            # Partially render the next item if there's room for at least 1 line of the item
            remaining_height = usable_height - visible_range.height
            if remaining_height > item_margin and visible_range.last + 1 < len(items):
                render_item_margin()
                render_item(visible_range.last + 1, remaining_height - item_margin)

            _Term.clear_lines_after()

            # Draw the footer
            _Term.move_to(terminal_height - 1)
            _Term.overwrite_line(truncate(f'>{current_position + 1} {visible_range.first + 1}-{visible_range.last + 1}/{len(items)}'), newline=False, bold=True, color=_Term.Color.CYAN)

            _Term.flush()

            # Input Handling
            key = _InputHandler.get_key()
            if key == 'UP':
                if current_position == visible_range.first:
                    scroll_up()

                current_position = (current_position - 1) % len(items)
            elif key == 'DOWN':
                if current_position == visible_range.last:
                    scroll_down()

                current_position = (current_position + 1) % len(items)
            elif key == 'HOME':
                scroll_to(0)
                current_position = 0
            elif key == 'END':
                scroll_to(scroll_max)
                current_position = len(items) - 1
            elif key in ('PGUP', 'PGDN'):
                if not visible_range:
                    continue

                if key == 'PGDN':
                    if visible_range.first == scroll_max:
                        current_position = len(items) - 1
                        continue

                    new_scroll = min(scroll_max, visible_range.last + 1)
                else: # PGUP
                    if visible_range.first == 0:
                        current_position = 0
                        continue

                    new_vr = get_visible_range(to=True, position=visible_range.first - 1)
                    if not new_vr:
                        render_viewport_too_small_error()
                        continue

                    new_scroll = new_vr.first

                selection_ratio = 0.0
                if len(visible_range) > 1:
                    selection_ratio = (current_position - visible_range.first) / (visible_range.last - visible_range.first)

                scroll_to(new_scroll)
                if not visible_range:
                    render_viewport_too_small_error()
                    current_position = new_scroll
                    continue

                current_position = visible_range.first + int(selection_ratio * (len(visible_range) - 1))
            elif key == 'SPACE':
                items[current_position].toggle()
            elif key == 'ENTER':
                break
            elif key == 'ESCAPE':
                raise KeyboardInterrupt

    except KeyboardInterrupt:
        return None
    finally:
        _Term.exit_app_mode()

    return [item.tag for item in items if item.checked]
