/**
 * Note Service
 * Business logic for note management
 * @module services/note
 */

import { 
  Note, 
  NoteWithRelations, 
  CreateNoteDTO, 
  UpdateNoteDTO, 
  SearchParams,
  PaginatedResult 
} from '../types/note.types';
import { NotFoundError, ValidationError, AuthorizationError } from '../errors/AppError';
import MarkdownIt from 'markdown-it';

export class NoteService {
  private markdownParser: MarkdownIt;

  constructor(
    private noteRepository: any,
    private tagRepository: any,
    private categoryRepository: any
  ) {
    this.markdownParser = new MarkdownIt({
      html: false,
      breaks: true,
      linkify: true,
      typographer: true
    });
  }

  /**
   * Create a new note
   */
  async create(data: CreateNoteDTO, userId: string): Promise<NoteWithRelations> {
    // Validate category if provided
    if (data.categoryId) {
      const category = await this.categoryRepository.findById(data.categoryId);
      if (!category) {
        throw new NotFoundError('Category');
      }
      if (category.user_id !== userId) {
        throw new AuthorizationError('Category does not belong to user');
      }
    }

    // Validate tags if provided
    if (data.tagIds && data.tagIds.length > 0) {
      await this.validateTags(data.tagIds, userId);
    }

    // Render markdown to HTML
    const contentHtml = this.markdownParser.render(data.content);

    // Create note
    const note = await this.noteRepository.create({
      user_id: userId,
      category_id: data.categoryId || null,
      title: data.title.trim(),
      content: data.content,
      content_html: contentHtml,
      is_pinned: data.isPinned || false,
      is_archived: false,
      color: data.color || '#ffffff'
    });

    // Associate tags
    if (data.tagIds && data.tagIds.length > 0) {
      await this.tagRepository.attachToNote(note.id, data.tagIds);
    }

    // Return note with relations
    return this.findById(note.id, userId) as Promise<NoteWithRelations>;
  }

  /**
   * Get note by ID
   */
  async findById(id: string, userId: string): Promise<NoteWithRelations | null> {
    const note = await this.noteRepository.findByIdWithRelations(id, userId);
    return note;
  }

  /**
   * Get note by ID or throw error
   */
  async findByIdOrThrow(id: string, userId: string): Promise<NoteWithRelations> {
    const note = await this.findById(id, userId);
    if (!note) {
      throw new NotFoundError('Note');
    }
    return note;
  }

  /**
   * Search and list notes with filtering
   */
  async search(userId: string, params: SearchParams): Promise<PaginatedResult<NoteWithRelations>> {
    const page = params.page || 1;
    const limit = Math.min(params.limit || 20, 100);
    const offset = (page - 1) * limit;

    // Build search query
    const result = await this.noteRepository.search(userId, {
      ...params,
      limit,
      offset
    });

    // Filter by tags if specified (post-query for complex AND logic)
    let filteredItems = result.items;
    if (params.tagIds && params.tagIds.length > 0) {
      filteredItems = result.items.filter((note: NoteWithRelations) => 
        params.tagIds!.every(tagId => note.tags.some(tag => tag.id === tagId))
      );
    }

    return {
      items: filteredItems,
      pagination: {
        page,
        limit,
        totalItems: result.total,
        totalPages: Math.ceil(result.total / limit),
        hasNext: page * limit < result.total,
        hasPrev: page > 1
      }
    };
  }

  /**
   * Update a note
   */
  async update(id: string, data: UpdateNoteDTO, userId: string): Promise<NoteWithRelations> {
    // Verify note exists and belongs to user
    const existingNote = await this.findByIdOrThrow(id, userId);

    // Validate category if changing
    if (data.categoryId !== undefined && data.categoryId !== null) {
      const category = await this.categoryRepository.findById(data.categoryId);
      if (!category) {
        throw new NotFoundError('Category');
      }
      if (category.user_id !== userId) {
        throw new AuthorizationError('Category does not belong to user');
      }
    }

    // Validate tags if changing
    if (data.tagIds) {
      await this.validateTags(data.tagIds, userId);
    }

    // Prepare updates
    const updates: any = {};

    if (data.title !== undefined) {
      updates.title = data.title.trim();
    }

    if (data.content !== undefined) {
      updates.content = data.content;
      updates.content_html = this.markdownParser.render(data.content);
    }

    if (data.categoryId !== undefined) {
      updates.category_id = data.categoryId;
    }

    if (data.color !== undefined) {
      updates.color = data.color;
    }

    if (data.isPinned !== undefined) {
      updates.is_pinned = data.isPinned;
    }

    if (data.isArchived !== undefined) {
      updates.is_archived = data.isArchived;
    }

    // Update note
    await this.noteRepository.update(id, updates);

    // Update tags if provided
    if (data.tagIds) {
      await this.tagRepository.detachAllFromNote(id);
      if (data.tagIds.length > 0) {
        await this.tagRepository.attachToNote(id, data.tagIds);
      }
    }

    // Return updated note
    return this.findByIdOrThrow(id, userId);
  }

  /**
   * Delete a note (soft delete)
   */
  async delete(id: string, userId: string): Promise<void> {
    // Verify note exists and belongs to user
    await this.findByIdOrThrow(id, userId);

    // Soft delete
    await this.noteRepository.softDelete(id);
  }

  /**
   * Toggle pin status
   */
  async togglePin(id: string, userId: string): Promise<Note> {
    const note = await this.findByIdOrThrow(id, userId);
    const updated = await this.noteRepository.update(id, { is_pinned: !note.isPinned });
    return updated;
  }

  /**
   * Toggle archive status
   */
  async toggleArchive(id: string, userId: string): Promise<Note> {
    const note = await this.findByIdOrThrow(id, userId);
    const updated = await this.noteRepository.update(id, { is_archived: !note.isArchived });
    return updated;
  }

  /**
   * Get notes statistics for a user
   */
  async getStats(userId: string): Promise<{
    total: number;
    pinned: number;
    archived: number;
    byCategory: { categoryId: string; count: number }[];
  }> {
    return this.noteRepository.getStats(userId);
  }

  /**
   * Validate tags belong to user
   */
  private async validateTags(tagIds: string[], userId: string): Promise<void> {
    const tags = await this.tagRepository.findByIds(tagIds);
    
    if (tags.length !== tagIds.length) {
      const foundIds = tags.map((t: any) => t.id);
      const missing = tagIds.filter(id => !foundIds.includes(id));
      throw new ValidationError('Invalid tags', { tagIds: [`Tags not found: ${missing.join(', ')}`] });
    }

    const unauthorized = tags.filter((t: any) => t.user_id !== userId);
    if (unauthorized.length > 0) {
      throw new AuthorizationError('Some tags do not belong to user');
    }
  }
}
