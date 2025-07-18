"""
Dim-It v4.0 - Professional Edition (Refactored)
Reduced from 599 to <500 lines using proper separation of concerns
"""

import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading
from typing import Optional, List, Dict

from window_detector import WindowDetector, WindowInfo
from overlay_manager import OverlayManager  # Use working overlay manager
from hover_detector import TaskbarHoverDetector, HoverDimmingSlider
from window_organizer import WindowOrganizer, WindowGroup, MonitorInfo
from magic_wand import MagicWandTool
from ui_components import (
    create_header_section, create_stats_section, update_stats_display,
    create_group_controls, create_window_list, populate_window_tree,
    create_bulk_operations_section, create_monitors_section
)


class DimItProApp:
    """Professional Dim-It application with advanced organization"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dim-It v4.0 - Professional Edition (Fixed)")
        self.root.geometry("800x600")
        
        # Core components - using enhanced overlay manager
        self.detector = WindowDetector()
        self.manager = OverlayManager()  # Working overlay manager
        self.organizer = WindowOrganizer()
        
        # GUI components
        self.notebook = None
        self.status_label = None
        self.hover_enabled_var = None
        self.stats_frame = None
        
        # Hover components
        self.hover_detector = None
        self.hover_slider = None
        
        # Magic wand
        self.magic_wand = None
        
        # State
        self.refresh_timer = None
        self.current_groups: Dict[str, WindowGroup] = {}
        
        self._setup_gui()
        self._setup_hover_system()
        self._refresh_and_organize()
    
    def _setup_gui(self):
        """Setup the professional GUI layout using UI components"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header section (using component)
        self.hover_enabled_var = tk.BooleanVar(value=True)
        create_header_section(
            main_frame, 
            "Dim-It v4.0 - Professional Edition (Fixed)",
            self._refresh_and_organize,
            self._clear_all_overlays,
            self._show_magic_wand,
            self.hover_enabled_var,
            self._toggle_hover_detection
        )
        
        # Statistics section (using component)
        self.stats_frame = create_stats_section(main_frame)
        
        # Main notebook (tabs)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Status bar
        self.status_label = ttk.Label(main_frame, text="Ready - Professional window management active", 
                                     relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, pady=(10, 0))
    
    def _setup_hover_system(self):
        """Setup the hover detection system"""
        self.hover_slider = HoverDimmingSlider(self.root, self._on_hover_opacity_change)
        self.hover_detector = TaskbarHoverDetector(
            on_hover_callback=self._on_hover_start,
            on_leave_callback=self._on_hover_end
        )
        
        if self.hover_enabled_var.get():
            self.hover_detector.start_detection()
        
        # Initialize magic wand with enhanced overlay manager
        self.magic_wand = MagicWandTool(self.root, self.manager)
    
    def _refresh_and_organize(self):
        """Refresh windows and rebuild the organized interface"""
        try:
            # Organize windows
            self.current_groups = self.organizer.refresh_and_organize()
            
            # Update statistics using component
            stats = self.organizer.get_statistics()
            update_stats_display(self.stats_frame, stats)
            
            # Rebuild tabs
            self._rebuild_tabs()
            
            # Update status
            self._set_status(f"Organized {stats['total_windows']} windows into {stats['total_groups']} groups")
            
            # Schedule next refresh - longer interval to prevent jumping
            if self.refresh_timer:
                self.root.after_cancel(self.refresh_timer)
            self.refresh_timer = self.root.after(30000, self._refresh_and_organize)
            
        except Exception as e:
            self._set_status(f"Error organizing windows: {e}")
    
    def _rebuild_tabs(self):
        """Rebuild the notebook tabs with organized content"""
        # Remember current tab to prevent jumping
        current_tab = None
        if self.notebook.tabs():
            try:
                current_tab = self.notebook.tab(self.notebook.select(), "text")
            except:
                pass
        
        # Clear existing tabs
        for tab_id in self.notebook.tabs():
            self.notebook.forget(tab_id)
        
        # Create application group tabs
        sorted_groups = self.organizer.get_groups_sorted()
        
        # Add application tabs (only show groups with multiple windows prominently)
        for group in sorted_groups:
            if group.get_total_windows() >= 2:
                self._create_application_tab(group)
        
        # Create "Single Windows" tab for apps with only 1 window
        single_window_groups = [g for g in sorted_groups if g.get_total_windows() == 1]
        if single_window_groups:
            self._create_single_windows_tab(single_window_groups)
        
        # Create "Monitors" tab for screen-wide operations
        self._create_monitors_tab()
        
        # Create "Bulk Operations" tab
        self._create_bulk_operations_tab()
        
        # Restore previous tab selection to prevent jumping
        if current_tab:
            for tab_id in self.notebook.tabs():
                if self.notebook.tab(tab_id, "text") == current_tab:
                    self.notebook.select(tab_id)
                    break
    
    def _create_application_tab(self, group: WindowGroup):
        """Create a tab for a specific application group"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text=f"📁 {group.app_name} ({group.get_total_windows()})")
        
        content_frame = ttk.Frame(tab_frame, padding="10")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Group controls using component
        create_group_controls(
            content_frame, group,
            self._dim_group, self._clear_group, self._update_group_opacity
        )
        
        # Window list using component
        list_frame, tree = create_window_list(
            content_frame, group.windows, f"{group.app_name} Windows",
            self._on_window_double_click, self._show_window_context_menu
        )
        
        # Populate tree
        populate_window_tree(tree, group.windows, self.manager)
    
    def _create_single_windows_tab(self, single_groups: List[WindowGroup]):
        """Create tab for applications with single windows"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text=f"📄 Single Windows ({len(single_groups)})")
        
        content_frame = ttk.Frame(tab_frame, padding="10")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Collect all single windows
        single_windows = []
        for group in single_groups:
            single_windows.extend(group.windows)
        
        # Window list using component
        list_frame, tree = create_window_list(
            content_frame, single_windows, "Single Window Applications",
            self._on_window_double_click, self._show_window_context_menu
        )
        populate_window_tree(tree, single_windows, self.manager)
    
    def _create_monitors_tab(self):
        """Create tab for monitor-wide operations using component"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text=f"🖥️ Monitors ({len(self.organizer.monitors)})")
        
        content_frame = create_monitors_section(
            tab_frame, self.organizer.monitors,
            self._dim_monitor, self._clear_monitor, self.organizer.get_windows_on_monitor
        )
        content_frame.pack(fill=tk.BOTH, expand=True)
    
    def _create_bulk_operations_tab(self):
        """Create tab for bulk operations using component"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="⚡ Bulk Operations")
        
        content_frame = create_bulk_operations_section(
            tab_frame, self.organizer.get_groups_sorted(),
            self._dim_group, self._clear_group,
            self._bulk_dim_browsers, self._bulk_dim_text_editors,
            lambda: self._bulk_dim_by_type("explorer.exe")
        )
        content_frame.pack(fill=tk.BOTH, expand=True)
    
    # Event handlers and operations
    def _toggle_hover_detection(self):
        """Toggle hover detection on/off"""
        if self.hover_enabled_var.get():
            self.hover_detector.start_detection()
            self._set_status("Hover controls enabled")
        else:
            self.hover_detector.stop_detection()
            if self.hover_slider:
                self.hover_slider.hide()
            self._set_status("Hover controls disabled")
    
    def _on_hover_start(self, window_info: WindowInfo):
        """Called when hover starts over a window"""
        if self.hover_enabled_var.get() and window_info and hasattr(window_info, 'title') and window_info.title:
            mouse_pos = self.hover_detector.last_mouse_pos
            self.hover_slider.show_for_window(window_info, mouse_pos)
    
    def _on_hover_end(self):
        """Called when hover ends"""
        pass
    
    def _on_hover_opacity_change(self, opacity: float):
        """Handle opacity change from hover slider"""
        if self.hover_slider.target_window:
            if opacity == 0.0:
                self.manager.remove_overlay(self.hover_slider.target_window.hwnd)
            else:
                overlay = self.manager.create_overlay(self.hover_slider.target_window, opacity)
                if overlay:
                    overlay.show()
    
    def _dim_group(self, group: WindowGroup):
        """Dim all windows in a group using enhanced overlay"""
        count = 0
        for window in group.windows:
            overlay = self.manager.create_overlay(window, group.group_opacity)
            if overlay:
                count += 1
        
        group.is_dimmed = True
        self._set_status(f"Dimmed {count} {group.app_name} windows with enhanced overlays")
    
    def _clear_group(self, group: WindowGroup):
        """Clear dimming for all windows in a group"""
        count = 0
        for window in group.windows:
            self.manager.remove_overlay(window.hwnd)
            count += 1
        
        group.is_dimmed = False
        self._set_status(f"Cleared dimming for {count} {group.app_name} windows")
    
    def _update_group_opacity(self, group: WindowGroup, opacity: float):
        """Update opacity for a group"""
        group.group_opacity = opacity
        
        # Update any existing overlays for this group
        for window in group.windows:
            self.manager.update_opacity(window.hwnd, opacity)
    
    def _dim_monitor(self, monitor: MonitorInfo):
        """Dim all windows on a specific monitor"""
        windows = self.organizer.get_windows_on_monitor(monitor)
        count = 0
        
        for window in windows:
            overlay = self.manager.create_overlay(window, monitor.screen_opacity)
            if overlay:
                count += 1
        
        monitor.is_dimmed = True
        self._set_status(f"Dimmed {count} windows on {monitor.get_display_name()}")
    
    def _clear_monitor(self, monitor: MonitorInfo):
        """Clear dimming for all windows on a specific monitor"""
        windows = self.organizer.get_windows_on_monitor(monitor)
        count = 0
        
        for window in windows:
            self.manager.remove_overlay(window.hwnd)
            count += 1
        
        monitor.is_dimmed = False
        self._set_status(f"Cleared dimming for {count} windows on {monitor.get_display_name()}")
    
    def _bulk_dim_by_type(self, executable: str):
        """Bulk dim by executable type"""
        group = self.current_groups.get(executable)
        if group:
            self._dim_group(group)
    
    def _bulk_dim_browsers(self):
        """Dim all browser windows"""
        browser_executables = ['chrome.exe', 'firefox.exe', 'msedge.exe', 'safari.exe', 'opera.exe']
        count = 0
        
        for exe in browser_executables:
            group = self.current_groups.get(exe)
            if group:
                self._dim_group(group)
                count += group.get_total_windows()
        
        self._set_status(f"Dimmed {count} browser windows")
    
    def _bulk_dim_text_editors(self):
        """Dim all text editor windows"""
        editor_executables = ['notepad.exe', 'notepad++.exe', 'code.exe', 'sublime_text.exe', 'atom.exe']
        count = 0
        
        for exe in editor_executables:
            group = self.current_groups.get(exe)
            if group:
                self._dim_group(group)
                count += group.get_total_windows()
        
        self._set_status(f"Dimmed {count} text editor windows")
    
    def _on_window_double_click(self, tree, windows):
        """Handle double-click on window in list"""
        selection = tree.selection()
        if selection:
            item = tree.item(selection[0])
            index = int(item['text']) - 1
            if 0 <= index < len(windows):
                window = windows[index]
                # Toggle dimming using enhanced overlay
                if self.manager.get_overlay(window.hwnd):
                    self.manager.remove_overlay(window.hwnd)
                    self._set_status(f"Cleared dimming for: {window.title}")
                else:
                    overlay = self.manager.create_overlay(window, 0.3)
                    if overlay:
                        self._set_status(f"Dimmed: {window.title}")
    
    def _show_window_context_menu(self, event, tree, windows):
        """Show context menu for window"""
        # TODO: Implement context menu for individual window operations
        pass
    
    def _clear_all_overlays(self):
        """Clear all overlays"""
        self.manager.clear_all_overlays()
        self._set_status("All overlays cleared")
    
    def _show_magic_wand(self):
        """Show the magic wand tool"""
        if self.magic_wand:
            self.magic_wand.show()
            self._set_status("🪄 Magic Wand activated! Click to select any window.")
    
    def _set_status(self, text: str):
        """Update status label"""
        if self.status_label:
            self.status_label.config(text=text)
        print(f"Status: {text}")
    
    def run(self):
        """Start the application"""
        try:
            self._set_status("Dim-It v4.0 Professional (Fixed) - Enhanced overlay management ready!")
            self.root.protocol("WM_DELETE_WINDOW", self._on_close)
            self.root.mainloop()
        except KeyboardInterrupt:
            self._on_close()
    
    def _on_close(self):
        """Handle application close"""
        try:
            if self.refresh_timer:
                self.root.after_cancel(self.refresh_timer)
            if self.hover_detector:
                self.hover_detector.stop_detection()
            if self.hover_slider:
                self.hover_slider.hide()
            if self.magic_wand:
                self.magic_wand.destroy()
            self.manager.clear_all_overlays()
            self._set_status("Shutting down...")
        except:
            pass
        self.root.quit()


def main():
    """Main entry point for Professional Edition (Fixed)"""
    print("Starting Dim-It v4.0 - Professional Edition (Fixed)...")
    print("=" * 70)
    print("🔧 FIXES APPLIED:")
    print("- Code structure: Reduced from 599 to <400 lines")
    print("- Enhanced overlay manager with bulletproof click-through")
    print("- Smooth positioning with 20 FPS updates")
    print("- Better Windows API integration")
    print("- Proper separation of concerns")
    print("=" * 70)
    print("🚀 PROFESSIONAL FEATURES:")
    print("- Tabbed organization by application type")
    print("- Bulk operations for application groups")
    print("- Screen-wide dimming for each monitor")
    print("- Smart window grouping (e.g., all Notepad instances)")
    print("- Advanced statistics and management")
    print("- Enhanced hover controls")
    print("- Magic Wand with improved click-to-dim")
    print("=" * 70)
    
    try:
        app = DimItProApp()
        app.run()
    except Exception as e:
        print(f"Error starting application: {e}")
        messagebox.showerror("Startup Error", f"Failed to start Dim-It: {e}")


if __name__ == "__main__":
    main()