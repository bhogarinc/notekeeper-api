/**
 * Notes Slice - Redux Toolkit
 * Manages notes state with optimistic updates
 * @module slices/notes
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { notesApi } from '../api/notesApi';
import { Note, NoteFilters, PaginationInfo } from '../types/note.types';

// Types
interface NotesState {
  items: Note[];
  selectedNoteId: string | null;
  filters: NoteFilters;
  pagination: PaginationInfo;
  isLoading: boolean;
  isCreating: boolean;
  isUpdating: boolean;
  isDeleting: boolean;
  error: string | null;
}

const initialState: NotesState = {
  items: [],
  selectedNoteId: null,
  filters: {
    searchQuery: '',
    categoryId: null,
    tagIds: [],
    isArchived: false,
    sortBy: 'updated_at',
    sortOrder: 'desc',
  },
  pagination: {
    page: 1,
    limit: 20,
    totalItems: 0,
    totalPages: 1,
    hasNext: false,
    hasPrev: false,
  },
  isLoading: false,
  isCreating: false,
  isUpdating: false,
  isDeleting: false,
  error: null,
};

// Async thunks
export const fetchNotes = createAsyncThunk(
  'notes/fetchNotes',
  async (_, { getState, rejectWithValue }) => {
    try {
      const state = getState() as { notes: NotesState };
      const { filters, pagination } = state.notes;
      
      const response = await notesApi.search({
        ...filters,
        page: pagination.page,
        limit: pagination.limit,
      });
      
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to fetch notes');
    }
  }
);

export const createNote = createAsyncThunk(
  'notes/createNote',
  async (noteData: Partial<Note>, { dispatch, rejectWithValue }) => {
    try {
      const response = await notesApi.create(noteData);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to create note');
    }
  }
);

export const updateNote = createAsyncThunk(
  'notes/updateNote',
  async ({ id, data }: { id: string; data: Partial<Note> }, { dispatch, rejectWithValue }) => {
    try {
      const response = await notesApi.update(id, data);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to update note');
    }
  }
);

export const deleteNote = createAsyncThunk(
  'notes/deleteNote',
  async (id: string, { rejectWithValue }) => {
    try {
      await notesApi.delete(id);
      return id;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to delete note');
    }
  }
);

export const togglePin = createAsyncThunk(
  'notes/togglePin',
  async ({ id, isPinned }: { id: string; isPinned: boolean }, { rejectWithValue }) => {
    try {
      const response = await notesApi.togglePin(id, isPinned);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to update pin status');
    }
  }
);

// Slice
const notesSlice = createSlice({
  name: 'notes',
  initialState,
  reducers: {
    setSelectedNote: (state, action: PayloadAction<string | null>) => {
      state.selectedNoteId = action.payload;
    },
    setFilters: (state, action: PayloadAction<Partial<NoteFilters>>) => {
      state.filters = { ...state.filters, ...action.payload };
      state.pagination.page = 1; // Reset to first page when filters change
    },
    clearFilters: (state) => {
      state.filters = initialState.filters;
      state.pagination.page = 1;
    },
    setPage: (state, action: PayloadAction<number>) => {
      state.pagination.page = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
    // Optimistic update for note content (for real-time collaboration)
    updateNoteContentOptimistic: (state, action: PayloadAction<{ id: string; content: string }>) => {
      const note = state.items.find(n => n.id === action.payload.id);
      if (note) {
        note.content = action.payload.content;
        note.isDirty = true;
      }
    },
  },
  extraReducers: (builder) => {
    // Fetch notes
    builder
      .addCase(fetchNotes.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchNotes.fulfilled, (state, action) => {
        state.isLoading = false;
        state.items = action.payload.items;
        state.pagination = action.payload.pagination;
      })
      .addCase(fetchNotes.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Create note
    builder
      .addCase(createNote.pending, (state) => {
        state.isCreating = true;
      })
      .addCase(createNote.fulfilled, (state, action) => {
        state.isCreating = false;
        state.items.unshift(action.payload);
        state.pagination.totalItems += 1;
      })
      .addCase(createNote.rejected, (state, action) => {
        state.isCreating = false;
        state.error = action.payload as string;
      });

    // Update note
    builder
      .addCase(updateNote.pending, (state) => {
        state.isUpdating = true;
      })
      .addCase(updateNote.fulfilled, (state, action) => {
        state.isUpdating = false;
        const index = state.items.findIndex(n => n.id === action.payload.id);
        if (index !== -1) {
          state.items[index] = { ...state.items[index], ...action.payload };
        }
      })
      .addCase(updateNote.rejected, (state, action) => {
        state.isUpdating = false;
        state.error = action.payload as string;
      });

    // Delete note
    builder
      .addCase(deleteNote.pending, (state) => {
        state.isDeleting = true;
      })
      .addCase(deleteNote.fulfilled, (state, action) => {
        state.isDeleting = false;
        state.items = state.items.filter(n => n.id !== action.payload);
        state.pagination.totalItems -= 1;
        if (state.selectedNoteId === action.payload) {
          state.selectedNoteId = null;
        }
      })
      .addCase(deleteNote.rejected, (state, action) => {
        state.isDeleting = false;
        state.error = action.payload as string;
      });

    // Toggle pin
    builder
      .addCase(togglePin.fulfilled, (state, action) => {
        const index = state.items.findIndex(n => n.id === action.payload.id);
        if (index !== -1) {
          state.items[index].isPinned = action.payload.isPinned;
          // Re-sort items to show pinned first
          state.items.sort((a, b) => {
            if (a.isPinned === b.isPinned) {
              return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
            }
            return a.isPinned ? -1 : 1;
          });
        }
      });
  },
});

export const {
  setSelectedNote,
  setFilters,
  clearFilters,
  setPage,
  clearError,
  updateNoteContentOptimistic,
} = notesSlice.actions;

export default notesSlice.reducer;
