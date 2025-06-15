# ===== SCENE ASSEMBLY HELPER METHODS =====
# These methods will be added to the main app.py file

# Handler methods for new object types
def _create_spline_with_defaults(self, spline_type: str):
    """Create spline with default settings"""
    if not hasattr(self, 'c4d_client') or not self.c4d_client._connected:
        self.status_bar.showMessage("Cinema4D not connected", 3000)
        return
    
    self.status_bar.showMessage(f"Creating {spline_type} spline...", 0)
    self._run_async_task(self._execute_create_spline(spline_type))

def _create_mograph_with_defaults(self, mograph_type: str):
    """Create MoGraph object with default settings"""
    if not hasattr(self, 'c4d_client') or not self.c4d_client._connected:
        self.status_bar.showMessage("Cinema4D not connected", 3000)
        return
    
    self.status_bar.showMessage(f"Creating {mograph_type}...", 0)
    self._run_async_task(self._execute_create_mograph(mograph_type))

def _create_dynamics_with_defaults(self, dynamics_type: str):
    """Create dynamics object with default settings"""
    if not hasattr(self, 'c4d_client') or not self.c4d_client._connected:
        self.status_bar.showMessage("Cinema4D not connected", 3000)
        return
    
    self.status_bar.showMessage(f"Creating {dynamics_type}...", 0)
    self._run_async_task(self._execute_create_dynamics(dynamics_type))

def _create_light_with_defaults(self, light_type: str):
    """Create light with default settings"""
    if not hasattr(self, 'c4d_client') or not self.c4d_client._connected:
        self.status_bar.showMessage("Cinema4D not connected", 3000)
        return
    
    self.status_bar.showMessage(f"Creating {light_type}...", 0)
    self._run_async_task(self._execute_create_light(light_type))

def _create_camera_with_defaults(self, camera_type: str):
    """Create camera with default settings"""
    if not hasattr(self, 'c4d_client') or not self.c4d_client._connected:
        self.status_bar.showMessage("Cinema4D not connected", 3000)
        return
    
    self.status_bar.showMessage(f"Creating {camera_type}...", 0)
    self._run_async_task(self._execute_create_camera(camera_type))

def _create_material_with_defaults(self, material_type: str):
    """Create material with default settings"""
    if not hasattr(self, 'c4d_client') or not self.c4d_client._connected:
        self.status_bar.showMessage("Cinema4D not connected", 3000)
        return
    
    self.status_bar.showMessage(f"Creating {material_type}...", 0)
    self._run_async_task(self._execute_create_material(material_type))

def _create_character_with_defaults(self, character_type: str):
    """Create character object with default settings"""
    if not hasattr(self, 'c4d_client') or not self.c4d_client._connected:
        self.status_bar.showMessage("Cinema4D not connected", 3000)
        return
    
    self.status_bar.showMessage(f"Creating {character_type}...", 0)
    self._run_async_task(self._execute_create_character(character_type))

def _create_volume_with_defaults(self, volume_type: str):
    """Create volume object with default settings"""
    if not hasattr(self, 'c4d_client') or not self.c4d_client._connected:
        self.status_bar.showMessage("Cinema4D not connected", 3000)
        return
    
    self.status_bar.showMessage(f"Creating {volume_type}...", 0)
    self._run_async_task(self._execute_create_volume(volume_type))

def _remove_command_from_dictionary(self, object_type: str):
    """Remove command from dictionary (for buggy commands)"""
    try:
        # This would remove the command from the internal dictionary
        # For now, we'll just disable the button and show a message
        self.status_bar.showMessage(f"Command {object_type} marked for removal", 3000)
        self.logger.info(f"Command {object_type} marked for removal due to bugs/crashes")
    except Exception as e:
        self.logger.error(f"Error removing command {object_type}: {e}")

def _save_nl_trigger(self, object_type: str, trigger_text: str):
    """Save natural language trigger words for an object type"""
    try:
        # Save to a JSON file or database for NLP training
        nl_triggers_file = self.config.config_dir / "nl_triggers.json"
        
        # Load existing triggers
        triggers = {}
        if nl_triggers_file.exists():
            import json
            with open(nl_triggers_file, 'r') as f:
                triggers = json.load(f)
        
        # Update with new trigger
        triggers[object_type] = trigger_text
        
        # Save back to file
        with open(nl_triggers_file, 'w') as f:
            json.dump(triggers, f, indent=2)
        
        self.logger.debug(f"Saved NL trigger for {object_type}: {trigger_text}")
    except Exception as e:
        self.logger.error(f"Error saving NL trigger for {object_type}: {e}")

def _show_object_settings_dialog(self, object_type: str, object_name: str):
    """Show settings dialog for object parameters"""
    try:
        # For now, show a simple dialog. This will be expanded with Maxon SDK parameter discovery
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{object_name} Settings")
        dialog.setModal(True)
        dialog.resize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        info_label = QLabel(f"Settings for {object_name}\n\nThis will include:\n• Position and rotation controls\n• Object-specific parameters from Maxon SDK\n• Default value overrides")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Add standard OK/Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec()
        
    except Exception as e:
        self.logger.error(f"Error showing settings dialog for {object_type}: {e}")
        self.status_bar.showMessage(f"Error showing settings for {object_name}", 3000)

def _test_c4d_connection(self):
    """Test Cinema4D connection"""
    if hasattr(self, 'c4d_client'):
        self._run_async_task(self.c4d_client.test_connection())
    else:
        self.status_bar.showMessage("Cinema4D client not initialized", 3000)

def _reconnect_c4d(self):
    """Reconnect to Cinema4D"""
    if hasattr(self, 'c4d_client'):
        self._run_async_task(self.c4d_client.connect())
    else:
        self.status_bar.showMessage("Cinema4D client not initialized", 3000)

def _browse_for_models(self):
    """Browse for 3D model files"""
    try:
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("3D Models (*.obj *.fbx *.gltf *.glb)")
        file_dialog.setDirectory(str(self.config.models_3d_dir))
        
        if file_dialog.exec():
            selected_files = [Path(f) for f in file_dialog.selectedFiles()]
            self.selected_models = selected_files
            self._update_import_selection_display()
            
    except Exception as e:
        self.logger.error(f"Error browsing for models: {e}")
        self.status_bar.showMessage("Error browsing for models", 3000)

def _update_import_selection_display(self):
    """Update the import selection display"""
    if hasattr(self, 'import_selection_label'):
        if hasattr(self, 'selected_models') and self.selected_models:
            count = len(self.selected_models)
            self.import_selection_label.setText(f"{count} model{'s' if count != 1 else ''} selected")
        else:
            self.import_selection_label.setText("No models selected")

def _import_selected_models(self):
    """Import selected 3D models to Cinema4D"""
    if not hasattr(self, 'selected_models') or not self.selected_models:
        self.status_bar.showMessage("No models selected for import", 3000)
        return
    
    if not hasattr(self, 'c4d_client') or not self.c4d_client._connected:
        self.status_bar.showMessage("Cinema4D not connected", 3000)
        return
    
    self.status_bar.showMessage(f"Importing {len(self.selected_models)} models...", 0)
    self._run_async_task(self._execute_import_models(self.selected_models))

async def _execute_import_models(self, model_paths):
    """Execute model import to Cinema4D"""
    try:
        for model_path in model_paths:
            result = await self.c4d_client.import_obj(model_path)
            if result:
                self.logger.info(f"Successfully imported {model_path.name}")
            else:
                self.logger.error(f"Failed to import {model_path.name}")
        
        QTimer.singleShot(0, lambda: self.status_bar.showMessage(f"✅ Imported {len(model_paths)} models", 3000))
        
    except Exception as e:
        self.logger.error(f"Error importing models: {e}")
        QTimer.singleShot(0, lambda: self.status_bar.showMessage(f"❌ Error importing models: {str(e)}", 5000))

# Placeholder execution methods for new object types
async def _execute_create_spline(self, spline_type: str):
    """Execute spline creation using Cinema4D constants"""
    # Implementation will use Cinema4D spline constants
    QTimer.singleShot(0, lambda: self.status_bar.showMessage(f"Spline creation not yet implemented", 3000))

async def _execute_create_mograph(self, mograph_type: str):
    """Execute MoGraph object creation using Cinema4D constants"""
    # Implementation will use existing cloner/effector patterns
    QTimer.singleShot(0, lambda: self.status_bar.showMessage(f"MoGraph creation not yet implemented", 3000))

async def _execute_create_dynamics(self, dynamics_type: str):
    """Execute dynamics object creation using Cinema4D constants"""
    # Implementation will use existing tag creation patterns
    QTimer.singleShot(0, lambda: self.status_bar.showMessage(f"Dynamics creation not yet implemented", 3000))

async def _execute_create_light(self, light_type: str):
    """Execute light creation using Cinema4D constants"""
    # Implementation will use Cinema4D light constants
    QTimer.singleShot(0, lambda: self.status_bar.showMessage(f"Light creation not yet implemented", 3000))

async def _execute_create_camera(self, camera_type: str):
    """Execute camera creation using Cinema4D constants"""
    # Implementation will use Cinema4D camera constants
    QTimer.singleShot(0, lambda: self.status_bar.showMessage(f"Camera creation not yet implemented", 3000))

async def _execute_create_material(self, material_type: str):
    """Execute material creation using Cinema4D constants"""
    # Implementation will use Cinema4D material constants
    QTimer.singleShot(0, lambda: self.status_bar.showMessage(f"Material creation not yet implemented", 3000))

async def _execute_create_character(self, character_type: str):
    """Execute character object creation using Cinema4D constants"""
    # Implementation will use Cinema4D character constants
    QTimer.singleShot(0, lambda: self.status_bar.showMessage(f"Character creation not yet implemented", 3000))

async def _execute_create_volume(self, volume_type: str):
    """Execute volume object creation using Cinema4D constants"""
    # Implementation will use Cinema4D volume constants
    QTimer.singleShot(0, lambda: self.status_bar.showMessage(f"Volume creation not yet implemented", 3000))