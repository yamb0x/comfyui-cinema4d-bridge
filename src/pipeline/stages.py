"""
Pipeline stages for the ComfyUI to Cinema4D workflow
"""

import asyncio
import random
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod
from datetime import datetime

from loguru import logger

from core.config_adapter import AppConfig
from core.workflow_manager import WorkflowManager
from mcp.comfyui_client import ComfyUIClient
from mcp.cinema4d_client import Cinema4DClient
from utils.logger import LoggerMixin


class PipelineStage(ABC, LoggerMixin):
    """Base class for pipeline stages"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self._running = False
        self._current_task = None
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> bool:
        """Execute the pipeline stage"""
        pass
    
    async def cancel(self):
        """Cancel current execution"""
        self._running = False
        if self._current_task:
            self._current_task.cancel()
            try:
                await self._current_task
            except asyncio.CancelledError:
                pass
    
    @property
    def is_running(self) -> bool:
        """Check if stage is currently running"""
        return self._running


class ImageGenerationStage(PipelineStage):
    """Stage 1: Generate images from text prompts"""
    
    def __init__(self, comfyui_client: ComfyUIClient, 
                 workflow_manager: WorkflowManager,
                 config: AppConfig):
        super().__init__(config)
        self.comfyui_client = comfyui_client
        self.workflow_manager = workflow_manager
    
    async def execute(self, params: Dict[str, Any], 
                      batch_size: int = 1) -> bool:
        """
        Generate images based on parameters
        
        Args:
            params: Generation parameters including prompts
            batch_size: Number of images to generate
            
        Returns:
            Success status
        """
        if self._running:
            self.logger.warning("Image generation already running")
            return False
        
        self._running = True
        
        try:
            # Load workflow
            workflow_name = self.config.workflows.image_workflow
            workflow = self.workflow_manager.load_workflow(workflow_name)
            if not workflow:
                self.logger.error(f"Failed to load workflow: {workflow_name}")
                return False
            
            # Validate workflow
            is_valid, errors = self.workflow_manager.validate_workflow(workflow)
            if not is_valid:
                self.logger.error(f"Invalid workflow: {errors}")
                return False
            
            # Generate seed if random
            if params.get("seed", -1) < 0:
                params["seed"] = random.randint(0, 999999999)
                self.logger.info(f"Using random seed: {params['seed']}")
            
            # Inject parameters
            workflow = self.workflow_manager.inject_parameters(workflow, params)
            
            # Execute for each batch item
            prompt_ids = []
            for i in range(batch_size):
                # Update seed for variation
                if i > 0:
                    workflow_copy = self.workflow_manager.inject_parameters(
                        workflow, {"seed": params["seed"] + i}
                    )
                else:
                    workflow_copy = workflow
                
                # Queue prompt
                prompt_id = await self.comfyui_client.queue_prompt(workflow_copy)
                if prompt_id:
                    prompt_ids.append(prompt_id)
                    self.logger.info(f"Queued image {i+1}/{batch_size}: {prompt_id}")
                else:
                    self.logger.error(f"Failed to queue image {i+1}")
            
            # Wait for completion
            if prompt_ids:
                self.logger.info(f"Generating {len(prompt_ids)} images...")
                # Monitor progress through callbacks
                return True
            else:
                return False
            
        except Exception as e:
            self.logger.exception(f"Image generation failed: {e}")
            return False
        finally:
            self._running = False


class Model3DGenerationStage(PipelineStage):
    """Stage 2: Generate 3D models from images"""
    
    def __init__(self, comfyui_client: ComfyUIClient,
                 workflow_manager: WorkflowManager,
                 config: AppConfig):
        super().__init__(config)
        self.comfyui_client = comfyui_client
        self.workflow_manager = workflow_manager
    
    async def execute(self, image_path: Path,
                      params: Dict[str, Any]) -> bool:
        """
        Generate 3D model from image
        
        Args:
            image_path: Path to input image
            params: 3D generation parameters
            
        Returns:
            Success status
        """
        if self._running:
            self.logger.warning("3D generation already running")
            return False
        
        self._running = True
        
        try:
            # Load 3D generation workflow
            workflow_name = self.config.workflows.model_3d_workflow
            workflow = self.workflow_manager.load_workflow(workflow_name)
            if not workflow:
                self.logger.error(f"Failed to load workflow: {workflow_name}")
                return False
            
            # Find image loader node and update path
            image_updated = False
            for node_id, node_data in workflow.items():
                if node_data.get("class_type") == "LoadImage":
                    node_data["inputs"]["image"] = str(image_path)
                    image_updated = True
                    self.logger.debug(f"Updated image path in node {node_id}")
                    break
            
            if not image_updated:
                self.logger.error("No LoadImage node found in workflow")
                return False
            
            # Update 3D generation parameters
            for node_id, node_data in workflow.items():
                class_type = node_data.get("class_type", "")
                
                # Update Hy3D specific nodes based on parameters
                if "Hy3D" in class_type or "3D" in class_type:
                    inputs = node_data.get("inputs", {})
                    
                    # Map parameters to node inputs
                    if "mesh_density" in params and "density" in inputs:
                        inputs["density"] = params["mesh_density"]
                    
                    if "texture_resolution" in params and "texture_size" in inputs:
                        inputs["texture_size"] = params["texture_resolution"]
                    
                    if "normal_map" in params and "generate_normal" in inputs:
                        inputs["generate_normal"] = params["normal_map"]
                    
                    if "optimize_mesh" in params and "optimize" in inputs:
                        inputs["optimize"] = params["optimize_mesh"]
            
            # Queue prompt
            prompt_id = await self.comfyui_client.queue_prompt(workflow)
            if prompt_id:
                self.logger.info(f"Generating 3D model from {image_path.name}")
                return True
            else:
                return False
            
        except Exception as e:
            self.logger.exception(f"3D generation failed: {e}")
            return False
        finally:
            self._running = False


class SceneAssemblyStage(PipelineStage):
    """Stage 3: Import and arrange 3D models in Cinema4D"""
    
    def __init__(self, c4d_client: Cinema4DClient, config: AppConfig):
        super().__init__(config)
        self.c4d_client = c4d_client
        self.imported_objects: List[str] = []
    
    async def execute(self, models: List[Path]) -> bool:
        """
        Import multiple models into Cinema4D scene
        
        Args:
            models: List of model paths to import
            
        Returns:
            Success status
        """
        if self._running:
            self.logger.warning("Scene assembly already running")
            return False
        
        self._running = True
        success_count = 0
        
        try:
            for i, model_path in enumerate(models):
                if not model_path.exists():
                    self.logger.warning(f"Model not found: {model_path}")
                    continue
                
                # Calculate position for grid layout
                grid_size = 500  # Units between objects
                row = i // 4
                col = i % 4
                position = (col * grid_size, 0, row * grid_size)
                
                # Import model
                success = await self.c4d_client.import_obj(
                    model_path,
                    position=position,
                    scale=1.0
                )
                
                if success:
                    success_count += 1
                    self.imported_objects.append(model_path.stem)
                    self.logger.info(f"Imported {model_path.name} at position {position}")
                else:
                    self.logger.error(f"Failed to import {model_path.name}")
            
            self.logger.info(f"Successfully imported {success_count}/{len(models)} models")
            return success_count > 0
            
        except Exception as e:
            self.logger.exception(f"Scene assembly failed: {e}")
            return False
        finally:
            self._running = False
    
    async def import_model(self, model_path: Path,
                          position: tuple[float, float, float] = (0, 0, 0),
                          scale: float = 1.0) -> bool:
        """Import single model"""
        if not model_path.exists():
            self.logger.error(f"Model not found: {model_path}")
            return False
        
        success = await self.c4d_client.import_obj(model_path, position, scale)
        if success:
            self.imported_objects.append(model_path.stem)
        
        return success
    
    async def apply_procedural_setup(self, script_name: str,
                                   target_objects: List[str] = None) -> bool:
        """Apply procedural Python script to objects"""
        # Load script from library
        script_path = self.config.base_dir / "scripts" / "c4d" / f"{script_name}.py"
        
        if not script_path.exists():
            self.logger.error(f"Script not found: {script_path}")
            return False
        
        try:
            with open(script_path, "r") as f:
                script_content = f.read()
            
            # Replace target objects placeholder
            if target_objects:
                objects_str = str(target_objects)
                script_content = script_content.replace(
                    "TARGET_OBJECTS = []",
                    f"TARGET_OBJECTS = {objects_str}"
                )
            
            # Execute script
            result = await self.c4d_client.execute_python(script_content)
            return result.get("success", False)
            
        except Exception as e:
            self.logger.exception(f"Failed to apply procedural setup: {e}")
            return False


class ExportStage(PipelineStage):
    """Stage 4: Export Cinema4D project"""
    
    def __init__(self, c4d_client: Cinema4DClient, config: AppConfig):
        super().__init__(config)
        self.c4d_client = c4d_client
    
    async def execute(self, project_path: Path,
                      copy_textures: bool = True,
                      create_backup: bool = True,
                      generate_report: bool = True) -> bool:
        """
        Export Cinema4D project with options
        
        Args:
            project_path: Path to save project
            copy_textures: Copy textures to project folder
            create_backup: Create backup of project
            generate_report: Generate scene report
            
        Returns:
            Success status
        """
        if self._running:
            self.logger.warning("Export already running")
            return False
        
        self._running = True
        
        try:
            # Create project directory
            project_dir = project_path.parent
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # Save project
            success = await self.c4d_client.save_project(project_path)
            if not success:
                self.logger.error("Failed to save Cinema4D project")
                return False
            
            # Copy textures if requested
            if copy_textures:
                textures_dir = project_dir / "tex"
                textures_dir.mkdir(exist_ok=True)
                self.logger.info(f"Created textures directory: {textures_dir}")
                
                # Execute texture collection script
                script = f"""
import c4d
from c4d import documents
import shutil
from pathlib import Path

def collect_textures():
    doc = documents.GetActiveDocument()
    if not doc:
        return False
    
    textures_dir = Path(r"{textures_dir}")
    collected = 0
    
    # Iterate through all materials
    mat = doc.GetFirstMaterial()
    while mat:
        # Check various texture channels
        for channel_id in [c4d.MATERIAL_COLOR_SHADER, c4d.MATERIAL_LUMINANCE_SHADER,
                          c4d.MATERIAL_DIFFUSION_SHADER, c4d.MATERIAL_BUMP_SHADER,
                          c4d.MATERIAL_NORMAL_SHADER, c4d.MATERIAL_ALPHA_SHADER]:
            shader = mat[channel_id]
            if shader and shader.GetType() == c4d.Xbitmap:
                texture_path = shader[c4d.BITMAPSHADER_FILENAME]
                if texture_path:
                    src = Path(texture_path)
                    if src.exists():
                        dst = textures_dir / src.name
                        shutil.copy2(src, dst)
                        # Update path in material
                        shader[c4d.BITMAPSHADER_FILENAME] = str(dst)
                        collected += 1
        
        mat = mat.GetNext()
    
    c4d.EventAdd()
    print(f"Collected {{collected}} textures")
    return True

if __name__ == '__main__':
    collect_textures()
"""
                await self.c4d_client.execute_python(script)
            
            # Create backup if requested
            if create_backup:
                backup_dir = project_dir / "backup"
                backup_dir.mkdir(exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = backup_dir / f"{project_path.stem}_{timestamp}.c4d"
                
                import shutil
                shutil.copy2(project_path, backup_path)
                self.logger.info(f"Created backup: {backup_path}")
            
            # Generate report if requested
            if generate_report:
                report_path = project_dir / f"{project_path.stem}_report.txt"
                
                # Get scene information
                objects = await self.c4d_client.get_scene_objects()
                
                # Write report
                with open(report_path, "w") as f:
                    f.write(f"Cinema4D Project Report\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Project: {project_path}\n")
                    f.write(f"\n{'='*50}\n\n")
                    
                    f.write(f"Scene Statistics:\n")
                    f.write(f"- Total objects: {len(objects)}\n")
                    f.write(f"- Project size: {project_path.stat().st_size / 1024 / 1024:.2f} MB\n")
                    
                    f.write(f"\n{'='*50}\n\n")
                    f.write(f"Object Hierarchy:\n")
                    
                    def write_object(obj, indent=0):
                        f.write(f"{'  ' * indent}- {obj['name']} ({obj['type']})\n")
                        for child in obj.get('children', []):
                            write_object(child, indent + 1)
                    
                    for obj in objects:
                        write_object(obj)
                
                self.logger.info(f"Generated report: {report_path}")
            
            self.logger.info(f"Export completed: {project_path}")
            return True
            
        except Exception as e:
            self.logger.exception(f"Export failed: {e}")
            return False
        finally:
            self._running = False