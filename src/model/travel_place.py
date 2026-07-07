from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from model.location import *

@dataclass
class TravelPlace:
    location: Location
    content_type_id: int
    place_name: str
    address: str
    api_content_id: int
    api_created_at: datetime
    api_updated_at: datetime
    created_at: datetime
    updated_at: datetime
    detail_address: Optional[str] = None
    use_time: Optional[str] = None
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    homepage: Optional[str] = None
    phone_number: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    description: Optional[str] = None
    


