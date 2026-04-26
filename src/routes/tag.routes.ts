/**
 * Tag Routes
 * @module routes/tags
 */

import { Router } from 'express';
import { TagController } from '../controllers/tag.controller';
import { 
  createTagSchema, 
  updateTagSchema,
  tagIdSchema
} from '../validators/tag.validator';
import { validate, validateParams } from '../middleware/validation.middleware';
import { authenticate } from '../middleware/auth.middleware';

const router = Router();
const tagController = new TagController();

router.use(authenticate);

// List all tags
router.get('/', tagController.getAll);

// Get popular tags
router.get('/popular', tagController.getPopular);

// Create tag
router.post('/', validate({ body: createTagSchema }), tagController.create);

// Get single tag
router.get('/:id', validateParams(tagIdSchema), tagController.getById);

// Update tag
router.put('/:id', validate({ params: tagIdSchema, body: updateTagSchema }), tagController.update);

// Delete tag
router.delete('/:id', validateParams(tagIdSchema), tagController.delete);

export default router;
