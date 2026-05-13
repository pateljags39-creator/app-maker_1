from fastapi import FastAPI, APIRouter
app = FastAPI()
router = APIRouter(prefix='/api')

_NOTES = []

@router.get('/notes')
def list_notes():
    return _NOTES

@router.post('/notes')
def create_note(note: dict):
    _NOTES.append(note)
    return note

@router.delete('/notes/{note_id}')
def delete_note(note_id: int):
    return {'deleted': note_id}

app.include_router(router)
