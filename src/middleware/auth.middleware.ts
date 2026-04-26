/**
 * Authentication Middleware
 * Validates JWT tokens and attaches user to request
 * @module middleware/auth
 */

import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { TokenPayload } from '../types/auth.types';
import { AuthenticationError, AuthorizationError } from '../errors/AppError';

// Extend Express Request type
declare global {
  namespace Express {
    interface Request {
      user?: TokenPayload;
    }
  }
}

/**
 * Verify JWT access token from Authorization header
 */
export const authenticate = (req: Request, res: Response, next: NextFunction): void => {
  try {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      throw new AuthenticationError('NO_TOKEN', 'Access token is required');
    }

    const token = authHeader.substring(7);

    if (!token) {
      throw new AuthenticationError('NO_TOKEN', 'Access token is required');
    }

    // Verify token
    const payload = jwt.verify(token, process.env.JWT_SECRET!) as TokenPayload;

    // Check token type
    if (payload.type !== 'access') {
      throw new AuthenticationError('INVALID_TOKEN_TYPE', 'Invalid token type');
    }

    // Attach user to request
    req.user = payload;

    next();
  } catch (error) {
    if (error instanceof jwt.TokenExpiredError) {
      next(new AuthenticationError('TOKEN_EXPIRED', 'Token has expired'));
    } else if (error instanceof jwt.JsonWebTokenError) {
      next(new AuthenticationError('INVALID_TOKEN', 'Invalid token'));
    } else {
      next(error);
    }
  }
};

/**
 * Optional authentication - attaches user if token present, doesn't fail if not
 */
export const optionalAuth = (req: Request, res: Response, next: NextFunction): void => {
  try {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return next();
    }

    const token = authHeader.substring(7);

    if (!token) {
      return next();
    }

    const payload = jwt.verify(token, process.env.JWT_SECRET!) as TokenPayload;
    
    if (payload.type === 'access') {
      req.user = payload;
    }

    next();
  } catch {
    // Ignore errors for optional auth
    next();
  }
};

/**
 * Require specific role
 */
export const requireRole = (...allowedRoles: string[]) => {
  return (req: Request, res: Response, next: NextFunction): void => {
    if (!req.user) {
      next(new AuthenticationError('UNAUTHORIZED', 'Authentication required'));
      return;
    }

    if (!allowedRoles.includes(req.user.role)) {
      next(new AuthorizationError('Insufficient permissions'));
      return;
    }

    next();
  };
};

/**
 * Rate limiting for auth endpoints
 */
import rateLimit from 'express-rate-limit';

export const authRateLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // 5 attempts per window
  message: {
    success: false,
    error: {
      code: 'RATE_LIMIT_EXCEEDED',
      message: 'Too many attempts, please try again later',
      status: 429
    }
  },
  standardHeaders: true,
  legacyHeaders: false,
  keyGenerator: (req: Request) => req.ip || 'unknown'
});

/**
 * General API rate limiter
 */
export const apiRateLimiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  max: 100, // 100 requests per minute
  message: {
    success: false,
    error: {
      code: 'RATE_LIMIT_EXCEEDED',
      message: 'Too many requests, please try again later',
      status: 429
    }
  },
  standardHeaders: true,
  legacyHeaders: false
});
