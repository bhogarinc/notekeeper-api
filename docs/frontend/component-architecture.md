# NoteKeeper Frontend Component Architecture

## Overview
NoteKeeper uses a vanilla JavaScript SPA architecture with a component-based design pattern.

## Architecture Principles

1. **Component-Based**: UI broken into reusable, self-contained components
2. **State Management**: Centralized store with unidirectional data flow
3. **Event-Driven**: Custom event bus for component communication
4. **Module Bundling**: ES6 modules with no build step required

## Directory Structure

```
public/
├── index.html              # Main HTML entry point
├── css/
│   ├── styles.css          # Global styles & CSS variables
│   ├── components/         # Component-specific styles
│   │   ├── note-editor.css
│   │   ├── note-list.css
│   │   ├── sidebar.css
│   │   └── modal.css
│   └── themes/
│       └── dark-theme.css  # Dark theme overrides
├── js/
│   ├── app.js              # Application bootstrap
│   ├── router.js           # Client-side routing
│   ├── store.js            # Centralized state management
│   ├── api.js              # HTTP client
│   ├── utils.js            # Utility functions
│   ├── components/         # UI Components
│   │   ├── Component.js    # Base component class
│   │   ├── NoteEditor.js
│   │   ├── NoteList.js
│   │   ├── NoteCard.js
│   │   ├── Sidebar.js
│   │   ├── SearchBar.js
│   │   ├── CategoryManager.js
│   │   ├── TagManager.js
│   │   ├── Modal.js
│   │   ├── Toast.js
│   │   └── AuthForm.js
│   └── services/           # Business logic
│       ├── authService.js
│       ├── noteService.js
│       ├── categoryService.js
│       └── tagService.js
└── assets/
    ├── icons/              # SVG icons
    └── fonts/              # Custom fonts
```

## Component Hierarchy

```
App (app.js)
├── Router (router.js)
│   ├── Route: /login
│   │   └── AuthForm
│   ├── Route: /notes
│   │   └── Layout
│   │       ├── Sidebar
│   │       │   ├── SearchBar
│   │       │   ├── CategoryList
│   │       │   └── TagList
│   │       └── MainContent
│   │           ├── NoteList
│   │           │   └── NoteCard[]
│   │           └── NoteEditor (when editing)
│   ├── Route: /notes/:id
│   │   └── Layout
│   │       └── NoteEditor
│   ├── Route: /categories
│   │   └── CategoryManager
│   └── Route: /tags
│       └── TagManager
└── ToastContainer
    └── Toast[]
```

## Base Component Class

```javascript
// js/components/Component.js
export class Component {
  constructor(selector, options = {}) {
    this.element = document.querySelector(selector);
    this.options = options;
    this.state = {};
    this.eventListeners = [];
  }

  // Initialize component
  init() {
    this.bindEvents();
    this.render();
  }

  // Render component HTML
  render() {
    // Override in subclass
  }

  // Bind event listeners
  bindEvents() {
    // Override in subclass
  }

  // Set state and re-render
  setState(newState) {
    this.state = { ...this.state, ...newState };
    this.render();
  }

  // Add event listener with automatic cleanup
  on(event, handler, element = this.element) {
    element.addEventListener(event, handler);
    this.eventListeners.push({ event, handler, element });
  }

  // Clean up event listeners
  destroy() {
    this.eventListeners.forEach(({ event, handler, element }) => {
      element.removeEventListener(event, handler);
    });
    this.eventListeners = [];
  }

  // Emit custom event
  emit(eventName, detail) {
    const event = new CustomEvent(eventName, { detail, bubbles: true });
    this.element.dispatchEvent(event);
  }
}
```

## State Management

```javascript
// js/store.js
class Store {
  constructor() {
    this.state = {
      // Auth
      user: null,
      isAuthenticated: false,
      
      // UI State
      currentRoute: '/notes',
      sidebarOpen: true,
      theme: 'dark',
      
      // Data
      notes: [],
      categories: [],
      tags: [],
      selectedNoteId: null,
      
      // Filters
      searchQuery: '',
      selectedCategoryId: null,
      selectedTagIds: [],
      showArchived: false,
      
      // Loading States
      isLoading: false,
      error: null
    };
    
    this.listeners = new Set();
  }

  // Get current state
  getState() {
    return { ...this.state };
  }

  // Subscribe to state changes
  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  // Update state and notify listeners
  setState(updates) {
    const prevState = { ...this.state };
    this.state = { ...this.state, ...updates };
    
    this.listeners.forEach(listener => {
      listener(this.state, prevState);
    });
  }

  // Action: Set user
  setUser(user) {
    this.setState({ user, isAuthenticated: !!user });
  }

  // Action: Set notes
  setNotes(notes) {
    this.setState({ notes });
  }

  // Action: Add note
  addNote(note) {
    this.setState({ notes: [note, ...this.state.notes] });
  }

  // Action: Update note
  updateNote(updatedNote) {
    const notes = this.state.notes.map(n => 
      n.id === updatedNote.id ? updatedNote : n
    );
    this.setState({ notes });
  }

  // Action: Delete note
  deleteNote(noteId) {
    const notes = this.state.notes.filter(n => n.id !== noteId);
    this.setState({ notes, selectedNoteId: null });
  }

  // Action: Set filters
  setFilters(filters) {
    this.setState({ ...filters });
  }

  // Action: Select note
  selectNote(noteId) {
    this.setState({ selectedNoteId: noteId });
  }

  // Action: Set loading
  setLoading(isLoading) {
    this.setState({ isLoading });
  }

  // Action: Set error
  setError(error) {
    this.setState({ error });
  }

  // Action: Clear error
  clearError() {
    this.setState({ error: null });
  }
}

// Singleton instance
export const store = new Store();
```

## Router Implementation

```javascript
// js/router.js
class Router {
  constructor() {
    this.routes = new Map();
    this.currentRoute = null;
    this.beforeHooks = [];
    
    // Handle browser back/forward
    window.addEventListener('popstate', () => this.handleRoute());
  }

  // Register route
  register(path, handler, options = {}) {
    const pattern = this.pathToRegex(path);
    this.routes.set(pattern, { handler, options, path });
  }

  // Convert path to regex
  pathToRegex(path) {
    const escaped = path.replace(/\//g, '\\/');
    const paramRegex = escaped.replace(/:([^/]+)/g, '(?<$1>[^/]+)');
    return new RegExp(`^${paramRegex}$`);
  }

  // Add before hook
  beforeEach(hook) {
    this.beforeHooks.push(hook);
  }

  // Navigate to route
  navigate(path, options = {}) {
    if (options.replace) {
      history.replaceState(null, '', path);
    } else {
      history.pushState(null, '', path);
    }
    this.handleRoute();
  }

  // Handle current route
  async handleRoute() {
    const path = window.location.pathname;
    const matched = this.matchRoute(path);
    
    if (!matched) {
      this.navigate('/404');
      return;
    }

    // Run before hooks
    for (const hook of this.beforeHooks) {
      const result = await hook(matched);
      if (result === false) return;
    }

    // Check authentication
    if (matched.options.requiresAuth && !store.getState().isAuthenticated) {
      this.navigate('/login');
      return;
    }

    // Execute handler
    this.currentRoute = matched;
    matched.handler(matched.params);
    
    // Update store
    store.setState({ currentRoute: path });
  }

  // Match path to registered route
  matchRoute(path) {
    for (const [pattern, route] of this.routes) {
      const match = path.match(pattern);
      if (match) {
        return {
          ...route,
          params: match.groups || {}
        };
      }
    }
    return null;
  }

  // Start router
  start() {
    this.handleRoute();
  }
}

// Singleton instance
export const router = new Router();
```

## API Client

```javascript
// js/api.js
const API_BASE_URL = window.location.hostname === 'localhost' 
  ? 'http://localhost:3000/api/v1'
  : 'https://notekeeper-bhogarai.azurewebsites.net/api/v1';

class ApiClient {
  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  // Get auth token from storage
  getToken() {
    return sessionStorage.getItem('accessToken');
  }

  // Make HTTP request
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(this.getToken() && { 'Authorization': `Bearer ${this.getToken()}` }),
        ...options.headers
      },
      ...options
    };

    if (config.body && typeof config.body === 'object') {
      config.body = JSON.stringify(config.body);
    }

    try {
      const response = await fetch(url, config);
      
      if (response.status === 401) {
        // Token expired, try refresh
        const refreshed = await this.refreshToken();
        if (refreshed) {
          return this.request(endpoint, options);
        } else {
          // Refresh failed, redirect to login
          window.location.href = '/login';
          return;
        }
      }

      if (!response.ok) {
        const error = await response.json();
        throw new ApiError(error.error.message, response.status, error.error);
      }

      if (response.status === 204) {
        return null;
      }

      return await response.json();
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError('Network error', 0, { message: error.message });
    }
  }

  // HTTP methods
  get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }

  post(endpoint, body) {
    return this.request(endpoint, { method: 'POST', body });
  }

  put(endpoint, body) {
    return this.request(endpoint, { method: 'PUT', body });
  }

  patch(endpoint, body) {
    return this.request(endpoint, { method: 'PATCH', body });
  }

  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }

  // Refresh access token
  async refreshToken() {
    const refreshToken = localStorage.getItem('refreshToken');
    if (!refreshToken) return false;

    try {
      const response = await fetch(`${this.baseUrl}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refreshToken })
      });

      if (!response.ok) {
        localStorage.removeItem('refreshToken');
        return false;
      }

      const data = await response.json();
      sessionStorage.setItem('accessToken', data.accessToken);
      localStorage.setItem('refreshToken', data.refreshToken);
      return true;
    } catch {
      return false;
    }
  }
}

// Custom API Error class
class ApiError extends Error {
  constructor(message, status, details) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

// Singleton instance
export const api = new ApiClient();
```

## Key Components

### NoteEditor Component
```javascript
// js/components/NoteEditor.js
import { Component } from './Component.js';
import { store } from '../store.js';
import { noteService } from '../services/noteService.js';
import { debounce } from '../utils.js';

export class NoteEditor extends Component {
  constructor(selector) {
    super(selector);
    this.autoSave = debounce(this.save.bind(this), 2000);
    this.unsubscribe = null;
  }

  init() {
    // Subscribe to store changes
    this.unsubscribe = store.subscribe((state) => {
      if (state.selectedNoteId !== this.currentNoteId) {
        this.loadNote(state.selectedNoteId);
      }
    });

    super.init();
  }

  render() {
    const note = this.state.note || {};
    
    this.element.innerHTML = `
      <div class="note-editor">
        <input 
          type="text" 
          class="note-title" 
          placeholder="Note title..."
          value="${note.title || ''}"
        >
        <div class="note-toolbar">
          <button class="btn-pin" title="Pin note">
            ${note.isPinned ? '📌' : '📍'}
          </button>
          <button class="btn-archive" title="Archive note">
            ${note.isArchived ? '📦' : '📋'}
          </button>
          <select class="category-select">
            <option value="">No Category</option>
            ${this.renderCategoryOptions()}
          </select>
          <div class="tag-input">
            <input type="text" placeholder="Add tag...">
            <div class="tag-list"></div>
          </div>
        </div>
        <textarea 
          class="note-content" 
          placeholder="Start writing..."
        >${note.content || ''}</textarea>
        <div class="note-preview markdown-body"></div>
        <div class="editor-footer">
          <span class="last-saved"></span>
          <div class="actions">
            <button class="btn-delete">Delete</button>
            <button class="btn-save">Save</button>
          </div>
        </div>
      </div>
    `;

    this.bindEvents();
  }

  bindEvents() {
    const titleInput = this.element.querySelector('.note-title');
    const contentInput = this.element.querySelector('.note-content');
    
    titleInput?.addEventListener('input', () => this.autoSave());
    contentInput?.addEventListener('input', () => {
      this.updatePreview(contentInput.value);
      this.autoSave();
    });

    this.element.querySelector('.btn-save')?.addEventListener('click', () => {
      this.save();
    });

    this.element.querySelector('.btn-delete')?.addEventListener('click', () => {
      this.delete();
    });
  }

  async loadNote(noteId) {
    this.currentNoteId = noteId;
    
    if (!noteId) {
      this.setState({ note: null });
      return;
    }

    try {
      const note = await noteService.getById(noteId);
      this.setState({ note });
    } catch (error) {
      store.setError(error.message);
    }
  }

  async save() {
    const title = this.element.querySelector('.note-title')?.value;
    const content = this.element.querySelector('.note-content')?.value;

    if (!title && !content) return;

    try {
      const noteData = { title, content };
      
      if (this.currentNoteId) {
        await noteService.update(this.currentNoteId, noteData);
      } else {
        const newNote = await noteService.create(noteData);
        store.addNote(newNote);
        this.currentNoteId = newNote.id;
      }

      this.showSavedIndicator();
    } catch (error) {
      store.setError(error.message);
    }
  }

  updatePreview(content) {
    const preview = this.element.querySelector('.note-preview');
    if (preview) {
      preview.innerHTML = marked.parse(content || '');
    }
  }

  showSavedIndicator() {
    const indicator = this.element.querySelector('.last-saved');
    if (indicator) {
      indicator.textContent = `Saved ${new Date().toLocaleTimeString()}`;
    }
  }

  destroy() {
    this.unsubscribe?.();
    super.destroy();
  }
}
```

### NoteList Component
```javascript
// js/components/NoteList.js
import { Component } from './Component.js';
import { store } from '../store.js';
import { NoteCard } from './NoteCard.js';

export class NoteList extends Component {
  constructor(selector) {
    super(selector);
    this.unsubscribe = null;
    this.noteCards = [];
  }

  init() {
    // Subscribe to notes changes
    this.unsubscribe = store.subscribe((state) => {
      this.setState({ 
        notes: this.filterNotes(state),
        isLoading: state.isLoading 
      });
    });

    this.loadNotes();
    super.init();
  }

  filterNotes(state) {
    let notes = [...state.notes];

    // Filter by search query
    if (state.searchQuery) {
      const query = state.searchQuery.toLowerCase();
      notes = notes.filter(n => 
        n.title?.toLowerCase().includes(query) ||
        n.content?.toLowerCase().includes(query)
      );
    }

    // Filter by category
    if (state.selectedCategoryId) {
      notes = notes.filter(n => n.categoryId === state.selectedCategoryId);
    }

    // Filter by tags
    if (state.selectedTagIds.length > 0) {
      notes = notes.filter(n => 
        n.tags?.some(t => state.selectedTagIds.includes(t.id))
      );
    }

    // Filter archived
    if (!state.showArchived) {
      notes = notes.filter(n => !n.isArchived);
    }

    // Sort: pinned first, then by updated date
    notes.sort((a, b) => {
      if (a.isPinned !== b.isPinned) {
        return a.isPinned ? -1 : 1;
      }
      return new Date(b.updatedAt) - new Date(a.updatedAt);
    });

    return notes;
  }

  async loadNotes() {
    store.setLoading(true);
    try {
      const notes = await noteService.getAll();
      store.setNotes(notes);
    } catch (error) {
      store.setError(error.message);
    } finally {
      store.setLoading(false);
    }
  }

  render() {
    const { notes, isLoading } = this.state;

    if (isLoading) {
      this.element.innerHTML = '<div class="loading">Loading notes...</div>';
      return;
    }

    if (notes.length === 0) {
      this.element.innerHTML = `
        <div class="empty-state">
          <p>No notes found</p>
          <button class="btn-create">Create your first note</button>
        </div>
      `;
      return;
    }

    this.element.innerHTML = `
      <div class="note-list">
        ${notes.map(note => `<div class="note-card-placeholder" data-id="${note.id}"></div>`).join('')}
      </div>
    `;

    // Render individual note cards
    this.noteCards.forEach(card => card.destroy());
    this.noteCards = [];

    notes.forEach(note => {
      const placeholder = this.element.querySelector(`[data-id="${note.id}"]`);
      if (placeholder) {
        const card = new NoteCard(placeholder, note);
        card.init();
        this.noteCards.push(card);
      }
    });
  }
}
```

## CSS Architecture

### CSS Variables (Design Tokens)
```css
/* css/styles.css */
:root {
  /* Colors - Dark Theme (Default) */
  --color-bg-primary: #1a1a2e;
  --color-bg-secondary: #16213e;
  --color-bg-tertiary: #0f3460;
  --color-bg-elevated: #252547;
  
  --color-text-primary: #eaeaea;
  --color-text-secondary: #a0a0a0;
  --color-text-muted: #6c6c6c;
  
  --color-accent-primary: #e94560;
  --color-accent-secondary: #533483;
  --color-accent-success: #4caf50;
  --color-accent-warning: #ff9800;
  --color-accent-error: #f44336;
  
  --color-border: #2a2a4a;
  --color-border-focus: #e94560;
  
  /* Typography */
  --font-family-base: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-family-mono: 'Fira Code', 'Consolas', monospace;
  
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
  --font-size-2xl: 1.5rem;
  
  /* Spacing */
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;
  --space-xl: 2rem;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.5);
  
  /* Borders */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  
  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-base: 250ms ease;
}
```

## Theme System

```javascript
// js/theme.js
class ThemeManager {
  constructor() {
    this.currentTheme = localStorage.getItem('theme') || 'dark';
    this.applyTheme(this.currentTheme);
  }

  applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    this.currentTheme = theme;
  }

  toggle() {
    const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
    this.applyTheme(newTheme);
  }
}

export const themeManager = new ThemeManager();
```

## Performance Optimizations

1. **Lazy Loading**: Components loaded on demand
2. **Virtual Scrolling**: For large note lists (future)
3. **Debounced Inputs**: Auto-save with debounce
4. **Memoization**: Computed values cached
5. **Event Delegation**: Single listeners for lists

## Accessibility

- Semantic HTML5 elements
- ARIA labels for interactive elements
- Keyboard navigation support
- Focus management
- Color contrast WCAG 2.1 AA compliant

---

*Last Updated: April 26, 2026*
