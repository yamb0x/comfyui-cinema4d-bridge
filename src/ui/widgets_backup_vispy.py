"""
Custom UI widgets for the application
"""

import sys
from pathlib import Path
from typing import List, Optional
import numpy as np

from PySide6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout,
    QScrollArea, QFrame, QPushButton, QTextEdit, QCheckBox,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer
from PySide6.QtGui import QPixmap, QPainter, QBrush, QColor, QFont, QImage

from PIL import Image
from loguru import logger

# 3D visualization imports
try:
    import trimesh
except ImportError as e:
    logger.warning(f"3D mesh processing not available: {e}")

# Import ThreeJS viewer for all 3D visualization
from ui.viewers.threejs_3d_viewer import ThreeJS3DViewer


class Simple3DViewer(QWidget):
    """Simple 3D model viewer using ThreeJS - wrapper for compatibility"""
    
    _active_viewers = []  # Track active viewers for cleanup purposes
    MAX_TOTAL_VIEWERS = 50  # Higher limit but still bounded
    MAX_SESSION_VIEWERS = 30  # Priority for Scene Objects (current session)
    
    def __init__(self, width=496, height=496, is_session_viewer=False):  # Updated default size to 1:1 aspect ratio
        super().__init__()
        self.setFixedSize(width, height)
        self.mesh_data = None
        self.canvas = None
        self._is_active = False
        self._model_path = None
        self._is_session_viewer = is_session_viewer  # Priority flag for Scene Objects
        
        # Setup will be done on demand - either fallback or 3D viewer
        self._layout_initialized = False
        # Initialize with fallback
        self._setup_fallback()
    
    def _setup_3d_viewer(self):
        """Setup vispy 3D viewer with better error handling"""
        try:
            # Use PySide6 backend for vispy
            use_app('pyside6')
            
            # Create vispy canvas with dark theme matching the UI
            self.canvas = scene.SceneCanvas(
                size=(self.width(), self.height()),  # Use the actual widget size
                parent=self,
                bgcolor='#1e1e1e',  # Darker background
                show=True,
                resizable=True
            )
            
            # Setup 3D view
            self.view = self.canvas.central_widget.add_view()
            
            # Setup camera
            try:
                self.view.camera = 'turntable'
            except Exception as e:
                logger.error(f"Turntable camera failed: {e}")
                self.view.camera = 'arcball'
            
            # Default view: look at objects at (0, -1, 1) with close distance
            self.view.camera.elevation = 35   # Higher elevation = more top-down
            self.view.camera.azimuth = 45     # Classic 45° side view  
            self.view.camera.distance = 2.5   # Close distance for large appearance
            self.view.camera.center = (0, -1, 1)  # Look at object position (adjusted for -1 Y)
            
            # Force camera update
            self.view.camera.set_range()
            
            # Create single finite grid plane (like reference image)
            self._setup_finite_grid()
            
            # Add 3D axis indicators (X=Red, Y=Green, Z=Blue)
            self._setup_3d_axes()
            
            # Store reference to axes for repositioning when model loads
            self.axes_objects = []
            
            # Setup lighting
            self._setup_lighting()
            
            # Clear fallback content and add 3D canvas
            layout = self.layout()
            
            # Remove fallback label if it exists
            if hasattr(self, 'fallback_label') and self.fallback_label:
                self.fallback_label.setParent(None)
                self.fallback_label.deleteLater()
                self.fallback_label = None
            
            # Add canvas to layout
            layout.addWidget(self.canvas.native)
            
            # Set camera view after everything is set up
            QTimer.singleShot(100, self._finalize_camera_setup)
            
            
        except Exception as e:
            logger.error(f"Failed to setup 3D viewer: {e}")
            self._setup_fallback()
    
    def _setup_3d_axes(self):
        """Setup colored 3D axis indicators"""
        try:
            from vispy.scene.visuals import Line
            
            # Axis length and offset (move axes down by 0.5 units)
            axis_length = 1.0
            axis_offset_y = -0.5
            
            # X-axis (Red) - moved down
            x_axis_points = np.array([[0, axis_offset_y, 0], [axis_length, axis_offset_y, 0]], dtype=np.float32)
            x_axis = Line(x_axis_points, color='red', width=3, parent=self.view.scene)
            
            # Y-axis (Green) - pointing up from lower position
            y_axis_points = np.array([[0, axis_offset_y, 0], [0, axis_length + axis_offset_y, 0]], dtype=np.float32)
            y_axis = Line(y_axis_points, color='green', width=3, parent=self.view.scene)
            
            # Z-axis (Blue) - moved down
            z_axis_points = np.array([[0, axis_offset_y, 0], [0, axis_offset_y, axis_length]], dtype=np.float32)
            z_axis = Line(z_axis_points, color='blue', width=3, parent=self.view.scene)
            
            # Store references
            self.x_axis = x_axis
            self.y_axis = y_axis
            self.z_axis = z_axis
            
            # Store axes for repositioning
            if hasattr(self, 'axes_objects'):
                self.axes_objects = [x_axis, y_axis, z_axis]
            
        except Exception as e:
            logger.error(f"Failed to setup 3D axes: {e}")
    
    def _setup_finite_grid(self):
        """Setup a finite grid plane on YX axis (vertical workplane)"""
        try:
            from vispy.scene.visuals import Line
            
            # Create finite grid on YX plane (vertical wall, not floor)
            grid_size = 10  # 10x10 grid
            grid_spacing = 0.5  # Distance between grid lines
            grid_extent = grid_size * grid_spacing / 2  # Half size for centering
            
            # Grid offset (move grid down by 0.5 units)
            grid_offset_y = -0.5
            
            # Grid lines in X direction (horizontal lines on YX plane)
            x_lines = []
            for i in range(grid_size + 1):
                y_pos = -grid_extent + i * grid_spacing + grid_offset_y
                x_line = np.array([
                    [-grid_extent, y_pos, 0],  # Z=0 for YX plane
                    [grid_extent, y_pos, 0]   # Z=0 for YX plane
                ], dtype=np.float32)
                x_lines.append(x_line)
            
            # Grid lines in Y direction (vertical lines on YX plane)
            y_lines = []
            for i in range(grid_size + 1):
                x_pos = -grid_extent + i * grid_spacing
                y_line = np.array([
                    [x_pos, -grid_extent + grid_offset_y, 0],  # Z=0 for YX plane
                    [x_pos, grid_extent + grid_offset_y, 0]   # Z=0 for YX plane
                ], dtype=np.float32)
                y_lines.append(y_line)
            
            # Create line visuals for the grid
            grid_color = (0.3, 0.3, 0.3, 0.8)  # Semi-transparent gray
            
            # Add X direction lines (horizontal)
            for line_points in x_lines:
                line = Line(line_points, color=grid_color, width=1, parent=self.view.scene)
            
            # Add Y direction lines (vertical)
            for line_points in y_lines:
                line = Line(line_points, color=grid_color, width=1, parent=self.view.scene)
            
            
        except Exception as e:
            logger.error(f"Failed to setup finite grid: {e}")
    
    def _finalize_camera_setup(self):
        """Finalize camera setup after scene is ready"""
        try:
            if hasattr(self, 'view') and self.view:
                # Camera setup for objects positioned at (0, -1, 1) - moved down 1 unit
                self.view.camera.elevation = 35
                self.view.camera.azimuth = 45
                self.view.camera.distance = 2.5
                self.view.camera.center = (0, -1, 1)
                
                # Set camera range to ensure proper viewing volume (adjusted for Y=-1 position)
                self.view.camera.set_range(x=(-5, 5), y=(-2, 3), z=(-5, 5))
                
                # Force canvas update/redraw
                try:
                    self.canvas.update()
                    self.view.camera.view_changed()
                except Exception as e:
                    logger.error(f"Error forcing canvas update: {e}")
                
                # Reset camera and set values again
                try:
                    self.view.camera.reset()
                    self.view.camera.elevation = 35
                    self.view.camera.azimuth = 45
                    self.view.camera.distance = 2.5
                    self.view.camera.center = (0, -1, 1)
                except Exception as e:
                    logger.error(f"Error resetting camera: {e}")
                
        except Exception as e:
            logger.error(f"Failed to finalize camera setup: {e}")
    
    def _setup_lighting(self):
        """Setup lighting system with adjustable direction and intensity"""
        try:
            # Default lighting settings - stronger intensity by default
            self.light_direction = 45.0  # degrees
            self.light_intensity = 2.0   # Max intensity (was 0.8, now 2.0 for stronger lighting)
            
            # Note: Lighting will be applied when mesh is loaded
            
        except Exception as e:
            logger.error(f"Failed to setup lighting: {e}")
    
    def _update_lighting(self):
        """Update lighting for the current mesh"""
        try:
            if hasattr(self, 'mesh_visual') and self.mesh_visual is not None and hasattr(self, '_original_vertices'):
                # Recreate the mesh with new lighting
                vertices = self._original_vertices
                faces = self._original_faces
                
                # Apply pure white base color for consistent material (same as initial load)
                pure_white = np.array([1.0, 1.0, 1.0])  # Pure white base
                white_colors = np.tile(pure_white, (len(vertices), 1))
                
                # Apply lighting to pure white colors (not original mesh colors)
                lit_colors = self._apply_lighting(vertices, white_colors)
                
                # Try to update existing mesh instead of recreating (more efficient)
                try:
                    # Update vertex colors directly if possible
                    self.mesh_visual.mesh_data.set_vertex_colors(lit_colors)
                    self.mesh_visual.update()
                except Exception:
                    # Fallback: recreate mesh if direct update fails
                    self.mesh_visual.parent = None
                    
                    from vispy.scene.visuals import Mesh
                    self.mesh_visual = Mesh(
                        vertices=vertices,
                        faces=faces,
                        vertex_colors=lit_colors,
                        shading='smooth'
                    )
                    
                    self.view.add(self.mesh_visual)
                    
        except Exception as e:
            logger.error(f"Failed to update lighting: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
    
    def _setup_fallback(self):
        """Setup fallback display"""
        # Only setup layout if not already initialized
        if not self._layout_initialized:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            self._layout_initialized = True
        else:
            layout = self.layout()
        
        self.fallback_label = QLabel("3D Preview\nLoading...")
        self.fallback_label.setAlignment(Qt.AlignCenter)
        self.fallback_label.setStyleSheet(
            "background-color: #2a2a2a; border: 1px solid #444; "
            "color: #666; font-size: 10px; padding: 5px;"
        )
        self.fallback_label.setWordWrap(True)
        layout.addWidget(self.fallback_label)
        
        # Make clickable to potentially activate 3D viewer
        self.fallback_label.mousePressEvent = self._on_fallback_click
    
    def _on_fallback_click(self, event):
        """Handle click on fallback - could activate 3D viewer if needed"""
        if event.button() == Qt.LeftButton and self._model_path:
            # For now, just show that it's clicked
            self.fallback_label.setStyleSheet(
                self.fallback_label.styleSheet().replace('#2a2a2a', '#3a3a3a')
            )
            QTimer.singleShot(200, self._reset_fallback_style)
    
    def _reset_fallback_style(self):
        """Reset fallback style after click"""
        self.fallback_label.setStyleSheet(
            self.fallback_label.styleSheet().replace('#3a3a3a', '#2a2a2a')
        )
    
    @classmethod
    def _cleanup_inactive_viewers(cls):
        """Clean up inactive 3D viewers to free memory"""
        try:
            initial_count = len(cls._active_viewers)
            
            # Remove viewers that are no longer active or have been deleted
            active_viewers = []
            for viewer in cls._active_viewers:
                try:
                    # Check if viewer still exists and is visible
                    if viewer and hasattr(viewer, '_is_active') and viewer._is_active:
                        # Check if parent widget still exists
                        if viewer.parent() is not None:
                            active_viewers.append(viewer)
                        else:
                            # Parent deleted, deactivate this viewer
                            viewer._is_active = False
                            if hasattr(viewer, 'canvas') and viewer.canvas:
                                viewer.canvas.close()
                                viewer.canvas = None
                except Exception:
                    # Viewer is corrupted, skip it
                    pass
            
            cls._active_viewers = active_viewers
            cleaned_count = initial_count - len(active_viewers)
            
            if cleaned_count > 0:
                logger.info(f"🧹 Cleaned up {cleaned_count} inactive 3D viewers ({initial_count} → {len(active_viewers)})")
            else:
                logger.info(f"🧹 No inactive viewers to clean (all {len(active_viewers)} are active)")
                
        except Exception as e:
            logger.error(f"Error during 3D viewer cleanup: {e}")
    
    @classmethod
    def _can_activate_3d_viewer(cls, is_session_viewer=False):
        """Check if we can activate a new 3D viewer with priority system"""
        # Always cleanup first
        cls._cleanup_inactive_viewers()
        
        current_count = len(cls._active_viewers)
        session_count = sum(1 for v in cls._active_viewers 
                          if hasattr(v, '_is_session_viewer') and v._is_session_viewer)
        
        # Session viewers (Scene Objects) get priority up to MAX_SESSION_VIEWERS
        if is_session_viewer:
            if session_count < cls.MAX_SESSION_VIEWERS:
                return True
            else:
                logger.info(f"Session viewer limit reached ({session_count}/{cls.MAX_SESSION_VIEWERS})")
                return False
        
        # Non-session viewers (View All) can use remaining slots
        if current_count < cls.MAX_TOTAL_VIEWERS:
            return True
        else:
            logger.info(f"Total viewer limit reached ({current_count}/{cls.MAX_TOTAL_VIEWERS})")
            return False
    
    def activate_3d_viewer(self):
        """Activate real 3D viewer on demand with limit checking"""
        if not VISPY_AVAILABLE or self._is_active:
            return False
        
        # Check if we can activate a new viewer
        if not Simple3DViewer._can_activate_3d_viewer(self._is_session_viewer):
            return False
        
        try:
            self._setup_3d_viewer()
            if self._model_path:
                self._load_3d_model(self._model_path)
            Simple3DViewer._active_viewers.append(self)
            self._is_active = True
            logger.info(f"✅ 3D viewer activated ({'session' if self._is_session_viewer else 'history'}): {self._model_path.name if self._model_path else 'unknown'}")
            return True
        except Exception as e:
            logger.error(f"Failed to activate 3D viewer: {e}")
            return False
    
    def deactivate_3d_viewer(self):
        """Deactivate 3D viewer to free memory"""
        if self._is_active and self in Simple3DViewer._active_viewers:
            Simple3DViewer._active_viewers.remove(self)
            self._is_active = False
            
            if self.canvas:
                # Remove canvas from layout
                if self.layout():
                    self.layout().removeWidget(self.canvas.native)
                self.canvas.close()
                self.canvas = None
            
            # Return to fallback
            self._setup_fallback()
            if self._model_path:
                self._render_thumbnail_fallback(self._model_path)
    
    def load_model(self, model_path: Path):
        """Load 3D model from file with smart resource management"""
        self._model_path = model_path
        
        # Try to activate 3D viewer with priority system and enhanced error handling
        if VISPY_AVAILABLE and Simple3DViewer._can_activate_3d_viewer(self._is_session_viewer):
            try:
                logger.info(f"🎯 Attempting 3D viewer for ({'session' if self._is_session_viewer else 'history'}): {model_path.name}")
                self._setup_3d_viewer()
                self._load_3d_model(model_path)
                Simple3DViewer._active_viewers.append(self)
                self._is_active = True
                logger.info(f"✅ 3D viewer activated ({'session' if self._is_session_viewer else 'history'}): {model_path.name}")
                return
            except Exception as e:
                logger.error(f"Failed to activate 3D viewer for {model_path.name}: {e}")
                import traceback
                logger.error(f"3D viewer error traceback: {traceback.format_exc()}")
                # Fall back to safe thumbnail on error
        
        # Fallback to safe thumbnail if limits reached, VISPY unavailable, or 3D setup failed
        if not VISPY_AVAILABLE:
            logger.info(f"📋 VISPY unavailable, using safe fallback for: {model_path.name}")
        elif not Simple3DViewer._can_activate_3d_viewer(self._is_session_viewer):
            logger.info(f"📋 Viewer limit reached, using safe fallback for: {model_path.name}")
        else:
            logger.info(f"📋 3D setup failed, using safe fallback for: {model_path.name}")
        
        self._render_thumbnail_fallback(model_path)
    
    def _load_3d_model(self, model_path: Path):
        """Load and display 3D model in vispy viewer"""
        if not self.canvas or not hasattr(self, 'view') or not self.view:
            logger.error(f"3D viewer not properly initialized for {model_path.name}")
            return
            
        try:
            # Load mesh using trimesh
            mesh = trimesh.load(str(model_path))
            
            # Handle both single meshes and scenes
            if hasattr(mesh, 'vertices') and hasattr(mesh, 'faces'):
                # Single mesh
                self._display_mesh(mesh)
            elif hasattr(mesh, 'geometry') and mesh.geometry:
                # Scene with multiple geometries - use the first one
                geometries = list(mesh.geometry.values())
                if geometries:
                    first_geom = geometries[0]
                    self._display_mesh(first_geom)
                else:
                    logger.warning("Scene has no geometries")
                    self._show_error("Empty Scene")
            else:
                logger.warning(f"Could not extract mesh data from {model_path}")
                self._show_error("Invalid mesh")
                
        except Exception as e:
            logger.error(f"❌ Failed to load 3D model {model_path}: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            self._show_error("Load failed")
    
    def _display_mesh(self, mesh):
        """Display mesh in the viewer with proper centering and ground positioning"""
        try:
            # Clear existing mesh
            if hasattr(self, 'mesh_visual'):
                self.mesh_visual.parent = None
            
            # Convert to vispy format
            vertices = np.array(mesh.vertices, dtype=np.float32)
            faces = np.array(mesh.faces, dtype=np.uint32)
            
            # Center the model at origin (0,0,0)
            vertices = self._center_model(vertices)
            
            # Standardize model size relative to grid
            vertices = self._standardize_model_size(vertices)
            
            # Rotate model +90° on X axis to lay flat on grid
            vertices = self._rotate_model_x(vertices, 90)
            
            # Position model at (0, 0, 1)
            vertices = self._position_model(vertices)
            
            # Create colors with lighting consideration
            if hasattr(mesh.visual, 'vertex_colors') and mesh.visual.vertex_colors is not None:
                colors = np.array(mesh.visual.vertex_colors[:, :3], dtype=np.float32) / 255.0
            else:
                # Default material color with lighting
                base_color = np.array([0.7, 0.7, 0.8])  # Slightly blue-gray
                colors = np.tile(base_color, (len(vertices), 1))
            
            # Store original data for lighting updates
            self._original_vertices = vertices.copy()
            self._original_faces = faces.copy()
            self._original_colors = colors.copy()
            
            # Apply pure white base color for consistent material appearance
            pure_white = np.array([1.0, 1.0, 1.0])  # Pure white base
            colors = np.tile(pure_white, (len(vertices), 1))
            
            # Apply lighting to the pure white colors with stronger default intensity
            colors = self._apply_lighting(vertices, colors)
            
            # Create mesh visual with brighter white shader
            from vispy.scene.visuals import Mesh
            self.mesh_visual = Mesh(
                vertices=vertices,
                faces=faces,
                vertex_colors=colors,
                shading='smooth'  # Use smooth shading for better appearance
            )
            
            # Apply bright white material properties 
            try:
                # Set material properties for bright appearance
                self.mesh_visual.set_gl_state('opaque', depth_test=True, cull_face=True)
                self.mesh_visual.shading_filter.specular = (0.3, 0.3, 0.3)  # Brighter specular
                self.mesh_visual.shading_filter.shininess = 64.0  # Higher shininess for more reflection
            except Exception as e:
                logger.debug(f"Could not apply advanced shader properties: {e}")
                # Fallback to basic shading
                pass
            
            # Reposition axes to object center (simple approach)
            self._reposition_axes_to_object_center(vertices)
            
            self.view.add(self.mesh_visual)
            
            # Set appropriate camera view for centered model
            self._setup_camera_for_model(vertices)
            
            # Force a complete redraw after model is loaded
            try:
                self.canvas.update()
                self.view.update()
            except Exception as e:
                logger.error(f"Error forcing update after model load: {e}")
            
        except Exception as e:
            logger.error(f"Failed to display mesh: {e}")
            self._show_error("Display failed")
    
    def _center_model(self, vertices):
        """Center model at origin (0,0,0) using proper bounding box method"""
        try:
            # Calculate bounding box center (your suggested method)
            bbox_min = np.min(vertices, axis=0)
            bbox_max = np.max(vertices, axis=0)
            center = (bbox_min + bbox_max) * 0.5
            
            # Translate to center
            centered_vertices = vertices - center
            
            return centered_vertices
            
        except Exception as e:
            logger.error(f"Failed to center model: {e}")
            return vertices
    
    def _standardize_model_size(self, vertices):
        """Standardize model size relative to grid for consistent appearance"""
        try:
            # Calculate current model dimensions
            min_coords = np.min(vertices, axis=0)
            max_coords = np.max(vertices, axis=0)
            current_size = np.max(max_coords - min_coords)
            
            # Target size: make all models appear as 2-3 grid units (1.0-1.5 units)
            # Grid spacing is 0.5, so 2-3 units = good visibility without being too large
            target_size = 1.5  # 3 grid spaces
            
            if current_size > 0:
                # Calculate scale factor
                scale_factor = target_size / current_size
                
                # Apply uniform scaling
                vertices *= scale_factor
                
            else:
                logger.warning("Model has zero size, cannot standardize")
            
            return vertices
            
        except Exception as e:
            logger.error(f"Failed to standardize model size: {e}")
            return vertices
    
    def _rotate_model_y(self, vertices, degrees):
        """Rotate model around Y axis by specified degrees"""
        try:
            # Convert degrees to radians
            angle_rad = np.radians(degrees)
            
            # Create Y-axis rotation matrix
            cos_a = np.cos(angle_rad)
            sin_a = np.sin(angle_rad)
            
            rotation_matrix = np.array([
                [cos_a,  0, sin_a],
                [0,      1, 0    ],
                [-sin_a, 0, cos_a]
            ])
            
            # Apply rotation to all vertices
            rotated_vertices = np.dot(vertices, rotation_matrix.T)
            
            return rotated_vertices
            
        except Exception as e:
            logger.error(f"Failed to rotate model: {e}")
            return vertices
    
    def _rotate_model_x(self, vertices, degrees):
        """Rotate model around X axis by specified degrees"""
        try:
            # Convert degrees to radians
            angle_rad = np.radians(degrees)
            
            # Create X-axis rotation matrix
            cos_a = np.cos(angle_rad)
            sin_a = np.sin(angle_rad)
            
            rotation_matrix = np.array([
                [1, 0,      0     ],
                [0, cos_a, -sin_a],
                [0, sin_a,  cos_a]
            ])
            
            # Apply rotation to all vertices
            rotated_vertices = np.dot(vertices, rotation_matrix.T)
            
            return rotated_vertices
            
        except Exception as e:
            logger.error(f"Failed to rotate model: {e}")
            return vertices
    
    def _position_model(self, vertices):
        """Position model at (0, -1, 1) - moved down 1 unit in Y"""
        try:
            # Find lowest Y coordinate for ground positioning
            min_y = np.min(vertices[:, 1])
            
            # First center the model at origin, then move to target position
            vertices[:, 1] -= min_y  # Place bottom at Y=0
            
            # Move model to final position (0, -1, 1) - down 1 unit in Y
            target_position = np.array([0, -1, 1])
            vertices[:, 1] += target_position[1]  # Move to Y=-1
            vertices[:, 2] += target_position[2]  # Move to Z=1
            
            return vertices
            
        except Exception as e:
            logger.error(f"Failed to position model: {e}")
            return vertices
    
    def _reposition_axes_to_object_center(self, vertices):
        """Reposition 3D axes to the center of the object using proper bounding box method"""
        try:
            if not hasattr(self, 'axes_objects') or not self.axes_objects:
                return
                
            # Calculate object center using same method as centering (proper bounding box)
            bbox_min = np.min(vertices, axis=0)
            bbox_max = np.max(vertices, axis=0)
            center = (bbox_min + bbox_max) * 0.5
            
            # Remove old axes
            for axis in self.axes_objects:
                if axis.parent:
                    axis.parent = None
            
            # Create new axes at object center
            from vispy.scene.visuals import Line
            axis_length = 0.5  # Smaller axes for object center
            
            # X-axis (Red) at object center
            x_axis_points = np.array([center, center + [axis_length, 0, 0]], dtype=np.float32)
            x_axis = Line(x_axis_points, color='red', width=3, parent=self.view.scene)
            
            # Y-axis (Green) at object center
            y_axis_points = np.array([center, center + [0, axis_length, 0]], dtype=np.float32)
            y_axis = Line(y_axis_points, color='green', width=3, parent=self.view.scene)
            
            # Z-axis (Blue) at object center
            z_axis_points = np.array([center, center + [0, 0, axis_length]], dtype=np.float32)
            z_axis = Line(z_axis_points, color='blue', width=3, parent=self.view.scene)
            
            # Update references
            self.axes_objects = [x_axis, y_axis, z_axis]
            
            
        except Exception as e:
            logger.error(f"Failed to reposition axes to object center: {e}")
    
    def _apply_lighting(self, vertices, colors):
        """Apply realistic directional lighting to vertex colors"""
        try:
            # Calculate light direction vector from angle (proper 3D rotation)
            light_direction_rad = np.radians(self.light_direction)
            
            # Create light vector rotating around Y axis, elevated 45° above horizon
            elevation_rad = np.radians(45)  # Standard key light elevation
            light_vector = np.array([
                np.cos(light_direction_rad) * np.cos(elevation_rad),  # X component
                np.sin(elevation_rad),                                 # Y component (height)
                np.sin(light_direction_rad) * np.cos(elevation_rad)   # Z component
            ])
            light_vector = light_vector / np.linalg.norm(light_vector)
            
            # Lighting components
            ambient_strength = 0.25  # Base ambient light
            directional_strength = self.light_intensity  # Now supports 0.1 to 2.0
            
            # Calculate position-based lighting (simulating directional light)
            # Use X and Z positions to simulate directional lighting from the light vector
            x_positions = vertices[:, 0] * light_vector[0]
            z_positions = vertices[:, 2] * light_vector[2]
            directional_factor = (x_positions + z_positions) * 0.3  # Directional influence
            
            # Add height-based lighting (Y position)
            y_positions = vertices[:, 1]
            if len(y_positions) > 0:
                y_normalized = (y_positions - np.min(y_positions)) / (np.max(y_positions) - np.min(y_positions) + 1e-6)
                height_lighting = y_normalized * 0.4 * directional_strength  # Top surfaces brighter
                height_lighting = height_lighting.reshape(-1, 1)
            else:
                height_lighting = 0
            
            # Combine all lighting effects
            directional_lighting = directional_factor.reshape(-1, 1) * directional_strength * 0.5
            base_lighting = ambient_strength + (directional_strength * 0.3)
            
            total_lighting = base_lighting + height_lighting + directional_lighting
            
            # Apply lighting to colors
            lit_colors = colors * total_lighting
            
            # Ensure colors stay in valid range
            lit_colors = np.clip(lit_colors, 0.0, 1.0)
            
            
            return lit_colors
            
        except Exception as e:
            logger.error(f"Failed to apply lighting: {e}")
            return colors
    
    def _setup_camera_for_model(self, vertices):
        """Setup camera view for the model"""
        try:
            # Calculate model size for proper distance
            min_coords = np.min(vertices, axis=0)
            max_coords = np.max(vertices, axis=0)
            model_size = np.max(max_coords - min_coords)
            model_height = max_coords[1] - min_coords[1]
            
            # Set distance for standardized models at (0, -1, 1) - close for large appearance
            distance = 2.0  # Close distance for large size
            
            # Same viewing angles as default view
            self.view.camera.elevation = 35   # Higher elevation = more top-down
            self.view.camera.azimuth = 45     # Classic 45° side view
            self.view.camera.distance = distance
            
            # Look at standardized model center at (0, -1, 1)
            # Models are standardized to 1.5 units, center is around Z=1, Y=-0.25 (moved down 1 unit)
            self.view.camera.center = (0, -0.25, 1)  # Look at model center (adjusted for -1 Y position)
            
            # Set viewing range for standardized models at (0, -1, 1)
            range_size = 3.0  # Fixed range for standardized 1.5-unit models
            self.view.camera.set_range(
                x=(-range_size, range_size),
                y=(-2, 2),  # Y range adjusted for models at Y=-1
                z=(-2, 4)  # Z range centered around 1
            )
            
            
        except Exception as e:
            logger.error(f"Failed to setup camera: {e}")
    
    def _render_thumbnail_fallback(self, model_path: Path):
        """Safe fallback display without loading 3D data to prevent crashes"""
        try:
            # SAFE APPROACH: Don't load any 3D data, just show file info
            file_type = model_path.suffix.upper().lstrip('.')
            file_size = model_path.stat().st_size if model_path.exists() else 0
            
            # Ensure fallback label exists
            if not hasattr(self, 'fallback_label') or self.fallback_label is None:
                self._setup_fallback()
            
            # Display safe file information without loading 3D data
            if file_size > 0:
                size_text = f"{file_size // 1024}KB" if file_size < 1024*1024 else f"{file_size // (1024*1024)}MB"
                self.fallback_label.setText(f"{file_type}\n{model_path.stem}\n{size_text}")
                self.fallback_label.setStyleSheet(
                    "background-color: #2a2a2a; border: 1px solid #444; "
                    "color: #aaa; font-size: 10px; padding: 5px;"
                )
                logger.info(f"📋 Safe fallback display for: {model_path.name} ({size_text})")
            else:
                self.fallback_label.setText(f"{file_type}\nFile Error\n⚠️")
                logger.warning(f"File size is 0 or doesn't exist: {model_path}")
                
        except Exception as e:
            logger.error(f"Error in safe fallback display: {e}")
            # Ultra-safe fallback
            if hasattr(self, 'fallback_label') and self.fallback_label:
                self.fallback_label.setText("3D Model\nDisplay Error\n⚠️")
    
    def _display_mesh_info(self, mesh, model_path: Path, scene_info: str = None):
        """Display mesh information in the thumbnail"""
        try:
            file_type = model_path.suffix.upper().lstrip('.')
            vertex_count = len(mesh.vertices) if hasattr(mesh, 'vertices') else 0
            face_count = len(mesh.faces) if hasattr(mesh, 'faces') else 0
            
            if scene_info:
                info_text = f"{file_type}\n{scene_info}\n{vertex_count:,} verts"
            else:
                info_text = f"{file_type}\n{vertex_count:,} verts\n{face_count:,} faces"
            
            # Ensure fallback label exists
            if not hasattr(self, 'fallback_label') or self.fallback_label is None:
                self._setup_fallback()
                
            self.fallback_label.setText(info_text)
            self.fallback_label.setStyleSheet(
                self.fallback_label.styleSheet() + 
                "; color: #aaa; font-size: 9px;"
            )
        except Exception as e:
            logger.error(f"Error displaying mesh info: {e}")
            self._display_file_info_fallback(model_path, "Info Error")
    
    def _display_file_info_fallback(self, model_path: Path, status: str):
        """Display basic file info when mesh data unavailable"""
        file_type = model_path.suffix.upper().lstrip('.')
        
        # Ensure fallback label exists
        if not hasattr(self, 'fallback_label') or self.fallback_label is None:
            self._setup_fallback()
            
        self.fallback_label.setText(f"{file_type}\n{status}\n⚠️")
    
    def _show_error(self, error_msg: str):
        """Show error in viewer"""
        if hasattr(self, 'fallback_label'):
            self.fallback_label.setText(f"Error\n{error_msg}")
        elif self.canvas:
            # Clear canvas and show error
            self.view.children.clear()
            # Could add text visual here if needed


class ImageThumbnail(QFrame):
    """Thumbnail widget for images"""
    
    clicked = Signal(Path)
    selected = Signal(Path, bool)
    
    def __init__(self, image_path: Path, size: int = 256):
        super().__init__()
        self.image_path = image_path
        self.size = size
        self._selected = False
        
        self.setFixedSize(size + 20, size + 40)
        self.setFrameStyle(QFrame.NoFrame)  # Remove default frame, use CSS instead
        self.setObjectName("image_thumbnail")  # Set object name for specific CSS targeting
        
        # Main layout without spacing for absolute positioning
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(3)
        
        # Container for image with overlay checkbox
        image_container = QWidget()
        image_container.setFixedSize(size, size)
        main_layout.addWidget(image_container)
        
        # Image label (fills container)
        self.image_label = QLabel(image_container)
        self.image_label.setFixedSize(size, size)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #2a2a2a;")
        
        # Selection checkbox (positioned in bottom-right corner)
        self.select_check = QCheckBox(image_container)
        self.select_check.setText("")  # No text, just checkbox
        checkbox_size = 16
        self.select_check.setFixedSize(checkbox_size, checkbox_size)
        self.select_check.move(size - checkbox_size - 4, size - checkbox_size - 4)  # 4px margin from edges
        self.select_check.setStyleSheet("""
            QCheckBox::indicator {
                width: 12px;
                height: 12px;
                background-color: rgba(23, 23, 23, 180);
                border: 1px solid #404040;
                border-radius: 2px;
            }
            QCheckBox::indicator:checked {
                background-color: #22c55e;
                border-color: #22c55e;
            }
            QCheckBox::indicator:hover {
                border-color: #22c55e;
                background-color: rgba(34, 197, 94, 50);
            }
        """)
        self.select_check.stateChanged.connect(self._on_selection_changed)
        self.select_check.show()
        
        # Debug: Log initial checkbox state
        from loguru import logger
        logger.info(f"ImageThumbnail created: {image_path.name}, checkbox checked: {self.select_check.isChecked()}, _selected: {self._selected}")
        
        # Filename label
        self.name_label = QLabel(image_path.name)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setMaximumWidth(size)
        self.name_label.setWordWrap(True)
        font = self.name_label.font()
        font.setPointSize(9)
        self.name_label.setFont(font)
        main_layout.addWidget(self.name_label)
        
        # Load thumbnail
        self._load_thumbnail()
        
        # Apply initial style
        self._update_style()
        
    def _load_thumbnail(self):
        """Load and display thumbnail"""
        try:
            # Load with PIL for better format support
            img = Image.open(self.image_path)
            img.thumbnail((self.size, self.size), Image.Resampling.LANCZOS)
            
            # Convert to QPixmap
            if img.mode == "RGBA":
                # Handle transparency
                data = img.tobytes("raw", "RGBA")
                qimage = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
            else:
                # Convert to RGB
                img = img.convert("RGB")
                data = img.tobytes("raw", "RGB")
                qimage = QImage(data, img.width, img.height, QImage.Format_RGB888)
            
            pixmap = QPixmap.fromImage(qimage)
            
            # Scale to fit
            scaled_pixmap = pixmap.scaled(
                self.size, self.size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            self.image_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            logger.error(f"Failed to load thumbnail for {self.image_path}: {e}")
            self.image_label.setText("Failed to\nload image")
    
    def mousePressEvent(self, event):
        """Handle mouse press"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.image_path)
        super().mousePressEvent(event)
    
    def _on_selection_changed(self, state):
        """Handle selection change"""
        # Fix: State 2 = Checked, State 0 = Unchecked  
        self._selected = state == 2
        from loguru import logger
        logger.info(f"ImageThumbnail selection changed: {self.image_path.name}, Qt state: {state}, _selected: {self._selected}")
        self.selected.emit(self.image_path, self._selected)
        self._update_style()
    
    def _update_style(self):
        """Update visual style based on selection"""
        # Set property for CSS selector and force style update
        self.setProperty("selected", self._selected)
        
        # Apply base style that includes both states
        self.setStyleSheet("""
            QFrame#image_thumbnail {
                border: 1px solid transparent;
                border-radius: 3px;
                background-color: transparent;
            }
            QFrame#image_thumbnail[selected="true"] {
                border: 1px solid #4CAF50;
            }
        """)
        
        # Force style refresh
        self.style().polish(self)
    
    def set_selected(self, selected: bool):
        """Set selection state"""
        self.select_check.setChecked(selected)


class ImageGridWidget(QScrollArea):
    """Grid widget for displaying images"""
    
    image_selected = Signal(Path, bool)
    image_clicked = Signal(Path)
    
    def __init__(self, columns: int = 4, thumbnail_size: int = 256):
        super().__init__()
        self.columns = columns
        self.thumbnail_size = thumbnail_size
        self.thumbnails: List[ImageThumbnail] = []
        
        # Setup scroll area
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Content widget
        self.content = QWidget()
        self.setWidget(self.content)
        
        # Grid layout
        self.grid_layout = QGridLayout(self.content)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
    
    def add_image(self, image_path: Path):
        """Add image to grid"""
        # Create thumbnail
        thumbnail = ImageThumbnail(image_path, self.thumbnail_size)
        thumbnail.clicked.connect(self.image_clicked.emit)
        thumbnail.selected.connect(self.image_selected.emit)
        
        # Add to grid
        row = len(self.thumbnails) // self.columns
        col = len(self.thumbnails) % self.columns
        
        self.grid_layout.addWidget(thumbnail, row, col)
        self.thumbnails.append(thumbnail)
        
        # Ensure thumbnail and its checkbox are visible
        thumbnail.show()
        thumbnail.select_check.show()
        thumbnail.select_check.setVisible(True)
    
    def clear(self):
        """Clear all images"""
        for thumbnail in self.thumbnails:
            self.grid_layout.removeWidget(thumbnail)
            thumbnail.deleteLater()
        self.thumbnails.clear()
    
    def get_selected_images(self) -> List[Path]:
        """Get list of selected images"""
        selected = []
        for thumbnail in self.thumbnails:
            if thumbnail._selected:
                selected.append(thumbnail.image_path)
        return selected
    
    def set_columns(self, columns: int):
        """Set number of columns"""
        self.columns = columns
        self._reorganize_grid()
    
    def _reorganize_grid(self):
        """Reorganize grid layout"""
        # Remove all widgets
        for thumbnail in self.thumbnails:
            self.grid_layout.removeWidget(thumbnail)
        
        # Re-add in new configuration
        for i, thumbnail in enumerate(self.thumbnails):
            row = i // self.columns
            col = i % self.columns
            self.grid_layout.addWidget(thumbnail, row, col)


class Model3DPreviewCard(QFrame):
    """Preview card for a single 3D model"""
    
    clicked = Signal(Path)
    selected = Signal(Path, bool)
    
    def __init__(self, model_path: Path, is_session_viewer=False):
        super().__init__()
        self.model_path = model_path
        self._selected = False
        self._is_session_viewer = is_session_viewer
        
        # Match image card design exactly with 1:1 aspect ratio
        self.setFixedSize(512, 512)  # Same as image cards
        self.setObjectName("model_slot")  # For consistent styling
        
        # Main layout - matches image card structure
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)  # Same 8px padding as image cards
        layout.setSpacing(8)  # Same 8px spacing as image cards
        
        # Container for 3D viewer with overlay checkbox - now square 1:1 aspect ratio
        viewer_container = QWidget()
        viewer_container.setFixedSize(496, 496)  # Changed from 496x460 to 496x496 for 1:1 ratio
        layout.addWidget(viewer_container)
        
        # 3D model viewer with session priority flag - now square 1:1 aspect ratio
        self.viewer_3d = Simple3DViewer(496, 496, is_session_viewer=is_session_viewer)  # Changed from 496x460 to 496x496
        self.viewer_3d.setParent(viewer_container)
        
        # Selection checkbox overlay (positioned in bottom-right corner like images)
        self.select_check = QCheckBox(viewer_container)
        self.select_check.setText("")  # No text, just checkbox
        checkbox_size = 18  # Slightly larger than image checkboxes since model cards are bigger
        self.select_check.setFixedSize(checkbox_size, checkbox_size)
        self.select_check.move(496 - checkbox_size - 6, 460 - checkbox_size - 6)  # 6px margin from edges
        self.select_check.setStyleSheet("""
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                background-color: rgba(23, 23, 23, 180);
                border: 1px solid #404040;
                border-radius: 2px;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border-color: #4CAF50;
            }
            QCheckBox::indicator:hover {
                border-color: #4CAF50;
                background-color: rgba(76, 175, 80, 50);
            }
        """)
        self.select_check.stateChanged.connect(self._on_checkbox_changed)
        self.select_check.show()
        
        # Lighting controls (collapsible)
        lighting_layout = self._create_lighting_controls()
        layout.addWidget(lighting_layout)
        
        # Action buttons - matches image card design exactly
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)  # Same 8px spacing as image cards
        
        # Download button (left) - matches image card download button
        self.download_btn = QPushButton("⬇")
        self.download_btn.setObjectName("action_btn")  # Same styling as image cards
        self.download_btn.setFixedSize(32, 32)  # Same size as image cards
        self.download_btn.setToolTip("Download 3D model")
        self.download_btn.clicked.connect(self._download_model)
        actions_layout.addWidget(self.download_btn)
        
        # Lighting toggle button
        self.lighting_btn = QPushButton("💡")
        self.lighting_btn.setObjectName("action_btn")
        self.lighting_btn.setFixedSize(32, 32)
        self.lighting_btn.setToolTip("Toggle lighting controls")
        self.lighting_btn.clicked.connect(self._toggle_lighting_controls)
        actions_layout.addWidget(self.lighting_btn)
        
        # Add stretch to push pick button to the right
        actions_layout.addStretch()
        
        # Pick button (right) - matches image card pick button  
        self.pick_btn = QPushButton("✓")
        self.pick_btn.setObjectName("action_btn_primary")  # Same styling as image cards
        self.pick_btn.setFixedSize(32, 32)  # Same size as image cards
        self.pick_btn.setToolTip("Select for scene assembly")
        self.pick_btn.clicked.connect(self._toggle_selection)
        actions_layout.addWidget(self.pick_btn)
        
        layout.addLayout(actions_layout)
        
        # Load the model asynchronously to avoid blocking UI
        QTimer.singleShot(100, lambda: self._load_model_delayed())
    
    def _create_lighting_controls(self):
        """Create lighting control sliders"""
        from PySide6.QtWidgets import QGroupBox, QSlider, QLabel
        from PySide6.QtCore import Qt
        
        # Create collapsible group box
        self.lighting_group = QGroupBox("Lighting Controls")
        self.lighting_group.setCheckable(True)
        self.lighting_group.setChecked(False)  # Start collapsed
        self.lighting_group.setMaximumHeight(80)
        
        lighting_layout = QHBoxLayout(self.lighting_group)
        lighting_layout.setContentsMargins(5, 5, 5, 5)
        lighting_layout.setSpacing(10)
        
        # Light direction slider (0-360 degrees)
        direction_label = QLabel("Direction:")
        direction_label.setFixedWidth(50)
        lighting_layout.addWidget(direction_label)
        
        self.direction_slider = QSlider(Qt.Horizontal)
        self.direction_slider.setRange(0, 360)
        self.direction_slider.setValue(45)
        self.direction_slider.setToolTip("Light direction (0-360°)")
        # Use sliderReleased for better performance instead of valueChanged
        self.direction_slider.sliderReleased.connect(self._on_light_direction_released)
        lighting_layout.addWidget(self.direction_slider)
        
        # Light intensity slider (0-100%)
        intensity_label = QLabel("Intensity:")
        intensity_label.setFixedWidth(50)
        lighting_layout.addWidget(intensity_label)
        
        self.intensity_slider = QSlider(Qt.Horizontal)
        self.intensity_slider.setRange(10, 200)  # 10% to 200% (2x stronger)
        self.intensity_slider.setValue(200)  # 200% default (max intensity)
        self.intensity_slider.setToolTip("Light intensity (10-200%)")
        # Use sliderReleased for better performance instead of valueChanged
        self.intensity_slider.sliderReleased.connect(self._on_light_intensity_released)
        lighting_layout.addWidget(self.intensity_slider)
        
        return self.lighting_group
    
    def _toggle_lighting_controls(self):
        """Toggle lighting controls visibility"""
        self.lighting_group.setChecked(not self.lighting_group.isChecked())
    
    def _on_light_direction_released(self):
        """Handle light direction slider release - optimized for performance"""
        value = self.direction_slider.value()
        if hasattr(self.viewer_3d, 'light_direction'):
            self.viewer_3d.light_direction = float(value)
            self.viewer_3d._update_lighting()
    
    def _on_light_intensity_released(self):
        """Handle light intensity slider release - optimized for performance"""
        value = self.intensity_slider.value()
        if hasattr(self.viewer_3d, 'light_intensity'):
            self.viewer_3d.light_intensity = value / 100.0  # Convert to 0.0-2.0 range
            self.viewer_3d._update_lighting()
    
    # Keep old methods for compatibility but mark as deprecated
    def _on_light_direction_changed(self, value):
        """Legacy method - kept for compatibility"""
        pass
    
    def _on_light_intensity_changed(self, value):
        """Legacy method - kept for compatibility"""
        pass
    
    def mousePressEvent(self, event):
        """Handle mouse press"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.model_path)
        super().mousePressEvent(event)
    
    def _toggle_selection(self):
        """Toggle selection state - matches image card behavior"""
        self._selected = not self._selected
        self.selected.emit(self.model_path, self._selected)
        self._update_style()
        
    def _on_checkbox_changed(self, state):
        """Handle checkbox state change"""
        # Fix: State 2 = Checked, State 0 = Unchecked
        self._selected = state == 2
        self.selected.emit(self.model_path, self._selected)
        self._update_style()
    
    def _download_model(self):
        """Download 3D model file"""
        from PySide6.QtWidgets import QFileDialog
        try:
            # Ask user for save location
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save 3D Model",
                f"{self.model_path.stem}.{self.model_path.suffix[1:]}",
                f"3D Model Files (*{self.model_path.suffix})"
            )
            
            if save_path:
                import shutil
                shutil.copy2(self.model_path, save_path)
                logger.info(f"Downloaded 3D model to: {save_path}")
        except Exception as e:
            logger.error(f"Failed to download 3D model: {e}")
    
    def _update_style(self):
        """Update visual style based on selection - matches image card styling"""
        if self._selected:
            # Selected state - green checkmark like image cards
            self.pick_btn.setStyleSheet(
                "QPushButton { background-color: #4CAF50; color: white; }"
            )
            # Sync checkbox state
            if hasattr(self, 'select_check'):
                self.select_check.setChecked(True)
        else:
            # Unselected state - reset to default styling
            self.pick_btn.setStyleSheet("")
            # Sync checkbox state
            if hasattr(self, 'select_check'):
                self.select_check.setChecked(False)
    
    def _load_model_delayed(self):
        """Load 3D model with delay to avoid blocking UI startup"""
        try:
            if self.model_path.exists():
                try:
                    # Load the actual 3D model
                    self.viewer_3d.load_model(self.model_path)
                except Exception as model_e:
                    logger.error(f"3D model loading failed, showing file info fallback: {model_e}")
                    # Fallback to file info if 3D loading fails
                    try:
                        file_size = self.model_path.stat().st_size
                        file_info = f"{self.model_path.suffix.upper()}\n{self.model_path.name}\n{file_size // 1024}KB"
                        
                        # Update the fallback label if it exists
                        if hasattr(self.viewer_3d, 'fallback_label'):
                            self.viewer_3d.fallback_label.setText(file_info)
                            self.viewer_3d.fallback_label.setStyleSheet(
                                "background-color: #2a2a2a; border: 1px solid #444; "
                                "color: #aaa; font-size: 10px; padding: 5px;"
                            )
                        
                    except Exception as info_e:
                        logger.error(f"Failed to show file info fallback: {info_e}")
            else:
                logger.warning(f"3D model file not found: {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load 3D model preview: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
    
    def set_selected(self, selected: bool):
        """Set selection state - updated for checkbox and button system"""
        self._selected = selected
        self._update_style()
    
    def cleanup(self):
        """Clean up resources to prevent memory leaks"""
        try:
            if hasattr(self, 'viewer_3d') and self.viewer_3d:
                self.viewer_3d.deactivate_3d_viewer()
                self.viewer_3d.deleteLater()
        except Exception as e:
            logger.error(f"Error during 3D preview cleanup: {e}")
    
    def closeEvent(self, event):
        """Handle widget close event"""
        self.cleanup()
        super().closeEvent(event)


class Model3DPreviewWidget(QScrollArea):
    """Widget for previewing 3D models in a grid"""
    
    model_selected = Signal(Path, bool)
    model_clicked = Signal(Path)
    
    def __init__(self, columns: int = 3, is_session_widget=False):
        super().__init__()
        self.columns = columns
        self.models: List[Path] = []
        self.cards: List[Model3DPreviewCard] = []
        self._is_session_widget = is_session_widget  # Flag for Scene Objects vs View All
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI optimized for full screen usage"""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Set size policy to expand and use all available space
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Content widget with proper size policy
        self.content = QWidget()
        self.content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setWidget(self.content)
        
        # Main layout with minimal margins
        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(5, 5, 5, 5)  # Reduced from 10px to 5px
        layout.setSpacing(5)  # Reduced from 10px to 5px
        
        # Info label with reduced padding
        self.info_label = QLabel("No 3D models generated yet")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #888; font-size: 14px; padding: 10px;")  # Reduced padding
        layout.addWidget(self.info_label)
        
        # Grid for model cards with optimized spacing
        self.grid_widget = QWidget()
        # Set size policy for grid widget to use minimum space needed
        self.grid_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(15)  # Reduced from 20px to 15px for better space utilization
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        # Align items to top-left to prevent spreading when fewer items
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        layout.addWidget(self.grid_widget)
        
        # Remove addStretch() to prevent excessive empty space at bottom
        # This allows the content to naturally fill the available space
    
    def add_model(self, model_path: Path):
        """Add 3D model to the grid"""
        # Check if model already exists
        if model_path in self.models:
            logger.debug(f"Model {model_path.name} already in grid")
            return
        
        self.models.append(model_path)
        
        # Create preview card with session priority
        card = Model3DPreviewCard(model_path, is_session_viewer=self._is_session_widget)
        card.clicked.connect(self.model_clicked.emit)
        card.selected.connect(self.model_selected.emit)
        
        # Add to grid
        row = len(self.cards) // self.columns
        col = len(self.cards) % self.columns
        
        self.grid_layout.addWidget(card, row, col)
        self.cards.append(card)
        
        # Update info
        self._update_info_label()
        
    
    def clear_models(self):
        """Clear all models from the grid with proper cleanup"""
        for card in self.cards:
            # Clean up 3D resources first
            card.cleanup()
            self.grid_layout.removeWidget(card)
            card.deleteLater()
        
        self.cards.clear()
        self.models.clear()
        self._update_info_label()
    
    def get_selected_models(self) -> List[Path]:
        """Get list of selected models"""
        selected = []
        for card in self.cards:
            if card._selected:
                selected.append(card.model_path)
        return selected
    
    def load_existing_models(self, directory: Path, extensions: List[str] = None):
        """Load existing models from directory"""
        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return
        
        if extensions is None:
            extensions = ['.glb', '.obj', '.fbx', '.gltf']
        
        model_files = []
        # Only look in the root directory, not subdirectories
        all_files = list(directory.iterdir())
        
        for file_path in all_files:
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                model_files.append(file_path)
        
        # Sort by modification time (newest first)
        model_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        
        # Add each model
        for model_path in model_files:
            self.add_model(model_path)
        
        logger.info(f"Loaded {len(model_files)} existing 3D models")
    
    def _update_info_label(self):
        """Update the info label text"""
        if not self.models:
            self.info_label.setText("No 3D models generated yet")
        else:
            selected_count = len(self.get_selected_models())
            if selected_count > 0:
                self.info_label.setText(f"{len(self.models)} models loaded • {selected_count} selected")
            else:
                self.info_label.setText(f"{len(self.models)} 3D models loaded")
    
    def apply_viewer_settings(self, settings):
        """Apply viewer settings to all 3D viewers in this widget"""
        try:
            logger.debug(f"Applying viewer settings to {len(self.cards)} 3D model cards")
            
            for card in self.cards:
                if hasattr(card, 'viewer_3d') and card.viewer_3d:
                    # Apply settings to each Simple3DViewer widget
                    # For now, this is a placeholder - Simple3DViewer would need
                    # settings support similar to Studio3DViewer
                    logger.debug(f"Applied settings to card for {card.model_path}")
                    
            logger.info(f"Applied viewer settings to {len(self.cards)} 3D model cards")
        except Exception as e:
            logger.error(f"Failed to apply viewer settings to Model3DPreviewWidget: {e}")


class ConsoleWidget(QTextEdit):
    """Console output widget with logging integration"""
    
    # Signal for thread-safe logging
    log_message = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        
        # Use JetBrains Mono font with fallbacks
        font = QFont()
        font.setFamilies(["JetBrains Mono", "Consolas", "Monaco", "Courier New", "monospace"])
        font.setPointSize(10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        
        # Console styling - focus and selection colors handled by accent color CSS
        self.setStyleSheet("""
            QTextEdit {
                background-color: #000000;
                color: #fafafa;
                border: 1px solid #3a3a3a;
                border-radius: 3px;
                padding: 8px;
                line-height: 1.0;
            }
            QScrollBar:vertical {
                background-color: #1a1a1a;
                width: 12px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #3a3a3a;
                border-radius: 6px;
                min-height: 20px;
            }
        """)
        
        self.max_lines = 1000
        self._auto_scroll = True
        
        # Connect signal for thread-safe updates
        self.log_message.connect(self._append_log_message)
        
    def setup_logging(self):
        """Setup logging handler to capture logs"""
        from loguru import logger
        
        # Add custom sink
        logger.add(
            self._log_to_console,
            format="{time:HH:mm:ss} | <level>{level: <8}</level> | {message}",
            level="DEBUG",
            colorize=False
        )
    
    def _log_to_console(self, message):
        """Log message to console - thread-safe via signal"""
        # Emit signal instead of direct update (thread-safe)
        self.log_message.emit(message)
    
    @Slot(str)
    def _append_log_message(self, message):
        """Actually append the log message (runs on main thread)"""
        message = message.strip()
        
        # Enhanced color coding with more detailed parsing
        if "| ERROR" in message or "| CRITICAL" in message:
            level_color = "#ef4444"  # Red
            icon = "❌"
        elif "| WARNING" in message:
            level_color = "#f59e0b"  # Amber
            icon = "⚠️"
        elif "| INFO" in message:
            level_color = "#10b981"  # Emerald
            icon = "ℹ️"
        elif "| DEBUG" in message:
            level_color = "#6b7280"  # Gray
            icon = "🔍"
        elif "✅" in message:
            level_color = "#22c55e"  # Green
            icon = ""
        elif "🎯" in message:
            level_color = "#3b82f6"  # Blue
            icon = ""
        elif "🧹" in message:
            level_color = "#8b5cf6"  # Purple
            icon = ""
        else:
            level_color = "#e5e7eb"  # Light gray
            icon = ""
        
        # Parse timestamp and level for better formatting
        parts = message.split(" | ", 2)
        if len(parts) >= 3:
            timestamp = parts[0]
            level = parts[1]
            content = parts[2]
            
            # Format as single line to eliminate div spacing
            html = f'<span style="color: #6b7280; font-size: 9px;">{timestamp}</span> <span style="color: {level_color}; font-weight: bold;">{level}</span> <span style="color: #fafafa;">{content}</span><br>'
        else:
            # Fallback for messages without standard format
            html = f'<span style="color: {level_color}; font-family: \'JetBrains Mono\', monospace;">{message}</span><br>'
        
        self.insertHtml(html)
        
        # Limit lines
        if self.document().blockCount() > self.max_lines:
            cursor = self.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor, 
                              self.document().blockCount() - self.max_lines)
            cursor.removeSelectedText()
        
        # Auto scroll
        if self._auto_scroll:
            scrollbar = self.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def set_auto_scroll(self, enabled: bool):
        """Enable/disable auto scroll"""
        self._auto_scroll = enabled