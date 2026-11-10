from app.core.exceptions import ConflictError, NotFoundError


class RoomNotFound(NotFoundError):
    code = "room_not_found"
    detail = "Room not found"

class RoomConflict(ConflictError):
    code = "room_conflict"
    detail = "Room conflict"
    
class BuildingNotFound(NotFoundError):
    code = "building_not_found"
    detail = "Building not found"
    
class BuildingConflict(ConflictError):
    code = "building_conflict"
    detail = "Building conflict"