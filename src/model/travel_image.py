from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class TravelImage:
    place_id: int
    s3_object_key: str
    original_name: str
    file_name: str
    file_type: str
    file_size: float
    created_at: datetime
    updated_at: datetime
    is_thumbnail: bool
    api_file_url: str
    
    travel_image_id: Optional[int] = None
    serial_number: Optional[str] = None
