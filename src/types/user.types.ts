/**
 * User Domain Types
 * @module types/user
 */

export enum UserRole {
  USER = 'USER',
  ADMIN = 'ADMIN'
}

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  avatarUrl: string | null;
  role: UserRole;
  isActive: boolean;
  isVerified: boolean;
  emailVerifiedAt: Date | null;
  lastLoginAt: Date | null;
  createdAt: Date;
  updatedAt: Date;
}

export interface UserWithPrivate extends User {
  passwordHash: string;
  failedLoginAttempts: number;
  lockedUntil: Date | null;
}

export interface CreateUserDTO {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
}

export interface UpdateUserDTO {
  firstName?: string;
  lastName?: string;
  avatarUrl?: string | null;
}

export interface UserResponse {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  avatarUrl: string | null;
  role: UserRole;
  isVerified: boolean;
  createdAt: string;
}

export interface UserFilters {
  isActive?: boolean;
  isVerified?: boolean;
  role?: UserRole;
  search?: string;
}
