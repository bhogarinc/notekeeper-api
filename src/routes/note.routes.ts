/**
 * Note Routes
 * @module routes/notes
 */

import { Router } from 'express';
import { NoteController } from '../controllers/note.controller';
import { 
  createNoteSchema, 
  updateNoteSchema, 
  searchNotesSchema,
  noteIdSchema,
  togglePinSchema,
  toggleArchiveSchema
} from '../validators/note.validator';
import { validate, validateParams } from '../middleware/validation.middleware';
import { authenticate } from '../middleware/auth.middleware';

const router = Router();
const noteController = new NoteController();

// Apply authentication to all note routes
router.use(authenticate);

// Search and list notes
router.get('/', validate({ query: searchNotesSchema }), noteController.search);

// Create note
router.post('/', validate({ body: createNoteSchema }), noteController.create);

// Get single note
router.get('/:id', validateParams(noteIdSchema), noteController.getById);

// Update note
router.put('/:id', validate({ params: noteIdSchema, body: updateNoteSchema }), noteController.update);

// Delete note (soft delete)
router.delete('/:id', validateParams(noteIdSchema), noteController.delete);

// Toggle pin status
router.patch('/:id/pin', validate({ params: noteIdSchema, body: togglePinSchema }), noteController.togglePin);

// Toggle archive status
router.patch('/:id/archive', validate({ params: noteIdSchema, body: toggleArchiveSchema }), noteController.toggleArchive);

// Get note statistics
router.get('/stats/overview', noteController.getStats);

export default router;
