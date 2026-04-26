/**
 * Validation Middleware
 * Request validation using Joi schemas
 * @module middleware/validation
 */

import { Request, Response, NextFunction } from 'express';
import Joi from 'joi';
import { ValidationError } from '../errors/AppError';

/**
 * Validate request body against schema
 */
export const validateBody = (schema: Joi.ObjectSchema) => {
  return (req: Request, res: Response, next: NextFunction): void => {
    const { error, value } = schema.validate(req.body, {
      abortEarly: false,
      stripUnknown: true
    });

    if (error) {
      const details: Record<string, string[]> = {};
      
      error.details.forEach((detail) => {
        const path = detail.path.join('.');
        if (!details[path]) {
          details[path] = [];
        }
        details[path].push(detail.message);
      });

      next(new ValidationError('Validation failed', details));
      return;
    }

    // Replace body with validated/sanitized value
    req.body = value;
    next();
  };
};

/**
 * Validate request params against schema
 */
export const validateParams = (schema: Joi.ObjectSchema) => {
  return (req: Request, res: Response, next: NextFunction): void => {
    const { error, value } = schema.validate(req.params, {
      abortEarly: false,
      stripUnknown: true
    });

    if (error) {
      const details: Record<string, string[]> = {};
      
      error.details.forEach((detail) => {
        const path = detail.path.join('.');
        if (!details[path]) {
          details[path] = [];
        }
        details[path].push(detail.message);
      });

      next(new ValidationError('Invalid URL parameters', details));
      return;
    }

    req.params = value;
    next();
  };
};

/**
 * Validate request query against schema
 */
export const validateQuery = (schema: Joi.ObjectSchema) => {
  return (req: Request, res: Response, next: NextFunction): void => {
    const { error, value } = schema.validate(req.query, {
      abortEarly: false,
      stripUnknown: true,
      convert: true // Convert strings to numbers, booleans, etc.
    });

    if (error) {
      const details: Record<string, string[]> = {};
      
      error.details.forEach((detail) => {
        const path = detail.path.join('.');
        if (!details[path]) {
          details[path] = [];
        }
        details[path].push(detail.message);
      });

      next(new ValidationError('Invalid query parameters', details));
      return;
    }

    req.query = value;
    next();
  };
};

/**
 * Combined validation middleware
 */
export const validate = (schemas: {
  body?: Joi.ObjectSchema;
  params?: Joi.ObjectSchema;
  query?: Joi.ObjectSchema;
}) => {
  return (req: Request, res: Response, next: NextFunction): void => {
    const errors: Record<string, string[]> = {};

    // Validate body
    if (schemas.body) {
      const { error, value } = schemas.body.validate(req.body, {
        abortEarly: false,
        stripUnknown: true
      });

      if (error) {
        error.details.forEach((detail) => {
          const path = `body.${detail.path.join('.')}`;
          if (!errors[path]) errors[path] = [];
          errors[path].push(detail.message);
        });
      } else {
        req.body = value;
      }
    }

    // Validate params
    if (schemas.params) {
      const { error, value } = schemas.params.validate(req.params, {
        abortEarly: false,
        stripUnknown: true
      });

      if (error) {
        error.details.forEach((detail) => {
          const path = `params.${detail.path.join('.')}`;
          if (!errors[path]) errors[path] = [];
          errors[path].push(detail.message);
        });
      } else {
        req.params = value;
      }
    }

    // Validate query
    if (schemas.query) {
      const { error, value } = schemas.query.validate(req.query, {
        abortEarly: false,
        stripUnknown: true,
        convert: true
      });

      if (error) {
        error.details.forEach((detail) => {
          const path = `query.${detail.path.join('.')}`;
          if (!errors[path]) errors[path] = [];
          errors[path].push(detail.message);
        });
      } else {
        req.query = value;
      }
    }

    // If any validation errors, throw
    if (Object.keys(errors).length > 0) {
      next(new ValidationError('Validation failed', errors));
      return;
    }

    next();
  };
};
