/**
 * Authentication Service
 * Handles JWT token generation, password hashing, and authentication flows
 * @module services/auth
 */

import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import crypto from 'crypto';
import { 
  TokenPair, 
  TokenPayload, 
  LoginCredentials, 
  RegisterCredentials,
  RefreshToken 
} from '../types/auth.types';
import { User, UserWithPrivate, UserResponse } from '../types/user.types';
import { 
  AuthenticationError, 
  ConflictError, 
  ValidationError 
} from '../errors/AppError';

export class AuthService {
  private readonly accessTokenExpiry = 15 * 60; // 15 minutes
  private readonly refreshTokenExpiry = 7 * 24 * 60 * 60; // 7 days
  private readonly saltRounds = 12;
  private readonly maxLoginAttempts = 5;
  private readonly lockoutDuration = 30 * 60; // 30 minutes

  constructor(
    private userRepository: any,
    private refreshTokenRepository: any
  ) {}

  /**
   * Register a new user
   */
  async register(credentials: RegisterCredentials): Promise<{ user: User; tokens: TokenPair }> {
    // Check if email already exists
    const existingUser = await this.userRepository.findByEmail(credentials.email);
    if (existingUser) {
      throw new ConflictError('An account with this email already exists');
    }

    // Hash password
    const passwordHash = await bcrypt.hash(credentials.password, this.saltRounds);

    // Create user
    const user = await this.userRepository.create({
      email: credentials.email.toLowerCase(),
      password_hash: passwordHash,
      first_name: credentials.firstName,
      last_name: credentials.lastName,
      role: 'USER',
      is_active: true,
      is_verified: false
    });

    // Generate tokens
    const tokens = await this.generateTokenPair(user);

    return { user, tokens };
  }

  /**
   * Authenticate user with credentials
   */
  async login(credentials: LoginCredentials, ipAddress?: string, userAgent?: string): Promise<{ user: User; tokens: TokenPair }> {
    // Find user by email
    const user = await this.userRepository.findByEmail(credentials.email);
    if (!user) {
      throw new AuthenticationError('INVALID_CREDENTIALS', 'Invalid email or password');
    }

    // Check if account is locked
    if (user.locked_until && new Date(user.locked_until) > new Date()) {
      const remainingMinutes = Math.ceil((new Date(user.locked_until).getTime() - Date.now()) / 60000);
      throw new AuthenticationError('ACCOUNT_LOCKED', `Account is locked. Try again in ${remainingMinutes} minutes`);
    }

    // Check if account is active
    if (!user.is_active) {
      throw new AuthenticationError('ACCOUNT_INACTIVE', 'This account has been deactivated');
    }

    // Verify password
    const isPasswordValid = await bcrypt.compare(credentials.password, user.password_hash);
    if (!isPasswordValid) {
      await this.handleFailedLogin(user);
      throw new AuthenticationError('INVALID_CREDENTIALS', 'Invalid email or password');
    }

    // Reset failed login attempts
    if (user.failed_login_attempts > 0) {
      await this.userRepository.update(user.id, {
        failed_login_attempts: 0,
        locked_until: null
      });
    }

    // Update last login
    await this.userRepository.update(user.id, { last_login_at: new Date() });

    // Generate tokens
    const tokens = await this.generateTokenPair(user, ipAddress, userAgent);

    // Remove sensitive data before returning
    const { password_hash, failed_login_attempts, locked_until, ...safeUser } = user;

    return { user: safeUser as User, tokens };
  }

  /**
   * Refresh access token using refresh token
   */
  async refreshTokens(refreshToken: string): Promise<TokenPair> {
    // Hash the provided refresh token
    const tokenHash = crypto.createHash('sha256').update(refreshToken).digest('hex');

    // Find valid refresh token in database
    const storedToken = await this.refreshTokenRepository.findValidToken(tokenHash);
    if (!storedToken) {
      throw new AuthenticationError('INVALID_REFRESH_TOKEN', 'Refresh token is invalid or expired');
    }

    // Get user
    const user = await this.userRepository.findById(storedToken.user_id);
    if (!user || !user.is_active) {
      throw new AuthenticationError('INVALID_REFRESH_TOKEN', 'Refresh token is invalid');
    }

    // Revoke old refresh token (token rotation for security)
    await this.refreshTokenRepository.revoke(storedToken.id);

    // Generate new token pair
    return this.generateTokenPair(user);
  }

  /**
   * Logout user by revoking refresh token
   */
  async logout(refreshToken: string): Promise<void> {
    const tokenHash = crypto.createHash('sha256').update(refreshToken).digest('hex');
    await this.refreshTokenRepository.revokeByHash(tokenHash);
  }

  /**
   * Logout all sessions for a user
   */
  async logoutAll(userId: string): Promise<void> {
    await this.refreshTokenRepository.revokeAllForUser(userId);
  }

  /**
   * Verify access token and return payload
   */
  verifyAccessToken(token: string): TokenPayload {
    try {
      const payload = jwt.verify(token, process.env.JWT_SECRET!) as TokenPayload;
      
      if (payload.type !== 'access') {
        throw new AuthenticationError('INVALID_TOKEN', 'Invalid token type');
      }

      return payload;
    } catch (error) {
      if (error instanceof jwt.TokenExpiredError) {
        throw new AuthenticationError('TOKEN_EXPIRED', 'Token has expired');
      }
      throw new AuthenticationError('INVALID_TOKEN', 'Invalid token');
    }
  }

  /**
   * Generate JWT token pair
   */
  private async generateTokenPair(
    user: UserWithPrivate, 
    ipAddress?: string, 
    userAgent?: string
  ): Promise<TokenPair> {
    const now = Math.floor(Date.now() / 1000);
    const jti = crypto.randomUUID();

    // Generate access token
    const accessToken = jwt.sign(
      {
        sub: user.id,
        email: user.email,
        role: user.role,
        type: 'access',
        jti,
        iat: now,
        exp: now + this.accessTokenExpiry
      } as TokenPayload,
      process.env.JWT_SECRET!,
      { algorithm: 'HS256' }
    );

    // Generate refresh token
    const refreshToken = crypto.randomBytes(64).toString('base64url');
    const refreshTokenHash = crypto.createHash('sha256').update(refreshToken).digest('hex');

    // Store refresh token hash in database
    await this.refreshTokenRepository.create({
      user_id: user.id,
      token_hash: refreshTokenHash,
      expires_at: new Date((now + this.refreshTokenExpiry) * 1000),
      ip_address: ipAddress || null,
      user_agent: userAgent || null
    });

    return {
      accessToken,
      refreshToken,
      expiresIn: this.accessTokenExpiry
    };
  }

  /**
   * Handle failed login attempt
   */
  private async handleFailedLogin(user: UserWithPrivate): Promise<void> {
    const attempts = (user.failed_login_attempts || 0) + 1;
    const updates: any = { failed_login_attempts: attempts };

    // Lock account after max attempts
    if (attempts >= this.maxLoginAttempts) {
      updates.locked_until = new Date(Date.now() + this.lockoutDuration * 1000);
    }

    await this.userRepository.update(user.id, updates);
  }

  /**
   * Change user password
   */
  async changePassword(userId: string, currentPassword: string, newPassword: string): Promise<void> {
    const user = await this.userRepository.findById(userId);
    if (!user) {
      throw new NotFoundError('User');
    }

    // Verify current password
    const isValid = await bcrypt.compare(currentPassword, user.password_hash);
    if (!isValid) {
      throw new AuthenticationError('INVALID_PASSWORD', 'Current password is incorrect');
    }

    // Hash new password
    const newPasswordHash = await bcrypt.hash(newPassword, this.saltRounds);

    // Update password
    await this.userRepository.update(userId, { password_hash: newPasswordHash });

    // Revoke all refresh tokens for security
    await this.refreshTokenRepository.revokeAllForUser(userId);
  }

  /**
   * Request password reset
   */
  async requestPasswordReset(email: string): Promise<void> {
    const user = await this.userRepository.findByEmail(email);
    if (!user) {
      // Don't reveal if email exists
      return;
    }

    // Generate reset token
    const resetToken = crypto.randomBytes(32).toString('hex');
    const resetTokenHash = crypto.createHash('sha256').update(resetToken).digest('hex');

    // Store in database (1 hour expiry)
    await this.passwordResetRepository.create({
      user_id: user.id,
      token_hash: resetTokenHash,
      expires_at: new Date(Date.now() + 60 * 60 * 1000)
    });

    // TODO: Send email with resetToken
    // Email service integration will be implemented separately
  }
}
