import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import pandas as pd
import os

class SelectionManager:
    """Manages selection independently from TreeView"""
    def __init__(self):
        self.selected_ids = set()  # Selected IDs as strings - SET prevents duplicates
        
    def toggle_selection(self, id_str):
        """Toggle selection of an ID"""
        id_str = str(id_str)  # Ensure it's a string
        if id_str in self.selected_ids:
            self.selected_ids.remove(id_str)
        else:
            self.selected_ids.add(id_str)
    
    def select_all(self, id_list):
        """Select all IDs from list"""
        new_ids = set(str(id_val) for id_val in id_list)
        self.selected_ids.update(new_ids)
    
    def select_only(self, id_list):
        """Replace entire selection with provided list"""
        self.selected_ids = set(str(id_val) for id_val in id_list)
    
    def deselect_all(self):
        """Deselect everything"""
        self.selected_ids.clear()
    
    def is_selected(self, id_str):
        """Check if an ID is selected"""
        return str(id_str) in self.selected_ids
    
    def get_selected_from_filtered(self, filtered_ids):
        """Get only selected IDs that are also in current filter"""
        filtered_ids_str = set(str(id_val) for id_val in filtered_ids)
        result = self.selected_ids.intersection(filtered_ids_str)
        return result

class ContactChannelEditor:
    def __init__(self, parent, contacts_df=None, channels_df=None, converter=None):
        self.parent = parent
        self.contacts_df = contacts_df
        self.channels_df = channels_df
        self.converter = converter
        
        # Create editor window
        self.editor_window = tk.Toplevel(parent.root)
        self.editor_window.title("Preview & Edit - Select items to import")
        self.editor_window.geometry("1000x700")
        self.editor_window.transient(parent.root)
        self.editor_window.grab_set()
        
        # Selection managers - completely independent from TreeView
        self.contact_selection = SelectionManager()
        self.channel_selection = SelectionManager()
        
        # Initialize tree references
        self.contacts_tree = None
        self.channels_tree = None
        
        # Track original dataframes for filtering
        self.original_contacts_df = contacts_df.copy() if contacts_df is not None else None
        self.original_channels_df = channels_df.copy() if channels_df is not None else None
        
        # Create checkbox images
        self.create_checkbox_images()
        
        self.setup_editor_gui()
        
    def create_checkbox_images(self):
        """Create checkbox images for checked/unchecked states"""
        self.checked_image = tk.PhotoImage(width=16, height=16)
        self.unchecked_image = tk.PhotoImage(width=16, height=16)
        
        # Simple checked box (green with checkmark)
        self.checked_image.put("#00AA00", (0, 0, 16, 16))
        self.checked_image.put("#FFFFFF", (2, 2, 14, 14))
        for i in range(4, 8):
            self.checked_image.put("#00AA00", (i, 8 + (i - 4)))
        for i in range(8, 12):
            self.checked_image.put("#00AA00", (i, 12 - (i - 8)))
        
        # Simple unchecked box (gray border)
        self.unchecked_image.put("#808080", (0, 0, 16, 16))
        self.unchecked_image.put("#FFFFFF", (2, 2, 14, 14))
        
    def setup_editor_gui(self):
        # Header frame
        header_frame = tk.Frame(self.editor_window, bg="#2E86AB")
        header_frame.pack(fill="x")
        
        title_label = tk.Label(header_frame, text="Preview & Select Items for Import", 
                              font=("Arial", 14, "bold"), bg="#2E86AB", fg="white")
        title_label.pack(pady=10)
        
        # Main notebook for tabs
        self.notebook = ttk.Notebook(self.editor_window)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Contacts tab
        if self.contacts_df is not None:
            self.setup_contacts_tab()
            
        # Channels tab  
        if self.channels_df is not None:
            self.setup_channels_tab()
            
        # Bottom button frame
        self.setup_bottom_buttons()
        
        # Don't select everything automatically - let user choose
        self.update_counts()
        
    def setup_contacts_tab(self):
        contacts_frame = ttk.Frame(self.notebook)
        self.notebook.add(contacts_frame, text=f"Contacts ({len(self.contacts_df)})")
        
        # Control frame
        control_frame = ttk.Frame(contacts_frame)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        # Limit warning
        over_limit = len(self.contacts_df) > self.converter.MAX_CONTACTS
        limit_text = f"OpenGD77 Limit: {self.converter.MAX_CONTACTS} contacts max"
        if over_limit:
            limit_text += f" WARNING ({len(self.contacts_df) - self.converter.MAX_CONTACTS} excess)"
            
        self.contacts_limit_label = ttk.Label(control_frame, text=limit_text,
                                            foreground="red" if over_limit else "green")
        self.contacts_limit_label.pack(side="left")
        
        # Filter count label
        self.contacts_filter_label = ttk.Label(control_frame, text="", foreground="blue")
        self.contacts_filter_label.pack(side="left", padx=(20, 0))
        
        # Search frame
        search_frame = ttk.Frame(contacts_frame)
        search_frame.pack(fill="x", padx=5, pady=2)
        
        ttk.Label(search_frame, text="Search:").pack(side="left")
        self.contacts_search_var = tk.StringVar()
        self.contacts_search_var.trace("w", self.filter_contacts)
        ttk.Entry(search_frame, textvariable=self.contacts_search_var, width=30).pack(side="left", padx=5)
        
        # Filter combobox
        ttk.Label(search_frame, text="Type:").pack(side="left", padx=(20,5))
        self.contacts_filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(search_frame, textvariable=self.contacts_filter_var,
                                   values=["All", "Group", "Private"], state="readonly", width=10)
        filter_combo.pack(side="left")
        filter_combo.bind("<<ComboboxSelected>>", self.filter_contacts)
        
        # Selection control frame
        selection_frame = ttk.Frame(contacts_frame)
        selection_frame.pack(fill="x", padx=5, pady=2)
        
        ttk.Button(selection_frame, text="Select All Visible", 
                  command=self.select_all_contacts).pack(side="left", padx=2)
        ttk.Button(selection_frame, text="Deselect All", 
                  command=self.deselect_all_contacts).pack(side="left", padx=2)
        
        # Selected count label
        self.contacts_selected_label = ttk.Label(selection_frame, text="Selected: 0 for import", 
                                               foreground="green", font=("Arial", 9, "bold"))
        self.contacts_selected_label.pack(side="left", padx=(20, 0))
        
        # Instructions
        instruction_frame = ttk.Frame(contacts_frame)
        instruction_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(instruction_frame, text="Click on checkbox or double-click row to select/deselect. Selection preserved when filtering.", 
                 font=("Arial", 8), foreground="blue").pack(side="left")
        
        # Treeview frame for contacts
        tree_frame = ttk.Frame(contacts_frame)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal")
        h_scrollbar.pack(side="bottom", fill="x")
        
        # Treeview for contacts
        self.contacts_tree = ttk.Treeview(tree_frame, 
                                         columns=("name", "id", "type"),
                                         show="tree headings",
                                         yscrollcommand=v_scrollbar.set,
                                         xscrollcommand=h_scrollbar.set)
        
        # Configure scrollbars
        v_scrollbar.config(command=self.contacts_tree.yview)
        h_scrollbar.config(command=self.contacts_tree.xview)
        
        # Configure columns
        self.contacts_tree.heading("#0", text="Select")
        self.contacts_tree.heading("name", text="Contact Name")
        self.contacts_tree.heading("id", text="ID")
        self.contacts_tree.heading("type", text="Type")
        
        self.contacts_tree.column("#0", width=60, anchor="center")
        self.contacts_tree.column("name", width=400)
        self.contacts_tree.column("id", width=100)
        self.contacts_tree.column("type", width=80)
        
        self.contacts_tree.pack(fill="both", expand=True)
        
        # Bind events
        self.contacts_tree.bind("<Button-1>", self.on_contacts_click)
        self.contacts_tree.bind("<Double-1>", self.on_contacts_double_click)
        
        # Populate tree
        self.populate_contacts_tree()

    def setup_channels_tab(self):
        channels_frame = ttk.Frame(self.notebook)
        self.notebook.add(channels_frame, text=f"Channels ({len(self.channels_df)})")
        
        # Control frame
        control_frame = ttk.Frame(channels_frame)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(control_frame, text="All channels will be imported", 
                 foreground="green").pack(side="left")
        
        # Filter count label
        self.channels_filter_label = ttk.Label(control_frame, text="", foreground="blue")
        self.channels_filter_label.pack(side="left", padx=(20, 0))
        
        # Search frame
        search_frame = ttk.Frame(channels_frame)
        search_frame.pack(fill="x", padx=5, pady=2)
        
        ttk.Label(search_frame, text="Search:").pack(side="left")
        self.channels_search_var = tk.StringVar()
        self.channels_search_var.trace("w", self.filter_channels)
        ttk.Entry(search_frame, textvariable=self.channels_search_var, width=30).pack(side="left", padx=5)
        
        # Filter combobox
        ttk.Label(search_frame, text="Type:").pack(side="left", padx=(20,5))
        self.channels_filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(search_frame, textvariable=self.channels_filter_var,
                                   values=["All", "Analogue", "Digital"], state="readonly", width=10)
        filter_combo.pack(side="left")
        filter_combo.bind("<<ComboboxSelected>>", self.filter_channels)
        
        # Selection control frame
        selection_frame = ttk.Frame(channels_frame)
        selection_frame.pack(fill="x", padx=5, pady=2)
        
        ttk.Button(selection_frame, text="Select All Visible", 
                  command=self.select_all_channels).pack(side="left", padx=2)
        ttk.Button(selection_frame, text="Deselect All", 
                  command=self.deselect_all_channels).pack(side="left", padx=2)
        
        # Selected count label
        self.channels_selected_label = ttk.Label(selection_frame, text="Selected: 0 for import", 
                                               foreground="green", font=("Arial", 9, "bold"))
        self.channels_selected_label.pack(side="left", padx=(20, 0))
        
        # Instructions
        instruction_frame = ttk.Frame(channels_frame)
        instruction_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(instruction_frame, text="Click on checkbox or double-click row to select/deselect. Selection preserved when filtering.", 
                 font=("Arial", 8), foreground="blue").pack(side="left")
        
        # Treeview frame for channels
        tree_frame = ttk.Frame(channels_frame)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Scrollbars
        v_scrollbar_ch = ttk.Scrollbar(tree_frame)
        v_scrollbar_ch.pack(side="right", fill="y")
        h_scrollbar_ch = ttk.Scrollbar(tree_frame, orient="horizontal")
        h_scrollbar_ch.pack(side="bottom", fill="x")
        
        # Treeview for channels
        self.channels_tree = ttk.Treeview(tree_frame, 
                                         columns=("name", "type", "rx_freq", "tx_freq"),
                                         show="tree headings",
                                         yscrollcommand=v_scrollbar_ch.set,
                                         xscrollcommand=h_scrollbar_ch.set)
        
        # Configure scrollbars
        v_scrollbar_ch.config(command=self.channels_tree.yview)
        h_scrollbar_ch.config(command=self.channels_tree.xview)
        
        # Configure columns
        self.channels_tree.heading("#0", text="Select")
        self.channels_tree.heading("name", text="Channel Name")
        self.channels_tree.heading("type", text="Type")
        self.channels_tree.heading("rx_freq", text="RX Freq")
        self.channels_tree.heading("tx_freq", text="TX Freq")
        
        self.channels_tree.column("#0", width=60, anchor="center")
        self.channels_tree.column("name", width=250)
        self.channels_tree.column("type", width=80)
        self.channels_tree.column("rx_freq", width=100)
        self.channels_tree.column("tx_freq", width=100)
        
        self.channels_tree.pack(fill="both", expand=True)
        
        # Bind events
        self.channels_tree.bind("<Button-1>", self.on_channels_click)
        self.channels_tree.bind("<Double-1>", self.on_channels_double_click)
        
        # Populate tree
        self.populate_channels_tree()
        
    def populate_contacts_tree(self):
        """Populate TreeView based on SelectionManager state"""
        if self.contacts_tree is None:
            return
            
        # Clear existing items
        for item in self.contacts_tree.get_children():
            self.contacts_tree.delete(item)
            
        # Add contacts with selection state from SelectionManager
        for idx, row in self.contacts_df.iterrows():
            contact_id_str = str(row['ID'])
            is_selected = self.contact_selection.is_selected(contact_id_str)
            
            if idx >= self.converter.MAX_CONTACTS:
                tags = ("over_limit",)
            else:
                tags = ()
                
            # Use unique IID
            unique_iid = f"contact_{contact_id_str}_{idx}"
            
            self.contacts_tree.insert("", "end", 
                                     iid=unique_iid,
                                     text="",
                                     image=self.checked_image if is_selected else self.unchecked_image,
                                     values=(row['Contact Name'], row['ID'], row['ID Type']),
                                     tags=tags)
            
        # Configure tags
        self.contacts_tree.tag_configure("over_limit", background="#ffeeee")
        
        # Update counts
        self.update_counts()
        
    def populate_channels_tree(self):
        """Populate TreeView based on SelectionManager state"""
        if self.channels_tree is None:
            return
            
        # Clear existing items
        for item in self.channels_tree.get_children():
            self.channels_tree.delete(item)
            
        # Add channels with selection state from SelectionManager
        for idx, row in self.channels_df.iterrows():
            channel_id_str = str(row['Channel Number'])
            is_selected = self.channel_selection.is_selected(channel_id_str)
            
            # Use unique IID
            unique_iid = f"channel_{channel_id_str}_{idx}"
            
            self.channels_tree.insert("", "end", 
                                     iid=unique_iid,
                                     text="",
                                     image=self.checked_image if is_selected else self.unchecked_image,
                                     values=(row['Channel Name'], row['Channel Type'], 
                                            row['Rx Frequency'], row['Tx Frequency']))
                                                      
        # Update counts
        self.update_counts()
    
    def filter_contacts(self, *args):
        if self.contacts_tree is None:
            return
            
        search_text = self.contacts_search_var.get().lower()
        filter_type = self.contacts_filter_var.get()
        
        # Filter dataframe
        filtered_df = self.original_contacts_df.copy()
        
        if search_text:
            filtered_df = filtered_df[filtered_df['Contact Name'].str.lower().str.contains(search_text, na=False)]
            
        if filter_type != "All":
            filtered_df = filtered_df[filtered_df['ID Type'] == filter_type]
            
        self.contacts_df = filtered_df
        self.populate_contacts_tree()
        
    def filter_channels(self, *args):
        if self.channels_tree is None:
            return
            
        search_text = self.channels_search_var.get().lower()
        filter_type = self.channels_filter_var.get()
        
        # Filter dataframe
        filtered_df = self.original_channels_df.copy()
        
        if search_text:
            filtered_df = filtered_df[filtered_df['Channel Name'].str.lower().str.contains(search_text, na=False)]
            
        if filter_type != "All":
            filtered_df = filtered_df[filtered_df['Channel Type'] == filter_type]
            
        self.channels_df = filtered_df
        self.populate_channels_tree()
        
    def on_contacts_click(self, event):
        if self.contacts_tree is None:
            return
        
        item = self.contacts_tree.identify_row(event.y)
        region = self.contacts_tree.identify_region(event.x, event.y)
        
        if item and region == "tree":
            self.toggle_contact_selection(item)
            return "break"
                    
    def on_channels_click(self, event):
        if self.channels_tree is None:
            return
        
        item = self.channels_tree.identify_row(event.y)
        region = self.channels_tree.identify_region(event.x, event.y)
        
        if item and region == "tree":
            self.toggle_channel_selection(item)
            return "break"
            
    def on_contacts_double_click(self, event):
        if self.contacts_tree is None:
            return
        
        item = self.contacts_tree.identify_row(event.y)
        if item:
            self.toggle_contact_selection(item)
            
    def on_channels_double_click(self, event):
        if self.channels_tree is None:
            return
        
        item = self.channels_tree.identify_row(event.y)
        if item:
            self.toggle_channel_selection(item)
                
    def toggle_contact_selection(self, item):
        """Toggle contact selection using SelectionManager"""
        try:
            # Get contact ID from values
            item_values = self.contacts_tree.item(item, 'values')
            contact_id_str = str(item_values[1])  # ID is in column 1
            
            # Check limit before adding
            if not self.contact_selection.is_selected(contact_id_str):
                current_selected = len(self.contact_selection.selected_ids)
                if current_selected >= self.converter.MAX_CONTACTS:
                    messagebox.showwarning("Limit Reached", 
                                         f"Cannot select more than {self.converter.MAX_CONTACTS} contacts!")
                    return
            
            # Toggle in SelectionManager
            self.contact_selection.toggle_selection(contact_id_str)
            
            # Update visual state
            is_selected = self.contact_selection.is_selected(contact_id_str)
            self.contacts_tree.item(item, image=self.checked_image if is_selected else self.unchecked_image)
            
            # Update counts
            self.update_counts()
            
        except Exception as e:
            print(f"Error toggling contact selection: {e}")
        
    def toggle_channel_selection(self, item):
        """Toggle channel selection using SelectionManager"""
        try:
            # Get channel name and find ID from dataframe
            item_values = self.channels_tree.item(item, 'values')
            channel_name = item_values[0]  # Channel name is in column 0
            
            # Find channel ID from dataframe
            channel_row = self.channels_df[self.channels_df['Channel Name'] == channel_name]
            if channel_row.empty:
                return
            channel_id_str = str(channel_row.iloc[0]['Channel Number'])
            
            # Toggle in SelectionManager
            self.channel_selection.toggle_selection(channel_id_str)
            
            # Update visual state
            is_selected = self.channel_selection.is_selected(channel_id_str)
            self.channels_tree.item(item, image=self.checked_image if is_selected else self.unchecked_image)
            
            # Update counts
            self.update_counts()
            
        except Exception as e:
            print(f"Error toggling channel selection: {e}")
        
    def select_all_contacts(self):
        """Add visible contacts to existing selection instead of replacing"""
        if self.contacts_tree is None:
            return
            
        # Get IDs of currently visible contacts
        visible_ids = []
        for idx, row in self.contacts_df.iterrows():
            visible_ids.append(str(row['ID']))
        
        # Add to existing selection instead of replacing
        for contact_id in visible_ids:
            if len(self.contact_selection.selected_ids) < self.converter.MAX_CONTACTS:
                self.contact_selection.selected_ids.add(contact_id)
            else:
                break
        
        # Refresh TreeView
        self.populate_contacts_tree()
        
    def deselect_all_contacts(self):
        """Deselect all contacts using SelectionManager"""
        if self.contacts_tree is None:
            return
            
        self.contact_selection.deselect_all()
        self.populate_contacts_tree()
        
    def select_all_channels(self):
        """Add visible channels to existing selection instead of replacing"""
        if self.channels_tree is None:
            return
            
        # Get IDs of currently visible channels
        visible_ids = [str(row['Channel Number']) for idx, row in self.channels_df.iterrows()]
        
        # Add to existing selection
        for channel_id in visible_ids:
            self.channel_selection.selected_ids.add(channel_id)
        
        # Refresh TreeView
        self.populate_channels_tree()
        
    def deselect_all_channels(self):
        """Deselect all channels using SelectionManager"""
        if self.channels_tree is None:
            return
            
        self.channel_selection.deselect_all()
        self.populate_channels_tree()
        
    def update_counts(self):
        """CORRECTED: Update counts using SelectionManager and filtered DataFrames"""
        
        # Get currently filtered IDs
        if self.contacts_df is not None:
            filtered_contact_ids = set(str(id_val) for id_val in self.contacts_df['ID'].tolist())
        else:
            filtered_contact_ids = set()
            
        if self.channels_df is not None:
            filtered_channel_ids = set(str(id_val) for id_val in self.channels_df['Channel Number'].tolist())
        else:
            filtered_channel_ids = set()
        
        # Count selected from filtered
        selected_filtered_contacts = self.contact_selection.selected_ids.intersection(filtered_contact_ids)
        selected_filtered_channels = self.channel_selection.selected_ids.intersection(filtered_channel_ids)
        
        # Total selected counts (GLOBAL)
        total_contacts_selected = len(self.contact_selection.selected_ids)
        total_channels_selected = len(self.channel_selection.selected_ids)
        
        # Update labels with ENHANCED INFO
        if hasattr(self, 'contacts_filter_label'):
            self.contacts_filter_label.config(text=f"Showing: {len(filtered_contact_ids)} contacts")
            
        if hasattr(self, 'contacts_selected_label'):
            if total_contacts_selected > len(selected_filtered_contacts):
                self.contacts_selected_label.config(
                    text=f"Selected in filter: {len(selected_filtered_contacts)}, Total selected: {total_contacts_selected}")
            else:
                self.contacts_selected_label.config(
                    text=f"Selected: {len(selected_filtered_contacts)} for import")
        
        if hasattr(self, 'channels_filter_label'):
            self.channels_filter_label.config(text=f"Showing: {len(filtered_channel_ids)} channels")
            
        if hasattr(self, 'channels_selected_label'):
            if total_channels_selected > len(selected_filtered_channels):
                self.channels_selected_label.config(
                    text=f"Selected in filter: {len(selected_filtered_channels)}, Total selected: {total_channels_selected}")
            else:
                self.channels_selected_label.config(
                    text=f"Selected: {len(selected_filtered_channels)} for import")
        
        # CORRECTED: Update bottom label to show TOTAL that will be exported (not just filtered)
        if hasattr(self, 'selection_label'):
            self.selection_label.config(text=f"Ready to import: {total_contacts_selected} contacts, {total_channels_selected} channels")
            
        # Update tab titles
        if self.contacts_df is not None:
            tab_id = 0
            self.notebook.tab(tab_id, text=f"Contacts ({len(selected_filtered_contacts)}/{len(filtered_contact_ids)})")
            
        if self.channels_df is not None:
            tab_id = 1 if self.contacts_df is not None else 0
            self.notebook.tab(tab_id, text=f"Channels ({len(selected_filtered_channels)}/{len(filtered_channel_ids)})")
            
    def setup_bottom_buttons(self):
        button_frame = ttk.Frame(self.editor_window)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        # Selection info
        self.selection_label = ttk.Label(button_frame, text="Ready to import: 0 contacts, 0 channels", 
                                        font=("Arial", 10, "bold"))
        self.selection_label.pack(side="left")
        
        # Buttons
        ttk.Button(button_frame, text="Cancel", 
                  command=self.cancel_editor).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Import Selected", 
                  command=self.import_selected).pack(side="right", padx=5)
                  
    def cancel_editor(self):
        self.editor_window.destroy()
        
    def import_selected(self):
        """CORRECTED: Export ALL selected items globally, not just those in current filter"""
        
        # Get ALL selected IDs from SelectionManager (GLOBAL SELECTION)
        selected_contacts_global = self.contact_selection.selected_ids
        selected_channels_global = self.channel_selection.selected_ids
        
        if not selected_contacts_global and not selected_channels_global:
            messagebox.showwarning("No Selection", "Please select at least one item to import!")
            return
            
        try:
            selected_contacts_df = None
            selected_channels_df = None
            
            if selected_contacts_global:
                # Convert to sorted list without duplicates
                selected_contact_ids_int = list(set(int(id_str) for id_str in selected_contacts_global))
                selected_contact_ids_int.sort()
                
                # CORRECTED: Use ORIGINAL DataFrame to include ALL selected items
                selected_contacts_df = self.original_contacts_df[
                    self.original_contacts_df['ID'].isin(selected_contact_ids_int)
                ].copy()
                
                # Remove duplicates if they exist
                selected_contacts_df = selected_contacts_df.drop_duplicates(subset=['ID']).reset_index(drop=True)
                
                print(f"DEBUG IMPORT: Global selected: {len(selected_contacts_global)}")
                print(f"DEBUG IMPORT: Unique int IDs: {len(selected_contact_ids_int)}")
                print(f"DEBUG IMPORT: Final DataFrame: {len(selected_contacts_df)} contacts")
                print(f"DEBUG IMPORT: Final Contact IDs: {sorted(selected_contacts_df['ID'].tolist())}")
                
            if selected_channels_global:
                # Same logic for channels
                selected_channel_ids_int = list(set(int(id_str) for id_str in selected_channels_global))
                selected_channel_ids_int.sort()
                
                # CORRECTED: Use ORIGINAL DataFrame to include ALL selected items
                selected_channels_df = self.original_channels_df[
                    self.original_channels_df['Channel Number'].isin(selected_channel_ids_int)
                ].copy()
                
                selected_channels_df = selected_channels_df.drop_duplicates(subset=['Channel Number']).reset_index(drop=True)
                
                print(f"DEBUG IMPORT: Final {len(selected_channels_df)} channels")
                
            # Close editor and return to main conversion
            self.editor_window.destroy()
            
            # Continue with import using selected data
            self.parent.continue_conversion_with_selection(selected_contacts_df, selected_channels_df)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import selection: {str(e)}")
            print(f"Error details: {e}")

class OpenGD77Converter:
    MAX_CONTACTS = 1024
    
    def __init__(self, logger=None):
        self.log_messages = []
        self.logger = logger
        self._contacts_truncated = False
    
    def log(self, message):
        self.log_messages.append(message)
        print(message)
        if self.logger:
            self.logger(message)
    
    def _read_csv_with_log(self, filepath):
        encodings_to_try = ['utf-8', 'cp1252', 'iso-8859-1', 'latin-1']
        for encoding in encodings_to_try:
            try:
                df = pd.read_csv(filepath, encoding=encoding)
                self.log(f"File loaded with {encoding} encoding")
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                self.log(f"File error: {str(e)}")
                break
        self.log("Failed to read file with supported encodings")
        return None
    
    def convert_contacts(self, contacts_file):
        try:
            df = self._read_csv_with_log(contacts_file)
            if df is None:
                return None
            
            self.log(f"Loaded {len(df)} contacts from file")
            
            if 'Call Type' in df.columns and 'Call ID' in df.columns:
                result = self._convert_tyt_contacts(df)
            elif 'Radio ID' in df.columns and 'Callsign' in df.columns:
                result = self._convert_dc9al_contacts(df)
            else:
                self.log("Unknown contact file format")
                return None
            
            return result
            
        except Exception as e:
            self.log(f"Contact conversion error: {str(e)}")
            return None
    
    def _convert_tyt_contacts(self, df):
        gd77_contacts = pd.DataFrame()
        gd77_contacts['Contact Name'] = df['Contact Name']
        gd77_contacts['ID'] = df['Call ID']
        gd77_contacts['ID Type'] = df['Call Type'].map({1: 'Group', 2: 'Private'})
        gd77_contacts['TS Override'] = 'None'
        
        groups = len(gd77_contacts[gd77_contacts['ID Type'] == 'Group'])
        privates = len(gd77_contacts[gd77_contacts['ID Type'] == 'Private'])
        
        self.log(f"Converted TYT format: {groups} TG, {privates} Private")
        return gd77_contacts
    
    def _convert_dc9al_contacts(self, df):
        gd77_contacts = pd.DataFrame()
        
        gd77_contacts['Contact Name'] = df.apply(
            lambda row: f"{str(row['Callsign']).strip()} {str(row['Name']).strip()}".strip() 
            if pd.notna(row['Name']) and str(row['Name']).strip() 
            else str(row['Callsign']).strip(), 
            axis=1
        )
        
        gd77_contacts['ID'] = pd.to_numeric(df['Radio ID'], errors='coerce')
        gd77_contacts['ID Type'] = 'Private'
        gd77_contacts['TS Override'] = 'None'
        
        gd77_contacts = gd77_contacts.dropna(subset=['ID'])
        gd77_contacts = gd77_contacts[gd77_contacts['ID'] > 0]
        gd77_contacts = gd77_contacts.drop_duplicates(subset=['ID'])
        
        gd77_contacts['Contact Name'] = gd77_contacts['Contact Name'].str.replace('"', '').str.replace("'", "").str.replace(',', ' ')
        
        self.log(f"Converted DC9AL format: {len(gd77_contacts)} Private contacts")
        return gd77_contacts
    
    def convert_channels(self, tyt_channels_file):
        try:
            df = self._read_csv_with_log(tyt_channels_file)
            if df is None:
                return None
            
            self.log(f"Loaded {len(df)} channels from TYT")
            
            gd77_channels = pd.DataFrame()
            gd77_channels['Channel Number'] = range(1, len(df) + 1)
            gd77_channels['Channel Name'] = df['Channel Name']
            gd77_channels['Channel Type'] = df['Channel Mode'].map({1: 'Analogue', 2: 'Digital'})
            gd77_channels['Rx Frequency'] = df['RX Frequency(MHz)']
            gd77_channels['Tx Frequency'] = df['TX Frequency(MHz)']
            
            gd77_channels['Bandwidth (kHz)'] = df['Channel Mode'].apply(lambda x: '25' if x == 1 else '')
            gd77_channels['Colour Code'] = df.apply(lambda row: str(row['Color Code']) if row['Channel Mode'] == 2 and row['Color Code'] > 0 else '', axis=1)
            gd77_channels['Timeslot'] = df.apply(lambda row: str(row['Repeater Slot']) if row['Channel Mode'] == 2 and row['Repeater Slot'] > 0 else '', axis=1)
            gd77_channels['Contact'] = 'None'
            gd77_channels['TG List'] = 'None'
            gd77_channels['DMR ID'] = 'None'
            gd77_channels['TS1_TA_Tx'] = 'Off'
            gd77_channels['TS2_TA_Tx'] = 'Off'
            
            gd77_channels['RX Tone'] = ''
            gd77_channels['TX Tone'] = df['CTCSS/DCS Enc'].apply(lambda x: str(x) if x != 'None' and pd.notna(x) and x != 0 else '')
            
            gd77_channels['Squelch'] = 'Master'
            gd77_channels['Power'] = 'Master'
            gd77_channels['Rx Only'] = 'No'
            gd77_channels['Zone Skip'] = 'No'
            gd77_channels['All Skip'] = 'No'
            gd77_channels['TOT'] = '180'
            gd77_channels['VOX'] = 'Off'
            gd77_channels['No Beep'] = 'No'
            gd77_channels['No Eco'] = 'No'
            gd77_channels['APRS'] = 'None'
            gd77_channels['Latitude'] = '0'
            gd77_channels['Longitude'] = '0'
            gd77_channels['Use Location'] = 'No'
            
            analog = len(gd77_channels[gd77_channels['Channel Type'] == 'Analogue'])
            digital = len(gd77_channels[gd77_channels['Channel Type'] == 'Digital'])
            
            self.log(f"Converted: {analog} analogue, {digital} digital")
            return gd77_channels
        except Exception as e:
            self.log(f"Channel conversion error: {str(e)}")
            return None
    
    def save_csv(self, dataframe, output_path):
        try:
            dataframe.to_csv(output_path, index=False, sep=';', encoding='utf-8')
            self.log(f"Saved: {os.path.basename(output_path)}")
            return True
        except Exception as e:
            self.log(f"Save error {output_path}: {str(e)}")
            return False

class OpenGD77GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TYT/Retevis OpenGD77 CSV Converter v1.0 - By N1k0Droid/IT9KVB")
        self.root.geometry("650x500")
        self.root.resizable(False, False)
        
        self.channels_file = tk.StringVar()
        self.contacts_file = tk.StringVar()
        self.output_folder = tk.StringVar(value=os.getcwd())
        
        self.converter = OpenGD77Converter(logger=self.log)
        self.setup_gui()
        
    def setup_gui(self):
        header_frame = tk.Frame(self.root, bg="#2E86AB")
        header_frame.pack(fill="x")
        
        title_label = tk.Label(header_frame, text="TYT/Retevis OpenGD77 CSV Converter v1.0", 
                              font=("Arial", 16, "bold"), bg="#2E86AB", fg="white")
        title_label.pack(pady=(10,0))
        
        author_label = tk.Label(header_frame, text="By N1k0Droid/IT9KVB", 
                               font=("Arial", 11), bg="#2E86AB", fg="#A2D2FF")
        author_label.pack(pady=(0,10))
        
        file_frame = tk.LabelFrame(self.root, text="Input Files", font=("Arial", 10, "bold"))
        file_frame.pack(pady=10, padx=10, fill="x")
        
        tk.Label(file_frame, text="TYT Channels:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        tk.Entry(file_frame, textvariable=self.channels_file, width=50).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(file_frame, text="Browse", command=self.browse_channels, width=10).grid(row=0, column=2, padx=5, pady=5)
        
        tk.Label(file_frame, text="Contacts:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        tk.Entry(file_frame, textvariable=self.contacts_file, width=50).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(file_frame, text="Browse", command=self.browse_contacts, width=10).grid(row=1, column=2, padx=5, pady=5)
        
        info_label = tk.Label(file_frame, text="Supported: TYT Digital Contacts, DC9AL ContactLists", 
                             font=("Arial", 8), fg="#666666")
        info_label.grid(row=2, column=0, columnspan=3, pady=(0,5))
        
        output_frame = tk.LabelFrame(self.root, text="Output", font=("Arial", 10, "bold"))
        output_frame.pack(pady=10, padx=10, fill="x")
        
        tk.Label(output_frame, text="Output Folder:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        tk.Entry(output_frame, textvariable=self.output_folder, width=50).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(output_frame, text="Browse", command=self.browse_output, width=10).grid(row=0, column=2, padx=5, pady=5)
        
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Preview & Convert", command=self.convert_files, 
                 bg="#28A745", fg="white", font=("Arial", 12, "bold"), width=15).pack(side="left", padx=5)
        tk.Button(button_frame, text="About", command=self.show_about, 
                 bg="#6C757D", fg="white", width=12).pack(side="left", padx=5)
        
        log_frame = tk.LabelFrame(self.root, text="Conversion Log", font=("Arial", 10, "bold"))
        log_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, width=70, font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.log("OpenGD77 CSV Converter v1.0 ready!")
        self.log(f"Default output folder: {os.getcwd()}")
        self.log(f"OpenGD77 contact limit: {self.converter.MAX_CONTACTS} contacts max")
        self.log("Features: Preview & Select interface with checkbox selection")
        self.log("FIXED: Export includes ALL selected contacts (preserves across filters)")
        self.log("Compatible: TYT MD-UV380/390, Retevis RT3S, Baofeng DM-1701")
        self.log("Supports: TYT Contacts, DC9AL ContactLists from GitHub")
        self.log("Auto-detects file encoding (UTF-8, CP1252, ISO-8859-1)")
        self.log("Use only CSV exported from original firmware")
    
    def browse_channels(self):
        filename = filedialog.askopenfilename(title="Select TYT Channels CSV", initialdir=os.getcwd(), filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if filename:
            self.channels_file.set(filename)
            self.log(f"Selected channels: {os.path.basename(filename)}")
    
    def browse_contacts(self):
        filename = filedialog.askopenfilename(title="Select Contacts CSV (TYT or DC9AL)", initialdir=os.getcwd(), filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if filename:
            self.contacts_file.set(filename)
            self.log(f"Selected contacts: {os.path.basename(filename)}")
    
    def browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder", initialdir=self.output_folder.get())
        if folder:
            self.output_folder.set(folder)
            self.log(f"Output folder: {folder}")
    
    def log(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def convert_files(self):
        try:
            if not self.channels_file.get() and not self.contacts_file.get():
                messagebox.showerror("Error", "Select at least one input file!")
                return
            
            output_dir = self.output_folder.get()
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                self.log(f"Created output directory: {output_dir}")
            
            self.log("Loading files for preview...")
            
            contacts_df = None
            channels_df = None
            
            if self.contacts_file.get():
                self.log("Converting contacts for preview...")
                contacts_df = self.converter.convert_contacts(self.contacts_file.get())
                if contacts_df is not None:
                    if len(contacts_df) > self.converter.MAX_CONTACTS:
                        self.log(f"WARNING: {len(contacts_df)} contacts found, OpenGD77 limit is {self.converter.MAX_CONTACTS}")
                
            if self.channels_file.get():
                self.log("Converting channels for preview...")
                channels_df = self.converter.convert_channels(self.channels_file.get())
                
            if contacts_df is not None or channels_df is not None:
                self.log("Opening preview editor...")
                editor = ContactChannelEditor(self, contacts_df, channels_df, self.converter)
            else:
                messagebox.showerror("Error", "No valid data to preview!")
                
        except Exception as e:
            error_msg = f"Preview failed: {str(e)}"
            self.log(error_msg)
            messagebox.showerror("Error", error_msg)

    def continue_conversion_with_selection(self, selected_contacts_df, selected_channels_df):
        try:
            output_dir = self.output_folder.get()
            
            if selected_contacts_df is not None:
                output_path = os.path.join(output_dir, "Contacts.csv")
                self.converter.save_csv(selected_contacts_df, output_path)
                self.log(f"Imported {len(selected_contacts_df)} selected contacts")
                
            if selected_channels_df is not None:
                output_path = os.path.join(output_dir, "Channels.csv")
                self.converter.save_csv(selected_channels_df, output_path)
                self.log(f"Imported {len(selected_channels_df)} selected channels")
                
            self.log("Import completed successfully!")
            self.log(f"Files saved to: {output_dir}")
            
            success_msg = f"Import completed successfully!\n\nFiles saved to:\n{output_dir}"
            if selected_contacts_df is not None:
                success_msg += f"\n\n{len(selected_contacts_df)} contacts imported"
            if selected_channels_df is not None:
                success_msg += f"\n{len(selected_channels_df)} channels imported"
                
            messagebox.showinfo("Success", success_msg)
            
        except Exception as e:
            error_msg = f"Import failed: {str(e)}"
            self.log(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def show_about(self):
        about_text = """TYT/Retevis OpenGD77 CSV Converter v1.0
By N1k0Droid/IT9KVB

Converts CSV files to OpenGD77 compatible format.

KEY FEATURES:
- Preview & Select interface with checkbox selection
- Search & filter capabilities with preserved selection
- Contact limit enforcement (1024 max for OpenGD77)
- Select All Visible adds to existing selection
- Export includes ALL selected contacts (preserves across filters)
- Accurate counting with multiple filter combinations

Supported Input Formats:
- TYT MD-UV380/390 Channels & Digital Contacts
- Retevis RT3S Channels & Digital Contacts  
- Baofeng DM-1701 Channels & Digital Contacts
- DC9AL ContactLists from GitHub (RADIODDITY/GD77)

Technical Features:
- Auto-detects file encoding (UTF-8, CP1252, ISO-8859-1)
- Real-time conversion logging
- Robust error handling and duplicate prevention
- Independent selection system for reliable operation

Selection Methods:
- Click on checkbox icon to toggle selection
- Double-click anywhere on row to toggle
- Use Select All Visible / Deselect All buttons

Note: "Selected in filter" shows items selected within current 
filter, while "Total selected" shows all selected items globally. 
The export will include ALL selected items regardless of current filter.

Use only CSV exported from original firmware or official sources.
Not responsible for damages from improper use.
"""
        messagebox.showinfo("About", about_text)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = OpenGD77GUI()
    app.run()
