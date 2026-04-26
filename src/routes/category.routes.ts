/**
 * Category Routes
 * @module routes/categories
 */

import { Router } from 'express';
import { CategoryController } from '../controllers/category.controller';
import { 
  createCategorySchema, 
  updateCategorySchema,
  categoryIdSchema
} from '../validators/category.validator';
import { validate, validateParams } from '../middleware/validation.middleware';
import { authenticate } from '../middleware/auth.middleware';

const router = Router();
const categoryController = new CategoryController();

router.use(authenticate);

// List all categories
router.get('/', categoryController.getAll);

// Get categories with note counts
router.get('/with-counts', categoryController.getAllWithCounts);

// Create category
router.post('/', validate({ body: createCategorySchema }), categoryController.create);

// Get single category
router.get('/:id', validateParams(categoryIdSchema), categoryController.getById);

// Update category
router.put('/:id', validate({ params: categoryIdSchema, body: updateCategorySchema }), categoryController.update);

// Delete category
router.delete('/:id', validateParams(categoryIdSchema), categoryController.delete);

export default router;
