"""
Texture Atlas System for 2D Game Engine

This module provides texture atlas functionality for optimizing rendering performance
by packing multiple textures into single atlas textures.
"""
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any

from engine.assets.typesg.asset_types import TexturePackingStrategy

@dataclass
class AtlasRegion:
    """Region within a texture atlas."""
    name: str
    x: int
    y: int
    width: int
    height: int
    rotated: bool = False
    atlas_id: str = ""
    
    @property
    def uv_coords(self) -> Tuple[float, float, float, float]:
        """Get UV coordinates for this region (u1, v1, u2, v2)."""
        # These would be calculated based on atlas dimensions
        return (0.0, 0.0, 1.0, 1.0)  # Placeholder

@dataclass
class TextureInfo:
    """Information about a texture to be packed."""
    name: str
    width: int
    height: int
    data: Any  # Actual texture data
    padding: int = 1

class Rectangle:
    """Rectangle for packing algorithms."""
    
    def __init__(self, x: int = 0, y: int = 0, width: int = 0, height: int = 0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.used = False
    
    def fits(self, width: int, height: int) -> bool:
        """Check if a texture of given size fits in this rectangle."""
        return width <= self.width and height <= self.height
    
    def split(self, width: int, height: int) -> List['Rectangle']:
        """Split rectangle after placing a texture."""
        result = []
        
        # Right rectangle
        if self.x + width < self.x + self.width:
            result.append(Rectangle(
                self.x + width, self.y, 
                self.width - width, height
            ))
        
        # Bottom rectangle
        if self.y + height < self.y + self.height:
            result.append(Rectangle(
                self.x, self.y + height,
                self.width, self.height - height
            ))
        
        return result

class TextureAtlas:
    """
    Texture atlas for packing multiple textures into single atlas textures.
    
    Features:
    - Multiple packing strategies
    - Automatic atlas sizing
    - UV coordinate generation
    - Runtime texture addition
    - Multiple atlas support
    """
    
    def __init__(self, 
                 max_width: int = 2048,
                 max_height: int = 2048,
                 padding: int = 1,
                 strategy: TexturePackingStrategy = TexturePackingStrategy.BEST_FIT):
        """
        Initialize texture atlas.
        
        Args:
            max_width: Maximum atlas width
            max_height: Maximum atlas height
            padding: Padding between textures
            strategy: Packing strategy to use
        """
        self.max_width = max_width
        self.max_height = max_height
        self.padding = padding
        self.strategy = strategy
        
        # Atlas management
        self.atlases: Dict[str, Any] = {}  # Atlas ID -> Atlas data
        self.regions: Dict[str, AtlasRegion] = {}  # Texture name -> Region
        self.free_rectangles: Dict[str, List[Rectangle]] = {}  # Atlas ID -> Free rects
        
        # Statistics
        self.atlas_count = 0
        self.total_textures = 0
        self.efficiency = 0.0
    
    def pack_textures(self, textures: List[TextureInfo]) -> bool:
        """
        Pack multiple textures into atlases.
        
        Args:
            textures: List of textures to pack
            
        Returns:
            True if all textures were packed successfully
        """
        # Sort textures by area (largest first) for better packing
        sorted_textures = sorted(textures, 
                               key=lambda t: t.width * t.height, 
                               reverse=True)
        
        packed_count = 0
        
        for texture in sorted_textures:
            if self.add_texture(texture):
                packed_count += 1
        
        self.total_textures = len(textures)
        self._calculate_efficiency()
        
        return packed_count == len(textures)
    
    def add_texture(self, texture: TextureInfo) -> bool:
        """
        Add a single texture to the atlas.
        
        Args:
            texture: Texture to add
            
        Returns:
            True if texture was successfully added
        """
        # Try to fit in existing atlases
        for atlas_id in self.atlases:
            if self._try_fit_texture(atlas_id, texture):
                return True
        
        # Create new atlas
        atlas_id = f"atlas_{self.atlas_count}"
        self.atlas_count += 1
        
        self._create_atlas(atlas_id)
        return self._try_fit_texture(atlas_id, texture)
    
    def get_region(self, texture_name: str) -> Optional[AtlasRegion]:
        """Get atlas region for a texture."""
        return self.regions.get(texture_name)
    
    def get_uv_coordinates(self, texture_name: str) -> Optional[Tuple[float, float, float, float]]:
        """Get UV coordinates for a texture."""
        region = self.get_region(texture_name)
        if region:
            return region.uv_coords
        return None
    
    def remove_texture(self, texture_name: str) -> bool:
        """
        Remove a texture from the atlas.
        Note: This creates fragmentation and may require atlas rebuilding.
        """
        if texture_name not in self.regions:
            return False
        
        region = self.regions[texture_name]
        
        # Add the region back to free rectangles
        if region.atlas_id in self.free_rectangles:
            self.free_rectangles[region.atlas_id].append(
                Rectangle(region.x, region.y, region.width, region.height)
            )
        
        del self.regions[texture_name]
        return True
    
    def rebuild_atlas(self, atlas_id: str) -> bool:
        """Rebuild an atlas to reduce fragmentation."""
        # Get all textures in this atlas
        atlas_textures = [
            region for region in self.regions.values()
            if region.atlas_id == atlas_id
        ]
        
        if not atlas_textures:
            return True
        
        # Clear the atlas
        self.free_rectangles[atlas_id] = [
            Rectangle(0, 0, self.max_width, self.max_height)
        ]
        
        # Re-pack textures
        for region in atlas_textures:
            # Would need access to original texture data here
            pass
        
        return True
    
    def get_atlas_info(self) -> Dict[str, Any]:
        """Get information about all atlases."""
        return {
            'atlas_count': self.atlas_count,
            'total_textures': self.total_textures,
            'efficiency': self.efficiency,
            'atlases': list(self.atlases.keys()),
            'regions': len(self.regions)
        }
    
    def _create_atlas(self, atlas_id: str):
        """Create a new atlas."""
        self.atlases[atlas_id] = {
            'width': self.max_width,
            'height': self.max_height,
            'data': None  # Would hold actual texture data
        }
        
        self.free_rectangles[atlas_id] = [
            Rectangle(0, 0, self.max_width, self.max_height)
        ]
    
    def _try_fit_texture(self, atlas_id: str, texture: TextureInfo) -> bool:
        """Try to fit a texture in the specified atlas."""
        required_width = texture.width + self.padding * 2
        required_height = texture.height + self.padding * 2
        
        if self.strategy == TexturePackingStrategy.BEST_FIT:
            return self._fit_best_fit(atlas_id, texture, required_width, required_height)
        elif self.strategy == TexturePackingStrategy.BOTTOM_LEFT:
            return self._fit_bottom_left(atlas_id, texture, required_width, required_height)
        else:
            # Default to best fit
            return self._fit_best_fit(atlas_id, texture, required_width, required_height)
    
    def _fit_best_fit(self, atlas_id: str, texture: TextureInfo, 
                     required_width: int, required_height: int) -> bool:
        """Fit texture using best-fit strategy."""
        free_rects = self.free_rectangles[atlas_id]
        best_rect = None
        best_short_side = float('inf')
        best_long_side = float('inf')
        
        for rect in free_rects:
            if rect.fits(required_width, required_height):
                leftover_horizontal = rect.width - required_width
                leftover_vertical = rect.height - required_height
                short_side = min(leftover_horizontal, leftover_vertical)
                long_side = max(leftover_horizontal, leftover_vertical)
                
                if short_side < best_short_side or \
                   (short_side == best_short_side and long_side < best_long_side):
                    best_rect = rect
                    best_short_side = short_side
                    best_long_side = long_side
        
        if best_rect:
            self._place_texture(atlas_id, texture, best_rect, required_width, required_height)
            return True
        
        return False
    
    def _fit_bottom_left(self, atlas_id: str, texture: TextureInfo,
                        required_width: int, required_height: int) -> bool:
        """Fit texture using bottom-left strategy."""
        free_rects = self.free_rectangles[atlas_id]
        best_rect = None
        best_y = float('inf')
        best_x = float('inf')
        
        for rect in free_rects:
            if rect.fits(required_width, required_height):
                if rect.y < best_y or (rect.y == best_y and rect.x < best_x):
                    best_rect = rect
                    best_y = rect.y
                    best_x = rect.x
        
        if best_rect:
            self._place_texture(atlas_id, texture, best_rect, required_width, required_height)
            return True
        
        return False
    
    def _place_texture(self, atlas_id: str, texture: TextureInfo, 
                      rect: Rectangle, width: int, height: int):
        """Place texture in the specified rectangle."""
        # Create region
        region = AtlasRegion(
            name=texture.name,
            x=rect.x + self.padding,
            y=rect.y + self.padding,
            width=texture.width,
            height=texture.height,
            atlas_id=atlas_id
        )
        
        self.regions[texture.name] = region
        
        # Remove used rectangle
        self.free_rectangles[atlas_id].remove(rect)
        
        # Add split rectangles
        split_rects = rect.split(width, height)
        self.free_rectangles[atlas_id].extend(split_rects)
        
        # Merge adjacent rectangles (optimization)
        self._merge_rectangles(atlas_id)
    
    def _merge_rectangles(self, atlas_id: str):
        """Merge adjacent free rectangles to reduce fragmentation."""
        # Simple implementation - could be optimized
        free_rects = self.free_rectangles[atlas_id]
        
        i = 0
        while i < len(free_rects):
            j = i + 1
            while j < len(free_rects):
                rect1 = free_rects[i]
                rect2 = free_rects[j]
                
                # Check if rectangles can be merged horizontally
                if (rect1.x == rect2.x and rect1.width == rect2.width and
                    rect1.y + rect1.height == rect2.y):
                    # Merge vertically
                    rect1.height += rect2.height
                    free_rects.remove(rect2)
                    continue
                
                # Check if rectangles can be merged vertically
                if (rect1.y == rect2.y and rect1.height == rect2.height and
                    rect1.x + rect1.width == rect2.x):
                    # Merge horizontally
                    rect1.width += rect2.width
                    free_rects.remove(rect2)
                    continue
                
                j += 1
            i += 1
    
    def _calculate_efficiency(self):
        """Calculate atlas packing efficiency."""
        if not self.atlases:
            self.efficiency = 0.0
            return
        
        total_atlas_area = len(self.atlases) * self.max_width * self.max_height
        used_area = sum(
            region.width * region.height 
            for region in self.regions.values()
        )
        
        self.efficiency = (used_area / total_atlas_area) * 100 if total_atlas_area > 0 else 0.0
