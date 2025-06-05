"""
Font loading and management utilities
"""

from pathlib import Path
from PySide6.QtGui import QFontDatabase, QFont
from loguru import logger


class FontManager:
    """Manages custom font loading"""
    
    def __init__(self):
        self.font_db = QFontDatabase()
        self.loaded_fonts = {}
        
    def load_font(self, font_path: Path, family_name: str) -> bool:
        """Load a font from file"""
        try:
            if not font_path.exists():
                logger.warning(f"Font file not found: {font_path}")
                return False
                
            font_id = self.font_db.addApplicationFont(str(font_path))
            if font_id == -1:
                logger.error(f"Failed to load font: {font_path}")
                return False
                
            families = self.font_db.applicationFontFamilies(font_id)
            if families:
                actual_family = families[0]
                self.loaded_fonts[family_name] = actual_family
                logger.info(f"Loaded font '{actual_family}' as '{family_name}'")
                return True
            else:
                logger.error(f"No font families found in: {font_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error loading font {font_path}: {e}")
            return False
    
    def get_font(self, family_name: str, size: int = 12, weight: QFont.Weight = QFont.Normal) -> QFont:
        """Get a QFont instance with the specified family"""
        if family_name in self.loaded_fonts:
            font = QFont(self.loaded_fonts[family_name], size, weight)
        else:
            # Fallback to system fonts
            if family_name.lower() == 'kalice':
                font = QFont('serif', size, weight)
            elif family_name.lower() == 'basis grotesque':
                font = QFont('sans-serif', size, weight)
            else:
                font = QFont('sans-serif', size, weight)
                
        return font
    
    def is_loaded(self, family_name: str) -> bool:
        """Check if font family is loaded"""
        return family_name in self.loaded_fonts


def load_project_fonts(font_manager: FontManager, base_dir: Path) -> None:
    """Load all project fonts"""
    fonts_dir = base_dir / "fonts"
    
    if not fonts_dir.exists():
        logger.warning(f"Fonts directory not found: {fonts_dir}")
        return
    
    # Try to convert WOFF fonts to TTF or use system fonts as fallback
    # Qt has better support for TTF/OTF than WOFF
    
    # Check what fonts are actually available
    available_fonts = list(fonts_dir.glob("*"))
    logger.info(f"Available font files: {[f.name for f in available_fonts]}")
    
    # Since Qt doesn't handle WOFF well, we'll use CSS font-family fallbacks
    # The stylesheet will handle the font selection
    logger.info("Using CSS fallback fonts for typography")
    
    # For now, we'll rely on system fonts with proper CSS fallbacks:
    # 'Basis Grotesque' will fallback to 'Arial', 'Helvetica', sans-serif
    # 'Kalice' will fallback to 'Georgia', 'Times', serif


# Global font manager instance
_font_manager = None

def get_font_manager() -> FontManager:
    """Get the global font manager instance"""
    global _font_manager
    if _font_manager is None:
        _font_manager = FontManager()
    return _font_manager