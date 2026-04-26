/**
 * Error Handling Middleware
 * Centralized error handling for Express
 * @module middleware/errorHandler
 */

import { Request, Response, NextFunction } from 'express';
import { AppError } from '../errors/AppError';
import { v4 as uuidv4 } from 'uuid';

/**
 * Request ID middleware - attaches unique ID to each request
 */
export const requestId = (req: Request, res: Response, next: NextFunction): void => {
  req.id = uuidv4();
  res.setHeader('X-Request-Id', req.id);
  next();
};

// Extend Express Request
declare global {
  namespace Express {
    interface Request {
      id?: string;
    }
  }
}

/**
 * Global error handler
 */
export const errorHandler = (
  err: Error,
  req: Request,
  res: Response,
  next: NextFunction
): void => {
  const requestId = req.id || uuidv4();

  // Log error details
  console.error({
    requestId,
    error: err.message,
    stack: err.stack,
    path: req.path,
    method: req.method,
    userId: (req as any).user?.sub
  });

  // Handle operational errors (expected application errors)
  if (err instanceof AppError) {
    res.status(err.statusCode).json({
      success: false,
      error: {
        code: err.code,
        message: err.message,
        status: err.statusCode,
        details: Object.keys(err.details).length > 0 ? err.details : undefined,
        requestId
      }
    });
    return;
  }

  // Handle JWT errors
  if (err.name === 'JsonWebTokenError') {
    res.status(401).json({
      success: false,
      error: {
        code: 'INVALID_TOKEN',
        message: 'Invalid authentication token',
        status: 401,
        requestId
      }
    });
    return;
  }

  if (err.name === 'TokenExpiredError') {
    res.status(401).json({
      success: false,
      error: {
        code: 'TOKEN_EXPIRED',
        message: 'Authentication token has expired',
        status: 401,
        requestId
      }
    });
    return;
  }

  // Handle validation errors from libraries
  if (err.name === 'ValidationError') {
    res.status(400).json({
      success: false,
      error: {
        code: 'VALIDATION_ERROR',
        message: err.message,
        status: 400,
        requestId
      }
    });
    return;
  }

  // Handle database unique constraint errors
  if ((err as any).code === '23505') {
    res.status(409).json({
      success: false,
      error: {
        code: 'DUPLICATE_ENTRY',
        message: 'A resource with this information already exists',
        status: 409,
        requestId
      }
    });
    return;
  }

  // Handle database foreign key constraint errors
  if ((err as any).code === '23503') {
    res.status(400).json({
      success: false,
      error: {
        code: 'INVALID_REFERENCE',
        message: 'Referenced resource does not exist',
        status: 400,
        requestId
      }
    });
    return;
  }

  // Handle unexpected errors (don't leak details in production)
  const isDevelopment = process.env.NODE_ENV === 'development';
  
  res.status(500).json({
    success: false,
    error: {
      code: 'INTERNAL_ERROR',
      message: isDevelopment ? err.message : 'An unexpected error occurred',
      status: 500,
      ...(isDevelopment && { stack: err.stack }),
      requestId
    }
  });
};

/**
 * 404 Not Found handler
 */
export const notFoundHandler = (req: Request, res: Response): void => {
  res.status(404).json({
    success: false,
    error: {
      code: 'ROUTE_NOT_FOUND',
      message: `Route ${req.method} ${req.path} not found`,
      status: 404,
      requestId: req.id
    }
  });
};
