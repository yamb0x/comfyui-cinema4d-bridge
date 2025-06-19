"""
Image to 3D Model Association System
Tracks relationships between generated images and their corresponding 3D models
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from loguru import logger


@dataclass
class ImageModelAssociation:
    """Association between an image and its 3D model"""
    image_path: str
    model_path: str
    image_name: str
    model_name: str
    created_at: str
    image_selected: bool = False
    model_selected: bool = False
    
    @classmethod
    def from_paths(cls, image_path: Path, model_path: Path) -> "ImageModelAssociation":
        """Create association from file paths"""
        return cls(
            image_path=str(image_path),
            model_path=str(model_path),
            image_name=image_path.name,
            model_name=model_path.name,
            created_at=datetime.now().isoformat(),
            image_selected=False,
            model_selected=False
        )


class ImageModelAssociationManager:
    """Manages associations between images and 3D models"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.associations_file = config_dir / "image_model_associations.json"
        self.associations: Dict[str, ImageModelAssociation] = {}
        self.load_associations()
    
    def load_associations(self):
        """Load associations from file"""
        try:
            if self.associations_file.exists():
                with open(self.associations_file, 'r') as f:
                    data = json.load(f)
                    self.associations = {
                        k: ImageModelAssociation(**v) for k, v in data.items()
                    }
                logger.info(f"Loaded {len(self.associations)} image-model associations")
            else:
                logger.debug("No existing associations file found, starting fresh")
        except Exception as e:
            logger.error(f"Failed to load associations: {e}")
            self.associations = {}
    
    def save_associations(self):
        """Save associations to file"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.associations_file, 'w') as f:
                data = {k: asdict(v) for k, v in self.associations.items()}
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(self.associations)} associations")
        except Exception as e:
            logger.error(f"Failed to save associations: {e}")
    
    def create_association(self, image_path: Path, model_path: Path) -> str:
        """Create new association between image and model"""
        association = ImageModelAssociation.from_paths(image_path, model_path)
        key = self._get_association_key(image_path)
        self.associations[key] = association
        self.save_associations()
        logger.info(f"Created association: {image_path.name} → {model_path.name}")
        return key
    
    def get_model_for_image(self, image_path: Path) -> Optional[Path]:
        """Get the 3D model path for a given image"""
        key = self._get_association_key(image_path)
        if key in self.associations:
            model_path = Path(self.associations[key].model_path)
            if model_path.exists():
                return model_path
            else:
                logger.warning(f"Associated model no longer exists: {model_path}")
        return None
    
    def get_image_for_model(self, model_path: Path) -> Optional[Path]:
        """Get the source image path for a given 3D model"""
        for association in self.associations.values():
            if Path(association.model_path) == model_path:
                image_path = Path(association.image_path)
                if image_path.exists():
                    return image_path
                else:
                    logger.warning(f"Associated image no longer exists: {image_path}")
        return None
    
    def set_image_selected(self, image_path: Path, selected: bool):
        """Mark an image as selected/deselected"""
        key = self._get_association_key(image_path)
        if key in self.associations:
            self.associations[key].image_selected = selected
            self.save_associations()
            logger.debug(f"Image {image_path.name} selection: {selected}")
    
    def set_model_selected(self, model_path: Path, selected: bool):
        """Mark a model as selected/deselected"""
        for key, association in self.associations.items():
            if Path(association.model_path) == model_path:
                association.model_selected = selected
                self.save_associations()
                logger.debug(f"Model {model_path.name} selection: {selected}")
                break
    
    def get_selected_images(self) -> List[Path]:
        """Get all currently selected images"""
        selected = []
        for association in self.associations.values():
            if association.image_selected:
                image_path = Path(association.image_path)
                if image_path.exists():
                    selected.append(image_path)
        return selected
    
    def get_selected_models(self) -> List[Path]:
        """Get all currently selected models"""
        selected = []
        for association in self.associations.values():
            if association.model_selected:
                model_path = Path(association.model_path)
                if model_path.exists():
                    selected.append(model_path)
        return selected
    
    def get_images_with_models(self) -> List[Path]:
        """Get all images that have corresponding 3D models"""
        images_with_models = []
        for association in self.associations.values():
            image_path = Path(association.image_path)
            model_path = Path(association.model_path)
            if image_path.exists() and model_path.exists():
                images_with_models.append(image_path)
        return images_with_models
    
    def get_models_for_selected_images(self) -> List[Path]:
        """Get 3D models corresponding to currently selected images"""
        models = []
        for association in self.associations.values():
            if association.image_selected:
                model_path = Path(association.model_path)
                if model_path.exists():
                    models.append(model_path)
        return models
    
    def auto_detect_associations(self, images_dir: Path, models_dir: Path):
        """Auto-detect associations based on filename patterns"""
        logger.info("Auto-detecting image-model associations...")
        
        # Get all images and models
        image_files = []
        for ext in ['.png', '.jpg', '.jpeg']:
            image_files.extend(images_dir.glob(f"*{ext}"))
        
        model_files = []
        for ext in ['.glb', '.obj', '.fbx', '.gltf']:
            model_files.extend(models_dir.glob(f"*{ext}"))
        
        # Try to match based on similar naming patterns
        new_associations = 0
        for image_path in image_files:
            if self.get_model_for_image(image_path):
                continue  # Already has association
            
            # Look for models with similar names
            image_stem = image_path.stem.lower()
            for model_path in model_files:
                model_stem = model_path.stem.lower()
                
                # Basic name matching (can be improved with more sophisticated logic)
                if self._names_match(image_stem, model_stem):
                    self.create_association(image_path, model_path)
                    new_associations += 1
                    break
        
        if new_associations > 0:
            logger.info(f"Auto-detected {new_associations} new associations")
        else:
            logger.info("No new associations detected")
    
    def _get_association_key(self, image_path: Path) -> str:
        """Generate a unique key for an image"""
        return f"{image_path.stem}_{image_path.suffix}"
    
    def _names_match(self, image_name: str, model_name: str) -> bool:
        """Check if image and model names likely correspond to each other"""
        # Remove common prefixes/suffixes and numbers
        import re
        
        # Remove timestamps and common patterns
        image_clean = re.sub(r'[_-]?\d+[_-]?', '', image_name)
        model_clean = re.sub(r'[_-]?\d+[_-]?', '', model_name)
        
        # Remove common prefixes
        for prefix in ['comfyui_', 'hy3d_', 'image_', 'model_']:
            image_clean = image_clean.replace(prefix, '')
            model_clean = model_clean.replace(prefix, '')
        
        # Check if they have significant overlap
        if len(image_clean) > 3 and len(model_clean) > 3:
            return image_clean in model_clean or model_clean in image_clean
        
        return False
    
    def cleanup_missing_files(self):
        """Remove associations where files no longer exist"""
        to_remove = []
        for key, association in self.associations.items():
            image_exists = Path(association.image_path).exists()
            model_exists = Path(association.model_path).exists()
            
            if not image_exists or not model_exists:
                to_remove.append(key)
                logger.debug(f"Removing association for missing files: {association.image_name} → {association.model_name}")
        
        for key in to_remove:
            del self.associations[key]
        
        if to_remove:
            self.save_associations()
            logger.info(f"Cleaned up {len(to_remove)} associations with missing files")
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about current associations"""
        return {
            "total_associations": len(self.associations),
            "selected_images": len(self.get_selected_images()),
            "selected_models": len(self.get_selected_models()),
            "images_with_models": len(self.get_images_with_models())
        }