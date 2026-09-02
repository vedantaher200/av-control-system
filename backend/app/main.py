from datetime import datetime, timezone
from typing import Any, Literal
import os
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

try:
    from supabase import Client, create_client
except ImportError:  # Demo mode remains available without optional dependency installation.
    Client = Any
    create_client = None

app = FastAPI(title='AV Control System API', version='2.0.0', description='REST API for a simulated conference room AV control system.')
origins = [origin.strip() for origin in os.getenv('CORS_ORIGINS', '*').split(',') if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=['*'], allow_headers=['*'])

ROLES = {'Super Admin', 'Admin', 'Room Operator', 'Viewer'}
PROFILE: dict[str, Any] = {'id': 'demo-admin', 'full_name': 'Admin User', 'email': 'admin@avsystem.com', 'phone': '+91 98765 43210', 'job_title': 'AV System Administrator', 'department': 'AV Operations', 'company_name': 'AV Control System', 'work_location': 'Main Office', 'employee_id': 'AV-001', 'role': 'Admin', 'status': 'Active', 'bio': 'Responsible for keeping conference room systems reliable and ready for every meeting.', 'avatar_url': '', 'created_at': '2026-01-15T00:00:00+00:00', 'updated_at': '2026-09-02T00:00:00+00:00'}
ROOMS = [{'id': 1, 'name': 'Main Conference Room', 'location': 'HQ - 2nd Floor', 'capacity': 12, 'temperature': 23.8, 'humidity': 45, 'network_status': 'Connected', 'power_status': 'Stable', 'mode': 'Available'}]
DEVICES: list[dict[str, Any]] = [
    {'id': 1, 'room_id': 1, 'name': 'Main Display', 'category': 'Video', 'manufacturer': 'Samsung', 'model': '65 4K', 'connection_type': 'HDMI', 'state': 'On', 'health': 'Healthy', 'last_updated': 'Just now'},
    {'id': 2, 'room_id': 1, 'name': 'PTZ Conference Camera', 'category': 'Video', 'manufacturer': 'Logitech', 'model': 'Rally', 'connection_type': 'USB', 'state': 'Active', 'health': 'Healthy', 'last_updated': '18 min ago'},
    {'id': 3, 'room_id': 1, 'name': 'Wireless Microphone', 'category': 'Audio', 'manufacturer': 'Shure', 'model': 'MXW', 'connection_type': 'Wireless', 'state': 'Active', 'health': 'Healthy', 'last_updated': 'Just now'},
    {'id': 4, 'room_id': 1, 'name': 'Ceiling Speakers', 'category': 'Audio', 'manufacturer': 'Bose', 'model': 'Professional', 'connection_type': 'Network', 'state': 'On', 'health': 'Healthy', 'last_updated': 'Just now'},
    {'id': 5, 'room_id': 1, 'name': 'Room Lights', 'category': 'Lighting', 'manufacturer': 'Philips', 'model': 'Hue', 'connection_type': 'Network', 'state': 'On', 'health': 'Healthy', 'last_updated': '42 min ago'},
    {'id': 6, 'room_id': 1, 'name': 'AV Processor', 'category': 'Control', 'manufacturer': 'Crestron', 'model': 'AM-3100', 'connection_type': 'Network', 'state': 'Online', 'health': 'Healthy', 'last_updated': 'Just now'},
]
AUTOMATIONS = [{'id': i, 'name': name, 'description': description, 'trigger_type': 'Manual', 'is_active': True, 'last_run': None} for i, (name, description) in enumerate([('Start Meeting', 'Prepare the room for a meeting.'), ('Presentation Mode', 'Optimize display, audio, and lighting.'), ('Video Conference', 'Prepare the room for a video call.'), ('End Meeting', 'Return the room to standby.'), ('Emergency Standby', 'Safely pause applicable equipment.')], 1)]
ACTIVITIES: list[dict[str, Any]] = [{'id': 1, 'user': 'System', 'category': 'System', 'action': 'Health check', 'title': 'System health check completed', 'status': 'Success', 'details': 'All connected systems are operating normally.', 'time': '2 min ago'}]
NOTIFICATIONS: list[dict[str, Any]] = [{'id': 1, 'title': 'System health check completed', 'message': 'All connected systems are operating normally.', 'notification_type': 'System', 'is_read': False, 'time': '2 min ago'}]
SETTINGS: dict[str, Any] = {'system_name': 'AV Control System', 'organization_name': 'AV Control System', 'default_room_id': 1, 'temperature_warning_high': 27, 'humidity_warning_high': 65, 'notifications_enabled': True, 'default_audio_volume': 72, 'auto_refresh_seconds': 30}
AUDIO = {'volume': 72, 'muted': False, 'microphone_on': True, 'speakers_on': True}
SUPABASE: Client | None = None
if create_client and os.getenv('SUPABASE_URL') and (os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')):
    SUPABASE = create_client(os.environ['SUPABASE_URL'], os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.environ['SUPABASE_KEY'])

class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    full_name: str = Field(min_length=1, max_length=120)
    email: str = Field(pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$', max_length=200)
    phone: str = Field(default='', max_length=40)
    job_title: str = Field(default='', max_length=120)
    department: str = Field(default='', max_length=120)
    company_name: str = Field(default='', max_length=160)
    work_location: str = Field(default='', max_length=160)
    employee_id: str = Field(default='', max_length=50)
    role: Literal['Super Admin', 'Admin', 'Room Operator', 'Viewer'] = 'Admin'
    bio: str = Field(default='', max_length=500)
    avatar_url: str = Field(default='', max_length=4_000_000)

class StateUpdate(BaseModel):
    state: Literal['On', 'Active', 'Standby', 'Offline', 'Online']

class AudioUpdate(BaseModel):
    volume: int | None = Field(default=None, ge=0, le=100)
    muted: bool | None = None
    microphone_on: bool | None = None
    speakers_on: bool | None = None

class SettingsUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    system_name: str = Field(min_length=1, max_length=120)
    organization_name: str = Field(min_length=1, max_length=160)
    default_room_id: int = 1
    temperature_warning_high: float = Field(ge=0, le=60)
    humidity_warning_high: float = Field(ge=0, le=100)
    notifications_enabled: bool = True
    default_audio_volume: int = Field(ge=0, le=100)
    auto_refresh_seconds: int = Field(ge=5, le=3600)

def stamp() -> str:
    return datetime.now(timezone.utc).isoformat()

def current_role(x_user_role: str = Header(default='Admin')) -> str:
    role = x_user_role if x_user_role in ROLES else 'Viewer'
    return role

def require_control(role: str = Depends(current_role)) -> str:
    if role == 'Viewer':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Viewer accounts cannot control room systems.')
    return role

def require_admin(role: str = Depends(current_role)) -> str:
    if role not in {'Super Admin', 'Admin'}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Administrator permission is required.')
    return role

def record(title: str, category: str, details: str = '') -> None:
    item = {'id': int(datetime.now().timestamp() * 1000), 'user': PROFILE['full_name'], 'category': category, 'action': title, 'title': title, 'status': 'Success', 'details': details or f'{category} activity completed.', 'time': 'Just now'}
    ACTIVITIES.insert(0, item)
    if SETTINGS['notifications_enabled']:
        NOTIFICATIONS.insert(0, {'id': item['id'] + 1, 'title': title, 'message': item['details'], 'notification_type': category, 'is_read': False, 'time': 'Just now'})
    if SUPABASE:
        try:
            SUPABASE.table('activity_logs').insert({'category': category, 'action': title, 'title': title, 'status': 'Success', 'details': item['details']}).execute()
            if SETTINGS['notifications_enabled']:
                SUPABASE.table('notifications').insert({'title': title, 'message': item['details'], 'notification_type': category, 'is_read': False}).execute()
        except Exception:
            pass

@app.get('/api/health')
def health():
    return {'status': 'ok', 'mode': 'supabase' if SUPABASE else 'demo', 'database': 'connected' if SUPABASE else 'demo-fallback'}

@app.get('/api/dashboard')
def dashboard():
    return {'room': ROOMS[0], 'devices': DEVICES, 'automations': AUTOMATIONS, 'activities': ACTIVITIES[:20], 'notifications': NOTIFICATIONS[:20], 'profile': PROFILE, 'audio': AUDIO}

@app.get('/api/profile')
@app.get('/api/users/me')
def get_profile():
    if SUPABASE and PROFILE.get('id') != 'demo-admin':
        try:
            result = SUPABASE.table('profiles').select('*').eq('id', PROFILE['id']).limit(1).execute()
            if result.data:
                PROFILE.update(result.data[0])
        except Exception:
            pass
    return PROFILE

@app.put('/api/profile')
@app.patch('/api/users/me')
def update_profile(update: ProfileUpdate):
    PROFILE.update(update.model_dump())
    PROFILE['updated_at'] = stamp()
    if SUPABASE and PROFILE.get('id') != 'demo-admin':
        try:
            SUPABASE.table('profiles').update(update.model_dump()).eq('id', PROFILE['id']).execute()
        except Exception:
            pass
    record('User profile updated', 'Profile', 'Profile information was updated.')
    return PROFILE

@app.get('/api/users')
def list_users(role: str = Depends(require_admin)):
    return [PROFILE]

@app.get('/api/rooms')
def list_rooms():
    return ROOMS

@app.get('/api/devices')
def list_devices():
    return DEVICES

@app.patch('/api/devices/{device_id}/state')
def update_device(device_id: int, update: StateUpdate, role: str = Depends(require_control)):
    device = next((item for item in DEVICES if item['id'] == device_id), None)
    if not device:
        raise HTTPException(status_code=404, detail='Device not found.')
    device['state'] = update.state
    device['last_updated'] = 'Just now'
    record(f"{device['name']} set to {update.state}", 'Device')
    return device

@app.get('/api/automations')
def list_automations():
    return AUTOMATIONS

@app.post('/api/automations/{name}/run')
def run_automation(name: str, role: str = Depends(require_control)):
    automation = next((item for item in AUTOMATIONS if item['name'] == name), None)
    if not automation:
        raise HTTPException(status_code=404, detail='Automation not found.')
    standby = name in {'End Meeting', 'Emergency Standby'}
    for device in DEVICES:
        device['state'] = 'Standby' if standby else ('Active' if device['name'] == 'Wireless Microphone' else 'On')
        device['last_updated'] = 'Just now'
    ROOMS[0]['mode'] = 'Standby' if standby else name
    automation['last_run'] = stamp()
    record(f'{name} executed', 'Automation', f'{name} updated the simulated room and device states.')
    return {'status': 'success', 'automation': automation, 'devices': DEVICES, 'room': ROOMS[0]}

@app.get('/api/audio')
def get_audio():
    return AUDIO

@app.patch('/api/audio')
def update_audio(update: AudioUpdate, role: str = Depends(require_control)):
    AUDIO.update(update.model_dump(exclude_none=True))
    record('Audio controls updated', 'Audio', f"Volume {AUDIO['volume']}%, muted: {AUDIO['muted']}.")
    return AUDIO

@app.get('/api/monitoring')
def monitoring():
    online = sum(device['state'] not in {'Offline', 'Standby'} for device in DEVICES)
    return {'room': ROOMS[0], 'device_health': {'online': online, 'offline': len(DEVICES) - online, 'total': len(DEVICES)}, 'system_health': 'Operational', 'alerts': [], 'last_refreshed': stamp()}

@app.get('/api/activity-logs')
def activity_logs():
    return ACTIVITIES

@app.get('/api/notifications')
def list_notifications():
    return NOTIFICATIONS

@app.patch('/api/notifications/{notification_id}/read')
def read_notification(notification_id: int):
    notification = next((item for item in NOTIFICATIONS if item['id'] == notification_id), None)
    if not notification:
        raise HTTPException(status_code=404, detail='Notification not found.')
    notification['is_read'] = True
    return notification

@app.patch('/api/notifications/read-all')
def read_all_notifications():
    for notification in NOTIFICATIONS:
        notification['is_read'] = True
    return NOTIFICATIONS

@app.delete('/api/notifications')
def clear_notifications(role: str = Depends(require_control)):
    NOTIFICATIONS.clear()
    return {'status': 'success'}

@app.get('/api/settings')
def get_settings():
    return SETTINGS

@app.put('/api/settings')
def update_settings(update: SettingsUpdate, role: str = Depends(require_admin)):
    SETTINGS.update(update.model_dump())
    record('System settings updated', 'Settings')
    return SETTINGS
