"""
Configure 3D Generation Parameters Dialog
Allows users to select which workflow nodes should have their parameters exposed in the 3D generation UI
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Set
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTreeWidget, QTreeWidgetItem, QCheckBox, QFileDialog,
    QGroupBox, QScrollArea, QWidget, QTextEdit, QSplitter,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from loguru import logger


class Configure3DParametersDialog(QDialog):
    """Dialog for configuring which 3D workflow parameters to expose in the UI"""
    
    # Signal emitted when configuration is saved
    configuration_saved = Signal(dict)
    
    # Node types to hide from UI (utility nodes with no meaningful parameters)
    HIDDEN_NODE_TYPES = {
        "Reroute",
        "GetNode", 
        "VAEDecode",
        "VAEEncode",
        "PrimitiveNode"  # Also hide primitive nodes as they're just value holders
    }
    
    # Node types we support for 3D parameter extraction
    SUPPORTED_NODE_TYPES = {
        # Core generation nodes
        "LoadImage": "Input image from generation",
        "CheckpointLoaderSimple": "Load checkpoint model",
        "CLIPTextEncode": "Text prompt encoding",
        "KSampler": "Main sampling parameters",
        "VAEDecode": "VAE decoding",
        "SaveImage": "Save generated images",
        "PreviewImage": "Preview images",
        
        # ControlNet nodes
        "ControlNetLoader": "Load ControlNet model",
        "SetUnionControlNetType": "Set ControlNet type",
        "ControlNetApplyAdvanced": "Apply ControlNet advanced",
        
        # Upscaling nodes
        "Upscale Model Loader": "Load upscaling model",
        "UpscaleModelLoader": "Load upscaling model (alt)",
        "UltimateSDUpscale": "Ultimate SD upscaling",
        
        # Image processing nodes
        "ImageRemoveBackground+": "Advanced background removal",
        "TransparentBGSession+": "Background removal session",
        "ImageCompositeMasked": "Image compositing",
        "SolidMask": "Background mask settings",
        "ImageBlend": "Blend images",
        "ImageInvert": "Invert image colors",
        "ImageResizeKJv2": "Advanced image resizing",
        "NormalMapSimple": "Generate normal maps",
        
        # 3D mesh generation nodes
        "Hy3DGenerateMesh": "3D mesh generation parameters",
        "Hy3DVAEDecode": "VAE decoding for 3D mesh",
        "Hy3DPostprocessMesh": "Mesh post-processing options",
        "Hy3DUploadMesh": "Upload 3D mesh for texturing",
        "Hy3DExportMesh": "Mesh export options",
        
        # 3D texturing nodes
        "Hy3DDelightImage": "Image delighting parameters",
        "DownloadAndLoadHy3DDelightModel": "Delight model loading",
        "DownloadAndLoadHy3DPaintModel": "Load paint model",
        "Hy3DApplyTexture": "Apply texture to mesh",
        "Hy3DBakeFromMultiview": "Bake texture from multiview",
        "Hy3DMeshUVWrap": "UV wrapping for mesh",
        "Hy3DSetMeshPBRTextures": "Set PBR textures",
        "CV2InpaintTexture": "Texture inpainting",
        "Hy3DMeshVerticeInpaintTexture": "Mesh vertex texture inpainting",
        
        # 3D rendering nodes
        "Hy3DRenderMultiView": "Multi-view rendering",
        "Hy3DRenderMultiViewDepth": "Multi-view depth rendering",
        "Hy3DSampleMultiView": "Sample multi-view images",
        "Hy3DCameraConfig": "Camera configuration",
        "Preview3D": "3D preview",
        
        # Scheduler and model nodes
        "Hy3DDiffusersSchedulerConfig": "Diffusion scheduler configuration",
        "Hy3DModelLoader": "3D model loading",
        
        # Face detail nodes
        "FaceDetailer": "Face detail enhancement",
        "UltralyticsDetectorProvider": "Face detection provider",
        
        # Utility nodes
        "EmptyLatentImage": "Create empty latent",
        "GetNode": "Get node reference",
        "SetNode": "Set node value",
        "PrimitiveInt": "Integer input",
        "PrimitiveNode": "Primitive value",
        "PrimitiveStringMultiline": "Multiline text input",
        "JoinStrings": "Join text strings",
        "SimpleMath+": "Mathematical operations",
        "Note": "Workflow notes and documentation",
        "MarkdownNote": "Markdown documentation"
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logger
        self.workflow_data = None
        self.config_path = Path("config/3d_parameters_config.json")
        self.selected_nodes = set()
        
        self.setWindowTitle("Configure 3D Generation Parameters")
        self.setModal(True)
        self.resize(900, 700)
        
        # Apply dark theme
        self._apply_dark_theme()
        
        # Initialize UI
        self._init_ui()
        
        # Apply accent colors
        self._apply_accent_colors()
        
        # Load existing configuration
        self._load_configuration()
        
        # Try to load default 3D workflow
        self._load_default_workflow()
    
    def _apply_dark_theme(self):
        """Apply dark theme to dialog"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            
            QGroupBox {
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
                font-weight: bold;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            QPushButton {
                background-color: #3a3a3a;
                border: 1px solid #4a4a4a;
                border-radius: 3px;
                padding: 5px 15px;
                color: #e0e0e0;
            }
            
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
            
            QPushButton#primary_button {
                background-color: #4CAF50;
                border: none;
            }
            
            QPushButton#primary_button:hover {
                background-color: #5CBF60;
            }
            
            QTreeWidget {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 3px;
                padding: 5px;
            }
            
            QTreeWidget::item {
                padding: 4px;
            }
            
            QTreeWidget::item:hover {
                background-color: #3a3a3a;
            }
            
            QTreeWidget::item:selected {
                background-color: #4a4a4a;
            }
            
            QCheckBox {
                spacing: 5px;
            }
            
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            
            QCheckBox::indicator:unchecked {
                background-color: #2a2a2a;
                border: 1px solid #4a4a4a;
                border-radius: 2px;
            }
            
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border: 1px solid #4CAF50;
                border-radius: 2px;
            }
            
            QTextEdit {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 3px;
                padding: 5px;
                font-family: 'Consolas', 'Monaco', monospace;
            }
            
            QLabel {
                color: #e0e0e0;
            }
            
            QSplitter::handle {
                background-color: #3a3a3a;
            }
        """)
    
    def _init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header_label = QLabel("Select 3D workflow nodes whose parameters should be exposed in the UI")
        header_label.setWordWrap(True)
        layout.addWidget(header_label)
        
        # Workflow loading section
        load_group = QGroupBox("Load 3D Workflow")
        load_layout = QHBoxLayout()
        
        self.workflow_path_label = QLabel("No workflow loaded")
        self.workflow_path_label.setStyleSheet("color: #888888;")
        load_layout.addWidget(self.workflow_path_label, 1)
        
        load_btn = QPushButton("Load 3D Workflow JSON")
        load_btn.clicked.connect(self._load_workflow)
        load_layout.addWidget(load_btn)
        
        load_group.setLayout(load_layout)
        layout.addWidget(load_group)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: Node selection tree
        nodes_group = QGroupBox("Available Nodes")
        nodes_layout = QVBoxLayout()
        
        # Filter for supported nodes checkbox
        self.show_supported_only = QCheckBox("Show only supported 3D node types")
        self.show_supported_only.setChecked(False)  # Changed to show all by default
        self.show_supported_only.stateChanged.connect(self._refresh_node_tree)
        nodes_layout.addWidget(self.show_supported_only)
        
        # Node tree
        self.node_tree = QTreeWidget()
        self.node_tree.setHeaderLabels(["Node Type", "Node ID", "Title"])
        self.node_tree.itemChanged.connect(self._on_node_selection_changed)
        nodes_layout.addWidget(self.node_tree)
        
        nodes_group.setLayout(nodes_layout)
        splitter.addWidget(nodes_group)
        
        # Right side: Node details
        details_group = QGroupBox("Node Details")
        details_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setPlaceholderText("Select a node to view its parameters")
        details_layout.addWidget(self.details_text)
        
        details_group.setLayout(details_layout)
        splitter.addWidget(details_group)
        
        # Set splitter sizes (60% for tree, 40% for details)
        splitter.setSizes([540, 360])
        layout.addWidget(splitter, 1)
        
        # Selected nodes summary
        self.summary_label = QLabel("No nodes selected")
        self.summary_label.setStyleSheet("color: #888888; padding: 5px;")
        layout.addWidget(self.summary_label)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save Configuration")
        save_btn.setObjectName("primary_button")
        save_btn.clicked.connect(self._save_configuration)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def _load_default_workflow(self):
        """Try to load the default 3D workflow"""
        default_workflow = Path("workflows/generate_3D_withUVs_09-06-2025.json")
        if default_workflow.exists():
            try:
                with open(default_workflow, 'r', encoding='utf-8') as f:
                    self.workflow_data = json.load(f)
                
                self.loaded_workflow_path = default_workflow
                self.workflow_filename = default_workflow.name
                
                self.workflow_path_label.setText(f"Loaded: {self.workflow_filename}")
                # Get accent color from settings
                from PySide6.QtCore import QSettings
                settings = QSettings("ComfyUI-Cinema4D", "Bridge")
                accent_color = settings.value("interface/accent_color", "#4CAF50")
                self.workflow_path_label.setStyleSheet(f"color: {accent_color};")
                
                # Populate the node tree
                self._populate_node_tree()
                
                self.logger.info("Loaded default 3D workflow")
                
            except Exception as e:
                self.logger.error(f"Failed to load default 3D workflow: {e}")
    
    def _load_workflow(self):
        """Load a 3D workflow JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select 3D Workflow JSON",
            "workflows",
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.workflow_data = json.load(f)
            
            # Store the full path for later use
            self.loaded_workflow_path = Path(file_path)
            
            # Check if the workflow is in the standard workflows directory
            workflows_dir = Path("workflows")
            try:
                # Try to get relative path from workflows directory
                relative_path = self.loaded_workflow_path.relative_to(workflows_dir.resolve())
                # If successful, the file is in workflows dir, use just the filename
                display_name = relative_path.name
                self.workflow_filename = relative_path.name
            except ValueError:
                # File is outside workflows directory, store full path
                display_name = self.loaded_workflow_path.name
                self.workflow_filename = str(self.loaded_workflow_path)
                self.logger.warning(f"3D workflow loaded from outside workflows directory: {self.loaded_workflow_path}")
            
            self.workflow_path_label.setText(f"Loaded: {display_name}")
            # Get accent color from settings
            from PySide6.QtCore import QSettings
            settings = QSettings("ComfyUI-Cinema4D", "Bridge")
            accent_color = settings.value("interface/accent_color", "#4CAF50")
            self.workflow_path_label.setStyleSheet(f"color: {accent_color};")
            
            # Populate the node tree
            self._populate_node_tree()
            
        except Exception as e:
            self.logger.error(f"Failed to load 3D workflow: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load 3D workflow:\n{str(e)}")
    
    def _populate_node_tree(self):
        """Populate the tree widget with workflow nodes"""
        self.node_tree.clear()
        
        if not self.workflow_data:
            return
        
        nodes = self.workflow_data.get("nodes", [])
        supported_count = 0
        total_count = 0
        hidden_count = 0
        
        # Collect unique node types for dynamic recognition
        unique_node_types = set()
        
        for node in nodes:
            node_type = node.get("type", "Unknown")
            node_id = str(node.get("id", ""))
            node_title = node.get("title", "")
            
            # Add to unique types
            unique_node_types.add(node_type)
            
            # Skip hidden utility nodes
            if node_type in self.HIDDEN_NODE_TYPES:
                hidden_count += 1
                continue
            
            # Skip if showing only supported and this isn't supported
            if self.show_supported_only.isChecked() and node_type not in self.SUPPORTED_NODE_TYPES:
                continue
            
            # Create tree item
            item = QTreeWidgetItem([node_type, node_id, node_title])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            
            # Check if this node is in our saved configuration
            if self._is_node_selected(node_type, node_id):
                item.setCheckState(0, Qt.CheckState.Checked)
            else:
                item.setCheckState(0, Qt.CheckState.Unchecked)
            
            # Store node data
            item.setData(0, Qt.ItemDataRole.UserRole, node)
            
            # Add description if supported
            if node_type in self.SUPPORTED_NODE_TYPES:
                item.setToolTip(0, self.SUPPORTED_NODE_TYPES[node_type])
                supported_count += 1
            else:
                # For unsupported nodes, add a generic tooltip
                item.setToolTip(0, f"{node_type} - Dynamically recognized node")
            
            self.node_tree.addTopLevelItem(item)
            total_count += 1
        
        # Log discovered node types
        unsupported_types = unique_node_types - set(self.SUPPORTED_NODE_TYPES.keys())
        if unsupported_types:
            self.logger.info(f"Discovered {len(unsupported_types)} new node types: {', '.join(sorted(unsupported_types))}")
        
        # Resize columns
        for i in range(3):
            self.node_tree.resizeColumnToContents(i)
        
        # Update summary with more info
        self._update_summary()
        
        # Update filter checkbox text to show counts
        if not self.show_supported_only.isChecked():
            self.show_supported_only.setText(f"Show only supported 3D node types ({supported_count}/{total_count} nodes)")
        else:
            self.show_supported_only.setText(f"Show only supported 3D node types ({supported_count} shown)")
        
        # Log hidden nodes info
        if hidden_count > 0:
            self.logger.debug(f"Hidden {hidden_count} utility nodes (Reroute, GetNode, VAEDecode, VAEEncode)")
        
        # Connect selection change
        self.node_tree.itemSelectionChanged.connect(self._on_tree_selection_changed)
    
    def _refresh_node_tree(self):
        """Refresh the node tree based on filter settings"""
        if self.workflow_data:
            self._populate_node_tree()
    
    def _on_tree_selection_changed(self):
        """Handle tree selection change to show node details"""
        items = self.node_tree.selectedItems()
        if not items:
            self.details_text.clear()
            return
        
        item = items[0]
        node = item.data(0, Qt.ItemDataRole.UserRole)
        
        if node:
            self._show_node_details(node)
    
    def _show_node_details(self, node: Dict[str, Any]):
        """Display detailed information about a node"""
        details = []
        details.append(f"Node Type: {node.get('type', 'Unknown')}")
        details.append(f"Node ID: {node.get('id', '')}")
        
        if node.get('title'):
            details.append(f"Title: {node.get('title')}")
        
        # Show position
        if 'pos' in node:
            details.append(f"Position: {node['pos']}")
        
        # Show widgets/parameters
        if 'widgets_values' in node and node['widgets_values']:
            details.append("\nWidget Values:")
            for i, value in enumerate(node['widgets_values']):
                details.append(f"  [{i}]: {value}")
        
        # Show inputs
        if 'inputs' in node and node['inputs']:
            details.append("\nInputs:")
            for inp in node['inputs']:
                details.append(f"  - {inp.get('name', 'Unknown')} ({inp.get('type', 'Unknown')})")
        
        # Show outputs
        if 'outputs' in node and node['outputs']:
            details.append("\nOutputs:")
            for out in node['outputs']:
                details.append(f"  - {out.get('name', 'Unknown')} ({out.get('type', 'Unknown')})")
        
        # Special handling for Note nodes
        if node.get('type') == 'Note' and 'widgets_values' in node:
            details.append("\nNote Content:")
            if node['widgets_values']:
                details.append(str(node['widgets_values'][0]))
        
        self.details_text.setText("\n".join(details))
    
    def _on_node_selection_changed(self, item: QTreeWidgetItem, column: int):
        """Handle checkbox state changes"""
        if column == 0:
            self._update_summary()
    
    def _update_summary(self):
        """Update the summary of selected nodes"""
        selected_count = 0
        selected_types = set()
        
        for i in range(self.node_tree.topLevelItemCount()):
            item = self.node_tree.topLevelItem(i)
            if item.checkState(0) == Qt.CheckState.Checked:
                selected_count += 1
                selected_types.add(item.text(0))
        
        if selected_count == 0:
            self.summary_label.setText("No nodes selected")
            self.summary_label.setStyleSheet("color: #888888; padding: 5px;")
        else:
            types_text = ", ".join(sorted(selected_types))
            self.summary_label.setText(f"Selected {selected_count} nodes: {types_text}")
            # Get accent color from settings
            from PySide6.QtCore import QSettings
            settings = QSettings("ComfyUI-Cinema4D", "Bridge")
            accent_color = settings.value("interface/accent_color", "#4CAF50")
            self.summary_label.setStyleSheet(f"color: {accent_color}; padding: 5px;")
    
    def _is_node_selected(self, node_type: str, node_id: str) -> bool:
        """Check if a node is in the saved configuration"""
        return f"{node_type}_{node_id}" in self.selected_nodes
    
    def _load_configuration(self):
        """Load existing configuration from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.selected_nodes = set(config.get("selected_nodes", []))
                    self.logger.info(f"Loaded {len(self.selected_nodes)} configured 3D nodes")
        except Exception as e:
            self.logger.error(f"Failed to load 3D configuration: {e}")
    
    def _save_configuration(self):
        """Save the current configuration"""
        try:
            # Collect selected nodes
            selected_nodes = []
            selected_info = {}
            discovered_types = set()
            
            for i in range(self.node_tree.topLevelItemCount()):
                item = self.node_tree.topLevelItem(i)
                node_type = item.text(0)
                
                # Track all discovered node types
                discovered_types.add(node_type)
                
                if item.checkState(0) == Qt.CheckState.Checked:
                    node_id = item.text(1)
                    node_key = f"{node_type}_{node_id}"
                    
                    selected_nodes.append(node_key)
                    
                    # Store additional info for each selected node
                    node = item.data(0, Qt.ItemDataRole.UserRole)
                    if node:
                        selected_info[node_key] = {
                            "type": node_type,
                            "id": node_id,
                            "title": node.get("title", ""),
                            "supported": node_type in self.SUPPORTED_NODE_TYPES,
                            "widgets_values": node.get("widgets_values", [])
                        }
            
            # Create configuration with discovered types
            config = {
                "selected_nodes": selected_nodes,
                "node_info": selected_info,
                "workflow_file": self.workflow_filename if hasattr(self, 'workflow_filename') and self.workflow_data else None,
                "discovered_node_types": list(discovered_types)
            }
            
            # Ensure config directory exists
            self.config_path.parent.mkdir(exist_ok=True)
            
            # Save configuration
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved 3D configuration with {len(selected_nodes)} nodes")
            
            # If we discovered new node types, save them for future reference
            new_types = discovered_types - set(self.SUPPORTED_NODE_TYPES.keys())
            if new_types:
                self._save_discovered_types(new_types)
            
            # Emit signal
            self.configuration_saved.emit(config)
            
            # Show success message
            QMessageBox.information(
                self,
                "Success",
                f"3D configuration saved successfully!\n\n"
                f"Selected {len(selected_nodes)} nodes for parameter extraction."
            )
            
            self.accept()
            
        except Exception as e:
            self.logger.error(f"Failed to save 3D configuration: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save 3D configuration:\n{str(e)}")
    
    def _save_discovered_types(self, new_types: Set[str]):
        """Save newly discovered node types for future reference"""
        discovered_path = self.config_path.parent / "discovered_node_types.json"
        
        # Load existing discovered types
        discovered_types = {}
        if discovered_path.exists():
            try:
                with open(discovered_path, 'r', encoding='utf-8') as f:
                    discovered_types = json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load discovered types: {e}")
        
        # Add new types with timestamp
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        
        for node_type in new_types:
            if node_type not in discovered_types:
                discovered_types[node_type] = {
                    "first_seen": timestamp,
                    "description": f"Dynamically discovered from workflow"
                }
        
        # Save updated discovered types
        try:
            with open(discovered_path, 'w', encoding='utf-8') as f:
                json.dump(discovered_types, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved {len(new_types)} newly discovered node types")
        except Exception as e:
            self.logger.error(f"Failed to save discovered types: {e}")
    
    def _apply_accent_colors(self):
        """Apply accent colors to override hardcoded green colors"""
        try:
            from PySide6.QtCore import QSettings
            settings = QSettings("ComfyUI-Cinema4D", "Bridge")
            accent_color = settings.value("interface/accent_color", "#4CAF50")
            
            # Create lighter hover color
            hex_color = accent_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16) 
            b = int(hex_color[4:6], 16)
            
            # Increase by 20 for hover effect
            r_hover = min(255, r + 20)
            g_hover = min(255, g + 20)
            b_hover = min(255, b + 20)
            hover_color = f"#{r_hover:02x}{g_hover:02x}{b_hover:02x}"
            
            accent_css = f"""
            QPushButton#primary_button {{
                background-color: {accent_color} !important;
                border: none !important;
            }}
            
            QPushButton#primary_button:hover {{
                background-color: {hover_color} !important;
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {accent_color} !important;
                border: 1px solid {accent_color} !important;
                border-radius: 2px;
            }}
            """
            
            # Apply the accent color CSS
            current_style = self.styleSheet()
            self.setStyleSheet(current_style + accent_css)
            
        except Exception as e:
            self.logger.error(f"Failed to apply accent colors: {e}")