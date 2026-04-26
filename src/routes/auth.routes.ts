/**
 * Authentication Routes
 * @module routes/auth
 */

import { Router } from 'express';
import { AuthController } from '../controllers/auth.controller';
import { 
  createUserSchema, 
  loginSchema, 
  changePasswordSchema 
} from '../validators/user.validator';
import { validateBody } from '../middleware/validation.middleware';
import { authenticate, authRateLimiter } from '../middleware/auth.middleware';

const router = Router();
const authController = new AuthController();

// Public routes with rate limiting
router.post('/register', authRateLimiter, validateBody(createUserSchema), authController.register);
router.post('/login', authRateLimiter, validateBody(loginSchema), authController.login);
router.post('/refresh', authController.refresh);
router.post('/forgot-password', authRateLimiter, authController.forgotPassword);
router.post('/reset-password', authController.resetPassword);

// Protected routes
router.post('/logout', authenticate, authController.logout);
router.post('/logout-all', authenticate, authController.logoutAll);
router.post('/change-password', authenticate, validateBody(changePasswordSchema), authController.changePassword);
router.get('/me', authenticate, authController.getCurrentUser);

export default router;
