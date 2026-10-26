from app.core.exceptions import ConflictError, NotFoundError


class RoomNotFound(NotFoundError):
    code = "room_not_found"
    message = "Room not found"

class RoomConflict(ConflictError):
    code = "room_conflict"
    message = "Room conflict"
    
    
class BuildingNotFound(NotFoundError):
    code = "building_not_found"
    message = "Building not found"
    
class BuildingConflict(ConflictError):
    code = "building_conflict"
    message = "Building conflict"