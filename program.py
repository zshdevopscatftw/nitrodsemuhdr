    # ╔═══════════════════════════════════════════════════════════════════════════╗
    # ║  Cat's EMU DS 0.1 infdev                                                  ║
    # ║  A CatOS-Powered Nintendo DS Emulator                                     ║
    # ║  By Team Flames / Samsoft                                                 ║
    # ║  NO$GBA-Style Interface · Pure Python · No BIOS Required                  ║
    # ╚═══════════════════════════════════════════════════════════════════════════╝
    #
    #  Usage: python cats_emu_ds.py [rom.nds]
    #
    #  Requirements:
    #    pip install py-desmume pillow
    #

    import os
    import sys
    import time
    import threading
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, font

    # === Emulator Core Import ===
    EMU_AVAILABLE = False
    try:
        from desmume.emulator import DeSmuME, DeSmuME_Savestate
        EMU_AVAILABLE = True
    except ImportError:
        pass

    # ═══════════════════════════════════════════════════════════════════════════════
    # THEME CONFIGURATION - NO$GBA Style + Cat Theme
    # ═══════════════════════════════════════════════════════════════════════════════

    class CatTheme:
        """NO$GBA-inspired dark theme with cat accents"""
        # Main colors (NO$GBA style dark grays)
        BG_DARK = "#1a1a2e"
        BG_MEDIUM = "#16213e"
        BG_LIGHT = "#0f3460"
        FG_TEXT = "#e0e0e0"
        FG_DIM = "#808080"
        FG_ACCENT = "#e94560"  # Cat's paw pink accent
        FG_HIGHLIGHT = "#ff6b6b"
        
        # Debug panel colors
        DEBUG_BG = "#0d1117"
        DEBUG_FG = "#58a6ff"
        DEBUG_ADDR = "#7ee787"
        DEBUG_DATA = "#ff7b72"
        DEBUG_COMMENT = "#8b949e"
        
        # Screen colors
        SCREEN_BORDER = "#e94560"
        SCREEN_BG = "#000000"
        
        # Menu colors
        MENU_BG = "#21262d"
        MENU_FG = "#c9d1d9"
        MENU_ACTIVE_BG = "#30363d"
        
        # Status bar
        STATUS_BG = "#161b22"
        STATUS_FG = "#8b949e"
        STATUS_ACTIVE = "#3fb950"


    # ═══════════════════════════════════════════════════════════════════════════════
    # MAIN EMULATOR CLASS
    # ═══════════════════════════════════════════════════════════════════════════════

    class CatsEmuDS:
        """
        Cat's EMU DS - NO$GBA-Style Nintendo DS Emulator
        
        Features:
        - Dual screen DS display (256x192 x2)
        - NO$GBA-inspired debug interface
        - Save states support
        - No BIOS files required
        - 60 FPS target framerate
        """
        
        VERSION = "0.1 infdev"
        TITLE = "Cat's EMU DS"
        
        # DS Hardware Constants
        DS_WIDTH = 256
        DS_HEIGHT = 192
        DS_TOTAL_HEIGHT = 384  # Both screens
        
        def __init__(self, rom_path=None):
            self.emu = None
            self.rom_path = None
            self.rom_name = "No ROM Loaded"
            self.running = False
            self.paused = True
            self.frame_count = 0
            self.fps = 0.0
            self.fps_timer = time.time()
            self.fps_frame_count = 0
            
            # Debug state
            self.show_debug = False
            self.debug_mode = "disasm"  # disasm, memory, registers, io
            
            # Initialize emulator core
            self._init_emulator()
            
            # Build GUI
            self._build_window()
            self._build_menu()
            self._build_main_layout()
            self._build_status_bar()
            self._bind_keys()
            
            # Load ROM if provided
            if rom_path:
                self.load_rom(rom_path)
        
        def _init_emulator(self):
            """Initialize the emulator core"""
            if EMU_AVAILABLE:
                try:
                    self.emu = DeSmuME()
                    self.emu.volume_set(100)
                except Exception as e:
                    print(f"[CatOS] Emulator init warning: {e}")
                    self.emu = None
            else:
                self.emu = None
        
        # ═══════════════════════════════════════════════════════════════════════════
        # GUI CONSTRUCTION
        # ═══════════════════════════════════════════════════════════════════════════
        
        def _build_window(self):
            """Create main window with NO$GBA styling"""
            self.window = tk.Tk()
            self.window.title(f"{self.TITLE} {self.VERSION} - {self.rom_name}")
            self.window.configure(bg=CatTheme.BG_DARK)
            self.window.resizable(True, True)
            
            # Set minimum size
            self.window.minsize(540, 500)
            
            # Default size (with debug panel hidden)
            self.window.geometry("540x520")
            
            # Custom fonts (NO$GBA uses fixed-width fonts)
            self.font_mono = font.Font(family="Consolas", size=9)
            self.font_mono_small = font.Font(family="Consolas", size=8)
            self.font_ui = font.Font(family="Segoe UI", size=9)
            self.font_title = font.Font(family="Consolas", size=10, weight="bold")
            
            # Handle close
            self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        
        def _build_menu(self):
            """Build NO$GBA-style menu bar"""
            self.menubar = tk.Menu(
                self.window,
                bg=CatTheme.MENU_BG,
                fg=CatTheme.MENU_FG,
                activebackground=CatTheme.MENU_ACTIVE_BG,
                activeforeground=CatTheme.FG_TEXT,
                relief=tk.FLAT,
                borderwidth=0
            )
            
            # === File Menu ===
            file_menu = tk.Menu(self.menubar, tearoff=0,
                            bg=CatTheme.MENU_BG, fg=CatTheme.MENU_FG,
                            activebackground=CatTheme.MENU_ACTIVE_BG,
                            activeforeground=CatTheme.FG_TEXT)
            file_menu.add_command(label="Open ROM...", command=self.open_rom_dialog,
                                accelerator="Ctrl+O")
            file_menu.add_command(label="Close ROM", command=self.close_rom)
            file_menu.add_separator()
            file_menu.add_command(label="Load State...", command=self.load_state,
                                accelerator="F7")
            file_menu.add_command(label="Save State...", command=self.save_state,
                                accelerator="F5")
            file_menu.add_separator()
            file_menu.add_command(label="Screenshot", command=self.take_screenshot,
                                accelerator="F12")
            file_menu.add_separator()
            file_menu.add_command(label="Exit", command=self._on_close,
                                accelerator="Alt+F4")
            self.menubar.add_cascade(label="File", menu=file_menu)
            
            # === Emulation Menu ===
            emu_menu = tk.Menu(self.menubar, tearoff=0,
                            bg=CatTheme.MENU_BG, fg=CatTheme.MENU_FG,
                            activebackground=CatTheme.MENU_ACTIVE_BG,
                            activeforeground=CatTheme.FG_TEXT)
            emu_menu.add_command(label="Run", command=self.run_emulation,
                                accelerator="F9")
            emu_menu.add_command(label="Pause", command=self.pause_emulation,
                                accelerator="F8")
            emu_menu.add_command(label="Reset", command=self.reset_emulation,
                                accelerator="Ctrl+R")
            emu_menu.add_separator()
            emu_menu.add_command(label="Frame Advance", command=self.frame_advance,
                                accelerator=".")
            self.menubar.add_cascade(label="Emulation", menu=emu_menu)
            
            # === Options Menu ===
            opt_menu = tk.Menu(self.menubar, tearoff=0,
                            bg=CatTheme.MENU_BG, fg=CatTheme.MENU_FG,
                            activebackground=CatTheme.MENU_ACTIVE_BG,
                            activeforeground=CatTheme.FG_TEXT)
            
            # Screen size submenu
            size_menu = tk.Menu(opt_menu, tearoff=0,
                            bg=CatTheme.MENU_BG, fg=CatTheme.MENU_FG,
                            activebackground=CatTheme.MENU_ACTIVE_BG)
            self.screen_scale = tk.IntVar(value=2)
            size_menu.add_radiobutton(label="1x (256x384)", variable=self.screen_scale,
                                    value=1, command=self._resize_screen)
            size_menu.add_radiobutton(label="2x (512x768)", variable=self.screen_scale,
                                    value=2, command=self._resize_screen)
            size_menu.add_radiobutton(label="3x (768x1152)", variable=self.screen_scale,
                                    value=3, command=self._resize_screen)
            opt_menu.add_cascade(label="Screen Size", menu=size_menu)
            
            # Screen layout submenu
            layout_menu = tk.Menu(opt_menu, tearoff=0,
                                bg=CatTheme.MENU_BG, fg=CatTheme.MENU_FG,
                                activebackground=CatTheme.MENU_ACTIVE_BG)
            self.screen_layout = tk.StringVar(value="vertical")
            layout_menu.add_radiobutton(label="Vertical", variable=self.screen_layout,
                                        value="vertical", command=self._update_layout)
            layout_menu.add_radiobutton(label="Horizontal", variable=self.screen_layout,
                                        value="horizontal", command=self._update_layout)
            opt_menu.add_cascade(label="Screen Layout", menu=layout_menu)
            
            opt_menu.add_separator()
            opt_menu.add_command(label="Input Config...", command=self._show_input_config)
            opt_menu.add_command(label="Audio Config...", command=self._show_audio_config)
            self.menubar.add_cascade(label="Options", menu=opt_menu)
            
            # === Debug Menu (NO$GBA signature feature) ===
            debug_menu = tk.Menu(self.menubar, tearoff=0,
                                bg=CatTheme.MENU_BG, fg=CatTheme.MENU_FG,
                                activebackground=CatTheme.MENU_ACTIVE_BG,
                                activeforeground=CatTheme.FG_TEXT)
            self.show_debug_var = tk.BooleanVar(value=False)
            debug_menu.add_checkbutton(label="Show Debug Panel", 
                                    variable=self.show_debug_var,
                                    command=self._toggle_debug_panel,
                                    accelerator="F1")
            debug_menu.add_separator()
            debug_menu.add_command(label="Disassembly View", 
                                command=lambda: self._set_debug_mode("disasm"))
            debug_menu.add_command(label="Memory View",
                                command=lambda: self._set_debug_mode("memory"))
            debug_menu.add_command(label="Register View",
                                command=lambda: self._set_debug_mode("registers"))
            debug_menu.add_command(label="I/O Map View",
                                command=lambda: self._set_debug_mode("io"))
            self.menubar.add_cascade(label="Debug", menu=debug_menu)
            
            # === Window Menu ===
            win_menu = tk.Menu(self.menubar, tearoff=0,
                            bg=CatTheme.MENU_BG, fg=CatTheme.MENU_FG,
                            activebackground=CatTheme.MENU_ACTIVE_BG,
                            activeforeground=CatTheme.FG_TEXT)
            win_menu.add_command(label="Reset Window Size", command=self._reset_window_size)
            self.menubar.add_cascade(label="Window", menu=win_menu)
            
            # === Help Menu ===
            help_menu = tk.Menu(self.menubar, tearoff=0,
                            bg=CatTheme.MENU_BG, fg=CatTheme.MENU_FG,
                            activebackground=CatTheme.MENU_ACTIVE_BG,
                            activeforeground=CatTheme.FG_TEXT)
            help_menu.add_command(label="About Cat's EMU DS", command=self._show_about)
            help_menu.add_command(label="Keyboard Shortcuts", command=self._show_shortcuts)
            self.menubar.add_cascade(label="Help", menu=help_menu)
            
            self.window.config(menu=self.menubar)
        
        def _build_main_layout(self):
            """Build main content area with screens and optional debug panel"""
            # Main container
            self.main_frame = tk.Frame(self.window, bg=CatTheme.BG_DARK)
            self.main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Left side: Screen display
            self.screen_frame = tk.Frame(self.main_frame, bg=CatTheme.BG_DARK)
            self.screen_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Screen header (NO$GBA style)
            header = tk.Frame(self.screen_frame, bg=CatTheme.BG_MEDIUM)
            header.pack(fill=tk.X)
            
            tk.Label(header, text="═══ TOP SCREEN (ARM9) ═══", 
                    font=self.font_mono_small, bg=CatTheme.BG_MEDIUM,
                    fg=CatTheme.FG_DIM).pack(pady=2)
            
            # Top screen canvas
            self.top_screen = tk.Canvas(
                self.screen_frame,
                width=self.DS_WIDTH * 2,
                height=self.DS_HEIGHT * 2,
                bg=CatTheme.SCREEN_BG,
                highlightthickness=2,
                highlightbackground=CatTheme.SCREEN_BORDER
            )
            self.top_screen.pack(pady=(0, 2))
            
            # Draw placeholder pattern
            self._draw_screen_placeholder(self.top_screen, "TOP")
            
            # Divider
            divider = tk.Frame(self.screen_frame, bg=CatTheme.BG_MEDIUM)
            divider.pack(fill=tk.X)
            
            tk.Label(divider, text="═══ BOTTOM SCREEN (TOUCH) ═══",
                    font=self.font_mono_small, bg=CatTheme.BG_MEDIUM,
                    fg=CatTheme.FG_DIM).pack(pady=2)
            
            # Bottom screen canvas (touchscreen)
            self.bottom_screen = tk.Canvas(
                self.screen_frame,
                width=self.DS_WIDTH * 2,
                height=self.DS_HEIGHT * 2,
                bg=CatTheme.SCREEN_BG,
                highlightthickness=2,
                highlightbackground=CatTheme.SCREEN_BORDER
            )
            self.bottom_screen.pack(pady=(0, 5))
            
            # Draw placeholder pattern
            self._draw_screen_placeholder(self.bottom_screen, "BOTTOM")
            
            # Touch input handling
            self.bottom_screen.bind("<Button-1>", self._on_touch_start)
            self.bottom_screen.bind("<B1-Motion>", self._on_touch_move)
            self.bottom_screen.bind("<ButtonRelease-1>", self._on_touch_end)
            
            # Right side: Debug panel (hidden by default)
            self.debug_frame = tk.Frame(self.main_frame, bg=CatTheme.DEBUG_BG, width=350)
            # Don't pack yet - toggled via menu
            
            self._build_debug_panel()
        
        def _draw_screen_placeholder(self, canvas, label):
            """Draw NO$GBA-style placeholder on screen"""
            w = int(canvas['width'])
            h = int(canvas['height'])
            
            # Grid pattern
            for i in range(0, w, 32):
                canvas.create_line(i, 0, i, h, fill="#1a1a2e", width=1)
            for i in range(0, h, 32):
                canvas.create_line(0, i, w, i, fill="#1a1a2e", width=1)
            
            # Center text
            canvas.create_text(w//2, h//2 - 20, text=f"Cat's EMU DS",
                            font=("Consolas", 14, "bold"), fill=CatTheme.FG_ACCENT)
            canvas.create_text(w//2, h//2 + 10, text=f"{label} SCREEN",
                            font=("Consolas", 10), fill=CatTheme.FG_DIM)
            canvas.create_text(w//2, h//2 + 30, text="Load a ROM to begin",
                            font=("Consolas", 9), fill=CatTheme.FG_DIM)
        
        def _build_debug_panel(self):
            """Build NO$GBA-style debug panel"""
            # Debug panel header
            header = tk.Frame(self.debug_frame, bg=CatTheme.BG_MEDIUM)
            header.pack(fill=tk.X)
            
            tk.Label(header, text="══════ DEBUG ══════",
                    font=self.font_title, bg=CatTheme.BG_MEDIUM,
                    fg=CatTheme.FG_ACCENT).pack(pady=5)
            
            # Debug mode tabs
            tab_frame = tk.Frame(self.debug_frame, bg=CatTheme.DEBUG_BG)
            tab_frame.pack(fill=tk.X, padx=5)
            
            modes = [("DISASM", "disasm"), ("MEMORY", "memory"), 
                    ("REGS", "registers"), ("I/O", "io")]
            
            for text, mode in modes:
                btn = tk.Button(tab_frame, text=text, font=self.font_mono_small,
                            bg=CatTheme.BG_MEDIUM, fg=CatTheme.FG_TEXT,
                            activebackground=CatTheme.FG_ACCENT,
                            relief=tk.FLAT, padx=8, pady=2,
                            command=lambda m=mode: self._set_debug_mode(m))
                btn.pack(side=tk.LEFT, padx=1)
            
            # Debug content area
            self.debug_text = tk.Text(
                self.debug_frame,
                font=self.font_mono,
                bg=CatTheme.DEBUG_BG,
                fg=CatTheme.DEBUG_FG,
                insertbackground=CatTheme.FG_TEXT,
                selectbackground=CatTheme.FG_ACCENT,
                relief=tk.FLAT,
                width=45,
                height=35,
                state=tk.DISABLED
            )
            self.debug_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Configure text tags for syntax highlighting
            self.debug_text.tag_configure("addr", foreground=CatTheme.DEBUG_ADDR)
            self.debug_text.tag_configure("data", foreground=CatTheme.DEBUG_DATA)
            self.debug_text.tag_configure("comment", foreground=CatTheme.DEBUG_COMMENT)
            self.debug_text.tag_configure("instruction", foreground=CatTheme.DEBUG_FG)
            
            # Initial debug content
            self._update_debug_view()
        
        def _build_status_bar(self):
            """Build NO$GBA-style status bar"""
            self.status_frame = tk.Frame(self.window, bg=CatTheme.STATUS_BG, height=22)
            self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
            self.status_frame.pack_propagate(False)
            
            # Left: Status message
            self.status_msg = tk.Label(
                self.status_frame,
                text="Ready - Load a ROM to begin",
                font=self.font_mono_small,
                bg=CatTheme.STATUS_BG,
                fg=CatTheme.STATUS_FG,
                anchor=tk.W
            )
            self.status_msg.pack(side=tk.LEFT, padx=5)
            
            # Right side indicators
            right_frame = tk.Frame(self.status_frame, bg=CatTheme.STATUS_BG)
            right_frame.pack(side=tk.RIGHT, padx=5)
            
            # FPS counter
            self.fps_label = tk.Label(
                right_frame,
                text="FPS: --",
                font=self.font_mono_small,
                bg=CatTheme.STATUS_BG,
                fg=CatTheme.STATUS_FG,
                width=10
            )
            self.fps_label.pack(side=tk.RIGHT, padx=5)
            
            # Frame counter
            self.frame_label = tk.Label(
                right_frame,
                text="Frame: 0",
                font=self.font_mono_small,
                bg=CatTheme.STATUS_BG,
                fg=CatTheme.STATUS_FG,
                width=14
            )
            self.frame_label.pack(side=tk.RIGHT, padx=5)
            
            # Emulation state indicator
            self.state_label = tk.Label(
                right_frame,
                text="● STOPPED",
                font=self.font_mono_small,
                bg=CatTheme.STATUS_BG,
                fg=CatTheme.FG_DIM,
                width=12
            )
            self.state_label.pack(side=tk.RIGHT, padx=5)
        
        def _bind_keys(self):
            """Bind keyboard shortcuts"""
            self.window.bind("<Control-o>", lambda e: self.open_rom_dialog())
            self.window.bind("<Control-r>", lambda e: self.reset_emulation())
            self.window.bind("<F1>", lambda e: self._toggle_debug_panel())
            self.window.bind("<F5>", lambda e: self.save_state())
            self.window.bind("<F7>", lambda e: self.load_state())
            self.window.bind("<F8>", lambda e: self.pause_emulation())
            self.window.bind("<F9>", lambda e: self.run_emulation())
            self.window.bind("<F12>", lambda e: self.take_screenshot())
            self.window.bind("<period>", lambda e: self.frame_advance())
            
            # DS Button mappings
            self.key_map = {
                'z': 'A', 'x': 'B', 'a': 'Y', 's': 'X',
                'q': 'L', 'w': 'R',
                'Return': 'START', 'BackSpace': 'SELECT',
                'Up': 'UP', 'Down': 'DOWN', 'Left': 'LEFT', 'Right': 'RIGHT'
            }
            
            for key in self.key_map:
                self.window.bind(f"<KeyPress-{key}>", self._on_key_press)
                self.window.bind(f"<KeyRelease-{key}>", self._on_key_release)
        
        # ═══════════════════════════════════════════════════════════════════════════
        # ROM HANDLING
        # ═══════════════════════════════════════════════════════════════════════════
        
        def open_rom_dialog(self):
            """Open file dialog to select ROM"""
            path = filedialog.askopenfilename(
                title="Open Nintendo DS ROM",
                filetypes=[
                    ("Nintendo DS ROMs", "*.nds *.ds"),
                    ("All Files", "*.*")
                ]
            )
            if path:
                self.load_rom(path)
        
        def load_rom(self, path):
            """Load a ROM file"""
            if not os.path.isfile(path):
                messagebox.showerror("Error", f"File not found:\n{path}")
                return False
            
            if not self.emu:
                messagebox.showerror(
                    "Emulator Core Missing",
                    "The emulator core is not available.\n\n"
                    "Please install py-desmume:\n"
                    "  pip install py-desmume\n\n"
                    "This provides the actual DS emulation backend."
                )
                return False
            
            try:
                # Pause if running
                was_running = self.running and not self.paused
                if was_running:
                    self.pause_emulation()
                
                # Load the ROM
                self.emu.open(path)
                self.rom_path = path
                self.rom_name = os.path.basename(path)
                
                # Update window title
                self.window.title(f"{self.TITLE} {self.VERSION} - {self.rom_name}")
                
                # Reset counters
                self.frame_count = 0
                self.fps = 0.0
                
                # Update status
                self._set_status(f"Loaded: {self.rom_name}")
                self._update_state_indicator("PAUSED")
                
                # Start emulation thread if not already running
                if not self.running:
                    self._start_emulation_thread()
                
                return True
                
            except Exception as e:
                messagebox.showerror("Load Error", f"Failed to load ROM:\n{e}")
                return False
        
        def close_rom(self):
            """Close current ROM"""
            self.paused = True
            self.rom_path = None
            self.rom_name = "No ROM Loaded"
            self.window.title(f"{self.TITLE} {self.VERSION}")
            self._set_status("ROM closed")
            self._update_state_indicator("STOPPED")
            
            # Clear screens
            self.top_screen.delete("all")
            self.bottom_screen.delete("all")
            self._draw_screen_placeholder(self.top_screen, "TOP")
            self._draw_screen_placeholder(self.bottom_screen, "BOTTOM")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # EMULATION CONTROL
        # ═══════════════════════════════════════════════════════════════════════════
        
        def _start_emulation_thread(self):
            """Start the emulation loop in a separate thread"""
            if self.running:
                return
            
            self.running = True
            self.emu_thread = threading.Thread(target=self._emulation_loop, daemon=True)
            self.emu_thread.start()
            
            # Start display update timer
            self._schedule_display_update()
        
        def _emulation_loop(self):
            """Main emulation loop (runs in separate thread)"""
            target_fps = 60
            frame_time = 1.0 / target_fps
            
            while self.running:
                if not self.paused and self.rom_path and self.emu:
                    start = time.perf_counter()
                    
                    try:
                        # Execute one frame
                        self.emu.cycle()
                        self.frame_count += 1
                        self.fps_frame_count += 1
                    except Exception as e:
                        print(f"[CatOS] Emulation error: {e}")
                        self.paused = True
                        continue
                    
                    # Frame timing
                    elapsed = time.perf_counter() - start
                    if elapsed < frame_time:
                        time.sleep(frame_time - elapsed)
                else:
                    # When paused, sleep to avoid busy-waiting
                    time.sleep(0.01)
        
        def _schedule_display_update(self):
            """Schedule periodic display updates"""
            if not self.running:
                return
            
            self._update_display()
            self._update_fps()
            
            # Schedule next update (~60 FPS)
            self.window.after(16, self._schedule_display_update)
        
        def _update_display(self):
            """Update screen display from emulator framebuffer"""
            if not self.rom_path or not self.emu:
                return
            
            try:
                # Get framebuffer from emulator
                buffer = self.emu.display_buffer_as_rgbx()
                
                # Convert to images
                from PIL import Image, ImageTk
                
                scale = self.screen_scale.get()
                
                # Top screen (first 192 lines)
                top_img = Image.frombytes("RGBX", (256, 384), buffer)
                top_img = top_img.crop((0, 0, 256, 192))
                if scale != 1:
                    top_img = top_img.resize((256 * scale, 192 * scale), Image.NEAREST)
                self.top_photo = ImageTk.PhotoImage(top_img)
                self.top_screen.delete("all")
                self.top_screen.create_image(0, 0, image=self.top_photo, anchor=tk.NW)
                
                # Bottom screen (last 192 lines)
                bottom_img = Image.frombytes("RGBX", (256, 384), buffer)
                bottom_img = bottom_img.crop((0, 192, 256, 384))
                if scale != 1:
                    bottom_img = bottom_img.resize((256 * scale, 192 * scale), Image.NEAREST)
                self.bottom_photo = ImageTk.PhotoImage(bottom_img)
                self.bottom_screen.delete("all")
                self.bottom_screen.create_image(0, 0, image=self.bottom_photo, anchor=tk.NW)
                
            except Exception as e:
                pass  # Silently ignore display errors
        
        def _update_fps(self):
            """Update FPS counter"""
            now = time.time()
            elapsed = now - self.fps_timer
            
            if elapsed >= 1.0:
                self.fps = self.fps_frame_count / elapsed
                self.fps_frame_count = 0
                self.fps_timer = now
                
                self.fps_label.config(text=f"FPS: {self.fps:.1f}")
                self.frame_label.config(text=f"Frame: {self.frame_count}")
        
        def run_emulation(self):
            """Resume emulation"""
            if not self.rom_path:
                messagebox.showinfo("Info", "Load a ROM first!")
                return
            
            self.paused = False
            if self.emu:
                self.emu.resume()
            self._set_status(f"Running: {self.rom_name}")
            self._update_state_indicator("RUNNING")
        
        def pause_emulation(self):
            """Pause emulation"""
            self.paused = True
            if self.emu:
                self.emu.pause()
            self._set_status("Paused")
            self._update_state_indicator("PAUSED")
        
        def reset_emulation(self):
            """Reset emulation"""
            if self.emu and self.rom_path:
                self.emu.reset()
                self.frame_count = 0
                self._set_status("Reset")
        
        def frame_advance(self):
            """Advance one frame"""
            if self.emu and self.rom_path:
                self.paused = True
                self.emu.cycle()
                self.frame_count += 1
                self._update_display()
                self._set_status(f"Frame: {self.frame_count}")
                self._update_state_indicator("PAUSED")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # SAVE STATES
        # ═══════════════════════════════════════════════════════════════════════════
        
        def save_state(self):
            """Save emulator state"""
            if not self.rom_path or not self.emu:
                return
            
            path = filedialog.asksaveasfilename(
                title="Save State",
                defaultextension=".cds",
                filetypes=[
                    ("Cat's EMU DS State", "*.cds"),
                    ("DeSmuME State", "*.dst"),
                    ("All Files", "*.*")
                ]
            )
            if path:
                try:
                    self.emu.savestate.save_file(path)
                    self._set_status(f"State saved: {os.path.basename(path)}")
                except Exception as e:
                    messagebox.showerror("Save Error", str(e))
        
        def load_state(self):
            """Load emulator state"""
            if not self.rom_path or not self.emu:
                return
            
            path = filedialog.askopenfilename(
                title="Load State",
                filetypes=[
                    ("Cat's EMU DS State", "*.cds"),
                    ("DeSmuME State", "*.dst"),
                    ("All Files", "*.*")
                ]
            )
            if path and os.path.isfile(path):
                try:
                    self.emu.savestate.load_file(path)
                    self._set_status(f"State loaded: {os.path.basename(path)}")
                except Exception as e:
                    messagebox.showerror("Load Error", str(e))
        
        def take_screenshot(self):
            """Save screenshot"""
            if not self.rom_path:
                return
            
            path = filedialog.asksaveasfilename(
                title="Save Screenshot",
                defaultextension=".png",
                filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")]
            )
            if path:
                try:
                    from PIL import Image
                    buffer = self.emu.display_buffer_as_rgbx()
                    img = Image.frombytes("RGBX", (256, 384), buffer)
                    img.save(path)
                    self._set_status(f"Screenshot saved: {os.path.basename(path)}")
                except Exception as e:
                    messagebox.showerror("Screenshot Error", str(e))
        
        # ═══════════════════════════════════════════════════════════════════════════
        # INPUT HANDLING
        # ═══════════════════════════════════════════════════════════════════════════
        
        def _on_key_press(self, event):
            """Handle key press"""
            if not self.emu or not self.rom_path:
                return
            
            key = event.keysym
            if key in self.key_map:
                button = self.key_map[key]
                try:
                    self.emu.input.keypad_add_key(button)
                except:
                    pass
        
        def _on_key_release(self, event):
            """Handle key release"""
            if not self.emu or not self.rom_path:
                return
            
            key = event.keysym
            if key in self.key_map:
                button = self.key_map[key]
                try:
                    self.emu.input.keypad_rm_key(button)
                except:
                    pass
        
        def _on_touch_start(self, event):
            """Handle touch screen press"""
            if not self.emu or not self.rom_path:
                return
            
            scale = self.screen_scale.get()
            x = event.x // scale
            y = event.y // scale
            
            if 0 <= x < 256 and 0 <= y < 192:
                try:
                    self.emu.input.touch_set_pos(x, y)
                except:
                    pass
        
        def _on_touch_move(self, event):
            """Handle touch screen drag"""
            self._on_touch_start(event)
        
        def _on_touch_end(self, event):
            """Handle touch screen release"""
            if self.emu:
                try:
                    self.emu.input.touch_release()
                except:
                    pass
        
        # ═══════════════════════════════════════════════════════════════════════════
        # DEBUG PANEL
        # ═══════════════════════════════════════════════════════════════════════════
        
        def _toggle_debug_panel(self):
            """Toggle debug panel visibility"""
            self.show_debug = not self.show_debug
            self.show_debug_var.set(self.show_debug)
            
            if self.show_debug:
                self.debug_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5)
                self.window.geometry("900x520")
            else:
                self.debug_frame.pack_forget()
                self.window.geometry("540x520")
            
            self._update_debug_view()
        
        def _set_debug_mode(self, mode):
            """Set debug view mode"""
            self.debug_mode = mode
            self._update_debug_view()
        
        def _update_debug_view(self):
            """Update debug panel content"""
            self.debug_text.config(state=tk.NORMAL)
            self.debug_text.delete("1.0", tk.END)
            
            if self.debug_mode == "disasm":
                self._show_disassembly()
            elif self.debug_mode == "memory":
                self._show_memory()
            elif self.debug_mode == "registers":
                self._show_registers()
            elif self.debug_mode == "io":
                self._show_io_map()
            
            self.debug_text.config(state=tk.DISABLED)
        
        def _show_disassembly(self):
            """Show disassembly view"""
            content = """
    ╔═══════════════════════════════════════╗
    ║      ARM9 DISASSEMBLY VIEW            ║
    ╚═══════════════════════════════════════╝

    [No ROM loaded or debug info unavailable]

    ─────────────────────────────────────
    Sample disassembly format:
    ─────────────────────────────────────

    02000000: E3A00000  MOV   R0, #0x0
    02000004: E3A01001  MOV   R1, #0x1
    02000008: E0800001  ADD   R0, R0, R1
    0200000C: E3500064  CMP   R0, #0x64
    02000010: 1AFFFFFC  BNE   0x02000008
    02000014: E12FFF1E  BX    LR

    ─────────────────────────────────────
    Cat's EMU DS Debug System
    """
            self.debug_text.insert(tk.END, content)
        
        def _show_memory(self):
            """Show memory viewer"""
            content = """
    ╔═══════════════════════════════════════╗
    ║        MEMORY VIEWER                  ║
    ╚═══════════════════════════════════════╝

    Address   00 01 02 03 04 05 06 07  ASCII
    ────────────────────────────────────────
    02000000: 00 00 00 EA 00 00 00 EA  ........
    02000008: 00 00 00 EA 00 00 00 EA  ........
    02000010: 00 00 00 EA 00 00 00 EA  ........
    02000018: 00 00 00 EA 00 00 00 EA  ........
    02000020: 00 00 00 EA 00 00 00 EA  ........
    02000028: 00 00 00 EA 00 00 00 EA  ........

    ─────────────────────────────────────
    Memory Regions:
    * Main RAM:    02000000-023FFFFF
    * VRAM:        06000000-06FFFFFF
    * OAM:         07000000-070003FF
    * I/O:         04000000-04FFFFFF
    ─────────────────────────────────────
    Cat's EMU DS Memory Inspector
    """
            self.debug_text.insert(tk.END, content)
        
        def _show_registers(self):
            """Show register view"""
            content = """
    ╔═══════════════════════════════════════╗
    ║       ARM9 REGISTERS                  ║
    ╚═══════════════════════════════════════╝

    R0  = 00000000    R8  = 00000000
    R1  = 00000000    R9  = 00000000
    R2  = 00000000    R10 = 00000000
    R3  = 00000000    R11 = 00000000
    R4  = 00000000    R12 = 00000000
    R5  = 00000000    R13 = 00000000 (SP)
    R6  = 00000000    R14 = 00000000 (LR)
    R7  = 00000000    R15 = 02000000 (PC)

    ─────────────────────────────────────
    CPSR = 000000D3
    [N=0 Z=0 C=0 V=0 I=1 F=1 T=0 M=SVC]
    ─────────────────────────────────────

    ╔═══════════════════════════════════════╗
    ║       ARM7 REGISTERS                  ║
    ╚═══════════════════════════════════════╝

    R0  = 00000000    R8  = 00000000
    R1  = 00000000    R9  = 00000000
    R2  = 00000000    R10 = 00000000
    R3  = 00000000    R11 = 00000000
    R4  = 00000000    R12 = 00000000
    R5  = 00000000    R13 = 00000000 (SP)
    R6  = 00000000    R14 = 00000000 (LR)
    R7  = 00000000    R15 = 00000000 (PC)

    Cat's EMU DS Register View
    """
            self.debug_text.insert(tk.END, content)
        
        def _show_io_map(self):
            """Show I/O map view"""
            content = """
    ╔═══════════════════════════════════════╗
    ║          I/O REGISTER MAP             ║
    ╚═══════════════════════════════════════╝

    Display Registers:
    ─────────────────────────────────────
    04000000 DISPCNT_A    = 00000000
    04000004 DISPSTAT     = 00000000
    04000006 VCOUNT       = 00000000
    04000008 BG0CNT       = 00000000
    0400000A BG1CNT       = 00000000

    DMA Registers:
    ─────────────────────────────────────
    040000B0 DMA0SAD      = 00000000
    040000B4 DMA0DAD      = 00000000
    040000B8 DMA0CNT      = 00000000

    Timer Registers:
    ─────────────────────────────────────
    04000100 TM0CNT_L     = 0000
    04000102 TM0CNT_H     = 0000

    Key Input:
    ─────────────────────────────────────
    04000130 KEYINPUT     = 03FF
    04000132 KEYCNT       = 0000

    Cat's EMU DS I/O Inspector
    """
            self.debug_text.insert(tk.END, content)
        
        # ═══════════════════════════════════════════════════════════════════════════
        # UI HELPERS
        # ═══════════════════════════════════════════════════════════════════════════
        
        def _set_status(self, msg):
            """Update status bar message"""
            self.status_msg.config(text=msg)
        
        def _update_state_indicator(self, state):
            """Update emulation state indicator"""
            colors = {
                "RUNNING": CatTheme.STATUS_ACTIVE,
                "PAUSED": CatTheme.FG_ACCENT,
                "STOPPED": CatTheme.FG_DIM
            }
            self.state_label.config(
                text=f"* {state}",
                fg=colors.get(state, CatTheme.FG_DIM)
            )
        
        def _resize_screen(self):
            """Resize screen canvases"""
            scale = self.screen_scale.get()
            w = self.DS_WIDTH * scale
            h = self.DS_HEIGHT * scale
            
            self.top_screen.config(width=w, height=h)
            self.bottom_screen.config(width=w, height=h)
            
            # Update window size
            base_width = w + 28  # padding
            if self.show_debug:
                base_width += 360
            self.window.geometry(f"{base_width}x{h*2 + 80}")
        
        def _update_layout(self):
            """Update screen layout (vertical/horizontal)"""
            # TODO: Implement horizontal layout
            pass
        
        def _reset_window_size(self):
            """Reset window to default size"""
            self.screen_scale.set(2)
            self._resize_screen()
        
        def _show_input_config(self):
            """Show input configuration dialog"""
            messagebox.showinfo(
                "Input Configuration",
                "Default Key Mappings:\n\n"
                "D-Pad: Arrow Keys\n"
                "A: Z\n"
                "B: X\n"
                "X: S\n"
                "Y: A\n"
                "L: Q\n"
                "R: W\n"
                "Start: Enter\n"
                "Select: Backspace\n\n"
                "Touch: Click bottom screen"
            )
        
        def _show_audio_config(self):
            """Show audio configuration dialog"""
            messagebox.showinfo(
                "Audio Configuration",
                "Audio settings coming in future versions!\n\n"
                "Cat's EMU DS"
            )
        
        def _show_about(self):
            """Show about dialog"""
            messagebox.showinfo(
                "About Cat's EMU DS",
                f"Cat's EMU DS {self.VERSION}\n\n"
                "A CatOS-Powered Nintendo DS Emulator\n"
                "With NO$GBA-Style Debug Interface\n\n"
                "By Team Flames / Samsoft\n\n"
                "Backend: py-desmume\n"
                "GUI: Tkinter\n\n"
                "No BIOS files required!\n"
                "Just load a ROM and play."
            )
        
        def _show_shortcuts(self):
            """Show keyboard shortcuts"""
            messagebox.showinfo(
                "Keyboard Shortcuts",
                "File:\n"
                "  Ctrl+O    Open ROM\n"
                "  F5        Save State\n"
                "  F7        Load State\n"
                "  F12       Screenshot\n\n"
                "Emulation:\n"
                "  F9        Run\n"
                "  F8        Pause\n"
                "  Ctrl+R    Reset\n"
                "  .         Frame Advance\n\n"
                "Debug:\n"
                "  F1        Toggle Debug Panel"
            )
        
        def _on_close(self):
            """Handle window close"""
            self.running = False
            if self.emu:
                try:
                    self.emu.destroy()
                except:
                    pass
            self.window.destroy()
        
        # ═══════════════════════════════════════════════════════════════════════════
        # MAIN ENTRY
        # ═══════════════════════════════════════════════════════════════════════════
        
        def run(self):
            """Start the emulator"""
            self.window.mainloop()


    # ═══════════════════════════════════════════════════════════════════════════════
    # ENTRY POINT
    # ═══════════════════════════════════════════════════════════════════════════════

    def main():
        """Main entry point"""
        print("=" * 65)
        print("  Cat's EMU DS 0.1 infdev")
        print("  A CatOS-Powered Nintendo DS Emulator")
        print("  By Team Flames / Samsoft")
        print("=" * 65)
        print()
        
        # Check for ROM argument
        rom_path = None
        if len(sys.argv) > 1:
            rom_path = sys.argv[1]
            print(f"[CatOS] Loading ROM: {rom_path}")
        
        # Check dependencies
        if not EMU_AVAILABLE:
            print("[CatOS] WARNING: py-desmume not installed!")
            print("[CatOS] Install with: pip install py-desmume")
            print("[CatOS] Running in GUI-only mode...")
        
        # Create and run emulator
        app = CatsEmuDS(rom_path)
        app.run()


    if __name__ == "__main__":
        main()
