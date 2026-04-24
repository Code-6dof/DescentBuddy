"""Settings dialog — configures paths and INI flags for Descent 1 and Descent 2.

Opened by clicking the game icon on the Launch panel. Path configuration is
shown for both games simultaneously. INI flag editing applies to the active game.
"""

import shutil
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.app_config import load_config, save_config
from core.game_detector import Game, config_key, data_dir, display_name, ini_names, ini_prefix
from core.ini_manager import IniManager


class SettingsDialog(QDialog):
    """Modal settings dialog showing path configuration for both D1 and D2.

    Call open_for(game, exe_path) before exec() to set the active game context.
    Path fields for both games are always shown. INI flag editing applies to
    whichever game the dialog was opened for.
    """

    exe_path_changed = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(720, 620)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint
        )

        self._game: Game = Game.D1
        self._exe_path: str = ""
        self._ini: IniManager | None = None
        self._controls: dict = {}
        self._loading = False

        # Per-game path controls — populated in _build_game_paths_section
        self._ini_path_edit: dict[Game, QLineEdit] = {}
        self._ini_status_label: dict[Game, QLabel] = {}
        self._activate_btn: dict[Game, QPushButton] = {}
        self._gamelog_path_edit: dict[Game, QLineEdit] = {}
        self._gamelog_status_label: dict[Game, QLabel] = {}
        self._netlog_path_edit: dict[Game, QLineEdit] = {}
        self._netlog_status_label: dict[Game, QLabel] = {}
        self._missions_dir_edit: dict[Game, QLineEdit] = {}
        self._missions_dir_status: dict[Game, QLabel] = {}
        self._archive_path_edit: dict[Game, QLineEdit] = {}
        self._archive_status: dict[Game, QLabel] = {}
        self._enable_log_btn: dict[Game, QPushButton] = {}

        self._build_ui()

    def open_for(self, game: Game, exe_path: str) -> None:
        """Set the active game context and refresh all fields."""
        self._game = game
        self._exe_path = exe_path
        self.setWindowTitle("Settings")
        self._exe_path_display.setText(exe_path or "No executable selected")
        self._ini_flags_heading.setText(f"{display_name(game).upper()} — INI FLAGS")
        self._clear_fields()
        exe_dir = Path(exe_path).parent if exe_path else None
        for g in Game:
            self._restore_ini_path(g)
            self._restore_gamelog_path(g)
            self._restore_netlog_path(g)
            self._restore_missions_settings(g)
            self._detect_missing_paths(g, exe_dir if g == game else None)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 28, 32, 20)
        outer.setSpacing(0)

        title = QLabel("Settings")
        title.setObjectName("panel-title")
        outer.addWidget(title)

        outer.addSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        content.setObjectName("settings-content")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 16, 16)
        layout.setSpacing(0)

        self._build_exe_section(layout)
        layout.addSpacing(20)

        for game in Game:
            self._build_game_paths_section(layout, game)
            layout.addSpacing(20)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(divider)
        layout.addSpacing(16)

        self._ini_flags_heading = QLabel("INI FLAGS")
        self._ini_flags_heading.setObjectName("section-label")
        layout.addWidget(self._ini_flags_heading)
        layout.addSpacing(10)

        self._build_basic_settings(layout)
        layout.addSpacing(16)

        self._advanced_toggle = QPushButton("ADVANCED  [show]")
        self._advanced_toggle.setObjectName("settings-collapse-btn")
        self._advanced_toggle.setCheckable(True)
        self._advanced_toggle.setChecked(False)
        self._advanced_toggle.clicked.connect(self._toggle_advanced)
        layout.addWidget(self._advanced_toggle)

        self._advanced_container = QWidget()
        self._advanced_container.setObjectName("settings-content")
        adv_layout = QVBoxLayout(self._advanced_container)
        adv_layout.setContentsMargins(0, 14, 0, 0)
        adv_layout.setSpacing(0)
        self._build_advanced_settings(adv_layout)
        self._advanced_container.setVisible(False)
        layout.addWidget(self._advanced_container)

        layout.addSpacing(20)

        divider2 = QFrame()
        divider2.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(divider2)
        layout.addSpacing(16)

        self._build_discord_section(layout)

        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _build_exe_section(self, layout: QVBoxLayout) -> None:
        heading = QLabel("EXECUTABLE")
        heading.setObjectName("section-label")
        layout.addWidget(heading)

        layout.addSpacing(6)

        row = QHBoxLayout()
        row.setSpacing(8)

        self._exe_path_display = QLabel("No executable selected")
        self._exe_path_display.setObjectName("exe-path-display")
        self._exe_path_display.setWordWrap(True)
        row.addWidget(self._exe_path_display, 1)

        change_btn = QPushButton("Change...")
        change_btn.setFixedWidth(80)
        change_btn.clicked.connect(self._browse_exe)
        row.addWidget(change_btn)

        layout.addLayout(row)

    def _build_game_paths_section(self, layout: QVBoxLayout, game: Game) -> None:
        """Build the INI/gamelog/netlog/missions path rows for one game."""
        heading = QLabel(display_name(game).upper())
        heading.setObjectName("section-label")
        layout.addWidget(heading)

        layout.addSpacing(10)

        # INI file
        ini_row = QHBoxLayout()
        ini_row.setSpacing(8)

        ini_edit = QLineEdit()
        ini_edit.setPlaceholderText("INI path — auto-detected from game data directory")
        ini_edit.editingFinished.connect(lambda g=game: self._on_ini_path_changed(g))
        ini_row.addWidget(ini_edit, 1)

        ini_browse = QPushButton("Browse")
        ini_browse.setFixedWidth(76)
        ini_browse.clicked.connect(lambda _, g=game: self._browse_ini(g))
        ini_row.addWidget(ini_browse)

        activate_btn = QPushButton("Activate")
        activate_btn.setFixedWidth(76)
        activate_btn.setVisible(False)
        activate_btn.setToolTip(
            "Copy the default INI template to make it the active configuration"
        )
        activate_btn.clicked.connect(lambda _, g=game: self._activate_default_ini(g))
        ini_row.addWidget(activate_btn)

        layout.addLayout(ini_row)
        layout.addSpacing(4)

        ini_status = QLabel("No INI file loaded.")
        ini_status.setObjectName("section-label")
        layout.addWidget(ini_status)

        self._ini_path_edit[game] = ini_edit
        self._ini_status_label[game] = ini_status
        self._activate_btn[game] = activate_btn

        layout.addSpacing(10)

        # Gamelog file
        gamelog_row = QHBoxLayout()
        gamelog_row.setSpacing(8)

        gamelog_edit = QLineEdit()
        gamelog_edit.setPlaceholderText(
            "gamelog.txt path — auto-detected from game data directory"
        )
        gamelog_edit.editingFinished.connect(lambda g=game: self._on_gamelog_path_changed(g))
        gamelog_row.addWidget(gamelog_edit, 1)

        gamelog_browse = QPushButton("Browse")
        gamelog_browse.setFixedWidth(76)
        gamelog_browse.clicked.connect(lambda _, g=game: self._browse_gamelog(g))
        gamelog_row.addWidget(gamelog_browse)

        layout.addLayout(gamelog_row)
        layout.addSpacing(4)

        gamelog_status = QLabel("No gamelog path configured.")
        gamelog_status.setObjectName("section-label")
        layout.addWidget(gamelog_status)

        self._gamelog_path_edit[game] = gamelog_edit
        self._gamelog_status_label[game] = gamelog_status

        layout.addSpacing(6)

        enable_log_btn = QPushButton("Enable logging flags in INI (-safelog -verbose -debug -showmeminfo)")
        enable_log_btn.clicked.connect(lambda _, g=game: self._enable_logging_flags(g))
        self._enable_log_btn[game] = enable_log_btn
        layout.addWidget(enable_log_btn)

        layout.addSpacing(10)

        # Netlog file
        netlog_row = QHBoxLayout()
        netlog_row.setSpacing(8)

        netlog_edit = QLineEdit()
        netlog_edit.setPlaceholderText(
            "netlog.txt path — auto-detected from game data directory"
        )
        netlog_edit.editingFinished.connect(lambda g=game: self._on_netlog_path_changed(g))
        netlog_row.addWidget(netlog_edit, 1)

        netlog_browse = QPushButton("Browse")
        netlog_browse.setFixedWidth(76)
        netlog_browse.clicked.connect(lambda _, g=game: self._browse_netlog(g))
        netlog_row.addWidget(netlog_browse)

        layout.addLayout(netlog_row)
        layout.addSpacing(4)

        netlog_status = QLabel("No netlog path configured.")
        netlog_status.setObjectName("section-label")
        layout.addWidget(netlog_status)

        self._netlog_path_edit[game] = netlog_edit
        self._netlog_status_label[game] = netlog_status

        layout.addSpacing(10)

        # Missions directory
        dir_row = QHBoxLayout()
        dir_row.setSpacing(8)

        prefix = ".d2x" if game == Game.D2 else ".d1x"
        dir_edit = QLineEdit()
        dir_edit.setPlaceholderText(
            f"Missions install directory (e.g. ~/{prefix}-redux/missions)"
        )
        dir_edit.editingFinished.connect(lambda g=game: self._on_missions_dir_changed(g))
        dir_row.addWidget(dir_edit, 1)

        dir_browse = QPushButton("Browse")
        dir_browse.setFixedWidth(76)
        dir_browse.clicked.connect(lambda _, g=game: self._browse_missions_dir(g))
        dir_row.addWidget(dir_browse)

        layout.addLayout(dir_row)
        layout.addSpacing(4)

        dir_status = QLabel(
            "Directory where missions will be installed for the game to load."
        )
        dir_status.setObjectName("section-label")
        layout.addWidget(dir_status)

        self._missions_dir_edit[game] = dir_edit
        self._missions_dir_status[game] = dir_status

        layout.addSpacing(10)

        # Local DXMA archive
        archive_row = QHBoxLayout()
        archive_row.setSpacing(8)

        archive_edit = QLineEdit()
        archive_edit.setPlaceholderText(
            "Local archive zip (dxma-files.zip) — used to install missions without downloading"
        )
        archive_edit.editingFinished.connect(lambda g=game: self._on_archive_path_changed(g))
        archive_row.addWidget(archive_edit, 1)

        archive_browse = QPushButton("Browse")
        
        archive_browse.setFixedWidth(76)
        archive_browse.clicked.connect(lambda _, g=game: self._browse_archive(g))
        archive_row.addWidget(archive_browse)

        layout.addLayout(archive_row)
        layout.addSpacing(4)

        archive_status = QLabel(
            "Optional — speeds up installs by reading from a local DXMA archive."
        )
        archive_status.setObjectName("section-label")
        layout.addWidget(archive_status)

        self._archive_path_edit[game] = archive_edit
        self._archive_status[game] = archive_status
    
    def _toggle_advanced(self, checked: bool) -> None:
        self._advanced_container.setVisible(checked)
        self._advanced_toggle.setText("ADVANCED  [hide]" if checked else "ADVANCED  [show]")

    # ------------------------------------------------------------------
    # Settings groups
    # ------------------------------------------------------------------

    def _build_basic_settings(self, layout: 
                              QVBoxLayout) -> None:
        self._add_group(layout, "PLAYER")
        self._add_lineedit_row(
            layout, "pilot", "Auto-select pilot on startup", "pilot name", 160,
            "Automatically load this pilot when the game starts.\nINI flag: -pilot <name>",
        )

        layout.addSpacing(14)

        self._add_group(layout, "DISPLAY")
        self._add_flag_row(
            layout, "window", "Run in window mode",
            "Launch the game in a window instead of fullscreen.\nINI flag: -window",
        )
        self._add_flag_row(
            layout, "notitles", "Skip title screens on startup",
            "Skip the intro cinematic and title screens.\nINI flag: -notitles",
        )
        self._add_flag_row(
            layout, "noborders", "No borders in window mode",
            "Remove window decorations when running windowed.\nINI flag: -noborders",
        )
        self._add_flag_row(
            layout, "use_players_dir", "Put player files in Players subdirectory",
            "Store pilot save files and demos in a Players/ subdirectory.\nINI flag: -use_players_dir",
        )
        self._add_spinbox_row(
            layout, "maxfps", "Maximum framerate", 1, 200, 200, "fps",
            "Cap the game framerate. Default and maximum is 200.\nINI flag: -maxfps <n>",
        )

        layout.addSpacing(14)

        self._add_group(layout, "AUDIO")
        self._add_flag_row(
            layout, "nosound", "Disable sound output",
            "Completely disable all sound effects.\nINI flag: -nosound",
        )
        self._add_flag_row(
            layout, "nomusic", "Disable music",
            "Disable in-game music playback.\nINI flag: -nomusic",
        )

        layout.addSpacing(14)

        self._add_group(layout, "CONTROLS")
        self._add_flag_row(
            layout, "nomouse", "Disable mouse input",
            "Ignore mouse input entirely during gameplay.\nINI flag: -nomouse",
        )
        self._add_flag_row(
            layout, "nojoystick", "Disable joystick input",
            "Ignore all joystick and gamepad input.\nINI flag: -nojoystick",
        )
        self._add_flag_row(
            layout, "nocursor", "Hide mouse cursor during play",
            "Hide the system cursor while the game is focused.\nINI flag: -nocursor",
        )

        layout.addSpacing(14)

        self._add_group(layout, "MULTIPLAYER")
        self._add_lineedit_row(
            layout, "tracker_hostaddr", "Tracker server address",
            "retro-tracker.game-server.cc", 220,
            "Address of the tracker used to list and register online games.\nINI flag: -tracker_hostaddr <address>",
        )
        self._add_lineedit_row(
            layout, "udp_hostaddr", "Host address for manual join",
            "e.g. 192.168.1.100", 180,
            "IP address or hostname to connect to when joining a game manually.\nINI flag: -udp_hostaddr <address>",
        )
        self._add_spinbox_row(
            layout, "udp_hostport", "Host port for manual join", 1, 65535, 42424, "",
            "UDP port of the host to join. Default is 42424.\nINI flag: -udp_hostport <n>",
        )
        self._add_spinbox_row(
            layout, "udp_myport", "My UDP port", 1, 65535, 42424, "",
            "The local UDP port this client listens on. Default is 42424.\nINI flag: -udp_myport <n>",
        )

    def _build_advanced_settings(self, layout: QVBoxLayout) -> None:
        self._add_group(layout, "PERFORMANCE")
        self._add_flag_row(
            layout, "lowmem", "Low memory mode",
            "Reduce animation detail to improve performance on low-memory systems.\nINI flag: -lowmem",
        )
        self._add_flag_row(
            layout, "nonicefps", "Do not yield CPU cycles between frames",
            "Disable CPU yielding. May improve frame pacing but increases CPU usage.\nINI flag: -nonicefps",
        )
        self._add_flag_row(
            layout, "nodoublebuffer", "Disable double buffering",
            "Turn off double buffering. Not recommended on modern hardware.\nINI flag: -nodoublebuffer",
        )
        self._add_flag_row(
            layout, "16bpp", "Use 16-bit color depth",
            "Run in 16-bit color instead of 32-bit. May help on very old GPUs.\nINI flag: -16bpp",
        )

        layout.addSpacing(14)

        self._add_group(layout, "RENDERING")
        self._add_flag_row(
            layout, "lowresfont", "Force low-resolution fonts",
            "Use low-res bitmap fonts regardless of display resolution.\nINI flag: -lowresfont",
        )
        self._add_flag_row(
            layout, "gl_fixedfont", "Do not scale fonts to current resolution",
            "Disable font scaling so fonts appear at their native pixel size.\nINI flag: -gl_fixedfont",
        )
        self._add_flag_row(
            layout, "nosdlmixer", "Disable SDL mixer audio output",
            "Bypass SDL_mixer for audio. Use if you have sound driver conflicts.\nINI flag: -nosdlmixer",
        )

        layout.addSpacing(14)

        self._add_group(layout, "BEHAVIOR")
        self._add_flag_row(
            layout, "nostickykeys", "Non-sticky modifier keys",
            "Make CapsLock and NumLock non-sticky during gameplay.\nINI flag: -nostickykeys",
        )
        self._add_flag_row(
            layout, "autodemo", "Start in demo mode automatically",
            "Boot directly into the auto-demo loop instead of the main menu.\nINI flag: -autodemo",
        )

        layout.addSpacing(14)

        self._add_group(layout, "DEBUG")
        self._add_flag_row(
            layout, "debug", "Enable debug output",
            "Print debug information to the console and gamelog.txt.\nINI flag: -debug",
        )
        self._add_flag_row(
            layout, "verbose", "Enable verbose output",
            "Print extended diagnostic messages. Use alongside -debug.\nINI flag: -verbose",
        )
        self._add_flag_row(
            layout, "safelog", "Write gamelog unbuffered",
            "Flush gamelog.txt after every write. Useful for tracing crashes.\nINI flag: -safelog",
        )
        self._add_flag_row(
            layout, "showmeminfo", "Show memory usage information",
            "Log memory allocation information to gamelog.txt.\nINI flag: -showmeminfo",
        )
        self._add_flag_row(
            layout, "renderstats", "Show render statistics by default",
            "Display framerate and rendering stats overlay on startup.\nINI flag: -renderstats",
        )

    # ------------------------------------------------------------------
    # Row builders
    # ------------------------------------------------------------------

    def _build_discord_section(self, layout: QVBoxLayout) -> None:
        heading = QLabel("DISCORD")
        heading.setObjectName("section-label")
        layout.addWidget(heading)

        layout.addSpacing(6)

        row = QWidget()
        row.setObjectName("settings-row")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(8, 5, 8, 5)
        row_layout.setSpacing(8)

        label = QLabel("Show Rich Presence while playing")
        label.setToolTip(
            "When enabled, your Discord status will show which game you are playing\n"
            "while a game is running through DescentBuddy."
        )
        row_layout.addWidget(label, 1)

        self._discord_checkbox = QCheckBox()
        self._discord_checkbox.setChecked(
            load_config().get("discord_presence_enabled", True)
        )
        self._discord_checkbox.stateChanged.connect(self._on_discord_toggled)
        row_layout.addWidget(self._discord_checkbox)

        layout.addWidget(row)

        if sys.platform != "win32":
            layout.addSpacing(8)
            note = QLabel(
                "Linux setup: Discord must expose its IPC socket at "
                "$XDG_RUNTIME_DIR/discord-ipc-0.\n"
                "Flatpak/Goofcord users: run once in a terminal —\n"
                "  ln -sf $XDG_RUNTIME_DIR/.flatpak/<app-id>/xdg-run/discord-ipc-0 "
                "$XDG_RUNTIME_DIR/discord-ipc-0\n"
                "Replace <app-id> with com.discordapp.Discord or "
                "io.github.milkshiift.GoofCord as appropriate.\n"
                "For Goofcord, also enable arRPC in its settings."
            )
            note.setObjectName("section-label")
            note.setWordWrap(True)
            layout.addWidget(note)

    def _on_discord_toggled(self, state: int) -> None:
        enabled = bool(state)
        config = load_config()
        config["discord_presence_enabled"] = enabled
        save_config(config)
        from core.discord_presence import clear_presence
        if not enabled:
            clear_presence()

    def _add_group(self, layout: QVBoxLayout, text: str) -> None:
        label = QLabel(text)
        label.setObjectName("section-label")
        layout.addWidget(label)
        layout.addSpacing(2)

    def _add_flag_row(self, layout: QVBoxLayout, flag: str, description: str, tooltip: str = "") -> None:
        tip = tooltip or f"INI flag: -{flag}"

        row = QWidget()
        row.setObjectName("settings-row")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(8, 5, 8, 5)
        row_layout.setSpacing(8)

        label = QLabel(description)
        label.setToolTip(tip)
        row_layout.addWidget(label, 1)

        checkbox = QCheckBox()
        checkbox.setEnabled(False)
        checkbox.setToolTip(tip)
        checkbox.stateChanged.connect(lambda state, f=flag: self._on_flag_changed(f, bool(state)))
        row_layout.addWidget(checkbox)

        layout.addWidget(row)
        self._controls[flag] = checkbox

    def _add_spinbox_row(
        self,
        layout: QVBoxLayout,
        flag: str,
        description: str,
        min_val: int,
        max_val: int,
        default: int,
        suffix: str = "",
        tooltip: str = "",
    ) -> None:
        tip = tooltip or f"INI flag: -{flag} <n>"

        row = QWidget()
        row.setObjectName("settings-row")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(8, 5, 8, 5)
        row_layout.setSpacing(8)

        label = QLabel(description)
        label.setToolTip(tip)
        row_layout.addWidget(label, 1)

        enable_cb = QCheckBox()
        enable_cb.setEnabled(False)
        enable_cb.setToolTip(tip)

        spinbox = QSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(default)
        spinbox.setEnabled(False)
        spinbox.setFixedWidth(96)
        spinbox.setToolTip(tip)
        if suffix:
            spinbox.setSuffix(f" {suffix}")

        enable_cb.stateChanged.connect(
            lambda state, f=flag, sb=spinbox: self._on_spinbox_enable_changed(f, bool(state), sb)
        )
        spinbox.valueChanged.connect(lambda val, f=flag: self._on_value_changed(f, str(val)))

        row_layout.addWidget(enable_cb)
        row_layout.addWidget(spinbox)

        layout.addWidget(row)
        self._controls[flag] = (enable_cb, spinbox)

    def _add_lineedit_row(
        self,
        layout: QVBoxLayout,
        flag: str,
        description: str,
        placeholder: str = "",
        field_width: int = 180,
        tooltip: str = "",
    ) -> None:
        tip = tooltip or f"INI flag: -{flag} <value>"

        row = QWidget()
        row.setObjectName("settings-row")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(8, 5, 8, 5)
        row_layout.setSpacing(8)

        label = QLabel(description)
        label.setToolTip(tip)
        row_layout.addWidget(label, 1)

        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setEnabled(False)
        edit.setFixedWidth(field_width)
        edit.setToolTip(tip)
        edit.editingFinished.connect(lambda f=flag: self._on_text_value_changed(f))
        row_layout.addWidget(edit)

        layout.addWidget(row)
        self._controls[flag] = edit

    # ------------------------------------------------------------------
    # Executable handling
    # ------------------------------------------------------------------

    def _browse_exe(self) -> None:
        if sys.platform == "win32":
            file_filter = "DXX-Redux Executable (*.exe);;All Files (*)"
        else:
            file_filter = "DXX-Redux AppImage (*.AppImage);;All Files (*)"
        start = str(Path(self._exe_path).parent) if self._exe_path else str(Path.home())
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Game Executable", start, file_filter,
        )
        if path:
            self._exe_path = path
            self._exe_path_display.setText(path)
            self.exe_path_changed.emit(path)

    # ------------------------------------------------------------------
    # INI path handling
    # ------------------------------------------------------------------

    def _browse_ini(self, game: Game) -> None:
        start_dir = self._ini_path_edit[game].text().strip()
        start_dir = str(Path(start_dir).parent) if start_dir else str(Path.home())
        path, _ = QFileDialog.getOpenFileName(
            self, "Select game INI file", start_dir, "INI files (*.ini);;All files (*)"
        )
        if path:
            self._ini_path_edit[game].setText(path)
            self._on_ini_path_changed(game)

    def _auto_detect_ini(self, game: Game, exe_directory: Path | None = None) -> None:
        candidates: list[Path] = []

        if sys.platform != "win32":
            game_data = data_dir(game)
            for name in ini_names(game):
                candidates.append(game_data / name)

        if exe_directory is not None:
            for name in ini_names(game):
                candidates.append(exe_directory / name)
                candidates.append(exe_directory.parent / name)

        for candidate in candidates:
            if candidate.exists():
                self._ini_path_edit[game].setText(str(candidate))
                self._on_ini_path_changed(game)
                return

        if exe_directory is not None:
            prefix = ini_prefix(game)
            self._ini_status_label[game].setText(
                f"No {prefix}.ini found. Checked {data_dir(game)}/ and the executable directory."
            )

    def _activate_default_ini(self, game: Game) -> None:
        prefix = ini_prefix(game)
        default_name = f"{prefix}-default.ini"
        active_name = f"{prefix}.ini"
        current_path = Path(self._ini_path_edit[game].text().strip())
        if current_path.name != default_name:
            return
        active_path = current_path.parent / active_name
        try:
            shutil.copy2(str(current_path), str(active_path))
        except OSError as exc:
            self._ini_status_label[game].setText(f"Could not activate: {exc}")
            return
        self._ini_path_edit[game].setText(str(active_path))
        self._on_ini_path_changed(game)

    def _on_ini_path_changed(self, game: Game) -> None:
        path = self._ini_path_edit[game].text().strip()
        if not path:
            if game == self._game:
                self._ini = None
                self._set_controls_enabled(False)
            self._ini_status_label[game].setText("No INI file loaded.")
            self._activate_btn[game].setVisible(False)
            return

        ini_manager = IniManager(path)
        config = load_config()
        config[config_key(game, "ini_path")] = path
        save_config(config)

        ini_file = Path(path)
        prefix = ini_prefix(game)
        default_name = f"{prefix}-default.ini"
        active_name = f"{prefix}.ini"
        is_default_template = ini_file.name == default_name
        active_exists = (ini_file.parent / active_name).exists()

        if not ini_file.exists():
            self._ini_status_label[game].setText(f"New file will be created: {ini_file.name}")
            self._activate_btn[game].setVisible(False)
        elif is_default_template and not active_exists:
            self._ini_status_label[game].setText("Loaded default template — not yet active.")
            self._activate_btn[game].setVisible(True)
        else:
            self._ini_status_label[game].setText(f"Active: {ini_file.name}")
            self._activate_btn[game].setVisible(False)

        if game == self._game:
            self._ini = ini_manager
            self._set_controls_enabled(True)
            self._load_from_ini()

    def _restore_ini_path(self, game: Game) -> None:
        config = load_config()
        saved_path = config.get(config_key(game, "ini_path"), "")
        if saved_path:
            self._ini_path_edit[game].setText(saved_path)
            self._on_ini_path_changed(game)

    # ------------------------------------------------------------------
    # Gamelog path handling
    # ------------------------------------------------------------------

    def _auto_detect_gamelog(self, game: Game, exe_directory: Path | None = None) -> None:
        candidates: list[Path] = []

        if sys.platform != "win32":
            candidates.append(data_dir(game) / "gamelog.txt")

        if exe_directory is not None:
            candidates.append(exe_directory / "gamelog.txt")

        for candidate in candidates:
            if candidate.exists():
                self._gamelog_path_edit[game].setText(str(candidate))
                self._on_gamelog_path_changed(game)
                return

        self._gamelog_status_label[game].setText(
            "No gamelog.txt found. Start the game once to generate it, or browse manually."
        )

    def _browse_gamelog(self, game: Game) -> None:
        start = self._gamelog_path_edit[game].text().strip()
        start_dir = str(Path(start).parent) if start else str(Path.home())
        path, _ = QFileDialog.getOpenFileName(
            self, "Select gamelog.txt", start_dir, "Text files (*.txt);;All files (*)"
        )
        if path:
            self._gamelog_path_edit[game].setText(path)
            self._on_gamelog_path_changed(game)

    def _on_gamelog_path_changed(self, game: Game) -> None:
        path = self._gamelog_path_edit[game].text().strip()
        if not path:
            self._gamelog_status_label[game].setText("No gamelog path configured.")
            return

        config = load_config()
        config[config_key(game, "gamelog_path")] = path
        save_config(config)

        gamelog = Path(path)
        if not gamelog.exists():
            self._gamelog_status_label[game].setText(
                "File not found — start the game once to generate it."
            )
        else:
            self._gamelog_status_label[game].setText(f"Active: {gamelog.name}")

    def _restore_gamelog_path(self, game: Game) -> None:
        config = load_config()
        saved = config.get(config_key(game, "gamelog_path"), "")
        if saved:
            self._gamelog_path_edit[game].setText(saved)
            self._on_gamelog_path_changed(game)

    # ------------------------------------------------------------------
    # Netlog path handling
    # ------------------------------------------------------------------

    def _auto_detect_netlog(self, game: Game, exe_directory: Path | None = None) -> None:
        candidates: list[Path] = []

        if sys.platform != "win32":
            candidates.append(data_dir(game) / "netlog.txt")

        if exe_directory is not None:
            candidates.append(exe_directory / "netlog.txt")

        for candidate in candidates:
            if candidate.exists():
                self._netlog_path_edit[game].setText(str(candidate))
                self._on_netlog_path_changed(game)
                return

        self._netlog_status_label[game].setText(
            "No netlog.txt found. Join a netgame once to generate it, or browse manually."
        )

    def _browse_netlog(self, game: Game) -> None:
        start = self._netlog_path_edit[game].text().strip()
        start_dir = str(Path(start).parent) if start else str(Path.home())
        path, _ = QFileDialog.getOpenFileName(
            self, "Select netlog.txt", start_dir, "Text files (*.txt);;All files (*)"
        )
        if path:
            self._netlog_path_edit[game].setText(path)
            self._on_netlog_path_changed(game)

    def _on_netlog_path_changed(self, game: Game) -> None:
        path = self._netlog_path_edit[game].text().strip()
        if not path:
            self._netlog_status_label[game].setText("No netlog path configured.")
            return

        config = load_config()
        config[config_key(game, "netlog_path")] = path
        save_config(config)

        netlog = Path(path)
        if not netlog.exists():
            self._netlog_status_label[game].setText(
                "File not found — join a netgame once to generate it."
            )
        else:
            self._netlog_status_label[game].setText(f"Active: {netlog.name}")

    def _restore_netlog_path(self, game: Game) -> None:
        config = load_config()
        saved = config.get(config_key(game, "netlog_path"), "")
        if saved:
            self._netlog_path_edit[game].setText(saved)
            self._on_netlog_path_changed(game)

    # ------------------------------------------------------------------
    # Missions path handling
    # ------------------------------------------------------------------

    def _browse_missions_dir(self, game: Game) -> None:
        start = self._missions_dir_edit[game].text().strip() or str(Path.home())
        path = QFileDialog.getExistingDirectory(self, "Select Missions Directory", start)
        if path:
            self._missions_dir_edit[game].setText(path)
            self._on_missions_dir_changed(game)

    def _on_missions_dir_changed(self, game: Game) -> None:
        path = self._missions_dir_edit[game].text().strip()
        config = load_config()
        config[config_key(game, "missions_dir")] = path
        save_config(config)
        if path:
            missions_dir = Path(path)
            if missions_dir.exists():
                count = sum(1 for p in missions_dir.iterdir() if p.suffix.lower() == ".hog")
                self._missions_dir_status[game].setText(
                    f"Active: {missions_dir.name}/ ({count} HOG files)"
                )
            else:
                self._missions_dir_status[game].setText(
                    "Directory does not exist yet — it will be created on first install."
                )
        else:
            self._missions_dir_status[game].setText(
                "Directory where missions will be installed for the game to load."
            )

    def _browse_archive(self, game: Game) -> None:
        start = self._archive_path_edit[game].text().strip()
        start_dir = str(Path(start).parent) if start else str(Path.home())
        path, _ = QFileDialog.getOpenFileName(
            self, "Select DXMA Archive", start_dir, "Zip archives (*.zip);;All files (*)"
        )
        if path:
            self._archive_path_edit[game].setText(path)
            self._on_archive_path_changed(game)

    def _on_archive_path_changed(self, game: Game) -> None:
        path = self._archive_path_edit[game].text().strip()
        config = load_config()
        config[config_key(game, "local_archive_path")] = path
        save_config(config)
        if path:
            archive = Path(path)
            if archive.exists():
                size_mb = archive.stat().st_size / 1_048_576
                self._archive_status[game].setText(f"Active: {archive.name} ({size_mb:.0f} MB)")
            else:
                self._archive_status[game].setText("File not found.")
        else:
            self._archive_status[game].setText(
                "Optional — speeds up installs by reading from a local DXMA archive."
            )

    def _restore_missions_settings(self, game: Game) -> None:
        config = load_config()

        missions_dir = config.get(config_key(game, "missions_dir"), "")
        if missions_dir:
            self._missions_dir_edit[game].setText(missions_dir)
            self._on_missions_dir_changed(game)
        else:
            if sys.platform == "win32":
                default_dir = Path(self._exe_path).parent / "missions" if self._exe_path else None
            else:
                default_dir = data_dir(game) / "missions"
            if default_dir and default_dir.exists():
                self._missions_dir_edit[game].setText(str(default_dir))
                self._on_missions_dir_changed(game)

        archive = config.get(config_key(game, "local_archive_path"), "")
        if archive:
            self._archive_path_edit[game].setText(archive)
            self._on_archive_path_changed(game)
        else:
            default_archive = Path.home() / "Documents" / "DescentBuddy" / "dxma-files.zip"
            if default_archive.exists():
                self._archive_path_edit[game].setText(str(default_archive))
                self._on_archive_path_changed(game)

    # ------------------------------------------------------------------
    # Auto-detection
    # ------------------------------------------------------------------

    def _enable_logging_flags(self, game: Game) -> None:
        """Enable the four flags required for gamelog and netlog output."""
        if game != self._game or self._ini is None:
            self._gamelog_status_label[game].setText(
                "Load the INI file for this game first, then click again."
            )
            return
        for flag in ("debug", "verbose", "safelog", "showmeminfo"):
            self._ini.set_flag(flag, True)
            control = self._controls.get(flag)
            if isinstance(control, QCheckBox):
                self._loading = True
                control.setChecked(True)
                self._loading = False
        self._gamelog_status_label[game].setText(
            "Logging flags enabled: -debug -verbose -safelog -showmeminfo"
        )

    def _detect_missing_paths(self, game: Game, exe_directory: Path | None = None) -> None:
        if not self._ini_path_edit[game].text().strip():
            self._auto_detect_ini(game, exe_directory)
        if not self._gamelog_path_edit[game].text().strip():
            self._auto_detect_gamelog(game, exe_directory)
        if not self._netlog_path_edit[game].text().strip():
            self._auto_detect_netlog(game, exe_directory)

    # ------------------------------------------------------------------
    # INI control management
    # ------------------------------------------------------------------

    def _set_controls_enabled(self, enabled: bool) -> None:
        for control in self._controls.values():
            if isinstance(control, tuple):
                enable_cb, _spinbox = control
                enable_cb.setEnabled(enabled)
            elif isinstance(control, (QCheckBox, QLineEdit)):
                control.setEnabled(enabled)

    def _load_from_ini(self) -> None:
        if self._ini is None:
            return

        self._loading = True
        try:
            for flag, control in self._controls.items():
                if isinstance(control, tuple):
                    enable_cb, spinbox = control
                    value = self._ini.get_value(flag)
                    if value is not None:
                        enable_cb.setChecked(True)
                        spinbox.setEnabled(True)
                        try:
                            spinbox.setValue(int(value))
                        except ValueError:
                            pass
                    else:
                        enable_cb.setChecked(False)
                        spinbox.setEnabled(False)
                elif isinstance(control, QCheckBox):
                    control.setChecked(self._ini.get_flag(flag))
                elif isinstance(control, QLineEdit):
                    value = self._ini.get_value(flag)
                    control.setText(value or "")
        finally:
            self._loading = False

    def _clear_fields(self) -> None:
        for game in Game:
            self._ini_path_edit[game].clear()
            self._gamelog_path_edit[game].clear()
            self._netlog_path_edit[game].clear()
            self._missions_dir_edit[game].clear()
            self._archive_path_edit[game].clear()
            self._ini_status_label[game].setText("No INI file loaded.")
            self._gamelog_status_label[game].setText("No gamelog path configured.")
            self._netlog_status_label[game].setText("No netlog path configured.")
            self._missions_dir_status[game].setText(
                "Directory where missions will be installed for the game to load."
            )
            self._archive_status[game].setText(
                "Optional — speeds up installs by reading from a local DXMA archive."
            )
            self._activate_btn[game].setVisible(False)

        self._ini = None
        self._set_controls_enabled(False)

        self._loading = True
        try:
            for control in self._controls.values():
                if isinstance(control, tuple):
                    enable_cb, spinbox = control
                    enable_cb.setChecked(False)
                    spinbox.setEnabled(False)
                elif isinstance(control, QCheckBox):
                    control.setChecked(False)
                elif isinstance(control, QLineEdit):
                    control.clear()
        finally:
            self._loading = False

    # ------------------------------------------------------------------
    # Change handlers
    # ------------------------------------------------------------------

    def _on_flag_changed(self, flag: str, enabled: bool) -> None:
        if self._loading or self._ini is None:
            return
        self._ini.set_flag(flag, enabled)

    def _on_spinbox_enable_changed(self, flag: str, enabled: bool, spinbox: QSpinBox) -> None:
        spinbox.setEnabled(enabled)
        if self._loading or self._ini is None:
            return
        if enabled:
            self._ini.set_value(flag, str(spinbox.value()))
        else:
            self._ini.remove_flag(flag)

    def _on_value_changed(self, flag: str, value: str) -> None:
        if self._loading or self._ini is None:
            return
        self._ini.set_value(flag, value)

    def _on_text_value_changed(self, flag: str) -> None:
        if self._loading or self._ini is None:
            return
        control = self._controls.get(flag)
        if isinstance(control, QLineEdit):
            text = control.text().strip()
            if text:
                self._ini.set_value(flag, text)
            else:
                self._ini.remove_flag(flag)
